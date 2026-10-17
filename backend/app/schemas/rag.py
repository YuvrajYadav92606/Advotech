from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    UPLOADED_DOCUMENT = "UPLOADED_DOCUMENT"
    STATUTE = "STATUTE"
    CASE_LAW = "CASE_LAW"
    AI_INFERENCE = "AI_INFERENCE"

class EpistemicNature(str, Enum):
    FACT = "FACT"
    ALLEGATION = "ALLEGATION"
    DEMAND = "DEMAND"
    LEGAL_REASONING = "LEGAL_REASONING"
    STATUTORY_RULE = "STATUTORY_RULE"
    JUDICIAL_RATIO = "JUDICIAL_RATIO"
    INFERENCE = "INFERENCE"

class CitationItem(BaseModel):
    citation_id: str = Field(..., description="Unique citation marker, e.g. [Doc: Para 2] or [Statute: NI Act Sec 138]")
    source_type: SourceType = Field(..., description="Category of legal source")
    title: str = Field(..., description="Source document or law title")
    reference_pointer: str = Field(..., description="Pinpoint reference (e.g. 'Clause 3', 'Section 138', 'Para 12')")
    quote_snippet: str = Field(..., description="Verbatim text quote from source")
    epistemic_nature: EpistemicNature = Field(..., description="Epistemic status of the cited content")
    relevance_score: float = Field(..., description="Retrieval similarity confidence score")

class EpistemicFactCheck(BaseModel):
    explicit_facts: List[str] = Field(default_factory=list, description="Verified facts explicitly stated in document context")
    allegations: List[str] = Field(default_factory=list, description="Unproven claims or allegations made by an opposing party")
    demands_obligations: List[str] = Field(default_factory=list, description="Demands, deadlines, or monetary requisitions")
    governing_statutes: List[str] = Field(default_factory=list, description="Relevant statutory sections retrieved from legal KB")
    judicial_precedents: List[str] = Field(default_factory=list, description="Binding or persuasive judicial precedents retrieved")
    ai_inferences: List[str] = Field(default_factory=list, description="Interpretive deductions or synthesis made by the AI model")

class RAGQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User's query or legal question in plain language")
    document_text: Optional[str] = Field(None, description="Optional uploaded document content for contextual Q&A")
    document_id: Optional[str] = Field(None, description="Optional stored document ID")
    max_sources: int = Field(default=4, ge=1, le=10, description="Maximum number of external legal sources to retrieve")
    language: str = Field(default="en", description="Output language preference ('en', 'hi', 'hinglish')")

class RAGAnswerResponse(BaseModel):
    question: str
    answer: str = Field(..., description="Clear, source-grounded explanation with inline citation markers")
    synthesis_engine: str = Field(..., description="Name of the generation engine (Gemini API or Offline Grounded Synthesizer)")
    citations: List[CitationItem] = Field(default_factory=list, description="List of granular sources cited in the response")
    epistemic_check: EpistemicFactCheck = Field(..., description="Formal segregation of facts, allegations, statutes, and inferences")
    confidence_score: float = Field(..., description="Overall confidence based on source relevance")
    limitations: List[str] = Field(default_factory=list, description="Explicit statements of missing information or boundaries")
    suggested_advocate_questions: List[str] = Field(default_factory=list, description="Tailored questions to ask a practicing advocate")
    legal_disclaimer: str = Field(
        default="Advo टेक provides educational and informational document intelligence. This analysis does not constitute formal legal advice or create an advocate-client relationship. Please consult a licensed advocate for legal proceedings.",
        description="Mandatory legal disclaimer"
    )

class EngineStatusResponse(BaseModel):
    engine_name: str
    gemini_api_configured: bool
    offline_fallback_ready: bool
    supported_languages: List[str]
    capabilities: List[str]
