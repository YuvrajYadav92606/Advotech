import sys
from fastapi.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.main import app
from app.schemas.search import SemanticSearchRequest
from app.retrieval.hybrid_search import get_hybrid_search_engine

def test_semantic_search_evaluation():
    print("=" * 75)
    print("=== Testing Advo टेक Phase 6: Semantic Legal Search & Hybrid Retrieval ===")
    print("=" * 75)

    engine = get_hybrid_search_engine()

    # 1. Test Query 1: Citizen Query with Zero Literal Word Overlap (Prompt Example)
    print("\n--- 1. Evaluating Citizen Query with Natural Phrasing (Zero Exact Match) ---")
    query1 = "My employer terminated me without giving notice"
    print(f"Citizen Query: \"{query1}\"")
    
    req1 = SemanticSearchRequest(query=query1, alpha=0.7, limit=3)
    results1 = engine.search(req1)
    
    assert len(results1) > 0, "Semantic search returned no results"
    top1 = results1[0]
    print(f"Top Retrieved: {top1.title} ({top1.doc_type})")
    print(f"  Semantic Score: {top1.semantic_score:.3f} | Keyword Score: {top1.keyword_score:.3f} | Hybrid: {top1.hybrid_score:.3f}")
    print(f"  Rationale: {top1.retrieval_rationale}")
    print(f"  Excerpt  : {top1.content_snippet[:120]}...")
    
    # Assert that employment or contract breach was identified
    assert any("contract" in r.title.lower() or "employment" in str(r.legal_issues).lower() for r in results1)
    print("[PASS] Natural phrasing successfully resolved to statutory breach and employment jurisprudence.")

    # 2. Test Query 2: Tenant Eviction
    print("\n--- 2. Evaluating Tenancy and Eviction Scenario ---")
    query2 = "Landlord asking to vacate flat within thirty days"
    print(f"Citizen Query: \"{query2}\"")
    
    req2 = SemanticSearchRequest(query=query2, alpha=0.6, limit=3)
    results2 = engine.search(req2)
    assert len(results2) > 0
    top2 = results2[0]
    print(f"Top Retrieved: {top2.title}")
    print(f"  Semantic Score: {top2.semantic_score:.3f} | Keyword Score: {top2.keyword_score:.3f} | Hybrid: {top2.hybrid_score:.3f}")
    print(f"  Rationale: {top2.retrieval_rationale}")
    assert "106" in top2.title or "Anthony" in top2.title or "Transfer of Property" in str(top2.statutory_provisions)
    print("[PASS] Tenancy dispute correctly matched to Section 106 Transfer of Property Act.")

    # 3. Test Query 3: Exact Statutory Section (Where Keywords Excel)
    print("\n--- 3. Evaluating Exact Statutory Citation (Hybrid Keyword Power) ---")
    query3 = "Section 138 dishonour of cheque"
    print(f"Statutory Query: \"{query3}\"")
    
    req3 = SemanticSearchRequest(query=query3, alpha=0.5, limit=3)
    results3 = engine.search(req3)
    assert len(results3) > 0
    top3 = results3[0]
    print(f"Top Retrieved: {top3.title}")
    print(f"  Semantic Score: {top3.semantic_score:.3f} | Keyword Score: {top3.keyword_score:.3f} | Hybrid: {top3.hybrid_score:.3f}")
    assert "138" in top3.title
    print("[PASS] Exact statutory reference prioritized via hybrid keyword-semantic scoring.")

    # 4. Test SIH Benchmark Comparison (Keyword vs Semantic vs Hybrid)
    print("\n--- 4. Benchmarking Side-by-Side: Keyword vs Semantic vs Hybrid ---")
    benchmark = engine.compare_retrieval_methods("My employer fired me without notice", limit=2)
    print(f"Benchmark Analysis:\n  {benchmark.benchmark_analysis}")
    print(f"Keyword-only top result : {benchmark.keyword_only_results[0].title if benchmark.keyword_only_results else 'None'}")
    print(f"Semantic-only top result: {benchmark.semantic_only_results[0].title if benchmark.semantic_only_results else 'None'}")
    print(f"Hybrid top result       : {benchmark.hybrid_results[0].title if benchmark.hybrid_results else 'None'}")
    assert len(benchmark.semantic_only_results) > 0
    print("[PASS] Side-by-side benchmark comparison verified.")

    # 5. Guardrail Notice Verification
    print("\n--- 5. Legal Guardrail Disclaimer Verification ---")
    for r in results1:
        assert len(r.legal_guardrail_notice) > 20
        assert "NOT indicate likelihood of winning" in r.legal_guardrail_notice
    print(f"[PASS] Mandatory SIH guardrail verified on all retrieved candidates: \"{results1[0].legal_guardrail_notice}\"")

    # 6. Test FastAPI Search Endpoints via TestClient
    print("\n--- 6. Testing FastAPI Search Endpoints ---")
    client = TestClient(app)

    post_res = client.post("/api/v1/search/hybrid", json={"query": "cheque bounce 15 days", "alpha": 0.6})
    assert post_res.status_code == 200, f"Hybrid search failed: {post_res.text}"
    post_data = post_res.json()
    assert post_data["total_results"] > 0
    print(f"[PASS] POST /api/v1/search/hybrid returned {post_data['total_results']} results")

    get_compare = client.get("/api/v1/search/compare", params={"q": "My employer fired me"})
    assert get_compare.status_code == 200, f"Compare failed: {get_compare.text}"
    print("[PASS] GET /api/v1/search/compare verified")

    print("\n" + "=" * 75)
    print(">>> ALL PHASE 6 TESTS PASSED! HYBRID SEMANTIC SEARCH VERIFIED. <<<")
    print("=" * 75)

if __name__ == "__main__":
    test_semantic_search_evaluation()
