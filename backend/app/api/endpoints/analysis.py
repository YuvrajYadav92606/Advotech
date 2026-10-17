from fastapi import APIRouter, File, UploadFile, HTTPException, status
from app.schemas.analysis import StructuredLegalAnalysisReport
from app.schemas.nlp import TextAnalysisRequest
from app.services.analysis_service import generate_structured_analysis
from app.nlp.preprocessor import preprocess_document_text
from app.nlp.legal_entities import extract_legal_rule_entities, extract_spacy_general_entities, resolve_entity_overlaps
from app.nlp.classifier import get_legal_classifier
from app.nlp.epistemic_parser import parse_document_epistemics
from app.services.analysis_service import (
    extract_parties,
    identify_legal_issues,
    detect_ambiguities_and_missing_info,
    generate_advocate_questions,
    generate_plain_summary
)

router = APIRouter()

@router.post(
    "/document",
    response_model=StructuredLegalAnalysisReport,
    summary="Upload document and generate structured legal analysis report",
    description="Processes legal document, classifies its category with TF-IDF, parses facts vs allegations, and identifies issues & questions."
)
async def analyze_document_structured(
    file: UploadFile = File(..., description="Legal document file (.pdf or .docx)")
) -> StructuredLegalAnalysisReport:
    return await generate_structured_analysis(file)

@router.post(
    "/text",
    response_model=StructuredLegalAnalysisReport,
    summary="Analyze legal text and generate structured report",
    description="Analyzes legal text snippet, classifies its category, parses facts vs allegations, and provides strategic legal questions."
)
async def analyze_text_structured(payload: TextAnalysisRequest) -> StructuredLegalAnalysisReport:
    full_text = payload.text.strip()
    if not full_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text payload cannot be empty."
        )
        
    preproc = preprocess_document_text(full_text)
    
    legal_ents = extract_legal_rule_entities(full_text)
    spacy_ents = extract_spacy_general_entities(full_text)
    resolved_ents = resolve_entity_overlaps(legal_ents + spacy_ents)
    
    entities_by_cat = {}
    for e in resolved_ents:
        if e.label not in entities_by_cat:
            entities_by_cat[e.label] = []
        if e.text not in entities_by_cat[e.label]:
            entities_by_cat[e.label].append(e.text)
            
    classifier = get_legal_classifier()
    cat_key, cat_name, confidence, top_keywords = classifier.predict(full_text)
    
    classified_statements = parse_document_epistemics(preproc.sentences)
    facts = [s.text for s in classified_statements if s.epistemic_type == "FACT"]
    allegations = [s.text for s in classified_statements if s.epistemic_type == "ALLEGATION"]
    demands = [s.text for s in classified_statements if s.epistemic_type == "DEMAND_OR_OBLIGATION"]
    
    sender, recipient = extract_parties(full_text, resolved_ents)
    
    deadlines = entities_by_cat.get("DEADLINE", [])
    amounts = entities_by_cat.get("MONEY", [])
    sections = entities_by_cat.get("LEGAL_SECTION", [])
    laws = entities_by_cat.get("LAW", [])
    
    legal_issues = identify_legal_issues(cat_key, laws, sections)
    ambiguities = detect_ambiguities_and_missing_info(cat_key, full_text)
    advocate_questions = generate_advocate_questions(cat_key, deadlines, amounts)
    summary = generate_plain_summary(cat_name, sender, recipient, amounts, deadlines)
    
    return StructuredLegalAnalysisReport(
        document_name="Text Input Snippet",
        document_category=cat_key,
        category_display_name=cat_name,
        classification_confidence=confidence,
        top_predictive_keywords=top_keywords,
        summary=summary,
        sender_or_claimant=sender,
        recipient_or_respondent=recipient,
        facts=facts[:5],
        allegations=allegations[:5],
        demands_and_obligations=demands[:5],
        actionable_deadlines=deadlines,
        monetary_claims=amounts,
        statutory_provisions_invoked=sections + laws,
        legal_issues=legal_issues,
        missing_information_or_ambiguities=ambiguities,
        suggested_advocate_questions=advocate_questions,
        entities_by_category=entities_by_cat
    )
