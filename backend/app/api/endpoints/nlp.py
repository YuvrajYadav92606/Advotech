from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.schemas.nlp import TextAnalysisRequest, DocumentNLPAnalysisResponse, EntityItem, PreprocessingSummary
from app.nlp.legal_entities import analyze_legal_text, extract_legal_rule_entities, extract_spacy_general_entities, resolve_entity_overlaps
from app.nlp.preprocessor import preprocess_document_text
from app.services.document_service import process_document_upload

router = APIRouter()

@router.post(
    "/analyze-text",
    response_model=DocumentNLPAnalysisResponse,
    summary="Analyze legal text for entities and structure",
    description="Preprocesses legal text, performs sentence segmentation, and extracts Indian legal entities, deadlines, and claims."
)
async def analyze_text_endpoint(payload: TextAnalysisRequest) -> DocumentNLPAnalysisResponse:
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty or whitespace."
        )
    return analyze_legal_text(payload.text)

@router.post(
    "/analyze-document",
    response_model=DocumentNLPAnalysisResponse,
    summary="Upload document and extract legal entities with page grounding",
    description="Upload a PDF or Word document to extract text and analyze entities with citation references."
)
async def analyze_document_endpoint(
    file: UploadFile = File(..., description="Legal document file (.pdf or .docx)")
) -> DocumentNLPAnalysisResponse:
    # 1. Process document upload and extract segments
    extraction = await process_document_upload(file)
    
    if not extraction.has_readable_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document contains no readable text layer (appears scanned). OCR is required before NLP analysis."
        )
        
    # 2. Extract entities segment-by-segment to preserve page/paragraph grounding
    all_entities: list[EntityItem] = []
    combined_sentences = []
    total_tokens = 0
    total_chars = 0
    
    for seg in extraction.segments:
        if not seg.content.strip():
            continue
            
        seg_summary = preprocess_document_text(seg.content, segment_ref=seg.reference_label)
        combined_sentences.extend(seg_summary.sentences)
        total_tokens += seg_summary.total_tokens
        total_chars += seg_summary.total_characters
        
        # Extract entities for this specific segment
        legal_ents = extract_legal_rule_entities(seg.content, segment_ref=seg.reference_label)
        spacy_ents = extract_spacy_general_entities(seg.content, segment_ref=seg.reference_label)
        resolved_seg_ents = resolve_entity_overlaps(legal_ents + spacy_ents)
        all_entities.extend(resolved_seg_ents)
        
    # 3. Group entities by category
    entities_by_category: dict[str, list[str]] = {}
    for ent in all_entities:
        if ent.label not in entities_by_category:
            entities_by_category[ent.label] = []
        if ent.text not in entities_by_category[ent.label]:
            entities_by_category[ent.label].append(ent.text)
            
    preprocessing = PreprocessingSummary(
        total_characters=total_chars,
        total_tokens=total_tokens,
        total_sentences=len(combined_sentences),
        sentences=combined_sentences
    )
    
    return DocumentNLPAnalysisResponse(
        document_name=extraction.filename,
        preprocessing=preprocessing,
        entities_by_category=entities_by_category,
        all_entities=all_entities,
        actionable_deadlines=entities_by_category.get("DEADLINE", []),
        monetary_obligations=entities_by_category.get("MONEY", [])
    )
