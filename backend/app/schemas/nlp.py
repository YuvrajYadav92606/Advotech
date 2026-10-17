from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class EntityItem(BaseModel):
    """
    An identified entity in legal text (e.g., Section 138, Rs. 2,50,000, 15 days).
    """
    text: str = Field(..., description="The exact entity text extracted from document")
    label: str = Field(..., description="Entity category: PERSON, ORG, COURT, LAW, LEGAL_SECTION, DEADLINE, MONEY, etc.")
    start_char: int = Field(..., description="Start character offset")
    end_char: int = Field(..., description="End character offset")
    source: str = Field(..., description="Extraction source: 'legal_pattern_engine' or 'spacy_statistical'")
    segment_reference: Optional[str] = Field(None, description="Page or Paragraph label where this entity appears")

class SentenceItem(BaseModel):
    """
    Individual segmented sentence with metadata.
    """
    index: int = Field(..., description="Sentence index")
    text: str = Field(..., description="Sentence text content")
    token_count: int = Field(..., description="Number of tokens in the sentence")
    segment_reference: Optional[str] = Field(None, description="Source page/paragraph")

class PreprocessingSummary(BaseModel):
    """
    Summary metrics from the NLP preprocessing pipeline.
    """
    total_characters: int
    total_tokens: int
    total_sentences: int
    sentences: List[SentenceItem]

class TextAnalysisRequest(BaseModel):
    """
    Request model for analyzing raw legal text snippet.
    """
    text: str = Field(..., min_length=5, description="Legal text to analyze")

class DocumentNLPAnalysisResponse(BaseModel):
    """
    Full structured NLP intelligence response for a document or text.
    """
    document_name: Optional[str] = Field(None, description="Filename if uploaded")
    preprocessing: PreprocessingSummary
    entities_by_category: Dict[str, List[str]] = Field(
        ..., 
        description="Entities grouped by legal category (COURT, LEGAL_SECTION, LAW, DEADLINE, MONEY, etc.)"
    )
    all_entities: List[EntityItem] = Field(..., description="Flat list of all extracted entities with character spans")
    actionable_deadlines: List[str] = Field(
        default_factory=list,
        description="High-priority deadlines and notice cure periods extracted from text"
    )
    monetary_obligations: List[str] = Field(
        default_factory=list,
        description="Monetary demands or settlement figures identified in text"
    )
