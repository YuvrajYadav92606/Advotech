from typing import List, Optional, Tuple
import numpy as np

from app.schemas.rag import (
    RAGQuestionRequest,
    RAGAnswerResponse,
    CitationItem,
    EpistemicFactCheck,
    SourceType,
    EpistemicNature
)
from app.schemas.search import SemanticSearchRequest
from app.retrieval.hybrid_search import get_hybrid_search_engine
from app.retrieval.embeddings import compute_dense_embeddings, compute_cosine_similarity
from app.nlp.preprocessor import segment_sentences, clean_legal_text
from app.nlp.legal_entities import analyze_legal_text
from app.nlp.epistemic_parser import classify_sentence_epistemic
from app.services.llm_connector import LLMConnector
from app.services.analysis_service import generate_advocate_questions

class RAGService:
    """
    Core RAG & Legal Question-Answering Service.
    Coordinates document chunking, epistemic classification, dense-sparse legal retrieval,
    and anti-hallucination grounded generation.
    """

    def __init__(self):
        self.hybrid_engine = get_hybrid_search_engine()
        self.llm_connector = LLMConnector()

    def answer_question(self, request: RAGQuestionRequest) -> RAGAnswerResponse:
        """
        Processes a legal question with source grounding, epistemic separation,
        and verbatim inline citations.
        """
        citations: List[CitationItem] = []
        epistemic_check = EpistemicFactCheck()
        doc_categories = set()

        # -------------------------------------------------------------
        # STEP 1: Process Uploaded Document Context (if provided)
        # -------------------------------------------------------------
        if request.document_text and len(request.document_text.strip()) > 10:
            cleaned_text = clean_legal_text(request.document_text)
            sentence_items = segment_sentences(cleaned_text)

            if sentence_items:
                sent_texts = [s.text for s in sentence_items]
                
                # Epistemic classification of document sentences
                classified_sentences = []
                for idx, s in enumerate(sentence_items):
                    epistemic_type, conf = classify_sentence_epistemic(s.text)
                    classified_sentences.append((s, epistemic_type, conf))
                    
                    if epistemic_type == "FACT":
                        epistemic_check.explicit_facts.append(s.text)
                    elif epistemic_type == "ALLEGATION":
                        epistemic_check.allegations.append(s.text)
                    elif epistemic_type == "DEMAND_OR_OBLIGATION":
                        epistemic_check.demands_obligations.append(s.text)
                    elif epistemic_type == "LEGAL_REASONING":
                        epistemic_check.explicit_facts.append(s.text)

                # Compute dense similarity between question and document sentences
                q_dense = compute_dense_embeddings([request.question])
                doc_dense = compute_dense_embeddings(sent_texts)
                sim_scores = compute_cosine_similarity(q_dense, doc_dense)

                # Rank sentences by relevance
                top_indices = np.argsort(sim_scores)[::-1]
                
                # Take top 3 most relevant sentences (threshold: >= 0.22)
                picked_count = 0
                for idx in top_indices:
                    score = float(sim_scores[idx])
                    if score < 0.22 and picked_count > 0:
                        break
                    
                    s, e_type, conf = classified_sentences[idx]
                    
                    # Map to schema enum
                    e_nature = EpistemicNature.FACT
                    if e_type == "ALLEGATION":
                        e_nature = EpistemicNature.ALLEGATION
                    elif e_type == "DEMAND_OR_OBLIGATION":
                        e_nature = EpistemicNature.DEMAND
                    elif e_type == "LEGAL_REASONING":
                        e_nature = EpistemicNature.LEGAL_REASONING

                    cit = CitationItem(
                        citation_id=f"[Doc: Line {s.index + 1}]",
                        source_type=SourceType.UPLOADED_DOCUMENT,
                        title="Uploaded Document Excerpt",
                        reference_pointer=f"Segment {s.index + 1}",
                        quote_snippet=s.text,
                        epistemic_nature=e_nature,
                        relevance_score=round(score, 3)
                    )
                    citations.append(cit)
                    picked_count += 1
                    if picked_count >= 3:
                        break

        # -------------------------------------------------------------
        # STEP 2: Retrieve External Legal Sources from Knowledge Base
        # -------------------------------------------------------------
        # Query external statutes and judicial precedents
        search_results = self.hybrid_engine.search(
            SemanticSearchRequest(
                query=request.question,
                alpha=0.7,
                limit=request.max_sources
            )
        )

        for res in search_results:
            # Relevancy gate: strict hybrid score threshold (>= 0.35) prevents false positive precedents
            if res.hybrid_score < 0.35:
                continue

            if res.doc_type == "STATUTE":
                statute_desc = f"{res.title}"
                if res.statutory_provisions:
                    statute_desc += f" ({', '.join(res.statutory_provisions)})"
                    
                epistemic_check.governing_statutes.append(statute_desc)
                
                citations.append(
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
                
                if "138" in res.title or "Negotiable" in res.title:
                    doc_categories.add("CHEQUE_BOUNCE_NOTICE")
                elif "106" in res.title or "Property" in res.title:
                    doc_categories.add("TENANCY_AND_EVICTION_NOTICE")
                elif "Contract" in res.title:
                    doc_categories.add("CONTRACT_BREACH_NOTICE")

            elif res.doc_type == "CASE_LAW":
                case_desc = f"{res.title} [{res.court_or_authority or 'Supreme Court'}]"
                if res.ratio_decidendi:
                    case_desc += f": {res.ratio_decidendi[:100]}..."
                epistemic_check.judicial_precedents.append(case_desc)

                snippet = res.ratio_decidendi if res.ratio_decidendi else res.content_snippet
                citations.append(
                    CitationItem(
                        citation_id=f"[Case: {res.title}]",
                        source_type=SourceType.CASE_LAW,
                        title=res.title,
                        reference_pointer=res.court_or_authority or "Supreme Court of India",
                        quote_snippet=snippet,
                        epistemic_nature=EpistemicNature.JUDICIAL_RATIO,
                        relevance_score=round(res.hybrid_score, 3)
                    )
                )

        # -------------------------------------------------------------
        # STEP 3: Generation via Modular LLM Connector
        # -------------------------------------------------------------
        answer, engine_name, gen_limitations = self.llm_connector.generate_response(
            question=request.question,
            citations=citations,
            epistemic_check=epistemic_check,
            language=request.language
        )

        # -------------------------------------------------------------
        # STEP 4: Advocate Consultation Questions
        # -------------------------------------------------------------
        primary_category = list(doc_categories)[0] if doc_categories else "GENERAL_CIVIL"
        advocate_questions = generate_advocate_questions(
            category=primary_category,
            deadlines=[],
            amounts=[]
        )
        if not advocate_questions:
            advocate_questions = [
                "Does the notice comply with statutory limitation and service requirements under Indian law?",
                "What documentary evidence should be compiled to counter the sender's allegations?",
                "Can an amicable settlement or mediation be explored before entering litigation?"
            ]

        # -------------------------------------------------------------
        # STEP 5: Confidence Calculation
        # -------------------------------------------------------------
        if citations:
            scores = [c.relevance_score for c in citations]
            avg_score = float(np.mean(scores))
            # Boost slightly if we have both document context and governing statute
            has_doc = any(c.source_type == SourceType.UPLOADED_DOCUMENT for c in citations)
            has_statute = any(c.source_type == SourceType.STATUTE for c in citations)
            if has_doc and has_statute:
                avg_score = min(avg_score * 1.15, 0.98)
            confidence = round(avg_score, 2)
        else:
            confidence = 0.15

        return RAGAnswerResponse(
            question=request.question,
            answer=answer,
            synthesis_engine=engine_name,
            citations=citations,
            epistemic_check=epistemic_check,
            confidence_score=confidence,
            limitations=gen_limitations,
            suggested_advocate_questions=advocate_questions[:4]
        )

# Singleton helper
_rag_service_instance = None

def get_rag_service() -> RAGService:
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance
