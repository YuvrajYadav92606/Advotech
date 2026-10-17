from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.nlp import EntityItem

class ClassifiedStatement(BaseModel):
    """
    A segmented document sentence labeled by its epistemic nature:
    FACT (verifiable event), ALLEGATION (unproven party claim),
    DEMAND_OR_OBLIGATION (required action), or LEGAL_REASONING.
    """
    statement_index: int
    text: str
    epistemic_type: str = Field(..., description="'FACT', 'ALLEGATION', 'DEMAND_OR_OBLIGATION', or 'LEGAL_REASONING'")
    segment_reference: Optional[str] = Field(None, description="Page or Paragraph label")
    confidence: float

class LegalIssue(BaseModel):
    """
    Identified substantive or procedural legal issue.
    """
    issue_title: str
    category: str
    explanation: str
    relevant_statutes: List[str]

class StructuredLegalAnalysisReport(BaseModel):
    """
    Comprehensive citizen-centric legal document intelligence report.
    """
    document_name: str
    document_category: str = Field(..., description="e.g. CHEQUE_BOUNCE_NOTICE, TENANCY_EVICTION_NOTICE")
    category_display_name: str = Field(..., description="Human-friendly label e.g. 'Cheque Dishonour Notice (Sec 138 NI Act)'")
    classification_confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    top_predictive_keywords: List[str] = Field(default_factory=list, description="Top TF-IDF signals driving this classification")
    
    # Executive Overview
    summary: str
    
    # Identified Parties
    sender_or_claimant: Optional[str]
    recipient_or_respondent: Optional[str]
    
    # Epistemic Breakdown (Critical Rule: Preserve allegations as allegations, not facts)
    facts: List[str] = Field(default_factory=list, description="Explicit stated facts (dates, cheque numbers, agreements)")
    allegations: List[str] = Field(default_factory=list, description="Claims made by the sender (not established facts)")
    demands_and_obligations: List[str] = Field(default_factory=list, description="Actions demanded of the recipient")
    
    # Actionable Specifics
    actionable_deadlines: List[str]
    monetary_claims: List[str]
    statutory_provisions_invoked: List[str]
    
    # Legal Issues & Strategic Advisory Guidance
    legal_issues: List[LegalIssue]
    missing_information_or_ambiguities: List[str] = Field(default_factory=list)
    suggested_advocate_questions: List[str] = Field(
        default_factory=list,
        description="Crucial legal questions the citizen should discuss with a qualified advocate"
    )
    
    # Raw Grounding Entities
    entities_by_category: Dict[str, List[str]]
