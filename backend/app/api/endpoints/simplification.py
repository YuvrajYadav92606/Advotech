from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.schemas.simplification import SimplificationRequest, DocumentSimplificationResponse, SimplifiedClause
from app.nlp.simplifier import simplify_document_clauses
from app.services.document_service import process_document_upload
from app.nlp.preprocessor import clean_legal_text

router = APIRouter()

@router.post(
    "/text",
    response_model=DocumentSimplificationResponse,
    summary="Simplify legal text snippet",
    description="Translates complex legalese into simple English, Hindi, and Hinglish, preserving allegations and deadlines."
)
async def simplify_text_endpoint(payload: SimplificationRequest) -> DocumentSimplificationResponse:
    cleaned = clean_legal_text(payload.text)
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text payload cannot be empty."
        )
    return simplify_document_clauses(cleaned)

@router.post(
    "/document",
    response_model=DocumentSimplificationResponse,
    summary="Upload document and generate trilingual simplification",
    description="Upload a PDF or Word document to get clause-by-clause simplification with page citations."
)
async def simplify_document_endpoint(
    file: UploadFile = File(..., description="Legal document file (.pdf or .docx)")
) -> DocumentSimplificationResponse:
    extraction = await process_document_upload(file)
    
    if not extraction.has_readable_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document contains no readable text layer (appears scanned). OCR is required."
        )
        
    all_clauses: list[SimplifiedClause] = []
    total_passes = 0
    
    # Process segment by segment to preserve page references
    for seg in extraction.segments:
        if not seg.content.strip():
            continue
        seg_res = simplify_document_clauses(seg.content, segment_ref=seg.reference_label)
        all_clauses.extend(seg_res.clauses)
        total_passes += sum(1 for c in seg_res.clauses if c.fidelity_check_passed)
        
    # Full document executive summary
    full_text = "\n\n".join(seg.content for seg in extraction.segments if seg.content)
    full_doc_res = simplify_document_clauses(full_text)
    
    avg_fidelity = (total_passes / len(all_clauses)) * 100.0 if all_clauses else 100.0
    
    return DocumentSimplificationResponse(
        document_name=extraction.filename,
        total_clauses=len(all_clauses),
        clauses=all_clauses,
        executive_summary_english=full_doc_res.executive_summary_english,
        executive_summary_hindi=full_doc_res.executive_summary_hindi,
        executive_summary_hinglish=full_doc_res.executive_summary_hinglish,
        average_fidelity_score=round(avg_fidelity, 1)
    )
