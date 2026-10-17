import re
from typing import List, Tuple, Dict, Optional
from app.schemas.simplification import SimplifiedClause, DocumentSimplificationResponse
from app.nlp.preprocessor import segment_sentences, clean_legal_text
from app.nlp.epistemic_parser import classify_sentence_epistemic
from app.nlp.legal_entities import extract_legal_rule_entities, extract_spacy_general_entities, resolve_entity_overlaps

# Legal jargon to plain language dictionary
LEGAL_PHRASE_MAPPINGS = [
    # Demands and calls to action
    (r"\byou\s+are\s+hereby\s+(?:called\s+upon|required|demanded|directed)\s+to\s+remit\b", "the sender requires you to pay"),
    (r"\byou\s+are\s+hereby\s+(?:called\s+upon|required|demanded|directed)\s+to\b", "the sender requires you to"),
    (r"\bthe\s+aforementioned\s+(?:sum|amount)\b", "the amount mentioned earlier"),
    (r"\baforementioned\b", "previously mentioned"),
    (r"\bthe\s+stipulated\s+period\s+of\b", "the specified deadline of"),
    (r"\bthe\s+stipulated\s+period\b", "the specified deadline"),
    (r"\bfailing\s+which\s+appropriate\s+legal\s+proceedings\s+shall\s+be\s+initiated\b", "or legal proceedings may follow"),
    (r"\bfailing\s+which\s+my\s+client\s+will\s+institute\s+criminal\s+proceedings\b", "or criminal proceedings may be filed against you"),
    (r"\bfailing\s+which\b", "if you do not do this"),
    (r"\bin\s+default\s+whereof\b", "if you fail to comply"),
    (r"\bforthwith\b", "immediately"),
    (r"\bwithout\s+prejudice\s+to\b", "without giving up any other legal rights"),
    (r"\binter\s+alia\b", "among other things"),
    (r"\bprima\s+facie\b", "at first glance"),
    (r"\bindemnify\s+and\s+hold\s+harmless\b", "compensate and protect from legal losses"),
    (r"\bforce\s+majeure\b", "unforeseeable emergency events beyond control"),
    (r"\bbona\s+fide\b", "honest and in good faith"),
    (r"\bmala\s+fide\b", "dishonest or in bad faith"),
    (r"\bhereinafter\s+referred\s+to\s+as\b", "referred to here as"),
    (r"\bstatus\s+quo\b", "the existing state of affairs without changes"),
    (r"\bmy\s+client\s+states\s+that\b", "the sender states that"),
    (r"\bunder\s+instructions\s+from\s+my\s+client\b", "on behalf of the sender"),
    (r"\bdeliberately\s+and\s+dishonestly\b", "intentionally (as claimed by the sender)"),
    (r"\bdischarge\s+your\s+legal\s+liability\b", "pay your legal debt or dues")
]

def simplify_english_sentence(sentence: str, epistemic_type: str) -> str:
    """
    Transforms formal legal prose into simple, accessible English
    while preserving epistemic clarity (never turning allegations into facts).
    """
    simplified = sentence
    
    # Clean introductory prefixes like 'Sir,'
    simplified = re.sub(r"^sir,\s*", "", simplified, flags=re.IGNORECASE)
    
    # 1. Apply phrase transformations
    for pattern, replacement in LEGAL_PHRASE_MAPPINGS:
        simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)
        
    # 2. Epistemic re-framing for allegations
    if epistemic_type == "ALLEGATION":
        has_epistemic_frame = re.search(r"\b(?:claims|alleges|states|the sender states)\b", simplified, re.IGNORECASE)
        if not has_epistemic_frame:
            simplified = f"The sender claims that {simplified[0].lower() + simplified[1:].rstrip('.')}"
            
    # 3. Clean capitalization and spacing
    simplified = re.sub(r"\s+", " ", simplified).strip()
    if simplified and not simplified.endswith("."):
        simplified += "."
    if simplified:
        simplified = simplified[0].upper() + simplified[1:]
        
    return simplified

