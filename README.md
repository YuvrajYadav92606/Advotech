# Advo टेक (Advotech)
### Verified AI for Legal Knowledge & Document Intelligence

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_+_Vite-61dafb.svg?style=flat&logo=react)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind_CSS_v4-38bdf8.svg?style=flat&logo=tailwindcss)](https://tailwindcss.com/)
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
6. **Case-Aware Multi-Document Workspaces**: Unified chronological timeline alignment, cross-document discrepancy checking, and multi-file cross-referencing.
7. **Trilingual Simplification**: Translating legal jargon into plain English, Hindi, and Hinglish.
8. **Modern Legal-Tech Web Application**: Interactive React + Tailwind CSS dashboard with instant sample scenario loaders, visual timeline plots, and conversational assistant.

---

## 📁 Repository Structure

```
Advotech/
├── .gitignore
├── requirements.txt
├── README.md
├── frontend/                       # Phase 9: Modern React + Vite + Tailwind Web Application
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js              # Vite config with backend API proxy
│   └── src/
│       ├── App.jsx                 # Master application controller
│       ├── main.jsx
│       ├── index.css               # Tailwind CSS v4 styles & judicial theme
│       ├── services/
│       │   └── api.js              # Unified backend API client
│       └── components/
│           ├── Navbar.jsx          # Header, brand, language switcher, status badge
│           ├── Dashboard.jsx       # Overview, metrics, capability cards
│           ├── SingleDocAnalyzer.jsx # Document ingestion, simplification, epistemics
│           ├── CaseWorkspaces.jsx  # Multi-doc timeline & conflict auditor
│           ├── LegalSearch.jsx     # Hybrid legal search & method benchmark
│           ├── LegalChatAssistant.jsx # Grounded conversational RAG assistant
│           └── Footer.jsx          # Legal disclaimers & provenance links
└── backend/
    ├── test_extraction.py          # Phase 1: PDF/DOCX extraction verification
    ├── test_nlp.py                 # Phase 2: Hybrid Legal NER & Preprocessing
    ├── test_phase3.py              # Phase 3: Classification & Epistemic Analysis
    ├── test_simplification.py      # Phase 4: Trilingual Legal Simplification
    ├── test_knowledge_base.py      # Phase 5: Indian Legal Knowledge Base & ML Exporter
    ├── test_semantic_search.py     # Phase 6: Dense-Sparse Hybrid Search Engine
    ├── test_rag.py                 # Phase 7: Grounded Legal RAG & Q&A Verification
    ├── test_case_workspace.py      # Phase 8: Multi-Document Case Workspace Verification
    └── app/
        ├── __init__.py
        ├── main.py                 # FastAPI application entrypoint with CORS
        ├── core/config.py          # App settings, size limits, allowed formats
        ├── schemas/                # Pydantic data schemas
        ├── services/               # Core business logic & processors
        ├── nlp/                    # Domain NLP engine
        ├── knowledge_base/         # Indian Statutes & Precedents
        ├── retrieval/              # Semantic & Hybrid Vector Search
        └── api/                    # Versioned endpoints
```

---

## 🚀 Quickstart & Verification (Windows / PowerShell)

### 1. Start the FastAPI Backend
```powershell
# In terminal 1:
c:\Users\ASUS\OneDrive\Desktop\Advotech\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Redoc UI: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2. Start the React Frontend Application
```powershell
# In terminal 2:
cd c:\Users\ASUS\OneDrive\Desktop\Advotech\frontend
npm run dev
```
- Web Application URL: [http://localhost:5173](http://localhost:5173)

### 3. Run Automated Backend Verification Suites
```powershell
# Run any phase verification:
python backend/test_case_workspace.py   # Phase 8: Multi-Doc Workspaces
python backend/test_rag.py              # Phase 7: Grounded Legal RAG
python backend/test_semantic_search.py  # Phase 6: Hybrid Search
python backend/test_knowledge_base.py   # Phase 5: Knowledge Base
python backend/test_simplification.py   # Phase 4: Trilingual Simplification
python backend/test_phase3.py           # Phase 3: Epistemics & Classification
python backend/test_nlp.py              # Phase 2: Legal NER
python backend/test_extraction.py       # Phase 1: Document Extraction
```

---

## 💻 Phase 9 Highlights: Web Application UI Modules

- **Executive Dashboard**: SIH presentation view with quick statistics, live backend engine status, and 1-click sample loaders.
- **Single Document Analyzer**: Drag-and-drop PDF/DOCX ingestion, trilingual simplification toggle (English, Hindi, Hinglish), epistemic statement color badges (Facts, Allegations, Demands, Legal Reasoning), and advocate question generator.
- **Multi-Document Case Workspaces**: Visual chronological timeline plotting dated milestones across files, cross-document discrepancy alerts (`ARBITRATION_CLAUSE_BYPASS`, `MONETARY_MISMATCH`), and missing evidence checklists.
- **Indian Legal Search**: Natural language statutory search with interactive alpha slider (BM25 Keyword to Dense Vector Semantic) and side-by-side benchmark comparison.
- **Source-Grounded RAG Assistant**: Conversational assistant with anti-hallucination verification, verbatim citation pills, and advocate preparation prompts.
