import os

class Settings:
    PROJECT_NAME: str = "Advo टेक"
    PROJECT_FULL_NAME: str = "Advo टेक — Verified AI for Legal Knowledge & Document Intelligence"
    API_V1_PREFIX: str = "/api/v1"
    
    # 20 MB max file upload size limit
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx"}
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

settings = Settings()
