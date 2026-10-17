from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["System"])
async def health_check():
    """
    Returns service health status and project metadata.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "full_name": settings.PROJECT_FULL_NAME,
        "version": "1.0.0",
        "supported_formats": list(settings.ALLOWED_EXTENSIONS)
    }
