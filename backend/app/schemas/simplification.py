from typing import List, Optional
from pydantic import BaseModel, Field

class SimplifiedClause(BaseModel):
    """
    A paired legal clause and its simplified, citizen-friendly translations.
    """
    clause_index: int
    original_text: str = Field(..., description="Original formal legal wording")
    simplified_english: str = Field(..., description="Simplified plain English explanation")
    simplified_hindi: Optional[str] = Field(None, description="Simple Hindi translation for vernacular accessibility")
    simplified_hinglish: Optional[str] = Field(None, description="Conversational Hinglish explanation")
    epistemic_type: str = Field(..., description="FACT, ALLEGATION, DEMAND_OR_OBLIGATION, or LEGAL_REASONING")
    preserved_entities: List[str] = Field(default_factory=list, description="Preserved critical entities (amounts, deadlines, dates)")
    fidelity_check_passed: bool = Field(..., description="True if key obligations and deadlines were verified as preserved")
    segment_reference: Optional[str] = Field(None, description="Page or Paragraph citation")

class SimplificationRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Legal text to simplify")

class DocumentSimplificationResponse(BaseModel):
    """
    Complete structured simplification output with preserved passage grounding.
    """
    document_name: Optional[str] = Field(None, description="Filename if uploaded")
    total_clauses: int
    clauses: List[SimplifiedClause]
    executive_summary_english: str
    executive_summary_hindi: str
    executive_summary_hinglish: str
    average_fidelity_score: float = Field(..., description="Percentage of clauses that preserved all critical entities and epistemic tone")
