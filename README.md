# Advo टेक (Advotech)
### Verified AI for Legal Knowledge & Document Intelligence

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.14-blue.svg?style=flat&logo=python)](https://python.org)
[![PyMuPDF](https://img.shields.io/badge/PDF_Engine-PyMuPDF-red.svg?style=flat)](https://pymupdf.readthedocs.io/)
[![SentenceTransformers](https://img.shields.io/badge/Embeddings-Sentence--Transformers-yellow.svg?style=flat)](https://sbert.net/)
[![spaCy](https://img.shields.io/badge/NER-spaCy--3.8-09a3d5.svg?style=flat)](https://spacy.io/)

---

## 🏛️ Project Vision & Purpose

**Advo टेक** is an NLP-powered legal document intelligence and judicial assistance platform designed to empower ordinary Indian citizens to comprehend complex legal notices, agreements, court orders, and contracts.

Rather than acting as an ungrounded general-purpose chatbot, **Advo टेक** delivers:
1. **Structural Document Intelligence**: In-memory parsing of legal PDFs and Word documents, preserving precise citations (page numbers, paragraphs, tabular schedules).
2. **Domain-Specific Indian Legal NLP**: Specialized entity recognition (courts, sections, acts, deadlines, money), issue tagging, and epistemic fact vs allegation separation.
3. **Statutory Knowledge Retrieval**: Curated and verifiable indexing of Indian central/state legislation and landmark judgments with amendment tracking (e.g. IPC to BNS).
4. **Hybrid Semantic Legal Search**: Dense vector retrieval (`all-MiniLM-L6-v2`) combined with sparse lexical indexing (TF-IDF/BM25) and explainable retrieval rationales.
5. **Grounded Legal RAG & Q&A**: Strict anti-hallucination question answering with epistemic boundary separation, verbatim inline citations, and zero-cost offline fallback.
6. **Trilingual Simplification**: Translating legal jargon into plain English, Hindi, and Hinglish.

---

## 📁 Repository Structure

```
Advotech/
├── .gitignore
├── requirements.txt
├── README.md
├── backend/
│   ├── test_extraction.py          # Phase 1: PDF/DOCX extraction verification
│   ├── test_nlp.py                 # Phase 2: Hybrid Legal NER & Preprocessing
│   ├── test_phase3.py              # Phase 3: Classification & Epistemic Analysis
│   ├── test_simplification.py      # Phase 4: Trilingual Legal Simplification
│   ├── test_knowledge_base.py      # Phase 5: Indian Legal Knowledge Base & ML Exporter
│   ├── test_semantic_search.py     # Phase 6: Dense-Sparse Hybrid Search Engine
│   ├── test_rag.py                 # Phase 7: Grounded Legal RAG & Q&A Verification
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI application entrypoint with CORS
│       ├── core/config.py          # App settings, size limits, allowed formats
│       ├── schemas/                # Pydantic data schemas
│       │   ├── document.py, nlp.py, analysis.py
│       │   ├── simplification.py, knowledge_base.py, search.py, rag.py
│       ├── services/               # Core business logic & processors
│       │   ├── pdf_extractor.py, docx_extractor.py, document_service.py
│       │   ├── analysis_service.py, rag_service.py, llm_connector.py
│       ├── nlp/                    # Domain NLP engine
│       │   ├── preprocessor.py, legal_entities.py, classifier.py
│       │   ├── epistemic_parser.py, simplifier.py
│       ├── knowledge_base/         # Indian Statutes & Precedents
│       │   ├── indexer.py
│       │   └── data/ (statutes.jsonl, case_laws.jsonl)
│       ├── retrieval/              # Semantic & Hybrid Vector Search
│       │   ├── embeddings.py, hybrid_search.py
│       └── api/
│           ├── router.py           # Unified versioned API router (/api/v1)
│           └── endpoints/          # health, documents, nlp, analysis, simplification, kb, search, rag
```

---

## 🚀 Quickstart & Verification (Windows / PowerShell)

### 1. Activate the Virtual Environment
```powershell
c:\Users\ASUS\OneDrive\Desktop\Advotech\.venv\Scripts\Activate.ps1
```

### 2. Run the Verification Suites
```powershell
# Phase 7: RAG & Legal Question Answering
python backend/test_rag.py

# Phase 6: Hybrid Semantic Search
python backend/test_semantic_search.py

# Phase 5: Knowledge Base & ML Exporter
python backend/test_knowledge_base.py

# Phase 4: Trilingual Simplification
python backend/test_simplification.py

# Phase 3: Structured Analysis & Epistemics
python backend/test_phase3.py

# Phase 2: NLP Preprocessing & Legal NER
python backend/test_nlp.py

# Phase 1: Document Ingestion & Extraction
python backend/test_extraction.py
```

### 3. Start the API Server
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Redoc UI: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## ⚖️ Phase 7 Highlights: Grounded Legal RAG & Q&A

- **Epistemic Segregation**: Explicitly differentiates between:
  - Facts objectively recorded in documents
  - Unproven allegations made by an opposing party
  - Governing statutory rules
  - Binding judicial precedents
  - Interpretive AI inferences
- **Verbatim Inline Citations**: Output rigorously pinned with `[Doc: Line X]`, `[Statute: Title]`, and `[Case: Title]`.
- **Anti-Hallucination Guardrails**: Queries outside available evidentiary ground truth return explicit limitation notices rather than invented legal assertions.
- **Dual Synthesis Architecture**:
  - **Online Mode**: Direct integration with Google Gemini API (`GEMINI_API_KEY`).
  - **Zero-Cost Offline Mode**: Deterministic extractive legal synthesizer ensuring full functionality without external API subscriptions.
