import re
from typing import List, Dict, Tuple, Optional
import spacy
from app.schemas.nlp import EntityItem, DocumentNLPAnalysisResponse, PreprocessingSummary
from app.nlp.preprocessor import preprocess_document_text

# Lazy-loaded spaCy model
_nlp_model = None

def get_spacy_nlp():
    """
    Singleton loader for spaCy general-purpose model.
    """
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
        except Exception:
            # Fallback blank English model if download was somehow interrupted
            _nlp_model = spacy.blank("en")
    return _nlp_model

# =====================================================================
# Indian Legal Pattern Rules (Regex & Context Heuristics)
# =====================================================================

LEGAL_PATTERNS = {
    "COURT": [
        r"\b(?:Supreme\s+Court\s+of\s+India|Hon'ble\s+Supreme\s+Court)\b",
        r"\b(?:High\s+Court\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|Hon'ble\s+High\s+Court)\b",
        r"\b(?:District\s+(?:&|and)\s+Sessions\s+Court|District\s+Court|Sessions\s+Court)\b",
        r"\b(?:Chief\s+Judicial\s+Magistrate|Metropolitan\s+Magistrate|Civil\s+Judge)\b",
        r"\b(?:National\s+Company\s+Law\s+Tribunal|NCLT|NCLAT|DRT|DRAT|RERA|NCDRC)\b"
    ],
    "LEGAL_SECTION": [
        r"\b(?:Section|Sec\.|u/s|Sections|Secs\.)\s+\d+[A-Za-z]*(?:\s*\([0-9a-zA-Z]+\))*(?:\s*(?:to|and|-)\s*\d+[A-Za-z]*)*\b",
        r"\b(?:Article|Art\.)\s+\d+[A-Za-z]*(?:\s*\([0-9a-zA-Z]+\))*\b",
        r"\b(?:Order\s+[A-Z0-9]+(?:\s+Rule\s+[0-9A-Z]+)?)\b",
        r"\bClause\s+\d+(?:\.\d+)*\b"
    ],
    "LAW": [
        r"\b(?:Negotiable\s+Instruments\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Indian\s+Penal\s+Code(?:,\s*\d{4})?|IPC)\b",
        r"\b(?:Code\s+of\s+Criminal\s+Procedure(?:,\s*\d{4})?|Cr\.?P\.?C\.?)\b",
        r"\b(?:Code\s+of\s+Civil\s+Procedure(?:,\s*\d{4})?|C\.?P\.?C\.?)\b",
        r"\b(?:Indian\s+Contract\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Arbitration\s+and\s+Conciliation\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Consumer\s+Protection\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Information\s+Technology\s+Act(?:,\s*\d{4})?|IT\s+Act)\b",
        r"\b(?:Companies\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Insolvency\s+and\s+Bankruptcy\s+Code(?:,\s*\d{4})?|IBC)\b",
        r"\b(?:Transfer\s+of\s+Property\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Specific\s+Relief\s+Act(?:,\s*\d{4})?)\b",
        r"\b(?:Constitution\s+of\s+India)\b",
        r"\b(?:Bharatiya\s+Nyaya\s+Sanhita(?:,\s*\d{4})?|BNS)\b",
        r"\b(?:Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita(?:,\s*\d{4})?|BNSS)\b",
        r"\b(?:Bharatiya\s+Sakshya\s+Adhiniyam(?:,\s*\d{4})?|BSA)\b"
    ],
    "DEADLINE": [
        r"\bwithin\s+(?:\d+|fifteen|thirty|seven|forty-five|sixty|ninety)\s+(?:days|hours|weeks|months)\b(?:\s+from\s+[^\.,;\n]+)?",
        r"\bstipulated\s+period\s+of\s+\d+\s+(?:days|weeks|months)\b",
        r"\bperiod\s+of\s+\d+\s+(?:days|weeks|months|years)\b",
        r"\bon\s+or\s+before\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+(?:\s+\d{4})?\b"
    ],
    "CASE_NUMBER": [
        r"\b(?:W\.?P\.?(?:\([A-Za-z]+\))?|Crl\.?\s*A\.?|Civil\s+Appeal|SLP(?:\([A-Za-z]+\))?|CS\s*(?:\([A-Za-z]+\))?|O\.?M\.?P\.?)\s*(?:No\.?)?\s*\d+\s*(?:of|/)\s*\d{4}\b",
        r"\bFIR\s+No\.?\s*\d+\s*(?:of|/)\s*\d{4}\b"
    ],
    "MONEY": [
        r"\b(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{1,2})?(?:\s*(?:lakhs?|crores?|/-))?\b",
        r"\b(?:Rupees|sum\s+of\s+Rs\.?)\s+[A-Za-z\s]+(?:only|/-)?\b"
    ]
}

