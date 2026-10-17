import re
from typing import List
from app.schemas.nlp import SentenceItem, PreprocessingSummary

# Common legal abbreviations in Indian jurisprudence that should NOT trigger sentence breaks
LEGAL_ABBREVIATION_PATTERNS = [
    r"\bAdv\.", r"\bHon'ble", r"\bSh\.", r"\bSmt\.", r"\bMr\.", r"\bMrs\.", r"\bMs\.", r"\bDr\.",
    r"\bvs\.", r"\bv\.", r"\bSec\.", r"\bSecs\.", r"\bu/s", r"\br/w", r"\bArt\.", r"\bArts\.",
    r"\bNo\.", r"\bNos\.", r"\bPvt\.", r"\bLtd\.", r"\bCo\.", r"\bCorp\.", r"\bLLP\.",
    r"\bCr\.P\.C\.", r"\bC\.P\.C\.", r"\bI\.P\.C\.", r"\bN\.I\.\s*Act", r"\bSCC\b", r"\bAIR\b", r"\bSCR\b",
    r"\bRs\."
]

def clean_legal_text(raw_text: str) -> str:
    """
    Normalizes erratic whitespace, legal typographical quotes, and unicode anomalies
    frequently encountered in Indian legal notices and judgments.
    """
    if not raw_text:
        return ""
        
    text = raw_text
    
    # 1. Normalize line endings and non-breaking spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ").replace("\u200b", "")
    
    # 2. Standardize quotation marks
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r"[''']", "'", text)
    
    # 3. Collapse multiple spaces while preserving single newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    
    return cleaned

def segment_sentences(text: str, segment_ref: str = None) -> List[SentenceItem]:
    """
    Splits legal text into grammatical sentences while protecting legal abbreviations
    such as 'Sec. 138', 'v.', 'Adv. Sharma', 'Pvt. Ltd.', 'Rs. 2,50,000'.
    Uses character masking to prevent punctuation splits without token-shifting artifacts.
    """
    cleaned = clean_legal_text(text)
    if not cleaned:
        return []
        
    masked_text = cleaned
    
    # Mask dots inside legal abbreviations using ASCII Unit Separator (\x1f)
    for pattern_str in LEGAL_ABBREVIATION_PATTERNS:
        regex = re.compile(pattern_str, re.IGNORECASE)
        masked_text = regex.sub(lambda m: m.group(0).replace(".", "\x1f"), masked_text)
            
    # Segment by sentence-ending punctuation (.!?) followed by whitespace or double newline
    raw_splits = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'(])|\n{2,}', masked_text)
    
    sentences: List[SentenceItem] = []
    sent_idx = 0
    
    for raw_sent in raw_splits:
        restored = raw_sent.replace("\x1f", ".").strip()
        if not restored:
            continue
            
        tokens = tokenize_legal_text(restored)
        sentences.append(
            SentenceItem(
                index=sent_idx,
                text=restored,
                token_count=len(tokens),
                segment_reference=segment_ref
            )
        )
        sent_idx += 1
        
    return sentences

def tokenize_legal_text(text: str) -> List[str]:
    """
    Tokenizes legal sentences into tokens while preserving:
    - Currency expressions: 'Rs.', 'INR', 'Rs. 2,50,000/-', '₹50,000'
    - Section references: 'u/s', 'Section 138', 'Art. 21'
    - Standard words and punctuation
    """
    token_pattern = re.compile(
        r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d+)?(?:/-)?|'  # Currency
        r'u/s\s*\d+[A-Za-z]*|'                        # u/s 138
        r'Section\s+\d+[A-Za-z]*|'                    # Section 138
        r'\b\w+(?:[\'-]\w+)*\b|'                      # Words with hyphens/apostrophes
        r'[^\w\s]'                                    # Individual punctuation marks
    )
    return token_pattern.findall(text)

def preprocess_document_text(text: str, segment_ref: str = None) -> PreprocessingSummary:
    """
    Executes full preprocessing and returns detailed metrics.
    """
    cleaned = clean_legal_text(text)
    sentences = segment_sentences(cleaned, segment_ref=segment_ref)
    all_tokens = tokenize_legal_text(cleaned)
    
    return PreprocessingSummary(
        total_characters=len(cleaned),
        total_tokens=len(all_tokens),
        total_sentences=len(sentences),
        sentences=sentences
    )
