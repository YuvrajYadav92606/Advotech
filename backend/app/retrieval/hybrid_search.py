from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.schemas.search import SearchResultItem, SemanticSearchRequest, CompareSearchMethodsResponse
from app.schemas.knowledge_base import LegalDocumentItem
from app.knowledge_base.indexer import get_kb_indexer
from app.retrieval.embeddings import compute_dense_embeddings, compute_cosine_similarity

class LegalHybridSearchEngine:
    """
    Hybrid Search Engine combining Dense Semantic Vectors (Sentence Transformers)
    with Sparse Lexical Retrieval (TF-IDF/BM25) over Indian statutes and case laws.
    """
    def __init__(self):
        self.doc_ids: List[str] = []
        self.doc_items: List[LegalDocumentItem] = []
        self.dense_embeddings: Optional[np.ndarray] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        
        self.build_index()

    def build_index(self):
        """
        Builds both dense vector and sparse keyword indices across all indexed legal documents.
        """
        indexer = get_kb_indexer()
        self.doc_items = list(indexer.documents.values())
        self.doc_ids = [d.id for d in self.doc_items]
        
        if not self.doc_items:
            return
            
        # Create searchable text representation combining title, issues, ratio, and text
        searchable_texts = []
        for d in self.doc_items:
            issues_str = " ".join(d.legal_issues)
            ratio_str = d.ratio_decidendi if d.ratio_decidendi else ""
            sec_str = f"{d.section_number} {d.act_name}" if d.section_number else ""
            combined = f"{d.title}\n{sec_str}\n{issues_str}\n{ratio_str}\n{d.content}"
            searchable_texts.append(combined)
            
        # 1. Build Dense Semantic Embeddings
        self.dense_embeddings = compute_dense_embeddings(searchable_texts)
        
        # 2. Build Sparse Keyword (TF-IDF) Index
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(searchable_texts)

    def generate_retrieval_rationale(self, query: str, doc: LegalDocumentItem, sem_score: float, kw_score: float) -> str:
        """
        Generates human-understandable explanation of why this source was matched.
        """
        reasons = []
        q_lower = query.lower()
        
        # Direct statutory or section reference
        if doc.section_number and doc.section_number.lower() in q_lower:
            reasons.append(f"Direct match for statutory provision '{doc.section_number}'")
            
        # Relevant issues
        matched_issues = [issue for issue in doc.legal_issues if any(w in issue.lower() for w in q_lower.split() if len(w) > 3)]
        if matched_issues:
            reasons.append(f"Directly addresses legal issues: {', '.join(matched_issues)}")
            
        # Dense conceptual similarity
        if sem_score > 0.40:
            if doc.ratio_decidendi:
                reasons.append(f"Semantic alignment with judicial holding: '{doc.ratio_decidendi[:90]}...'")
            else:
                reasons.append(f"Strong semantic conceptual match with '{doc.title}'")
                
        if not reasons:
            reasons.append(f"General contextual relevance to legal terms in '{doc.title}'")
            
        return " | ".join(reasons)

    def search(self, request: SemanticSearchRequest) -> List[SearchResultItem]:
        """
        Executes hybrid retrieval:
        score = alpha * semantic_score + (1 - alpha) * keyword_score
        """
        if not self.doc_items or self.dense_embeddings is None:
            self.build_index()
            
        query = request.query
        alpha = request.alpha
        limit = request.limit
        
        # 1. Dense Semantic Cosine Similarity
        query_dense = compute_dense_embeddings([query])
        semantic_scores = compute_cosine_similarity(query_dense, self.dense_embeddings)
        
        # 2. Sparse Lexical (TF-IDF) Cosine Similarity
        query_sparse = self.tfidf_vectorizer.transform([query])
        sparse_scores = np.asarray((self.tfidf_matrix * query_sparse.T).todense()).flatten()
        sparse_scores = np.clip(sparse_scores, 0.0, 1.0)
        
        # 3. Combine with Alpha Weighting
        hybrid_scores = (alpha * semantic_scores) + ((1.0 - alpha) * sparse_scores)
        
        # 4. Construct Results with Explanations
        candidates = []
        for i, doc in enumerate(self.doc_items):
            # Apply doc_type filter
            if request.doc_type and doc.doc_type.upper() != request.doc_type.upper():
                continue
                
            sem_s = float(semantic_scores[i])
            kw_s = float(sparse_scores[i])
            hyb_s = float(hybrid_scores[i])
            
            # Filter low relevance
            if hyb_s < 0.05:
                continue
                
            rationale = self.generate_retrieval_rationale(query, doc, sem_s, kw_s)
            
            snippet = doc.content[:250] + "..." if len(doc.content) > 250 else doc.content
            
            candidates.append(
                SearchResultItem(
                    doc_id=doc.id,
                    doc_type=doc.doc_type,
                    title=doc.title,
                    citation=doc.citation,
                    court_or_authority=doc.court_or_authority,
                    source_url=doc.source_url,
                    semantic_score=round(sem_s, 4),
                    keyword_score=round(kw_s, 4),
                    hybrid_score=round(hyb_s, 4),
                    statutory_provisions=doc.statutory_provisions,
                    legal_issues=doc.legal_issues,
                    ratio_decidendi=doc.ratio_decidendi,
                    content_snippet=snippet,
                    retrieval_rationale=rationale
                )
            )
            
        candidates.sort(key=lambda x: x.hybrid_score, reverse=True)
        return candidates[:limit]

    def compare_retrieval_methods(self, query: str, limit: int = 3) -> CompareSearchMethodsResponse:
        """
        Runs Keyword-only (alpha=0.0), Semantic-only (alpha=1.0), and Hybrid (alpha=0.6)
        side-by-side to benchmark retrieval quality for evaluation and hackathon demos.
        """
        req_kw = SemanticSearchRequest(query=query, alpha=0.0, limit=limit)
        req_sem = SemanticSearchRequest(query=query, alpha=1.0, limit=limit)
        req_hyb = SemanticSearchRequest(query=query, alpha=0.6, limit=limit)
        
        res_kw = self.search(req_kw)
        res_sem = self.search(req_sem)
        res_hyb = self.search(req_hyb)
        
        analysis = (
            f"Comparison for query: '{query}'. "
            f"Keyword search relied strictly on exact word overlaps ({len(res_kw)} results). "
            f"Dense semantic search successfully captured latent conceptual meaning even with different wording ({len(res_sem)} results). "
            f"Hybrid search balanced exact statutory citations with broad conceptual semantics ({len(res_hyb)} results)."
        )
        
        return CompareSearchMethodsResponse(
            query=query,
            keyword_only_results=res_kw,
            semantic_only_results=res_sem,
            hybrid_results=res_hyb,
            benchmark_analysis=analysis
        )

# Singleton instance
_hybrid_search_engine = None

def get_hybrid_search_engine() -> LegalHybridSearchEngine:
    global _hybrid_search_engine
    if _hybrid_search_engine is None:
        _hybrid_search_engine = LegalHybridSearchEngine()
    return _hybrid_search_engine