def extract_legal_rule_entities(text: str, segment_ref: str = None) -> List[EntityItem]:
    """
    Extracts high-precision Indian legal entities using targeted domain heuristics.
    """
    entities: List[EntityItem] = []
    
    for category, patterns in LEGAL_PATTERNS.items():
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                extracted_str = match.group(0).strip()
                entities.append(
                    EntityItem(
                        text=extracted_str,
                        label=category,
                        start_char=match.start(),
                        end_char=match.end(),
                        source="legal_pattern_engine",
                        segment_reference=segment_ref
                    )
                )
    return entities

def extract_spacy_general_entities(text: str, segment_ref: str = None) -> List[EntityItem]:
    """
    Extracts entities using the pretrained general spaCy statistical model.
    Maps spaCy's standard NER tags (PERSON, ORG, GPE, DATE, MONEY) into clean types.
    """
    nlp = get_spacy_nlp()
    doc = nlp(text)
    entities: List[EntityItem] = []
    
    spacy_label_map = {
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "GPE": "LOCATION",
        "DATE": "DATE",
        "MONEY": "MONEY"
    }
    
    for ent in doc.ents:
        if ent.label_ in spacy_label_map:
            entities.append(
                EntityItem(
                    text=ent.text.strip(),
                    label=spacy_label_map[ent.label_],
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    source="spacy_statistical",
                    segment_reference=segment_ref
                )
            )
    return entities

def resolve_entity_overlaps(entities: List[EntityItem]) -> List[EntityItem]:
    """
    Resolves overlaps between statistical general NER and legal pattern extraction.
    Rule: Domain-specific legal pattern extraction ALWAYS takes priority over generic NER.
    (e.g., 'High Court of Delhi' labeled as COURT overrides spaCy's generic ORG).
    """
    # Sort entities: legal_pattern_engine first, then by longer span
    sorted_ents = sorted(
        entities,
        key=lambda e: (
            0 if e.source == "legal_pattern_engine" else 1,
            -(e.end_char - e.start_char)
        )
    )
    
    final_entities: List[EntityItem] = []
    occupied_spans: List[Tuple[int, int]] = []
    
    for ent in sorted_ents:
        # Check overlap
        is_overlapping = any(
            not (ent.end_char <= start or ent.start_char >= end)
            for start, end in occupied_spans
        )
        if not is_overlapping:
            occupied_spans.append((ent.start_char, ent.end_char))
            final_entities.append(ent)
            
    # Sort chronologically by start character position in text
    final_entities.sort(key=lambda e: e.start_char)
    return final_entities

def analyze_legal_text(text: str, document_name: str = None, segment_ref: str = None) -> DocumentNLPAnalysisResponse:
    """
    Full end-to-end NLP analysis pipeline:
    1. Preprocessing & sentence segmentation
    2. Statistical general NER (spaCy)
    3. Indian legal domain pattern engine
    4. Span conflict resolution & category aggregation
    5. Actionable deadline and monetary claim extraction
    """
    preprocessing = preprocess_document_text(text, segment_ref=segment_ref)
    
    # Run both engines
    legal_ents = extract_legal_rule_entities(text, segment_ref=segment_ref)
    spacy_ents = extract_spacy_general_entities(text, segment_ref=segment_ref)
    
    # Merge and resolve overlaps
    all_resolved = resolve_entity_overlaps(legal_ents + spacy_ents)
    
    # Group entities by category
    entities_by_category: Dict[str, List[str]] = {}
    for ent in all_resolved:
        if ent.label not in entities_by_category:
            entities_by_category[ent.label] = []
        if ent.text not in entities_by_category[ent.label]:
            entities_by_category[ent.label].append(ent.text)
            
    # Extract high-priority actionable items for citizens
    actionable_deadlines = entities_by_category.get("DEADLINE", [])
    monetary_obligations = entities_by_category.get("MONEY", [])
    
    return DocumentNLPAnalysisResponse(
        document_name=document_name,
        preprocessing=preprocessing,
        entities_by_category=entities_by_category,
        all_entities=all_resolved,
        actionable_deadlines=actionable_deadlines,
        monetary_obligations=monetary_obligations
    )
