import re
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from app.schemas.case_workspace import (
    DocumentRole,
    CaseDocumentItem,
    CaseTimelineEvent,
    CaseDiscrepancyItem,
    CaseSummaryReport,
    CaseQARequest,
    CaseQAResponse
)
from app.schemas.rag import CitationItem, EpistemicFactCheck, SourceType, EpistemicNature
from app.schemas.search import SemanticSearchRequest
from app.nlp.preprocessor import segment_sentences, clean_legal_text
from app.nlp.legal_entities import analyze_legal_text
from app.nlp.epistemic_parser import classify_sentence_epistemic
from app.retrieval.embeddings import compute_dense_embeddings, compute_cosine_similarity
from app.retrieval.hybrid_search import get_hybrid_search_engine
from app.services.llm_connector import LLMConnector
from app.services.analysis_service import generate_advocate_questions

# In-memory case storage
_cases_store: Dict[str, Dict[str, Any]] = {}

DATE_EXTRACTION_PATTERNS = [
    r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4})\b",
    r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b",
    r"\b(?:dated\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b"
]

def auto_detect_document_role(text: str, filename: str) -> DocumentRole:
    """
    Automatically classifies the structural legal role of an uploaded file within a case.
    """
    text_lower = text.lower()
    fn_lower = filename.lower()
    
    if any(w in fn_lower for w in ["notice", "demand"]) or any(w in text_lower for w in ["legal notice", "statutory notice", "demand notice", "hereby call upon"]):
        return DocumentRole.LEGAL_NOTICE
        
    if any(w in fn_lower for w in ["agreement", "contract", "mou"]) or any(w in text_lower for w in ["agreement", "contract", "witnesseth", "terms and conditions", "between the parties"]):
        return DocumentRole.CONTRACT_AGREEMENT
        
    if any(w in fn_lower for w in ["memo", "dishonour", "return"]) or any(w in text_lower for w in ["return memo", "bank memo", "funds insufficient", "exceeds arrangement", "cheque return"]):
        return DocumentRole.BANK_MEMO
        
    if any(w in fn_lower for w in ["receipt", "invoice", "bill"]) or any(w in text_lower for w in ["receipt", "invoice", "payment voucher", "received with thanks"]):
        return DocumentRole.PAYMENT_RECEIPT
        
    if any(w in fn_lower for w in ["order", "judgment", "decree"]) or any(w in text_lower for w in ["in the court of", "hon'ble", "ordered that", "petitioner", "respondent"]):
        return DocumentRole.COURT_ORDER
        
    if any(w in fn_lower for w in ["letter", "email", "mail"]) or any(w in text_lower for w in ["dear sir", "regards", "subject:"]):
        return DocumentRole.CORRESPONDENCE
        
    return DocumentRole.SUPPORTING_EVIDENCE

