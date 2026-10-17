import sys
import io

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
import pymupdf
from app.main import app

client = TestClient(app)

DOC1_LEGAL_NOTICE = """
LEGAL DEMAND NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881

To,
Sh. Rajesh Kumar
Proprietor, M/s Kumar Enterprises
Connaught Place, New Delhi - 110001

Under instructions from and on behalf of my client, M/s Sharma Traders, having its registered office at Nehru Place, New Delhi, I hereby serve upon you this formal statutory legal notice:

1. My client states that you issued Cheque No. 458921 dated 15th January 2024 for an amount of Rs. 2,50,000/- drawn on State Bank of India towards the legally enforceable debt of building materials.
2. The said cheque was dishonoured with the remarks "Funds Insufficient" vide Bank Return Memo dated 20th January 2024.
3. You are hereby called upon to pay the sum of Rs. 2,50,000/- within 15 days of receipt of this notice, failing which criminal proceedings shall be instituted against you under Section 138 and Section 142 of Negotiable Instruments Act.

Adv. Priya Singh
Delhi High Court Bar Association
Dated: 25th January 2024
"""

DOC2_BANK_MEMO = """
STATE BANK OF INDIA - CHEQUE RETURN MEMO
Branch: Connaught Place, New Delhi
Date: 20th January 2024

Cheque Number: 458921
Cheque Date: 15th January 2024
Account Name: Kumar Enterprises
Payee: M/s Sharma Traders
Amount: Rs. 2,50,000/- (Rupees Two Lakh Fifty Thousand Only)

Reason for Return: [Code 01] - Funds Insufficient.
Cleared through RBI Cheque Truncation System (CTS).
Authorized Signatory, SBI
"""

DOC3_SUPPLY_AGREEMENT = """
COMMERCIAL SUPPLY AND DISTRIBUTION AGREEMENT

This Agreement is executed on 10th January 2023 at New Delhi between:
Party A: M/s Sharma Traders, New Delhi (Supplier)
Party B: M/s Kumar Enterprises, Connaught Place, New Delhi (Purchaser)

Clause 4. Payment Terms:
The Purchaser shall remit invoice amounts within 30 days of delivery through banking channels.

Clause 14. Dispute Resolution and Mandatory Arbitration:
In the event of any dispute, claim, or difference arising out of or relating to this agreement, the parties agree to resolve the dispute through binding arbitration in New Delhi under the Arbitration and Conciliation Act, 1996, before approaching any court of law.

IN WITNESS WHEREOF, the parties hereto have set their hands on 10th January 2023.
"""

