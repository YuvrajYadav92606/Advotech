import io
import sys
import pymupdf
from fastapi.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.main import app
from app.nlp.classifier import get_legal_classifier
from app.nlp.epistemic_parser import classify_sentence_epistemic

def test_phase3_evaluation():
    print("=" * 70)
    print("=== Testing Advo टेक Phase 3: Legal Classification & Analysis ===")
    print("=" * 70)

    classifier = get_legal_classifier()

    # 1. Multi-Class Document Categorization Benchmark
    test_docs = [
        (
            "LEGAL NOTICE FOR DISHONOUR OF CHEQUE UNDER SECTION 138 NI ACT. "
            "Cheque No. 452109 dated 15 Jan 2024 for Rs. 2,50,000/- returned unpaid with remarks funds insufficient. "
            "Pay the cheque amount within 15 days or face criminal complaint under section 138 of negotiable instruments act.",
            "CHEQUE_BOUNCE_NOTICE"
        ),
        (
            "NOTICE TO QUIT AND VACATE PREMISES UNDER SECTION 106 TRANSFER OF PROPERTY ACT. "
            "You have defaulted in paying the monthly rent of Rs. 35,000 for the past 4 months. "
            "You are hereby called upon to vacate and hand over peaceful vacant possession within 30 days.",
            "TENANCY_AND_EVICTION_NOTICE"
        ),
        (
            "NON-DISCLOSURE AND MUTUAL CONFIDENTIALITY AGREEMENT. "
            "This Agreement is entered into between Company and Contractor. "
            "Clause 5: Confidential Information shall not be disclosed to any third party for a period of 3 years. "
            "Governing law shall be the laws of India and disputes resolved via Arbitration.",
            "COMMERCIAL_CONTRACT"
        ),
        (
            "NOTICE REGARDING WRONGFUL TERMINATION AND RECOVERY OF UNPAID SALARY. "
            "My client was wrongfully terminated by employer without the mandatory 60 days notice period or severance pay. "
            "You are required to clear pending salary dues of Rs. 4,20,000 along with provident fund within 15 days.",
            "EMPLOYMENT_DISPUTE_NOTICE"
        )
    ]

    print("\n--- 1. Evaluating Document Classifier (TF-IDF + Calibrated Logistic Regression) ---")
    for text, expected_label in test_docs:
        cat_key, display_name, conf, keywords = classifier.predict(text)
        print(f"\n[Category] Predicted: {display_name} (Confidence: {conf * 100:.1f}%)")
        print(f"           Top Predictive TF-IDF Keywords: {keywords}")
        assert cat_key == expected_label, f"Expected {expected_label}, got {cat_key}"
        print(f"           [PASS] Correctly classified as {expected_label}")

    # 2. Epistemic Statement Parser Benchmark (Facts vs Allegations vs Demands)
    print("\n--- 2. Evaluating Epistemic Statement Parsing (Preserving Allegations vs Facts) ---")
    test_statements = [
        ("Cheque No. 452109 dated 15th January 2024 was drawn on State Bank of India.", "FACT"),
        ("You have dishonestly and fraudulently refused to clear the payment with malafide intention.", "ALLEGATION"),
        ("You are hereby called upon to remit the said sum of Rs. 2,50,000/- within 15 days of receipt.", "DEMAND_OR_OBLIGATION"),
        ("Under Section 138 of the Negotiable Instruments Act, 1881, dishonour of cheque constitutes a punishable offence.", "LEGAL_REASONING")
    ]

    for stmt, expected_type in test_statements:
        detected_type, conf = classify_sentence_epistemic(stmt)
        print(f"Statement: \"{stmt[:60]}...\"")
        print(f"  -> Type: {detected_type} (Confidence: {conf})")
        assert detected_type == expected_type, f"Expected {expected_type}, got {detected_type}"
        print(f"  -> [PASS] Epistemic validity confirmed.")

    # 3. Test End-to-End API via TestClient
    print("\n--- 3. Testing Full Structured Analysis API ---")
    client = TestClient(app)

    pdf_doc = pymupdf.open()
    page1 = pdf_doc.new_page()
    notice_text = (
        "LEGAL NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881.\n\n"
        "To: Mr. Ramesh Kumar, Resident of Gurugram.\n"
        "From: Adv. Suresh Sharma on behalf of M/s Apex Enterprises.\n\n"
        "Sir, my client states that Cheque No. 452109 dated 15th January 2024 for Rs. 2,50,000/- was returned unpaid. "
        "You have deliberately and dishonestly failed to discharge your legal liability. "
        "You are hereby called upon to pay Rs. 2,50,000/- within 15 days of receipt of this notice, "
        "failing which criminal proceedings will be instituted under Section 138 of Negotiable Instruments Act."
    )
    page1.insert_textbox(pymupdf.Rect(50, 50, 550, 750), notice_text)
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()

    res = client.post(
        "/api/v1/analysis/document",
        files={"file": ("cheque_notice.pdf", pdf_bytes, "application/pdf")}
    )
    assert res.status_code == 200, f"Analysis failed: {res.text}"
    report = res.json()

    print(f"\n[REPORT GENERATED SUCCESSFULLY]")
    print(f"Document Name: {report['document_name']}")
    print(f"Category: {report['category_display_name']} ({report['classification_confidence'] * 100:.1f}%)")
    print(f"Sender / Claimant: {report['sender_or_claimant']}")
    print(f"Recipient / Respondent: {report['recipient_or_respondent']}")
    print(f"Summary: {report['summary']}")
    print(f"\nIdentified Facts: {len(report['facts'])}")
    print(f"Identified Allegations: {len(report['allegations'])}")
    print(f"Demanded Obligations: {len(report['demands_and_obligations'])}")
    print(f"\nIdentified Legal Issues ({len(report['legal_issues'])}):")
    for issue in report['legal_issues']:
        print(f"  * {issue['issue_title']} ({issue['category']})")
    print(f"\nMissing Information / Procedural Ambiguities:")
    for amb in report['missing_information_or_ambiguities']:
        print(f"  ! {amb}")
    print(f"\nSuggested Questions for Citizen to Ask Advocate:")
    for q in report['suggested_advocate_questions']:
        print(f"  ? {q}")

    assert report['document_category'] == "CHEQUE_BOUNCE_NOTICE"
    assert len(report['legal_issues']) > 0
    assert len(report['suggested_advocate_questions']) > 0

    print("\n" + "=" * 70)
    print(">>> ALL PHASE 3 TESTS PASSED! STRUCTURED ANALYSIS VERIFIED. <<<")
    print("=" * 70)

if __name__ == "__main__":
    test_phase3_evaluation()