def simplify_hindi_sentence(sentence: str, epistemic_type: str, amounts: List[str], deadlines: List[str]) -> str:
    """
    Generates a natural, clear Hindi explanation (not hyper-formal legal Sanskrit).
    """
    text_lower = sentence.lower()
    amount_str = f" {amounts[0]}" if amounts else ""
    deadline_str = f" {deadlines[0]}" if deadlines else " तय समय के भीतर"
    
    if epistemic_type == "DEMAND_OR_OBLIGATION":
        if "pay" in text_lower or "remit" in text_lower:
            return f"भेजने वाले ने आपसे{amount_str} का भुगतान{deadline_str} करने की मांग की है, ऐसा न करने पर कानूनी कार्यवाही की चेतावनी दी गई है।"
        elif "vacate" in text_lower:
            return f"मकान/परिसर को{deadline_str} खाली करने और बकाया राशि चुकाने की मांग की गई है।"
        return f"आपको निर्देश दिया गया है कि तय समय में इस मांग का पालन करें, अन्यथा कानूनी कार्यवाही हो सकती है।"
        
    elif epistemic_type == "ALLEGATION":
        return f"भेजने वाले का यह आरोप (दावा) है कि आपने जानबूझकर अपनी कानूनी देनदारी या दायित्व का पालन नहीं किया है।"
        
    elif epistemic_type == "LEGAL_REASONING":
        return "इस दस्तावेज़ में संबंधित कानूनी धाराओं और कानूनों का हवाला दिया गया है जिसके तहत कार्यवाही की जा सकती है।"
        
    else:
        if "cheque" in text_lower and ("dishonour" in text_lower or "unpaid" in text_lower):
            return f"यह चेक के बैंक द्वारा बाउंस होने (अनादरित होने) से संबंधित तथ्य है।"
        return "दस्तावेज़ में उल्लिखित सामान्य पृष्ठभूमि एवं लेनदेन का विवरण।"

def simplify_hinglish_sentence(sentence: str, epistemic_type: str, amounts: List[str], deadlines: List[str]) -> str:
    """
    Generates a conversational Hinglish explanation.
    """
    text_lower = sentence.lower()
    amount_str = f" {amounts[0]}" if amounts else ""
    deadline_str = f" {deadlines[0]}" if deadlines else " diye gaye time ke andar"
    
    if epistemic_type == "DEMAND_OR_OBLIGATION":
        if "pay" in text_lower or "remit" in text_lower:
            return f"Sender aapse{amount_str} pay karne ki demand kar raha hai{deadline_str}. Agar pay nahi kiya toh legal action/court case ho sakta hai."
        elif "vacate" in text_lower:
            return f"Property ko{deadline_str} khali karne aur pending dues clear karne ko kaha gaya hai."
        return f"Aapko warning di gayi hai ki diye gaye time me compliance karein, warna legal proceedings shuru hogi."
        
    elif epistemic_type == "ALLEGATION":
        return "Sender ka yeh claim/allegation hai ki aapne intentionally apna obligation poora nahi kiya hai."
        
    elif epistemic_type == "LEGAL_REASONING":
        return "Isme legal sections aur acts ka reference diya gaya hai jiske under court case file ho sakta hai."
        
    else:
        return "Document me transaction aur background facts ka mention kiya gaya hai."

def verify_fidelity(original: str, simplified: str) -> Tuple[bool, List[str]]:
    """
    Verifies that critical entities (monetary amounts and deadlines)
    present in the original sentence were NOT accidentally lost in simplification.
    Normalizes numeric punctuation for robust comparison.
    """
    preserved_entities = []
    sim_normalized = re.sub(r"[,/\s\-]", "", simplified)
    
    # 1. Check explicit currency matches
    money_matches = re.findall(r"\b(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d+)?(?:/-)?\b", original)
    for m in money_matches:
        digits_only = re.sub(r"[^\d]", "", m)
        if digits_only and len(digits_only) >= 2:
            if digits_only in sim_normalized:
                preserved_entities.append(m.strip())
            else:
                return False, preserved_entities
                
    # 2. Check deadline mentions
    deadline_matches = re.findall(r"\b\d+\s+days\b", original, re.IGNORECASE)
    for d in deadline_matches:
        if d.lower() in simplified.lower():
            preserved_entities.append(d)
        else:
            return False, preserved_entities
            
    return True, preserved_entities

