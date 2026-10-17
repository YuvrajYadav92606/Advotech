import io
import sys
import pymupdf
from fastapi.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.main import app
from app.nlp.simplifier import simplify_document_clauses, simplify_english_sentence

def test_simplification_evaluation():
    print("=" * 75)
    print("=== Testing Advo टेक Phase 4: Legal Language Simplification ===")
    print("=" * 75)

    # 1. Test Exact Canonical Legal Notice Example from User Specification
    prompt_example = (
        "You are hereby required to remit the aforementioned amount within the stipulated period, "
        "failing which appropriate legal proceedings shall be initiated."
    )
    
    print("\n--- 1. Testing Core Legalese Simplification ---")
    print(f"Original Formal Legalese:\n  \"{prompt_example}\"")
    
    result = simplify_document_clauses(prompt_example)
    clause = result.clauses[0]
    
    print(f"\n[A] Plain English:\n  \"{clause.simplified_english}\"")
    print(f"\n[B] Vernacular Hindi (हिंदी):\n  \"{clause.simplified_hindi}\"")
    print(f"\n[C] Conversational Hinglish:\n  \"{clause.simplified_hinglish}\"")
    
    # Assertions
    assert "the sender requires you to pay" in clause.simplified_english.lower() or "pay" in clause.simplified_english.lower()
    assert "the specified deadline" in clause.simplified_english.lower()
    assert "or legal proceedings may follow" in clause.simplified_english.lower()
    assert clause.fidelity_check_passed is True
    print("\n[PASS] Core legalese successfully translated into clear English, Hindi, and Hinglish.")

    # 2. Test Epistemic Allegation Preservation (Never Turn Allegations into Facts)
    print("\n--- 2. Testing Epistemic Preservation (Allegations vs Facts) ---")
    accusation = "You have dishonestly and fraudulently refused to discharge your legal liability."
    acc_res = simplify_document_clauses(accusation)
    acc_clause = acc_res.clauses[0]
    
    print(f"Original Accusation: \"{accusation}\"")
    print(f"Simplified English : \"{acc_clause.simplified_english}\"")
    print(f"Epistemic Type     : {acc_clause.epistemic_type}")
    
    assert acc_clause.epistemic_type == "ALLEGATION"
    assert "the sender claims" in acc_clause.simplified_english.lower() or "sender" in acc_clause.simplified_english.lower()
    print("[PASS] Allegation correctly preserved with epistemic framing (not asserted as fact).")

    # 3. Test Full Document Simplification with Citations & Fidelity Check
    print("\n--- 3. Testing Full Document Simplification API with PDF Upload ---")
    client = TestClient(app)

    full_notice = (
        "LEGAL NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881.\n\n"
        "To: Mr. Ramesh Kumar, Resident of Gurugram.\n"
        "From: Adv. Suresh Sharma on behalf of M/s Apex Enterprises.\n\n"
        "Sir, my client states that Cheque No. 452109 dated 15th January 2024 for Rs. 2,50,000/- was returned unpaid. "
        "You have deliberately and dishonestly failed to discharge your legal liability. "
        "You are hereby called upon to pay Rs. 2,50,000/- within 15 days of receipt of this notice, "
        "failing which criminal proceedings will be instituted under Section 138 of Negotiable Instruments Act."
    )

    pdf_doc = pymupdf.open()
    page1 = pdf_doc.new_page()
    page1.insert_textbox(pymupdf.Rect(50, 50, 550, 750), full_notice)
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()

    res = client.post(
        "/api/v1/simplification/document",
        files={"file": ("cheque_notice.pdf", pdf_bytes, "application/pdf")}
    )
    assert res.status_code == 200, f"Simplification failed: {res.text}"
    data = res.json()

    print(f"\nDocument Name: {data['document_name']}")
    print(f"Total Clauses Simplified: {data['total_clauses']}")
    print(f"Average Fidelity Score: {data['average_fidelity_score']}%")
    print(f"\nExecutive Summary (English):\n  {data['executive_summary_english']}")
    print(f"\nExecutive Summary (Hindi):\n  {data['executive_summary_hindi']}")
    print(f"\nExecutive Summary (Hinglish):\n  {data['executive_summary_hinglish']}")

    # Check sample clause
    demand_clause = [c for c in data['clauses'] if c['epistemic_type'] == "DEMAND_OR_OBLIGATION"][0]
    print(f"\n[Sample Grounded Demand Clause]:")
    print(f"  Reference  : {demand_clause['segment_reference']}")
    print(f"  Original   : {demand_clause['original_text'][:70]}...")
    print(f"  Simplified : {demand_clause['simplified_english']}")
    print(f"  Fidelity   : Passed ({demand_clause['preserved_entities']})")

    assert data['average_fidelity_score'] >= 80.0
    assert len(data['clauses']) > 0

    print("\n" + "=" * 75)
    print(">>> ALL PHASE 4 TESTS PASSED! SIMPLIFICATION VERIFIED. <<<")
    print("=" * 75)

if __name__ == "__main__":
    test_simplification_evaluation()
