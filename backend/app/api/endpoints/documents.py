from fastapi import APIRouter, File, UploadFile
from app.schemas.document import DocumentExtractionResponse
from app.services.document_service import process_document_upload

router = APIRouter()

@router.post(
    "/upload",
    response_model=DocumentExtractionResponse,
    summary="Upload and extract text from legal document",
    description="Upload a PDF or DOCX legal document to extract structured text with page/section references."
)
async def upload_document(
    file: UploadFile = File(..., description="Legal document file (.pdf or .docx)")
) -> DocumentExtractionResponse:
    return await process_document_upload(file)
