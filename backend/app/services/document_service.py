import os
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings
from app.schemas.document import DocumentExtractionResponse
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.docx_extractor import extract_text_from_docx

async def process_document_upload(file: UploadFile) -> DocumentExtractionResponse:
    """
    Validates, reads, and extracts structured text and references from an uploaded legal document.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename."
        )
        
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
        
    # Read file contents into memory safely
    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )
        
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of {max_mb} MB."
        )
        
    # Extract according to format
    try:
        if ext == ".pdf":
            segments, total_chars, has_readable_text = extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            segments, total_chars, has_readable_text = extract_text_from_docx(file_bytes)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Handler for extension '{ext}' not implemented."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse document: {str(e)}"
        )
        
    # Generate unified preview snippet
    all_text = "\n\n".join(seg.content for seg in segments if seg.content)
    preview = all_text[:500] if all_text else ""
    
    warning = None
    if not has_readable_text:
        warning = (
            "No extractable text layer detected. This file appears to be a scanned document or image. "
            "OCR (Optical Character Recognition) will be applied in upcoming Phase 1 enhancements."
        )
        
    return DocumentExtractionResponse(
        filename=file.filename,
        file_type=ext,
        file_size_bytes=file_size,
        total_segments=len(segments),
        total_characters=total_chars,
        has_readable_text=has_readable_text,
        segments=segments,
        preview=preview,
        warning=warning
    )
