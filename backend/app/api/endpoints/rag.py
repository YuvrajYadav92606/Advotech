from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.schemas.rag import (
    RAGQuestionRequest,
    RAGAnswerResponse,
    EngineStatusResponse
)
from app.services.rag_service import get_rag_service, RAGService
from app.services.document_service import process_document_upload

router = APIRouter()

@router.post(
    "/ask",
    response_model=RAGAnswerResponse,
    summary="Ask legal question with grounded retrieval and citation verification",
    description="Combines user question, optional document text, relevant Indian statutes, and court precedents into an epistemically verified answer."
)
def ask_legal_question(
    request: RAGQuestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> RAGAnswerResponse:
    """
    RAG endpoint for textual queries + optional document text.
    """
    try:
        return rag_service.answer_question(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Legal question answering error: {str(e)}"
        )

@router.post(
    "/ask-document",
    response_model=RAGAnswerResponse,
    summary="Ask question directly against an uploaded PDF or DOCX document",
    description="Uploads a PDF or DOCX file, extracts structured text, and runs full epistemic RAG question answering."
)
async def ask_document_file(
    file: UploadFile = File(..., description="PDF or DOCX document to query"),
    question: str = Form(..., description="User's plain language question about the document"),
    language: str = Form("en", description="Output language ('en', 'hi', 'hinglish')"),
    max_sources: int = Form(4, description="Maximum number of external legal sources to retrieve"),
    rag_service: RAGService = Depends(get_rag_service)
) -> RAGAnswerResponse:
    """
    Direct document file Q&A via RAG pipeline.
    """
    extracted_doc = await process_document_upload(file)
    full_text = "\n\n".join([seg.content for seg in extracted_doc.segments if seg.content])
    
    request = RAGQuestionRequest(
        question=question,
        document_text=full_text,
        language=language,
        max_sources=max_sources
    )
    
    return rag_service.answer_question(request)

@router.get(
    "/engine-status",
    response_model=EngineStatusResponse,
    summary="Check status of RAG synthesis engine and models",
    description="Inspects whether online Google Gemini API or offline zero-cost grounded synthesizer is currently active."
)
def get_engine_status(
    rag_service: RAGService = Depends(get_rag_service)
) -> EngineStatusResponse:
    connector = rag_service.llm_connector
    is_gemini = connector.is_gemini_configured()
    
    engine_name = f"Google Gemini API ({connector.model_name})" if is_gemini else "Advo टेक Grounded Extractive Synthesizer (Offline Mode)"
    
    return EngineStatusResponse(
        engine_name=engine_name,
        gemini_api_configured=is_gemini,
        offline_fallback_ready=True,
        supported_languages=["en", "hi", "hinglish"],
        capabilities=[
            "Strict Anti-Hallucination Guardrails",
            "Epistemic Boundary Separation (Facts vs Allegations vs Inferences)",
            "Verbatim Inline Citations [Doc: ...], [Statute: ...], [Case: ...]",
            "Trilingual Explanations (English, Hindi, Hinglish)",
            "Zero-Cost Offline Fallback Mode"
        ]
    )
