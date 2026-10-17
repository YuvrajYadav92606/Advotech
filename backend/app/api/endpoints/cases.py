from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.case_workspace import (
    CaseCreateRequest,
    CaseDocumentItem,
    CaseSummaryReport,
    CaseQARequest,
    CaseQAResponse,
    DocumentRole
)
from app.services.case_workspace_service import get_case_workspace_service, CaseWorkspaceService
from app.services.document_service import process_document_upload

router = APIRouter()

class AddTextDocumentRequest(BaseModel):
    filename: str = Field(..., description="Document filename, e.g. 'Contract.txt'")
    text_content: str = Field(..., min_length=10, description="Full text content of document")
    doc_role: Optional[DocumentRole] = Field(None, description="Optional explicit role")

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new multi-document case workspace",
    description="Initializes an isolated legal workspace for grouping notices, contracts, bank memos, and evidence relating to the same matter."
)
def create_case_workspace(
    request: CaseCreateRequest,
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
):
    case_id = service.create_case(
        title=request.title,
        description=request.description,
        category=request.category or "GENERAL_LEGAL_DISPUTE"
    )
    return {
        "case_id": case_id,
        "message": f"Case workspace '{request.title}' created successfully.",
        "category": request.category
    }

@router.get(
    "/",
    summary="List all active case workspaces",
    description="Returns metadata and document counts for all cases."
)
def list_case_workspaces(
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
):
    return {"cases": service.list_cases()}

@router.get(
    "/{case_id}",
    summary="Get case details and attached documents",
    description="Retrieves case metadata and list of attached documents."
)
def get_case_details(
    case_id: str,
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
):
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found."
        )
    return case

@router.post(
    "/{case_id}/upload-document",
    response_model=CaseDocumentItem,
    summary="Upload PDF or DOCX to a case workspace",
    description="Parses uploaded file and auto-identifies its legal role within the case."
)
async def upload_document_to_case(
    case_id: str,
    file: UploadFile = File(..., description="PDF or DOCX document to attach"),
    custom_role: Optional[DocumentRole] = Form(None, description="Optional explicit role override"),
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
) -> CaseDocumentItem:
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found."
        )

    extracted_doc = await process_document_upload(file)
    full_text = "\n\n".join([seg.content for seg in extracted_doc.segments if seg.content])

    try:
        return service.add_document_to_case(
            case_id=case_id,
            filename=file.filename,
            text_content=full_text,
            file_type=extracted_doc.file_type,
            custom_role=custom_role
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document into case: {str(e)}"
        )

@router.post(
    "/{case_id}/add-text-document",
    response_model=CaseDocumentItem,
    summary="Add text document directly to case",
    description="Directly attaches a text document to the case without uploading a binary file."
)
def add_text_document_to_case(
    case_id: str,
    request: AddTextDocumentRequest,
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
) -> CaseDocumentItem:
    try:
        return service.add_document_to_case(
            case_id=case_id,
            filename=request.filename,
            text_content=request.text_content,
            file_type=".txt",
            custom_role=request.doc_role
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get(
    "/{case_id}/analysis",
    response_model=CaseSummaryReport,
    summary="Perform multi-document cross-analysis",
    description="Generates cross-document timeline, detects evidentiary discrepancies, identifies missing records, and crafts advocate questions."
)
def analyze_case_workspace(
    case_id: str,
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
) -> CaseSummaryReport:
    try:
        return service.analyze_case(case_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post(
    "/{case_id}/ask",
    response_model=CaseQAResponse,
    summary="Ask a question across all documents in a case workspace",
    description="Cross-references multiple files in the case, identifies conflicts, and provides pinpoint multi-document citations."
)
def ask_case_workspace_question(
    case_id: str,
    request: CaseQARequest,
    service: CaseWorkspaceService = Depends(get_case_workspace_service)
) -> CaseQAResponse:
    try:
        return service.ask_case_question(case_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cross-document Q&A error: {str(e)}"
        )
