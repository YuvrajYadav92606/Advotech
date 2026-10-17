from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.knowledge_base import (
    LegalDocumentItem,
    KBSearchQuery,
    KBSearchResponse,
    KBStatistics
)
from app.knowledge_base.indexer import get_kb_indexer

router = APIRouter()

@router.get(
    "/search",
    response_model=KBSearchResponse,
    summary="Search Indian statutes and case laws",
    description="Retrieve authoritative legislation from India Code and landmark Supreme Court judgments."
)
async def search_legal_knowledge(
    q: str = Query(..., min_length=2, description="Search term, section number, or legal concept"),
    doc_type: Optional[str] = Query(None, description="'STATUTE' or 'CASE_LAW'"),
    court: Optional[str] = Query(None, description="Filter by court e.g. 'Supreme Court'"),
    active_only: bool = Query(True, description="Exclude superseded or historical statutes (e.g. IPC)"),
    limit: int = Query(10, ge=1, le=50)
) -> KBSearchResponse:
    indexer = get_kb_indexer()
    search_query = KBSearchQuery(
        query=q,
        doc_type=doc_type,
        court=court,
        active_only=active_only,
        limit=limit
    )
    results = indexer.search(search_query)
    return KBSearchResponse(
        total_results=len(results),
        query=q,
        results=results
    )

@router.get(
    "/documents/{doc_id}",
    response_model=LegalDocumentItem,
    summary="Retrieve full legal document by ID",
    description="Fetches full statutory text or court judgment with complete citation and source provenance."
)
async def get_document(doc_id: str) -> LegalDocumentItem:
    indexer = get_kb_indexer()
    doc = indexer.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Legal document with ID '{doc_id}' not found in knowledge base."
        )
    return doc

@router.get(
    "/stats",
    response_model=KBStatistics,
    summary="Get knowledge base and ML training dataset statistics",
    description="Returns metrics on indexed statutes, landmark cases, courts, and training split distributions."
)
async def get_kb_stats() -> KBStatistics:
    indexer = get_kb_indexer()
    return indexer.get_statistics()

@router.get(
    "/export-dataset",
    summary="Export corpus for ML training and fine-tuning",
    description="Returns preprocessed training instances for legal NLP models (InLegalBERT / classification)."
)
async def export_training_data(
    split: Optional[str] = Query(None, description="Filter by split: 'train', 'validation', or 'test'")
) -> List[Dict[str, Any]]:
    indexer = get_kb_indexer()
    return indexer.export_training_dataset(split=split)
