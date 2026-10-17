from fastapi import APIRouter, Query
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    CompareSearchMethodsResponse
)
from app.retrieval.hybrid_search import get_hybrid_search_engine

router = APIRouter()

@router.post(
    "/hybrid",
    response_model=SemanticSearchResponse,
    summary="Hybrid semantic legal search",
    description="Combines dense transformer embeddings with sparse TF-IDF keyword indexing to retrieve relevant statutes and case laws."
)
async def hybrid_search_endpoint(payload: SemanticSearchRequest) -> SemanticSearchResponse:
    engine = get_hybrid_search_engine()
    results = engine.search(payload)
    return SemanticSearchResponse(
        query=payload.query,
        total_results=len(results),
        alpha=payload.alpha,
        results=results
    )

@router.get(
    "/compare",
    response_model=CompareSearchMethodsResponse,
    summary="Compare Keyword vs Semantic vs Hybrid retrieval",
    description="Runs all three retrieval paradigms side-by-side to showcase semantic generalization over traditional keyword search."
)
async def compare_search_endpoint(
    q: str = Query(..., min_length=3, description="Natural language legal query"),
    limit: int = Query(3, ge=1, le=10)
) -> CompareSearchMethodsResponse:
    engine = get_hybrid_search_engine()
    return engine.compare_retrieval_methods(query=q, limit=limit)
