from fastapi import APIRouter
from app.api.endpoints import health, documents, nlp

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(documents.router, prefix="/documents", tags=["Document Ingestion"])
api_router.include_router(nlp.router, prefix="/nlp", tags=["Legal NLP Intelligence"])