def test_full_case_workspace_lifecycle():
    print("\n===========================================================================")
    print("=== Testing Advo टेक Phase 8: Case-Aware Multi-Document Workspaces ===")
    print("===========================================================================")

    # Step 1: Create Case Workspace
    print("\n--- 1. Creating Case Workspace ---")
    case_payload = {
        "title": "Sharma Traders v. Kumar Enterprises - Commercial Cheque Dispute",
        "description": "Multi-document dispute involving cheque dishonour, bank memo, and commercial agreement.",
        "category": "CHEQUE_BOUNCE_DISPUTE"
    }
    create_resp = client.post("/api/v1/cases/", json=case_payload)
    assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
    case_id = create_resp.json()["case_id"]
    print(f"[PASS] Created Case ID: {case_id}")

    # Step 2: Upload Document 1 (Legal Notice PDF)
    print("\n--- 2. Uploading Document 1: Legal Notice (PDF) ---")
    doc_pdf = pymupdf.open()
    page = doc_pdf.new_page()
    page.insert_textbox(pymupdf.Rect(50, 50, 550, 750), DOC1_LEGAL_NOTICE, fontsize=10)
    pdf_bytes = doc_pdf.tobytes()
    doc_pdf.close()

    upload_resp1 = client.post(
        f"/api/v1/cases/{case_id}/upload-document",
        files={"file": ("Notice_Sec138.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_resp1.status_code == 200, f"Expected 200, got {upload_resp1.status_code}: {upload_resp1.text}"
    doc1_data = upload_resp1.json()
    print(f"[PASS] Ingested Notice: {doc1_data['filename']} | Detected Role: {doc1_data['doc_role']}")
    assert doc1_data['doc_role'] == "LEGAL_NOTICE"

    # Step 3: Upload Document 2 (Bank Memo PDF)
    print("\n--- 3. Uploading Document 2: Bank Return Memo (PDF) ---")
    memo_pdf = pymupdf.open()
    page2 = memo_pdf.new_page()
    page2.insert_textbox(pymupdf.Rect(50, 50, 550, 750), DOC2_BANK_MEMO, fontsize=10)
    memo_bytes = memo_pdf.tobytes()
    memo_pdf.close()

    upload_resp2 = client.post(
        f"/api/v1/cases/{case_id}/upload-document",
        files={"file": ("Bank_Return_Memo.pdf", memo_bytes, "application/pdf")}
    )
    assert upload_resp2.status_code == 200
    doc2_data = upload_resp2.json()
    print(f"[PASS] Ingested Memo: {doc2_data['filename']} | Detected Role: {doc2_data['doc_role']}")
    assert doc2_data['doc_role'] == "BANK_MEMO"

    # Step 4: Add Document 3 (Supply Agreement Text)
    print("\n--- 4. Adding Document 3: Supply Agreement (Text) ---")
    text_doc_payload = {
        "filename": "Commercial_Supply_Agreement.txt",
        "text_content": DOC3_SUPPLY_AGREEMENT
    }
    upload_resp3 = client.post(f"/api/v1/cases/{case_id}/add-text-document", json=text_doc_payload)
    assert upload_resp3.status_code == 200
    doc3_data = upload_resp3.json()
    print(f"[PASS] Ingested Agreement: {doc3_data['filename']} | Detected Role: {doc3_data['doc_role']}")
    assert doc3_data['doc_role'] == "CONTRACT_AGREEMENT"

    # Step 5: Multi-Document Holistic Analysis
    print("\n--- 5. Generating Cross-Document Case Analysis Report ---")
    analysis_resp = client.get(f"/api/v1/cases/{case_id}/analysis")
    assert analysis_resp.status_code == 200
    analysis = analysis_resp.json()

    print(f"Total Attached Documents: {analysis['total_documents']}")
    assert analysis['total_documents'] == 3

    print(f"\nChronological Timeline Events Extracted ({len(analysis['chronological_timeline'])}):")
    for ev in analysis['chronological_timeline']:
        print(f"  * [{ev['event_date']}] {ev['source_doc_filename']} ({ev['citation_pointer']}): {ev['event_description'][:80]}...")
    assert len(analysis['chronological_timeline']) >= 3

    print(f"\nIdentified Parties: {analysis['identified_parties']}")
    print(f"Aligned Monetary Claims: {len(analysis['aligned_monetary_claims'])} mentions")

    print(f"\nCross-Document Discrepancies & Evidentiary Inconsistencies ({len(analysis['cross_document_discrepancies'])}):")
    for disc in analysis['cross_document_discrepancies']:
        print(f"  ! [{disc['issue_type']}] ({disc['severity']}): {disc['description']}")
        print(f"    Recommended Action: {disc['advocate_action']}")
    
    # Check that Arbitration clause bypass is correctly flagged!
    assert any(d['issue_type'] == "ARBITRATION_CLAUSE_BYPASS" for d in analysis['cross_document_discrepancies']), "Should flag arbitration clause discrepancy"
    print("[PASS] Cross-document contradiction detection verified!")

    print(f"\nMissing Supporting Documents Identified: {analysis['missing_supporting_documents']}")
    assert len(analysis['missing_supporting_documents']) > 0

    # Step 6: Cross-Document Q&A
    print("\n--- 6. Testing Cross-Document RAG Q&A ---")
    qa_payload = {
        "question": "Does the agreement between the parties require arbitration before going to court?",
        "language": "en"
    }
    qa_resp = client.post(f"/api/v1/cases/{case_id}/ask", json=qa_payload)
    assert qa_resp.status_code == 200, f"Expected 200, got {qa_resp.status_code}: {qa_resp.text}"
    qa_data = qa_resp.json()

    print(f"Question: {qa_data['question']}")
    print(f"Synthesis Engine: {qa_data['synthesis_engine']}")
    print(f"Documents Referenced: {qa_data['documents_referenced']}")
    print("\nAnswer:\n", qa_data['answer'])

    print(f"\nMulti-Doc Citations ({len(qa_data['multi_doc_citations'])}):")
    for c in qa_data['multi_doc_citations']:
        print(f"  * {c['citation_id']} - {c['title']}: \"{c['quote_snippet'][:75]}...\"")

    assert any("Commercial_Supply_Agreement" in c['citation_id'] for c in qa_data['multi_doc_citations']), "Must cite the agreement"
    assert "arbitration" in qa_data['answer'].lower()
    print("[PASS] Multi-document cross-referencing and pinpoint citation pinning verified!")

    # Step 7: List Cases Endpoint
    print("\n--- 7. Testing Case Listing Endpoint ---")
    list_resp = client.get("/api/v1/cases/")
    assert list_resp.status_code == 200
    cases_list = list_resp.json()["cases"]
    assert any(c["case_id"] == case_id for c in cases_list)
    print(f"[PASS] Successfully verified case listing. Total active cases: {len(cases_list)}")

    print("\n===========================================================================")
    print(">>> ALL PHASE 8 TESTS PASSED! CASE-AWARE MULTI-DOC WORKSPACE VERIFIED. <<<")
    print("===========================================================================")

if __name__ == "__main__":
    test_full_case_workspace_lifecycle()
