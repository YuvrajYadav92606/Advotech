from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from app.schemas.rag import CitationItem, EpistemicFactCheck

class DocumentRole(str, Enum):
    LEGAL_NOTICE = "LEGAL_NOTICE"
    CONTRACT_AGREEMENT = "CONTRACT_AGREEMENT"
    BANK_MEMO = "BANK_MEMO"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT"
    CORRESPONDENCE = "CORRESPONDENCE"
    COURT_ORDER = "COURT_ORDER"
    SUPPORTING_EVIDENCE = "SUPPORTING_EVIDENCE"
    OTHER = "OTHER"

class CaseDocumentItem(BaseModel):
    doc_id: str = Field(..., description="Unique document ID within the case")
    filename: str = Field(..., description="Original filename")
    doc_role: DocumentRole = Field(default=DocumentRole.OTHER, description="Identified role of document in case")
    file_type: str = Field(..., description="File format (.pdf, .docx, or text)")
    char_count: int
    segment_count: int
    text_content: str
    key_entities: Dict[str, List[str]] = Field(default_factory=dict)
    uploaded_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class CaseTimelineEvent(BaseModel):
    event_date: str = Field(..., description="Extracted date or chronological marker")
    event_description: str = Field(..., description="Description of the event across documents")
    source_doc_filename: str = Field(..., description="Document in which this event was recorded")
    citation_pointer: str = Field(..., description="Pinpoint reference (e.g. 'Page 1, Para 2')")
    epistemic_nature: str = Field(default="FACT", description="FACT vs ALLEGATION")

class CaseDiscrepancyItem(BaseModel):
    issue_type: str = Field(..., description="Category: 'MONETARY_MISMATCH', 'DATE_ANOMALY', 'UNSUPPORTED_CLAIM', 'MISSING_EVIDENCE'")
    description: str = Field(..., description="Clear explanation of the conflict or inconsistency")
    involved_documents: List[str] = Field(..., description="Filenames of conflicting documents")
    severity: str = Field(default="MEDIUM", description="'HIGH', 'MEDIUM', 'LOW'")
    advocate_action: str = Field(..., description="Recommended question or action for legal counsel")

class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Title of the legal case / matter")
    description: Optional[str] = Field(None, description="Optional background overview of the dispute")
    category: Optional[str] = Field(default="GENERAL_LEGAL_DISPUTE", description="Dispute category")

class CaseSummaryReport(BaseModel):
    case_id: str
    title: str
    dispute_category: str
    total_documents: int
    documents: List[Dict[str, Any]]
    chronological_timeline: List[CaseTimelineEvent]
    identified_parties: Dict[str, List[str]] = Field(default_factory=dict, description="Aligned parties across all documents")
    aligned_monetary_claims: List[Dict[str, Any]] = Field(default_factory=list)
    cross_document_discrepancies: List[CaseDiscrepancyItem]
    missing_supporting_documents: List[str]
    strategic_advocate_questions: List[str]
    governing_statutes_identified: List[str]

class CaseQARequest(BaseModel):
    question: str = Field(..., min_length=3, description="User's question requiring cross-document synthesis")
    language: str = Field(default="en", description="'en', 'hi', 'hinglish'")
    max_sources: int = Field(default=5)

class CaseQAResponse(BaseModel):
    case_id: str
    question: str
    answer: str
    synthesis_engine: str
    multi_doc_citations: List[CitationItem]
    epistemic_check: EpistemicFactCheck
    documents_referenced: List[str]
    confidence_score: float
    limitations: List[str]
    suggested_advocate_questions: List[str]
