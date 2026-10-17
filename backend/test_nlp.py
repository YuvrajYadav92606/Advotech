import io
import sys
import pymupdf
from fastapi.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.main import app
from app.nlp.legal_entities import extract_spacy_general_entities, extract_legal_rule_entities, analyze_legal_text
from app.nlp.preprocessor import segment_sentences, clean_legal_text

def test_nlp_evaluation():
    print("=" * 65)
    print("=== Testing Advo टेक Phase 2: NLP Fundamentals & Legal NER ===")
    print("=" * 65)

    sample_legal_notice = (
        "LEGAL NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881.\n\n"
        "To: Mr. Ramesh Kumar, Resident of Sector 14, Gurugram, Haryana.\n"
        "From: Adv. Suresh Sharma, High Court of Delhi, on behalf of M/s Apex Enterprises.\n\n"
        "Sir, under instructions from my client, I hereby issue this legal notice regarding dishonour of Cheque No. 452109 "
        "dated 15th January 2024 for an amount of Rs. 2,50,000/- drawn on State Bank of India.\n"
        "You are hereby required to remit the said sum of Rs. 2,50,000/- within 15 days of receipt of this notice, "
        "failing which my client will institute criminal proceedings under Section 138 of the Negotiable Instruments Act, 1881 "
        "and Section 420 of the Indian Penal Code, 1860 before the Chief Judicial Magistrate, Gurugram."
    )

    # 1. Test Preprocessing & Legal Sentence Segmentation
    print("\n--- 1. Preprocessing & Sentence Segmentation ---")
    sentences = segment_sentences(sample_legal_notice)
    print(f"Total Sentences Identified: {len(sentences)}")
    for s in sentences:
        print(f"  [{s.index}] ({s.token_count} tokens) {s.text[:80]}...")
    assert len(sentences) >= 3, "Sentence segmentation failed"
    # Ensure 'Adv. Suresh Sharma' or 'Sec.' did not split mid-sentence
    assert any("Adv. Suresh Sharma" in s.text for s in sentences), "Abbreviation Adv. incorrectly split sentence"
    print("[PASS] Legal abbreviation handling and sentence segmentation verified.")

    # 2. Benchmark Evaluation: General spaCy NER vs Indian Legal Pipeline
    print("\n--- 2. Benchmark Evaluation: General spaCy vs. Advo टेक Legal NLP ---")
    spacy_only = extract_spacy_general_entities(sample_legal_notice)
    print("\n[A] Off-the-shelf spaCy ('en_core_web_sm') Extracted:")
    for e in spacy_only:
        print(f"    - {e.label:15}: '{e.text}'")

    legal_rules = extract_legal_rule_entities(sample_legal_notice)
    print("\n[B] Advo टेक Domain Legal Engine Extracted:")
    for e in legal_rules:
        print(f"    - {e.label:15}: '{e.text}'")

    analysis = analyze_legal_text(sample_legal_notice)
    print("\n[C] Unified Hybrid Advo टेक Intelligence Output:")
    for cat, items in analysis.entities_by_category.items():
        print(f"    * {cat:15}: {items}")

    # Critical assertions
    assert "LEGAL_SECTION" in analysis.entities_by_category, "Failed to identify legal sections"
    assert "LAW" in analysis.entities_by_category, "Failed to identify statutes"
    assert "COURT" in analysis.entities_by_category, "Failed to identify courts"
    assert "DEADLINE" in analysis.entities_by_category, "Failed to identify notice deadlines"
    assert len(analysis.actionable_deadlines) > 0, "No actionable deadlines surfaced"
    print(f"\n[PASS] Actionable Deadlines Identified: {analysis.actionable_deadlines}")
    print(f"[PASS] Monetary Claims Identified: {analysis.monetary_obligations}")

    # 3. Test API Endpoints via TestClient
    print("\n--- 3. Testing FastAPI Endpoints ---")
    client = TestClient(app)

    # Test /api/v1/nlp/analyze-text
    text_res = client.post("/api/v1/nlp/analyze-text", json={"text": sample_legal_notice})
    assert text_res.status_code == 200, f"Analyze text failed: {text_res.text}"
    text_data = text_res.json()
    assert "LEGAL_SECTION" in text_data["entities_by_category"]
    print("[PASS] POST /api/v1/nlp/analyze-text successful")

    # Test /api/v1/nlp/analyze-document with PDF
    pdf_doc = pymupdf.open()
    page1 = pdf_doc.new_page()
    page1.insert_text((50, 72), sample_legal_notice, fontsize=11)
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()

    doc_res = client.post(
        "/api/v1/nlp/analyze-document",
        files={"file": ("notice_test.pdf", pdf_bytes, "application/pdf")}
    )
    assert doc_res.status_code == 200, f"Analyze document failed: {doc_res.text}"
    doc_data = doc_res.json()
    assert doc_data["document_name"] == "notice_test.pdf"
    
    # Check that entities retain page citation references
    first_ent = doc_data["all_entities"][0]
    print(f"[PASS] Entity '{first_ent['text']}' grounded to segment: '{first_ent['segment_reference']}'")
    assert first_ent["segment_reference"] == "Page 1"
    print("[PASS] POST /api/v1/nlp/analyze-document with Page-Grounding successful")

    print("\n" + "=" * 65)
    print(">>> ALL NLP & LEGAL NER TESTS PASSED! PHASE 2 VERIFIED. <<<")
    print("=" * 65)

if __name__ == "__main__":
    test_nlp_evaluation()