def simplify_document_clauses(text: str, segment_ref: str = None) -> DocumentSimplificationResponse:
    """
    End-to-end clause simplification pipeline:
    1. Sentence segmentation with abbreviation protection
    2. Epistemic classification (Fact vs Allegation vs Demand)
    3. Trilingual simplification (English, Hindi, Hinglish)
    4. Entity fidelity verification
    5. Executive citizen-friendly summary
    """
    cleaned = clean_legal_text(text)
    sentences = segment_sentences(cleaned, segment_ref=segment_ref)
    
    simplified_clauses: List[SimplifiedClause] = []
    fidelity_passes = 0
    
    # Extract document-wide entities for context
    legal_ents = extract_legal_rule_entities(cleaned)
    spacy_ents = extract_spacy_general_entities(cleaned)
    resolved_ents = resolve_entity_overlaps(legal_ents + spacy_ents)
    
    amounts = [e.text for e in resolved_ents if e.label == "MONEY"]
    deadlines = [e.text for e in resolved_ents if e.label == "DEADLINE"]
    
    for sent in sentences:
        epistemic_type, _ = classify_sentence_epistemic(sent.text)
        
        sim_en = simplify_english_sentence(sent.text, epistemic_type)
        sim_hi = simplify_hindi_sentence(sent.text, epistemic_type, amounts, deadlines)
        sim_hinglish = simplify_hinglish_sentence(sent.text, epistemic_type, amounts, deadlines)
        
        passed, preserved = verify_fidelity(sent.text, sim_en)
        if passed:
            fidelity_passes += 1
            
        simplified_clauses.append(
            SimplifiedClause(
                clause_index=sent.index,
                original_text=sent.text,
                simplified_english=sim_en,
                simplified_hindi=sim_hi,
                simplified_hinglish=sim_hinglish,
                epistemic_type=epistemic_type,
                preserved_entities=preserved,
                fidelity_check_passed=passed,
                segment_reference=sent.segment_reference
            )
        )
        
    avg_fidelity = (fidelity_passes / len(sentences)) * 100.0 if sentences else 100.0
    
    # Executive summaries
    amount_disp = amounts[0] if amounts else "the demanded amount"
    deadline_disp = deadlines[0] if deadlines else "the specified deadline"
    
    exec_en = (
        f"In simple words: The sender claims you owe {amount_disp} and requires you to settle this {deadline_disp}. "
        f"The sender states that legal proceedings will be initiated if not settled. Note that allegations made in this document "
        f"are the sender's claims, not court-established facts."
    )
    exec_hi = (
        f"सरल शब्दों में: भेजने वाले का दावा है कि आपकी ओर {amount_disp} की देनदारी है और उन्होंने इसे {deadline_disp} चुकाने को कहा है। "
        f"भुगतान न करने पर कानूनी केस करने की चेतावनी दी गई है। ध्यान रहे कि ये केवल नोटिस भेजने वाले के आरोप हैं, अदालत का फैसला नहीं।"
    )
    exec_hinglish = (
        f"Aasaan shabdon me: Sender ka claim hai ki aapko {amount_disp} pay karna hai {deadline_disp}. "
        f"Agar pay nahi kiya toh court case ya legal action ho sakta hai. Yeh sirf sender ke allegations hain, court ka decision nahi."
    )
    
    return DocumentSimplificationResponse(
        total_clauses=len(simplified_clauses),
        clauses=simplified_clauses,
        executive_summary_english=exec_en,
        executive_summary_hindi=exec_hi,
        executive_summary_hinglish=exec_hinglish,
        average_fidelity_score=round(avg_fidelity, 1)
    )
