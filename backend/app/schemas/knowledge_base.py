from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LegalDocumentItem(BaseModel):
    """
    Unified schema for both Statutory Provisions and Indian Court Judgments.
    Designed to be 100% compatible with ML training datasets (ILDC, LegalEval, HuggingFace datasets).
    """
    id: str = Field(..., description="Unique legal document identifier, e.g. 'ACT_NI_1881_SEC_138' or 'SC_2001_DALMIA_CEMENT'")
    doc_type: str = Field(..., description="'STATUTE' or 'CASE_LAW'")
    title: str = Field(..., description="Formal legal title or case cause title (e.g. 'Dalmia Cement v. Galaxy Traders')")
    court_or_authority: Optional[str] = Field(None, description="e.g. 'Supreme Court of India', 'High Court of Delhi', or 'Parliament of India'")
    jurisdiction: str = Field(default="India", description="Applicable jurisdiction e.g. 'India' or specific state")
    decision_or_enactment_date: Optional[str] = Field(None, description="ISO format date (YYYY-MM-DD) or year")
    citation: Optional[str] = Field(None, description="Official legal citation e.g. '(2001) 1 SCC 631' or 'Act No. 26 of 1881'")
    
    # Statutory Specifics
    act_name: Optional[str] = Field(None, description="Parent statute name")
    section_number: Optional[str] = Field(None, description="Specific statutory section or article")
    is_amended_or_superseded: bool = Field(default=False, description="Flag tracking if amended or superseded (e.g. IPC -> BNS)")
    superseded_by: Optional[str] = Field(None, description="Successor statute or amendment details")
    
    # Case Law Specifics (For AI Training & Ratio Decidendi Extraction)
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    statutory_provisions: List[str] = Field(default_factory=list, description="Statutes interpreted in this judgment")
    legal_issues: List[str] = Field(default_factory=list, description="Substantive legal questions addressed")
    ratio_decidendi: Optional[str] = Field(None, description="Core legal holding or binding precedent of the court")
    
    # Content & Provenance
    content: str = Field(..., description="Full text or official operative text of the provision/judgment")
    source_url: str = Field(..., description="Verifiable authoritative source URL (India Code, SCI, eCourts)")
    
    # ML / Model Training Metadata
    dataset_source: Optional[str] = Field(default="AdvoTech_Curated", description="Source dataset tag (e.g. ILDC, SCI, IndiaCode)")
    training_split: Optional[str] = Field(default="train", description="'train', 'validation', or 'test'")

class KBSearchQuery(BaseModel):
    query: str = Field(..., min_length=2, description="Keywords, section numbers, or legal topic to search")
    doc_type: Optional[str] = Field(None, description="Filter by 'STATUTE' or 'CASE_LAW'")
    court: Optional[str] = Field(None, description="Filter by court e.g. 'Supreme Court of India'")
    active_only: bool = Field(default=True, description="If True, hides superseded provisions")
    limit: int = Field(default=10, ge=1, le=50)

class KBSearchResponse(BaseModel):
    total_results: int
    query: str
    results: List[LegalDocumentItem]

class KBStatistics(BaseModel):
    total_documents: int
    total_statutes: int
    total_case_laws: int
    categories: Dict[str, int]
    courts: Dict[str, int]
    training_splits: Dict[str, int]
