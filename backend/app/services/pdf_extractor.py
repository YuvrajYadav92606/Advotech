import pymupdf
from typing import List, Tuple
from app.schemas.document import DocumentSegment

def extract_text_from_pdf(file_bytes: bytes) -> Tuple[List[DocumentSegment], int, bool]:
    """
    Extracts text page-by-page from PDF bytes using PyMuPDF.
    Preserves page number references for citations and RAG grounding.
    
    Returns:
        segments: List of DocumentSegment (one per page)
        total_chars: Total count of extracted characters
        has_readable_text: True if readable text is found, False if scanned/empty
    """
    segments: List[DocumentSegment] = []
    total_chars = 0
    
    # Open PDF from memory buffer
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text("text").strip()
            
            char_count = len(text)
            total_chars += char_count
            
            segments.append(
                DocumentSegment(
                    segment_index=page_index,
                    reference_type="page",
                    reference_label=f"Page {page_index + 1}",
                    content=text,
                    char_count=char_count
                )
            )
    finally:
        doc.close()
        
    # A threshold of 20 characters across the entire doc signifies whether text layer exists
    has_readable_text = total_chars > 20
    
    return segments, total_chars, has_readable_text
