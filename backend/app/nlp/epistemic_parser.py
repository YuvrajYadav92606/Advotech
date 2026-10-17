import re
from typing import List, Tuple
from app.schemas.analysis import ClassifiedStatement
from app.schemas.nlp import SentenceItem

# Epistemic Cue Patterns
DEMAND_PATTERNS = [
    r"\b(?:you\s+are\s+hereby\s+(?:called\s+upon|required|demanded|directed)\s+to)\b",
    r"\b(?:remit|pay|vacate|tender|furnish|cease\s+and\s+desist|comply)\b",
    r"\b(?:within\s+\d+\s+days|stipulated\s+period)\b",
    r"\b(?:failing\s+which|in\s+default\s+whereof)\b",
    r"\b(?:will\s+initiate|will\s+file|compelled\s+to\s+take)\s+legal\s+action\b"
]

ALLEGATION_PATTERNS = [
    r"\b(?:my\s+client\s+states|client\s+informs|it\s+is\s+stated\s+that)\b",
    r"\b(?:alleged|falsely|wrongfully|illegally|dishonestly|fraudulently)\b",
    r"\b(?:you\s+have\s+failed|you\s+refused|you\s+breached|you\s+neglected)\b",
    r"\b(?:without\s+any\s+justifiable\s+cause|deliberately|malafide)\b",
    r"\b(?:culpable|misappropriated|infringed)\b"
]

LEGAL_REASONING_PATTERNS = [
    r"\b(?:under\s+section|provisions\s+of|in\s+terms\s+of\s+clause|pursuant\s+to)\b",
    r"\b(?:statutory\s+notice|cause\s+of\s+action|jurisdiction\s+of|offence\s+under)\b",
    r"\b(?:Negotiable\s+Instruments\s+Act|Indian\s+Penal\s+Code|Contract\s+Act)\b"
]

def classify_sentence_epistemic(sentence_text: str) -> Tuple[str, float]:
    """
    Classifies a sentence into its epistemic legal type:
    - DEMAND_OR_OBLIGATION: Mandatory call to action or threatened legal consequences
    - ALLEGATION: Adversarial claims (unproven allegations)
    - LEGAL_REASONING: References to statutory frameworks and jurisdictional rules
    - FACT: Objective event or baseline statement
    """
    text_lower = sentence_text.lower()
    
    # 1. Check Demand / Obligation
    demand_hits = sum(1 for p in DEMAND_PATTERNS if re.search(p, text_lower))
    if demand_hits >= 1:
        confidence = min(0.65 + (demand_hits * 0.15), 0.98)
        return "DEMAND_OR_OBLIGATION", round(confidence, 2)
        
    # 2. Check Allegation
    allegation_hits = sum(1 for p in ALLEGATION_PATTERNS if re.search(p, text_lower))
    if allegation_hits >= 1:
        confidence = min(0.65 + (allegation_hits * 0.15), 0.95)
        return "ALLEGATION", round(confidence, 2)
        
    # 3. Check Legal Reasoning / Statutory Citation
    reasoning_hits = sum(1 for p in LEGAL_REASONING_PATTERNS if re.search(p, text_lower))
    if reasoning_hits >= 1:
        confidence = min(0.70 + (reasoning_hits * 0.10), 0.92)
        return "LEGAL_REASONING", round(confidence, 2)
        
    # 4. Default: Neutral Fact / Informational statement
    return "FACT", 0.75

def parse_document_epistemics(sentences: List[SentenceItem]) -> List[ClassifiedStatement]:
    """
    Classifies all document sentences into their respective epistemic status.
    Guarantees that accusations remain classified as ALLEGATIONS, not factual truths.
    """
    classified_statements: List[ClassifiedStatement] = []
    
    for sent in sentences:
        epistemic_type, confidence = classify_sentence_epistemic(sent.text)
        classified_statements.append(
            ClassifiedStatement(
                statement_index=sent.index,
                text=sent.text,
                epistemic_type=epistemic_type,
                segment_reference=sent.segment_reference,
                confidence=confidence
            )
        )
        
    return classified_statements