class CaseWorkspaceService:
    """
    Service managing multi-document case workspaces, cross-document timeline synthesis,
    discrepancy checking, and multi-file contextual Q&A.
    """

    def __init__(self):
        self.hybrid_engine = get_hybrid_search_engine()
        self.llm_connector = LLMConnector()

    def create_case(self, title: str, description: Optional[str] = None, category: str = "GENERAL_LEGAL_DISPUTE") -> str:
        case_id = f"case_{uuid.uuid4().hex[:10]}"
        _cases_store[case_id] = {
            "case_id": case_id,
            "title": title,
            "description": description,
            "category": category,
            "documents": {},
            "created_at": datetime.utcnow().isoformat()
        }
        return case_id

    def list_cases(self) -> List[Dict[str, Any]]:
        return [
            {
                "case_id": c["case_id"],
                "title": c["title"],
                "category": c["category"],
                "total_documents": len(c["documents"]),
                "created_at": c["created_at"]
            }
            for c in _cases_store.values()
        ]

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        return _cases_store.get(case_id)

    def add_document_to_case(
        self,
        case_id: str,
        filename: str,
        text_content: str,
        file_type: str = ".txt",
        custom_role: Optional[DocumentRole] = None
    ) -> CaseDocumentItem:
        case = _cases_store.get(case_id)
        if not case:
            raise ValueError(f"Case with ID '{case_id}' does not exist.")

        cleaned = clean_legal_text(text_content)
        role = custom_role or auto_detect_document_role(cleaned, filename)
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"

        # Extract NLP features & entities
        nlp_res = analyze_legal_text(cleaned, document_name=filename)
        segments = segment_sentences(cleaned)

        doc_item = CaseDocumentItem(
            doc_id=doc_id,
            filename=filename,
            doc_role=role,
            file_type=file_type,
            char_count=len(cleaned),
            segment_count=len(segments),
            text_content=cleaned,
            key_entities=nlp_res.entities_by_category
        )

        case["documents"][doc_id] = doc_item
        return doc_item

    def analyze_case(self, case_id: str) -> CaseSummaryReport:
        """
        Performs holistic multi-document intelligence across all files in the case:
        1. Unified chronological timeline construction
        2. Party identity alignment
        3. Cross-document monetary reconciliation
        4. Inconsistency and discrepancy detection (date anomalies, amount mismatches)
        5. Missing supporting documents audit
        """
        case = _cases_store.get(case_id)
        if not case:
            raise ValueError(f"Case with ID '{case_id}' does not exist.")

        docs: List[CaseDocumentItem] = list(case["documents"].values())
        if not docs:
            return CaseSummaryReport(
                case_id=case_id,
                title=case["title"],
                dispute_category=case["category"],
                total_documents=0,
                documents=[],
                chronological_timeline=[],
                cross_document_discrepancies=[],
                missing_supporting_documents=["No documents uploaded to this case workspace yet."],
                strategic_advocate_questions=[]
            )

        # 1. Cross-Document Timeline Construction
        timeline_events = self._build_cross_document_timeline(docs)

        # 2. Party Alignment
        parties_aligned: Dict[str, List[str]] = {"PERSON": [], "ORGANIZATION": []}
        for d in docs:
            for p in d.key_entities.get("PERSON", []):
                if p not in parties_aligned["PERSON"]:
                    parties_aligned["PERSON"].append(p)
            for org in d.key_entities.get("ORGANIZATION", []):
                if org not in parties_aligned["ORGANIZATION"]:
                    parties_aligned["ORGANIZATION"].append(org)

        # 3. Monetary Claims Alignment
        monetary_items = []
        for d in docs:
            amounts = d.key_entities.get("MONEY", [])
            for amt in amounts:
                monetary_items.append({
                    "amount": amt,
                    "document": d.filename,
                    "document_role": d.doc_role.value
                })

        # 4. Cross-Document Discrepancies and Inconsistencies
        discrepancies, missing_docs = self._detect_cross_document_conflicts(docs)

        # 5. Strategic Questions for Advocate
        advocate_questions = self._generate_case_advocate_questions(case["category"], discrepancies, docs)

        # 6. Governing Statutes Identified
        all_statutes = set()
        for d in docs:
            for s in d.key_entities.get("LAW", []):
                all_statutes.add(s)
            for sec in d.key_entities.get("LEGAL_SECTION", []):
                all_statutes.add(sec)

        return CaseSummaryReport(
            case_id=case_id,
            title=case["title"],
            dispute_category=case["category"],
            total_documents=len(docs),
            documents=[
                {
                    "doc_id": d.doc_id,
                    "filename": d.filename,
                    "role": d.doc_role.value,
                    "char_count": d.char_count,
                    "segment_count": d.segment_count
                }
                for d in docs
            ],
            chronological_timeline=timeline_events,
            identified_parties=parties_aligned,
            aligned_monetary_claims=monetary_items,
            cross_document_discrepancies=discrepancies,
            missing_supporting_documents=missing_docs,
            strategic_advocate_questions=advocate_questions,
            governing_statutes_identified=list(all_statutes)
        )

    def _build_cross_document_timeline(self, docs: List[CaseDocumentItem]) -> List[CaseTimelineEvent]:
        """
        Scans all documents, extracts dated events, classifies their epistemic status,
        and constructs an aligned chronological record.
        """
        events: List[CaseTimelineEvent] = []

        for d in docs:
            sentences = segment_sentences(d.text_content)
            for s in sentences:
                for pat in DATE_EXTRACTION_PATTERNS:
                    match = re.search(pat, s.text, re.IGNORECASE)
                    if match:
                        date_str = match.group(0).replace("dated", "").strip()
                        epistemic_type, _ = classify_sentence_epistemic(s.text)
                        
                        event_text = s.text.strip()
                        if len(event_text) > 180:
                            event_text = event_text[:177] + "..."

                        events.append(
                            CaseTimelineEvent(
                                event_date=date_str,
                                event_description=event_text,
                                source_doc_filename=d.filename,
                                citation_pointer=f"Line {s.index + 1}",
                                epistemic_nature="ALLEGATION" if epistemic_type == "ALLEGATION" else "FACT"
                            )
                        )
                        break

        # Deduplicate and sort
        unique_events = []
        seen = set()
        for ev in events:
            key = (ev.event_date.lower(), ev.source_doc_filename, ev.citation_pointer)
            if key not in seen:
                seen.add(key)
                unique_events.append(ev)

        return unique_events

    def _detect_cross_document_conflicts(
        self,
        docs: List[CaseDocumentItem]
    ) -> Tuple[List[CaseDiscrepancyItem], List[str]]:
        """
        Audits multi-document cases for evidentiary inconsistencies, monetary mismatches,
        and missing supporting documentation.
        """
        discrepancies: List[CaseDiscrepancyItem] = []
        missing_docs: List[str] = []

        roles_present = {d.doc_role for d in docs}
        all_text = " ".join([d.text_content.lower() for d in docs])

        # Check A: Missing Contract / Agreement
        if DocumentRole.LEGAL_NOTICE in roles_present and DocumentRole.CONTRACT_AGREEMENT not in roles_present:
            if any(w in all_text for w in ["agreement dated", "contract dated", "terms of agreement", "clause"]):
                missing_docs.append("Underlying Contract or Agreement (referenced in Legal Notice but not uploaded).")

        # Check B: Missing Bank Return Memo (Cheque Bounce)
        if any(w in all_text for w in ["138", "cheque bounce", "dishonour"]):
            if DocumentRole.BANK_MEMO not in roles_present:
                missing_docs.append("Bank Dishonour Return Memo (mandatory to establish 30-day statutory limitation under Sec 138(b) NI Act).")

        # Check C: Missing Postal Proof of Service
        if DocumentRole.LEGAL_NOTICE in roles_present and not any(w in all_text for w in ["tracking report", "consignment track", "postal receipt"]):
            missing_docs.append("Postal Consignment Receipt / Delivery Tracking Report (proof of notice service).")

        # Check D: Monetary Mismatch across Documents
        notice_docs = [d for d in docs if d.doc_role == DocumentRole.LEGAL_NOTICE]
        other_docs = [d for d in docs if d.doc_role != DocumentRole.LEGAL_NOTICE]

        if notice_docs and other_docs:
            notice_amounts = set(notice_docs[0].key_entities.get("MONEY", []))
            other_amounts = set()
            for od in other_docs:
                for amt in od.key_entities.get("MONEY", []):
                    other_amounts.add(amt)

            # If notice mentions an amount not found in supporting docs
            if notice_amounts and other_amounts and not notice_amounts.intersection(other_amounts):
                discrepancies.append(
                    CaseDiscrepancyItem(
                        issue_type="MONETARY_MISMATCH",
                        description=(
                            f"Notice claims monetary amount(s) {list(notice_amounts)}, which do not match "
                            f"the figures {list(other_amounts)} specified in attached supporting documents."
                        ),
                        involved_documents=[notice_docs[0].filename] + [od.filename for od in other_docs],
                        severity="HIGH",
                        advocate_action="Verify if the claim includes unagreed interest, damages, or penalty charges not specified in the primary instrument."
                    )
                )

        # Check E: Dispute Resolution Clause in Agreement
        contract_docs = [d for d in docs if d.doc_role == DocumentRole.CONTRACT_AGREEMENT]
        if contract_docs:
            c_text = contract_docs[0].text_content.lower()
            if "arbitration" in c_text and DocumentRole.LEGAL_NOTICE in roles_present:
                discrepancies.append(
                    CaseDiscrepancyItem(
                        issue_type="ARBITRATION_CLAUSE_BYPASS",
                        description=(
                            f"Agreement '{contract_docs[0].filename}' contains a mandatory Arbitration/Dispute Resolution clause, "
                            f"yet the notice threatens direct court litigation."
                        ),
                        involved_documents=[contract_docs[0].filename, notice_docs[0].filename] if notice_docs else [contract_docs[0].filename],
                        severity="MEDIUM",
                        advocate_action="Consult advocate on filing an application under Section 8 of the Arbitration and Conciliation Act to refer dispute to arbitration."
                    )
                )

        return discrepancies, missing_docs

    def _generate_case_advocate_questions(
        self,
        category: str,
        discrepancies: List[CaseDiscrepancyItem],
        docs: List[CaseDocumentItem]
    ) -> List[str]:
        questions = []
        for disc in discrepancies:
            questions.append(disc.advocate_action)

        questions.append("Do the uploaded case documents establish a complete chain of evidentiary custody?")
        questions.append("Has the limitation period expired for filing a formal reply or counter-claim?")
        questions.append("Can an interim stay or pre-litigation mediation be initiated based on the available records?")
        return questions[:5]

    def ask_case_question(self, case_id: str, request: CaseQARequest) -> CaseQAResponse:
        """
        Executes cross-document RAG over all files in the case workspace.
        Pinpoints exact filenames, segment references, and statutory sources.
        """
        case = _cases_store.get(case_id)
        if not case:
            raise ValueError(f"Case with ID '{case_id}' does not exist.")

        docs: List[CaseDocumentItem] = list(case["documents"].values())
        if not docs:
            raise ValueError(f"Case '{case_id}' has no documents attached.")

        all_doc_sentences: List[Tuple[CaseDocumentItem, Any, str, float]] = []
        epistemic_check = EpistemicFactCheck()
        multi_doc_citations: List[CitationItem] = []
        referenced_files = set()

        # Step 1: Collect & epistemically classify sentences across all case files
        candidate_texts = []
        for d in docs:
            sentences = segment_sentences(d.text_content)
            for s in sentences:
                ep_type, conf = classify_sentence_epistemic(s.text)
                all_doc_sentences.append((d, s, ep_type, conf))
                candidate_texts.append(f"[{d.filename}] {s.text}")

                if ep_type == "FACT":
                    epistemic_check.explicit_facts.append(f"[{d.filename}] {s.text}")
                elif ep_type == "ALLEGATION":
                    epistemic_check.allegations.append(f"[{d.filename}] {s.text}")
                elif ep_type == "DEMAND_OR_OBLIGATION":
                    epistemic_check.demands_obligations.append(f"[{d.filename}] {s.text}")

        # Step 2: Dense semantic search across all document sentences
        q_dense = compute_dense_embeddings([request.question])
        corpus_dense = compute_dense_embeddings([t for _, s, _, _ in all_doc_sentences for t in [s.text]])
        sim_scores = compute_cosine_similarity(q_dense, corpus_dense)

        top_indices = np.argsort(sim_scores)[::-1]
        
        # Pick top 4 relevant sentences across all case documents
        picked = 0
        for idx in top_indices:
            score = float(sim_scores[idx])
            if score < 0.20 and picked > 0:
                break
                
            d, s, ep_type, conf = all_doc_sentences[idx]
            referenced_files.add(d.filename)
            
            e_nature = EpistemicNature.FACT
            if ep_type == "ALLEGATION":
                e_nature = EpistemicNature.ALLEGATION
            elif ep_type == "DEMAND_OR_OBLIGATION":
                e_nature = EpistemicNature.DEMAND
            elif ep_type == "LEGAL_REASONING":
                e_nature = EpistemicNature.LEGAL_REASONING

            cit = CitationItem(
                citation_id=f"[{d.filename}: Line {s.index + 1}]",
                source_type=SourceType.UPLOADED_DOCUMENT,
                title=f"{d.doc_role.value} ({d.filename})",
                reference_pointer=f"{d.filename}, Line {s.index + 1}",
                quote_snippet=s.text,
                epistemic_nature=e_nature,
                relevance_score=round(score, 3)
            )
            multi_doc_citations.append(cit)
            picked += 1
            if picked >= 4:
                break

        # Step 3: Retrieve external statutes/cases from legal KB
        kb_results = self.hybrid_engine.search(
            SemanticSearchRequest(
                query=request.question,
                alpha=0.7,
                limit=request.max_sources
            )
        )
        for res in kb_results:
            if res.hybrid_score < 0.35:
                continue

            if res.doc_type == "STATUTE":
                epistemic_check.governing_statutes.append(res.title)
                multi_doc_citations.append(
                    CitationItem(
                        citation_id=f"[Statute: {res.title}]",
                        source_type=SourceType.STATUTE,
                        title=res.title,
                        reference_pointer=res.citation or res.title,
                        quote_snippet=res.content_snippet,
                        epistemic_nature=EpistemicNature.STATUTORY_RULE,
                        relevance_score=round(res.hybrid_score, 3)
                    )
                )
            elif res.doc_type == "CASE_LAW":
                epistemic_check.judicial_precedents.append(res.title)
                multi_doc_citations.append(
                    CitationItem(
                        citation_id=f"[Case: {res.title}]",
                        source_type=SourceType.CASE_LAW,
                        title=res.title,
                        reference_pointer=res.court_or_authority or "Supreme Court",
                        quote_snippet=res.ratio_decidendi or res.content_snippet,
                        epistemic_nature=EpistemicNature.JUDICIAL_RATIO,
                        relevance_score=round(res.hybrid_score, 3)
                    )
                )

        # Step 4: Synthesize response
        answer, engine_name, limitations = self.llm_connector.generate_response(
            question=request.question,
            citations=multi_doc_citations,
            epistemic_check=epistemic_check,
            language=request.language
        )

        # Step 5: Suggested advocate questions
        advocate_questions = [
            f"How do the conflicting clauses between {', '.join(list(referenced_files)[:2])} affect our defense?",
            "What supplemental affidavits or bank certificates should be requisitioned before filing the response?"
        ]

        confidence = round(float(np.mean([c.relevance_score for c in multi_doc_citations])) if multi_doc_citations else 0.20, 2)

        return CaseQAResponse(
            case_id=case_id,
            question=request.question,
            answer=answer,
            synthesis_engine=engine_name,
            multi_doc_citations=multi_doc_citations,
            epistemic_check=epistemic_check,
            documents_referenced=list(referenced_files),
            confidence_score=confidence,
            limitations=limitations,
            suggested_advocate_questions=advocate_questions
        )

# Singleton helper
_case_workspace_service = None

def get_case_workspace_service() -> CaseWorkspaceService:
    global _case_workspace_service
    if _case_workspace_service is None:
        _case_workspace_service = CaseWorkspaceService()
    return _case_workspace_service
