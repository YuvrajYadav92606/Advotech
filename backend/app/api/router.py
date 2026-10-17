from fastapi import APIRouter
from app.api.endpoints import health, documents, nlp, analysis, simplification, knowledge_base, search, rag, cases

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(documents.router, prefix="/documents", tags=["Document Ingestion"])
api_router.include_router(nlp.router, prefix="/nlp", tags=["Legal NLP Intelligence"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Structured Legal Analysis"])
api_router.include_router(simplification.router, prefix="/simplification", tags=["Legal Language Simplification"])
api_router.include_router(knowledge_base.router, prefix="/kb", tags=["Indian Legal Knowledge Base"])
api_router.include_router(search.router, prefix="/search", tags=["Semantic Legal Search"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG & Legal Q&A"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case-Aware Multi-Document Workspaces"])
