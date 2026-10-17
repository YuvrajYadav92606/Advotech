import sys
from fastapi.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.main import app
from app.knowledge_base.indexer import get_kb_indexer
from app.schemas.knowledge_base import KBSearchQuery

def test_knowledge_base_evaluation():
    print("=" * 75)
    print("=== Testing Advo टेक Phase 5: Indian Legal Knowledge Base ===")
    print("=" * 75)

    indexer = get_kb_indexer()
    stats = indexer.get_statistics()
    
    print("\n--- 1. Knowledge Base Corpus Statistics ---")
    print(f"Total Documents Indexed: {stats.total_documents}")
    print(f"  Statutory Provisions : {stats.total_statutes}")
    print(f"  Landmark Case Laws   : {stats.total_case_laws}")
    print(f"  Courts Represented   : {list(stats.courts.keys())}")
    print(f"  ML Training Splits   : {stats.training_splits}")
    assert stats.total_documents >= 10, "Knowledge base failed to load all items"
    print("[PASS] Corpus loading and statistics verified.")

    # 2. Test Statutory Lookup (Section 138 NI Act)
    print("\n--- 2. Statutory Retrieval & Section Precision ---")
    query1 = KBSearchQuery(query="Section 138 cheque", doc_type="STATUTE")
    results1 = indexer.search(query1)
    assert len(results1) > 0, "Failed to retrieve Section 138"
    top_statute = results1[0]
    print(f"Found: {top_statute.title}")
    print(f"Citation: {top_statute.citation}")
    print(f"Source URL: {top_statute.source_url}")
    assert top_statute.section_number == "Section 138"
    assert "Negotiable Instruments Act" in top_statute.act_name
    print("[PASS] Statutory retrieval with provenance URL verified.")

    # 3. Test Landmark Case Law Retrieval (Dalmia Cement on 15-Day Notice Rule)
    print("\n--- 3. Landmark Case Law & Ratio Decidendi Retrieval ---")
    query2 = KBSearchQuery(query="Dalmia Cement 15 days notice", doc_type="CASE_LAW")
    results2 = indexer.search(query2)
    assert len(results2) > 0, "Failed to retrieve Dalmia Cement case"
    top_case = results2[0]
    print(f"Case Title: {top_case.title}")
    print(f"Court: {top_case.court_or_authority} ({top_case.decision_or_enactment_date})")
    print(f"Citation: {top_case.citation}")
    print(f"Ratio Decidendi:\n  \"{top_case.ratio_decidendi}\"")
    assert "Dalmia Cement" in top_case.title
    assert top_case.ratio_decidendi is not None
    print("[PASS] Landmark case law and ratio decidendi retrieved.")

    # 4. Test Amendment & Superseded Statute Tracking (IPC vs BNS)
    print("\n--- 4. Tracking Amended and Superseded Statutes (IPC -> BNS) ---")
    # With active_only=True (default), superseded Section 420 IPC should be omitted
    active_search = indexer.search(KBSearchQuery(query="Section 420 cheating", active_only=True))
    assert not any(d.id == "ACT_IPC_1860_SEC_420" for d in active_search), "Superseded IPC 420 was returned when active_only=True"
    print("[PASS] Active-only filter correctly omitted superseded legislation.")
    
    # With active_only=False, it should be retrieved with its successor information
    all_search = indexer.search(KBSearchQuery(query="Section 420 cheating", active_only=False))
    ipc_item = [d for d in all_search if d.id == "ACT_IPC_1860_SEC_420"][0]
    print(f"Found Historical Statute: {ipc_item.title}")
    print(f"  Amended/Superseded Flag: {ipc_item.is_amended_or_superseded}")
    print(f"  Superseded By          : {ipc_item.superseded_by}")
    assert ipc_item.is_amended_or_superseded is True
    assert "Bharatiya Nyaya Sanhita" in ipc_item.superseded_by
    print("[PASS] Superseded statute tracking and successor referral verified.")

    # 5. Test Dataset Export for Future ML Model Training
    print("\n--- 5. ML Training Dataset Exporter (HuggingFace / PyTorch Ready) ---")
    train_records = indexer.export_training_dataset(split="train")
    print(f"Total 'train' split records exported: {len(train_records)}")
    sample_train = train_records[0]
    print(f"Sample Record Structure:")
    print(f"  ID: {sample_train['id']}")
    print(f"  Type: {sample_train['doc_type']}")
    print(f"  Statutes: {sample_train['statutory_provisions']}")
    print(f"  Text Excerpt: {sample_train['text'][:80]}...")
    assert len(train_records) > 0
    assert "id" in sample_train and "text" in sample_train and "split" in sample_train
    print("[PASS] ML training dataset export verified.")

    # 6. Test FastAPI Knowledge Base Endpoints via TestClient
    print("\n--- 6. Testing FastAPI Endpoints ---")
    client = TestClient(app)

    # Test /api/v1/kb/search
    search_res = client.get("/api/v1/kb/search", params={"q": "Section 138"})
    assert search_res.status_code == 200, f"Search failed: {search_res.text}"
    search_data = search_res.json()
    assert search_data["total_results"] > 0
    print(f"[PASS] GET /api/v1/kb/search returned {search_data['total_results']} results")

    # Test /api/v1/kb/documents/{doc_id}
    doc_res = client.get("/api/v1/kb/documents/SC_2001_DALMIA_CEMENT")
    assert doc_res.status_code == 200, f"Document lookup failed: {doc_res.text}"
    doc_data = doc_res.json()
    assert doc_data["id"] == "SC_2001_DALMIA_CEMENT"
    print(f"[PASS] GET /api/v1/kb/documents/{{doc_id}} verified: '{doc_data['title']}'")

    # Test /api/v1/kb/stats
    stats_res = client.get("/api/v1/kb/stats")
    assert stats_res.status_code == 200
    print("[PASS] GET /api/v1/kb/stats verified")

    print("\n" + "=" * 75)
    print(">>> ALL PHASE 5 TESTS PASSED! KNOWLEDGE BASE & ML COMPATIBILITY VERIFIED. <<<")
    print("=" * 75)

if __name__ == "__main__":
    test_knowledge_base_evaluation()
