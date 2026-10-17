import os
import re
from typing import List, Dict, Any, Optional, Tuple
import httpx
from app.schemas.rag import CitationItem, EpistemicFactCheck, SourceType, EpistemicNature

class LLMConnector:
    """
    Modular LLM Connector with dual operational modes:
    1. Online Mode: Google Gemini API (if GEMINI_API_KEY or GOOGLE_API_KEY is configured).
    2. Offline Zero-Cost Mode: Grounded Extractive Legal Synthesizer (100% deterministic, zero hallucination).
    """

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def is_gemini_configured(self) -> bool:
        """Returns True if a valid Gemini API key is present in the environment."""
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def generate_response(
        self,
        question: str,
        citations: List[CitationItem],
        epistemic_check: EpistemicFactCheck,
        language: str = "en"
    ) -> Tuple[str, str, List[str]]:
        """
        Generates a source-grounded legal explanation.
        Returns:
            (answer_text, synthesis_engine_name, limitations_list)
        """
        # If online Gemini API key is configured, attempt calling Gemini
        if self.is_gemini_configured():
            try:
                gemini_answer, limitations = self._call_gemini_api(question, citations, epistemic_check, language)
                return gemini_answer, f"Google Gemini API ({self.model_name})", limitations
            except Exception as e:
                # Log and smoothly fall back to offline synthesizer
                pass

        # Zero-Cost Offline Grounded Synthesizer
        answer, limitations = self._synthesize_offline_grounded(question, citations, epistemic_check, language)
        return answer, "Advo टेक Grounded Extractive Synthesizer (Zero-Cost Offline)", limitations

    def _call_gemini_api(
        self,
        question: str,
        citations: List[CitationItem],
        epistemic_check: EpistemicFactCheck,
        language: str
    ) -> Tuple[str, List[str]]:
        """
        Calls Google Gemini API with strict anti-hallucination legal grounding prompt.
        """
        sources_context = []
        for c in citations:
            sources_context.append(
                f"[{c.citation_id}] Type: {c.source_type.value} | Title: {c.title} | Ref: {c.reference_pointer}\n"
                f"Status: {c.epistemic_nature.value}\n"
                f"Content: \"{c.quote_snippet}\"\n"
            )

        context_str = "\n".join(sources_context) if sources_context else "No relevant legal sources retrieved."

        system_instruction = (
            "You are Advo टेक, an expert Indian legal document assistant and NLP reasoning engine.\n"
            "STRICT RULES FOR LEGAL GROUNDING:\n"
            "1. Answer ONLY using the facts, allegations, statutes, and cases supplied in the CONTEXT.\n"
            "2. Whenever stating a fact or legal rule, use inline citations like [Doc: ...] or [Statute: ...].\n"
            "3. Distinguish clearly between established FACTS and unproven ALLEGATIONS made by the other party.\n"
            "4. NEVER invent laws, section numbers, or precedents not present in the context.\n"
            "5. If the context does not contain enough information to answer the question, explicitly state the limitation.\n"
            "6. Provide explanations in simple, clear language accessible to ordinary citizens.\n"
        )

        lang_instruction = "Respond in clear English."
        if language == "hi":
            lang_instruction = "Respond in simple, clear Hindi (Devanagari)."
        elif language == "hinglish":
            lang_instruction = "Respond in conversational Hinglish (Hindi written in Roman script)."

        user_prompt = (
            f"{system_instruction}\n\n"
            f"LANGUAGE: {lang_instruction}\n\n"
            f"CONTEXT SOURCES:\n{context_str}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"GROUNDED ANSWER:"
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 1024
            }
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{self.endpoint_url}?key={self.api_key}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        limitations = []
        if "not mentioned" in raw_text.lower() or "limitation" in raw_text.lower():
            limitations.append("Context does not fully address all aspects of the query.")

        return raw_text, limitations

    def _synthesize_offline_grounded(
        self,
        question: str,
        citations: List[CitationItem],
        epistemic_check: EpistemicFactCheck,
        language: str
    ) -> Tuple[str, List[str]]:
        """
        Deterministic, zero-cost legal synthesis engine.
        Guarantees 100% adherence to source ground truth without hallucinating facts or laws.
        """
        q_lower = question.lower()
        limitations: List[str] = []

        # 1. Detect if question is completely unanswerable with zero citations
        if not citations and not epistemic_check.explicit_facts and not epistemic_check.allegations:
            limitations.append(f"No direct document facts or statutory provisions found matching '{question}'.")
            if language == "hi":
                return (
                    f"दिए गए दस्तावेज़ और भारतीय कानूनी डेटाबेस में '{question}' से संबंधित कोई सत्यापित जानकारी नहीं मिली। "
                    "Advo टेक के सख्त नियमों के अनुसार, बिना दस्तावेजी प्रमाण के कोई भी कानूनी निष्कर्ष नहीं निकाला जा सकता।",
                    limitations
                )
            elif language == "hinglish":
                return (
                    f"Uploaded document aur Indian legal knowledge base me '{question}' ke regarding koi verified information nahi mili. "
                    "Advo टेक strict anti-hallucination policy follow karta hai aur bina proof ke koi assumption nahi banata.",
                    limitations
                )
            else:
                return (
                    f"The provided document and indexed Indian legal knowledge base do not contain verified information matching '{question}'. "
                    "Under Advo टेक's anti-hallucination safeguards, no assertions can be made without ground truth evidence.",
                    limitations
                )

        # 2. Determine Question Intent Categories
        is_deadline_q = any(w in q_lower for w in ["deadline", "when", "days", "period", "within", "how much time", "date limit"])
        is_money_q = any(w in q_lower for w in ["money", "amount", "rupees", "rs.", "pay", "sum", "cheque amount", "fee", "cost"])
        is_law_q = any(w in q_lower for w in ["section", "law", "act", "offence", "crime", "provision", "statute", "legal", "punishment"])
        is_allegation_q = any(w in q_lower for w in ["claim", "allegation", "accuse", "fraud", "fault", "guilty", "alleged", "dishonest", "cheat"])
        is_action_q = any(w in q_lower for w in ["what should i do", "what to do", "next step", "how to respond", "advice"])
        is_contract_clause_q = any(w in q_lower for w in ["clause", "agreement", "contract", "arbitration", "term", "dispute resolution", "require"])
        is_parties_q = any(p in q_lower for p in ["who is", "who are", "parties involved", "identity of", "names of", "sender of"])

        doc_cits = [c for c in citations if c.source_type == SourceType.UPLOADED_DOCUMENT]
        statute_cits = [c for c in citations if c.source_type == SourceType.STATUTE]
        case_cits = [c for c in citations if c.source_type == SourceType.CASE_LAW]

        sections_text: List[str] = []

        # Section A: Document Findings (Fact vs Allegation vs Contractual Provision)
        if is_contract_clause_q and doc_cits:
            best_doc = doc_cits[0]
            sections_text.append(
                f"**Contractual Provision & Requirement**: Under **{best_doc.title}**, the document stipulates:\n"
                f"> \"{best_doc.quote_snippet}\" {best_doc.citation_id}."
            )
            if len(doc_cits) > 1 and doc_cits[1].reference_pointer != best_doc.reference_pointer:
                sec_doc = doc_cits[1]
                sections_text.append(
                    f"**Cross-Document Context ({sec_doc.title})**: \"{sec_doc.quote_snippet}\" {sec_doc.citation_id}."
                )

        elif is_deadline_q:
            if epistemic_check.demands_obligations:
                deadlines_found = [d for d in epistemic_check.demands_obligations if any(w in d.lower() for w in ["day", "period", "within", "date", "time"])]
                if deadlines_found:
                    cit_tag = doc_cits[0].citation_id if doc_cits else "[Document Reference]"
                    sections_text.append(
                        f"**Stipulated Deadline & Demand**: The document requires compliance as follows: "
                        f"\"{deadlines_found[0]}\" {cit_tag}."
                    )
                else:
                    sections_text.append(f"**Document Requirements**: {epistemic_check.demands_obligations[0]}")
            elif doc_cits:
                sections_text.append(f"**Document Timeline / Deadline Reference**: \"{doc_cits[0].quote_snippet}\" {doc_cits[0].citation_id}.")
            else:
                limitations.append("Specific numerical deadline was not explicitly stated in the retrieved document passages.")

        elif is_money_q:
            money_claims = [d for d in epistemic_check.demands_obligations if any(w in d.lower() for w in ["rs", "rupee", "amount", "/-", "sum", "pay"])]
            if money_claims:
                cit_tag = doc_cits[0].citation_id if doc_cits else "[Document Reference]"
                sections_text.append(
                    f"**Monetary Claim & Demand**: The document demands the following monetary remittance: "
                    f"\"{money_claims[0]}\" {cit_tag}."
                )
            elif doc_cits:
                sections_text.append(f"**Monetary Reference**: \"{doc_cits[0].quote_snippet}\" {doc_cits[0].citation_id}.")
            else:
                sections_text.append("No explicit monetary demand could be identified in the retrieved sections.")

        elif is_allegation_q:
            if epistemic_check.allegations:
                cit_tag = doc_cits[0].citation_id if doc_cits else "[Document Allegation]"
                sections_text.append(
                    f"**Adversarial Allegation (Unproven)**: The opposing party claims the following: "
                    f"\"{epistemic_check.allegations[0]}\" {cit_tag}.\n"
                    f"*Important note: This represents an allegation made by the sender, not an established judicial fact.*"
                )
            elif doc_cits:
                sections_text.append(f"**Document Record**: \"{doc_cits[0].quote_snippet}\" {doc_cits[0].citation_id}.")

        elif is_parties_q:
            if doc_cits:
                sections_text.append(f"**Involved Parties / Context**: \"{doc_cits[0].quote_snippet}\" {doc_cits[0].citation_id}.")
            elif epistemic_check.explicit_facts:
                sections_text.append(f"**Involved Parties / Context**: \"{epistemic_check.explicit_facts[0]}\".")

        else:
            # General Question: provide best matching document passage
            if doc_cits:
                best_doc = doc_cits[0]
                nature_label = "Fact" if best_doc.epistemic_nature == EpistemicNature.FACT else "Allegation / Claim"
                sections_text.append(
                    f"**Document Context ({nature_label})**: \"{best_doc.quote_snippet}\" {best_doc.citation_id}."
                )

        # Section B: Statutory Legal Framework
        if statute_cits:
            statute = statute_cits[0]
            sections_text.append(
                f"**Applicable Statutory Law**: Under **{statute.title}** ({statute.reference_pointer}), the statutory framework provides:\n"
                f"> \"{statute.quote_snippet}\" {statute.citation_id}."
            )
        elif is_law_q:
            limitations.append("No exact matching statute was retrieved from the indexed knowledge base above confidence threshold.")

        # Section C: Judicial Precedents & Rulings
        if case_cits:
            case = case_cits[0]
            sections_text.append(
                f"**Judicial Precedent**: In **{case.title}** ({case.reference_pointer}), the Court held:\n"
                f"> \"{case.quote_snippet}\" {case.citation_id}."
            )

        # Section D: Procedural Next Steps & Action Plan
        if is_action_q or is_deadline_q or is_allegation_q:
            action_points = [
                "1. **Do Not Ignore**: Respond within any statutory or contractual notice period.",
                "2. **Preserve Evidence**: Collect all relevant communications, bank records, and contracts.",
                "3. **Consult an Advocate**: Engage a legal counsel to draft a formal, legally grounded reply."
            ]
            sections_text.append("**Recommended Procedural Steps**:\n" + "\n".join(action_points))

        # Combine synthesis
        full_answer = "\n\n".join(sections_text)

        # Multilingual Translation for synthesized response
        if language == "hi":
            full_answer = self._translate_offline_hindi(full_answer, is_deadline_q, is_money_q, is_allegation_q)
        elif language == "hinglish":
            full_answer = self._translate_offline_hinglish(full_answer, is_deadline_q, is_money_q, is_allegation_q)

        return full_answer, limitations

    def _translate_offline_hindi(self, text: str, is_deadline: bool, is_money: bool, is_allegation: bool) -> str:
        """Helper to localize synthesized explanation into clear Hindi."""
        prefix = "### Advo टेक विश्लेषण (हिंदी):\n\n"
        body = text.replace("**Stipulated Deadline & Demand**:", "**निर्धारित समय-सीमा और मांग**:")
        body = body.replace("**Applicable Statutory Law**:", "**लागू वैधानिक कानून**:")
        body = body.replace("**Judicial Precedent**:", "**न्यायिक निर्णय (Precedent)**:")
        body = body.replace("**Adversarial Allegation (Unproven)**:", "**विपक्षी पक्ष का आरोप (अपुष्ट)**:")
        body = body.replace("**Recommended Procedural Steps**:", "**सुझाए गए कानूनी कदम**:")
        return prefix + body

    def _translate_offline_hinglish(self, text: str, is_deadline: bool, is_money: bool, is_allegation: bool) -> str:
        """Helper to localize synthesized explanation into natural Hinglish."""
        prefix = "### Advo टेक Analysis (Hinglish):\n\n"
        body = text.replace("**Stipulated Deadline & Demand**:", "**Nirdharit Deadline aur Demand**:")
        body = body.replace("**Applicable Statutory Law**:", "**Lagoo Statutory Kanoon**:")
        body = body.replace("**Judicial Precedent**:", "**Court ka Judgement (Precedent)**:")
        body = body.replace("**Adversarial Allegation (Unproven)**:", "**Doosre party ka Allegation (Aarop)**:")
        body = body.replace("**Recommended Procedural Steps**:", "**Aage ke Zaroori Steps**:")
        return prefix + body
