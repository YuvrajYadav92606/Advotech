import sys
import io

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
import pymupdf
from app.main import app

client = TestClient(app)

SAMPLE_CHEQUE_NOTICE = """
LEGAL DEMAND NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881

To,
Sh. Rajesh Kumar
Proprietor, M/s Kumar Enterprises
Connaught Place, New Delhi - 110001

Under instructions from and on behalf of my client, M/s Sharma Traders, having its registered office at Nehru Place, New Delhi, I hereby serve upon you this formal statutory legal notice:

1. My client states that you issued Cheque No. 458921 dated 15th January 2024 for an amount of Rs. 2,50,000/- drawn on State Bank of India, Connaught Place Branch, towards the legally enforceable debt of supply of building materials.
2. The said cheque was presented by my client through their banker, HDFC Bank, but the same was returned dishonoured with the remarks "Funds Insufficient" vide Bank Return Memo dated 20th January 2024.
3. My client informs that you have dishonestly and intentionally issued the said cheque without maintaining sufficient balance, with an intention to defraud my client.
4. You are hereby called upon and required to remit and pay the aforementioned amount of Rs. 2,50,000/- within a period of 15 days from the receipt of this statutory notice, failing which my client will be constrained to initiate criminal proceedings against you under Section 138 and Section 142 of the Negotiable Instruments Act, 1881.

Yours faithfully,
Adv. Priya Singh
Enrolment No. D/458/2012
Delhi High Court Bar Association
"""

def test_rag_grounded_qa_deadline_and_money():
    print("\n--- Test 1: Grounded Q&A on Legal Notice (Deadlines & Monetary Claims) ---")
    payload = {
        "question": "What is the deadline for payment and how much money is claimed?",
        "document_text": SAMPLE_CHEQUE_NOTICE,
        "language": "en",
        "max_sources": 3
    }
    response = client.post("/api/v1/rag/ask", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    print(f"Question: {data['question']}")
    print(f"Synthesis Engine: {data['synthesis_engine']}")
    print(f"Confidence Score: {data['confidence_score']}")
    print("\nAnswer:\n", data['answer'])
    
    # Assertions
    assert "2,50,000" in data['answer'] or "Rs." in data['answer']
    assert "15 days" in data['answer'].lower() or "15" in data['answer']
    assert len(data['citations']) > 0, "Should have retrieved citations"
    assert any("[Doc:" in c['citation_id'] for c in data['citations']), "Should have at least one document citation"
    
    # Check epistemic classification
    assert len(data['epistemic_check']['demands_obligations']) > 0
    print(f"\nCaptured Demands/Obligations: {len(data['epistemic_check']['demands_obligations'])}")
    print(f"Captured Governing Statutes: {data['epistemic_check']['governing_statutes']}")
    print("Test 1 Passed successfully!")

def test_rag_epistemic_allegation_separation():
    print("\n--- Test 2: Epistemic Boundary (Allegations vs Established Facts) ---")
    payload = {
        "question": "Did I commit a fraud or dishonestly cheat the client?",
        "document_text": SAMPLE_CHEQUE_NOTICE,
        "language": "en"
    }
    response = client.post("/api/v1/rag/ask", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    print("Answer:\n", data['answer'])
    
    # Assertions
    # Must flag the accusation as an adversarial allegation
    assert len(data['epistemic_check']['allegations']) > 0, "Must capture the allegation in epistemic check"
    allegation_text = " ".join(data['epistemic_check']['allegations']).lower()
    assert "defraud" in allegation_text or "dishonestly" in allegation_text or "intent" in allegation_text
    
    print(f"Extracted Allegations: {data['epistemic_check']['allegations']}")
    print("Test 2 Passed: Allegations properly segregated from facts!")

def test_rag_anti_hallucination_out_of_scope():
    print("\n--- Test 3: Anti-Hallucination Guardrail (Out of Scope Query) ---")
    payload = {
        "question": "What is the statutory penalty for piloting an unregistered space satellite over Antarctica?",
        "language": "en"
    }
    response = client.post("/api/v1/rag/ask", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    print("Answer:\n", data['answer'])
    print(f"Limitations flagged: {data['limitations']}")
    
    # Must not invent fake laws
    assert len(data['limitations']) > 0
    assert "not contain verified information" in data['answer'] or "no direct document facts" in str(data['limitations']).lower()
    print("Test 3 Passed: Successfully prevented hallucination on out-of-scope query!")

def test_rag_multilingual_hindi():
    print("\n--- Test 4: Multilingual RAG in Hindi and Hinglish ---")
    payload_hi = {
        "question": "भुगतान की समय सीमा क्या है?",
        "document_text": SAMPLE_CHEQUE_NOTICE,
        "language": "hi"
    }
    resp_hi = client.post("/api/v1/rag/ask", json=payload_hi)
    assert resp_hi.status_code == 200
    data_hi = resp_hi.json()
    print("Hindi Answer Preview:")
    print(data_hi['answer'][:250] + "...")
    assert "Advo टेक" in data_hi['answer']

    payload_hinglish = {
        "question": "Payment ka deadline kitne din ka hai?",
        "document_text": SAMPLE_CHEQUE_NOTICE,
        "language": "hinglish"
    }
    resp_hinglish = client.post("/api/v1/rag/ask", json=payload_hinglish)
    assert resp_hinglish.status_code == 200
    data_hinglish = resp_hinglish.json()
    print("\nHinglish Answer Preview:")
    print(data_hinglish['answer'][:250] + "...")
    assert "Advo टेक" in data_hinglish['answer']
    print("Test 4 Passed successfully!")

def test_rag_ask_document_file_upload():
    print("\n--- Test 5: Direct PDF Document File Upload Q&A ---")
    
    # Create in-memory PDF using PyMuPDF
    doc = pymupdf.open()
    page = doc.new_page()
    rect = pymupdf.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, SAMPLE_CHEQUE_NOTICE, fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()
    
    files = {
        "file": ("cheque_notice.pdf", pdf_bytes, "application/pdf")
    }
    data = {
        "question": "What happens if I fail to pay within 15 days?",
        "language": "en"
    }
    
    response = client.post("/api/v1/rag/ask-document", files=files, data=data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    res_json = response.json()
    print("File Upload RAG Answer:\n", res_json['answer'])
    print(f"Citations count: {len(res_json['citations'])}")
    print(f"Suggested Advocate Questions: {res_json['suggested_advocate_questions']}")
    
    assert len(res_json['citations']) > 0
    assert len(res_json['suggested_advocate_questions']) > 0
    print("Test 5 Passed successfully!")

def test_rag_engine_status():
    print("\n--- Test 6: Engine Status Inspection ---")
    resp = client.get("/api/v1/rag/engine-status")
    assert resp.status_code == 200
    data = resp.json()
    print(f"Engine: {data['engine_name']}")
    print(f"Offline Ready: {data['offline_fallback_ready']}")
    print(f"Capabilities: {data['capabilities']}")
    assert data['offline_fallback_ready'] is True
    print("Test 6 Passed successfully!")

if __name__ == "__main__":
    test_rag_grounded_qa_deadline_and_money()
    test_rag_epistemic_allegation_separation()
    test_rag_anti_hallucination_out_of_scope()
    test_rag_multilingual_hindi()
    test_rag_ask_document_file_upload()
    test_rag_engine_status()
    print("\n==================================================")
    print("ALL PHASE 7 RAG & LEGAL Q&A TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
