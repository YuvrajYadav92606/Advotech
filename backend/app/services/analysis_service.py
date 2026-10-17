import re
from typing import List, Dict, Optional, Tuple
from fastapi import UploadFile
from app.schemas.analysis import StructuredLegalAnalysisReport, LegalIssue, ClassifiedStatement
from app.schemas.nlp import EntityItem
from app.services.document_service import process_document_upload
from app.nlp.preprocessor import preprocess_document_text
from app.nlp.legal_entities import extract_legal_rule_entities, extract_spacy_general_entities, resolve_entity_overlaps
from app.nlp.classifier import get_legal_classifier
from app.nlp.epistemic_parser import parse_document_epistemics

def extract_parties(text: str, entities: List[EntityItem]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the Sender (Claimant) and Recipient (Respondent/Addressee) using structural patterns and NER.
    """
    sender = None
    recipient = None
    
    # 1. Structural Regex for legal notices
    to_match = re.search(r"\bTo[:\s]+(?:Mr\.|Mrs\.|Ms\.|Sh\.|Smt\.)?\s*([A-Z][A-Za-z\s]+?)(?:,|\n|Resident)", text)
    if to_match:
        recipient = to_match.group(1).strip()
        
    from_match = re.search(r"\b(?:From|On\s+behalf\s+of)[:\s]+(?:Adv\.|M/s)?\s*([A-Z][A-Za-z\s]+?)(?:,|\n|High|Court)", text)
    if from_match:
        sender = from_match.group(1).strip()
        
    # 2. Fallback to NER PERSON / ORG entities if regex missed
    if not recipient:
        for ent in entities:
            if ent.label in ("PERSON", "ORGANIZATION") and ent.text != sender:
                recipient = ent.text
                break
                
    if not sender:
        for ent in entities:
            if ent.label in ("ORGANIZATION", "PERSON") and ent.text != recipient:
                sender = ent.text
                break
                
    return sender, recipient

def identify_legal_issues(category: str, laws: List[str], sections: List[str]) -> List[LegalIssue]:
    """
    Identifies core legal issues based on document classification and statutory sections invoked.
    """
    issues = []
    
    if category == "CHEQUE_BOUNCE_NOTICE" or any("138" in s for s in sections):
        issues.append(LegalIssue(
            issue_title="Dishonour of Cheque for Insufficient Funds",
            category="Criminal & Commercial Liability",
            explanation="The drawer of the cheque faces potential criminal liability if the demand amount is not settled within the 15-day statutory window.",
            relevant_statutes=["Section 138, Negotiable Instruments Act, 1881", "Section 142, Negotiable Instruments Act, 1881"]
        ))
        if any("420" in s for s in sections):
            issues.append(LegalIssue(
                issue_title="Allegation of Cheating and Dishonest Inducement",
                category="Criminal Law",
                explanation="The sender alleges dishonest intention at the time of issuing the cheque/entering the transaction.",
                relevant_statutes=["Section 420, Indian Penal Code, 1860"]
            ))
            
    elif category == "EMPLOYMENT_DISPUTE_NOTICE":
        issues.append(LegalIssue(
            issue_title="Wrongful Termination & Employment Dues",
            category="Labour and Employment Law",
            explanation="Dispute concerning termination of employment without mandated contractual notice or non-payment of accrued salary/severance.",
            relevant_statutes=["Industrial Disputes Act, 1947", "Indian Contract Act, 1872"]
        ))
        
    elif category == "TENANCY_AND_EVICTION_NOTICE":
        issues.append(LegalIssue(
            issue_title="Recovery of Arrears & Vacation of Leased Premises",
            category="Property and Tenancy Law",
            explanation="Landlord demanding vacation of premises and settlement of rental arrears under statutory notice requirements.",
            relevant_statutes=["Section 106, Transfer of Property Act, 1882"]
        ))
        
    elif category == "COMMERCIAL_CONTRACT":
        issues.append(LegalIssue(
            issue_title="Contractual Performance and Dispute Resolution",
            category="Commercial Law",
            explanation="Interpretation of contractual obligations, confidentiality, and arbitration dispute resolution mechanisms.",
            relevant_statutes=["Indian Contract Act, 1872", "Arbitration and Conciliation Act, 1996"]
        ))
        
    else:
        issues.append(LegalIssue(
            issue_title="General Legal Demand and Notice of Action",
            category="Civil/Statutory Dispute",
            explanation="A formal legal demand calling upon the recipient to settle claims prior to court litigation.",
            relevant_statutes=laws if laws else ["Civil Procedure Code, 1908"]
        ))
        
    return issues

def detect_ambiguities_and_missing_info(category: str, text: str) -> List[str]:
    """
    Identifies common legal ambiguities, missing procedural dates, or evidentiary gaps.
    """
    ambiguities = []
    text_lower = text.lower()
    
    if category == "CHEQUE_BOUNCE_NOTICE":
        if "bank memo" not in text_lower and "return memo" not in text_lower:
            ambiguities.append("No explicit mention or attachment of the Bank Return Memo date (crucial to establish whether notice was sent within 30 days of dishonour).")
        if "postal" not in text_lower and "consignment" not in text_lower and "speed post" not in text_lower:
            ambiguities.append("No postal tracking number or proof of dispatch mentioned in the text.")
        if "cheque date" not in text_lower and "dated" not in text_lower:
            ambiguities.append("Cheque issuance date may be missing or ambiguous.")
            
    elif category == "TENANCY_AND_EVICTION_NOTICE":
        if "security deposit" not in text_lower:
            ambiguities.append("Notice does not account for or mention adjustment against the existing Security Deposit held by the landlord.")
            
    elif category == "EMPLOYMENT_DISPUTE_NOTICE":
        if "appointment letter" not in text_lower and "contract" not in text_lower:
            ambiguities.append("Specific employment agreement or appointment letter date not referenced.")
            
    return ambiguities

def generate_advocate_questions(category: str, deadlines: List[str], amounts: List[str]) -> List[str]:
    """
    Generates strategic, high-value questions for the citizen to discuss with an advocate.
    """
    questions = []
    
    if category == "CHEQUE_BOUNCE_NOTICE":
        questions.append("Was this statutory notice received within 30 days from the date the bank issued the cheque return memo?")
        questions.append("How should the 15-day payment period be calculated (does it start from the date of post or actual date of receipt)?")
        questions.append("Was the cheque issued for a legally enforceable debt or as an unfulfilled advance/security?")
        questions.append("Can a formal legal reply be drafted within the 15-day period denying fraudulent intent?")
        
    elif category == "EMPLOYMENT_DISPUTE_NOTICE":
        questions.append("Does the employment contract mandate a 30/60-day notice period or payment in lieu of notice?")
        questions.append("Are non-compete clauses enforceable against an employee under Section 27 of the Indian Contract Act?")
        questions.append("Can a complaint be filed before the Labour Commissioner for recovery of withheld salary?")
        
    elif category == "TENANCY_AND_EVICTION_NOTICE":
        questions.append("Does the lease deed have an active lock-in period, and is a 15-day or 30-day notice required under Section 106?")
        questions.append("Can unpaid rent arrears be legally adjusted against the security deposit?")
        
    else:
        questions.append("Is there an arbitration clause that prevents this matter from being filed in civil court?")
        questions.append("What is the limitation period for the sender to file a suit based on these claims?")
        
    return questions

def generate_plain_summary(category_name: str, sender: Optional[str], recipient: Optional[str], amounts: List[str], deadlines: List[str]) -> str:
    """
    Generates an executive, plain-English summary of the document for an ordinary citizen.
    """
    sender_str = sender if sender else "The sender (claimant)"
    recipient_str = recipient if recipient else "the recipient"
    amount_str = f" of {amounts[0]}" if amounts else ""
    deadline_str = f" {deadlines[0]}" if deadlines else " within the stipulated period"
    
    return (
        f"This document is classified as a {category_name}. "
        f"{sender_str} has issued formal legal notice to {recipient_str}, claiming financial payment{amount_str}{deadline_str}. "
        f"The sender states that failure to settle the demanded obligations will result in judicial litigation."
    )

async def generate_structured_analysis(file: UploadFile) -> StructuredLegalAnalysisReport:
    """
    End-to-end Phase 3 pipeline: Document parsing -> Legal NER -> Classification -> Epistemic parsing -> Report generation.
    """
    extraction = await process_document_upload(file)
    full_text = "\n\n".join(seg.content for seg in extraction.segments if seg.content)
    
    # 1. Preprocessing & Sentence Segmentation
    preproc = preprocess_document_text(full_text)
    
    # 2. Extract Entities
    legal_ents = extract_legal_rule_entities(full_text)
    spacy_ents = extract_spacy_general_entities(full_text)
    resolved_ents = resolve_entity_overlaps(legal_ents + spacy_ents)
    
    entities_by_cat: Dict[str, List[str]] = {}
    for e in resolved_ents:
        if e.label not in entities_by_cat:
            entities_by_cat[e.label] = []
        if e.text not in entities_by_cat[e.label]:
            entities_by_cat[e.label].append(e.text)
            
    # 3. Classify Document Category
    classifier = get_legal_classifier()
    cat_key, cat_name, confidence, top_keywords = classifier.predict(full_text)
    
    # 4. Epistemic Parsing (Facts vs Allegations vs Demands)
    classified_statements = parse_document_epistemics(preproc.sentences)
    
    facts = [s.text for s in classified_statements if s.epistemic_type == "FACT"]
    allegations = [s.text for s in classified_statements if s.epistemic_type == "ALLEGATION"]
    demands = [s.text for s in classified_statements if s.epistemic_type == "DEMAND_OR_OBLIGATION"]
    
    # 5. Extract Parties
    sender, recipient = extract_parties(full_text, resolved_ents)
    
    # 6. Specific Actionable Items
    deadlines = entities_by_cat.get("DEADLINE", [])
    amounts = entities_by_cat.get("MONEY", [])
    sections = entities_by_cat.get("LEGAL_SECTION", [])
    laws = entities_by_cat.get("LAW", [])
    
    # 7. Synthesize Issues, Ambiguities, and Advocate Questions
    legal_issues = identify_legal_issues(cat_key, laws, sections)
    ambiguities = detect_ambiguities_and_missing_info(cat_key, full_text)
    advocate_questions = generate_advocate_questions(cat_key, deadlines, amounts)
    
    summary = generate_plain_summary(cat_name, sender, recipient, amounts, deadlines)
    
    return StructuredLegalAnalysisReport(
        document_name=extraction.filename,
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
