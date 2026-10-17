from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentSegment(BaseModel):
    """
    Represents a discrete structural unit of an uploaded document
    (e.g., Page 1 of a PDF, or Paragraph/Table in a DOCX).
    """
    segment_index: int = Field(..., description="Zero-based index of the segment")
    reference_type: str = Field(..., description="Type of segment: 'page', 'paragraph', or 'table'")
    reference_label: str = Field(..., description="Human-readable citation label, e.g., 'Page 1', 'Table 1'")
    content: str = Field(..., description="Extracted raw text content of the segment")
    char_count: int = Field(..., description="Character count of this segment")

class DocumentExtractionResponse(BaseModel):
    """
    Structured extraction response returned after analyzing a document.
    """
    filename: str = Field(..., description="Name of the uploaded file")
    file_type: str = Field(..., description="Detected file extension/type (.pdf or .docx)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    total_segments: int = Field(..., description="Total count of structural segments extracted")
    total_characters: int = Field(..., description="Total characters extracted across all segments")
    has_readable_text: bool = Field(..., description="Whether readable text was detected (False indicates scanned/image file)")
    segments: List[DocumentSegment] = Field(..., description="List of structural segments with preserved references")
    preview: str = Field(..., description="First 500 characters of extracted text for quick verification")
    warning: Optional[str] = Field(None, description="Actionable warning, e.g., if OCR is required")
