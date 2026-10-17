from typing import List, Optional
from pydantic import BaseModel, Field

class SearchResultItem(BaseModel):
    """
    A retrieved legal passage with hybrid scoring and explainable rationale.
    """
    doc_id: str
    doc_type: str = Field(..., description="'STATUTE' or 'CASE_LAW'")
    title: str
    citation: Optional[str] = None
    court_or_authority: Optional[str] = None
    source_url: str
    
    # Relevance Scores
    semantic_score: float = Field(..., description="Dense semantic cosine similarity (0.0 to 1.0)")
    keyword_score: float = Field(..., description="Sparse lexical/TF-IDF keyword score (0.0 to 1.0)")
    hybrid_score: float = Field(..., description="Weighted ensemble retrieval score (0.0 to 1.0)")
    
    # Key Content & Precedent
    statutory_provisions: List[str] = Field(default_factory=list)
    legal_issues: List[str] = Field(default_factory=list)
    ratio_decidendi: Optional[str] = None
    content_snippet: str
    
    # SIH Explainability & Guardrail
    retrieval_rationale: str = Field(..., description="Explains why this law or judgment was retrieved for user's query")
    legal_guardrail_notice: str = Field(
        default="Similarity score reflects linguistic relevance only and does NOT indicate likelihood of winning or legal equivalence.",
        description="Mandatory legal disclaimer"
    )

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language legal query or factual scenario")
    doc_type: Optional[str] = Field(None, description="Filter by 'STATUTE' or 'CASE_LAW'")
    alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight: 1.0 = Pure Semantic, 0.0 = Pure Keyword, 0.7 = Balanced Hybrid")
    limit: int = Field(default=5, ge=1, le=20)

class SemanticSearchResponse(BaseModel):
    query: str
    total_results: int
    alpha: float
    results: List[SearchResultItem]

class CompareSearchMethodsResponse(BaseModel):
    query: str
    keyword_only_results: List[SearchResultItem]
    semantic_only_results: List[SearchResultItem]
    hybrid_results: List[SearchResultItem]
    benchmark_analysis: str
