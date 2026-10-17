# Advo टेक (Advotech)
### Verified AI for Legal Knowledge & Document Intelligence

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.14-blue.svg?style=flat&logo=python)](https://python.org)
[![PyMuPDF](https://img.shields.io/badge/PDF_Engine-PyMuPDF-red.svg?style=flat)](https://pymupdf.readthedocs.io/)
[![python-docx](https://img.shields.io/badge/DOCX_Engine-python--docx-orange.svg?style=flat)](https://python-docx.readthedocs.io/)

---

## 🏛️ Project Vision & Purpose

**Advo टेक** is an NLP-powered legal document intelligence and judicial assistance platform designed to empower ordinary Indian citizens to comprehend complex legal notices, agreements, court orders, and contracts.

Rather than acting as an ungrounded general-purpose chatbot, **Advo टेक** combines:
1. **Structural Document Intelligence**: In-memory parsing of legal PDFs and Word documents, preserving precise citations (page numbers, paragraphs, tabular schedules).
2. **Domain-Specific Indian Legal NLP**: Specialized entity recognition, issue tagging, and obligation/deadline mapping.
3. **Statutory Knowledge Retrieval**: Curated and verifiable indexing of Indian central/state legislation and landmark judgments.
4. **Source-Grounded Explainability**: Clear, simple-language legal explanations backed by direct citations and actionable next steps.

---

## 📁 Repository Structure

```
Advotech/
├── .gitignore
├── requirements.txt
├── README.md
├── backend/
│   ├── test_extraction.py           # Automated end-to-end verification suite
│   └── app/
│       ├── __init__.py
│       ├── main.py                  # FastAPI application entrypoint with CORS
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py            # App settings, size limits, allowed formats
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── document.py          # Pydantic models for segments and responses
│       ├── services/
│       │   ├── __init__.py
│       │   ├── pdf_extractor.py     # Page-by-page PDF extraction via PyMuPDF
│       │   ├── docx_extractor.py    # Paragraph and table extraction via python-docx
│       │   └── document_service.py  # Validation & orchestration pipeline
│       └── api/
│           ├── __init__.py
│           ├── router.py            # Aggregated versioned API router (/api/v1)
│           └── endpoints/
│               ├── __init__.py
│               ├── health.py        # System health and project metadata
│               └── documents.py     # Document upload & structured parsing API
```

---

## 🚀 Quickstart & Verification (Windows / PowerShell)

### 1. Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Run the Automated Verification Suite
```powershell
cd backend
python test_extraction.py
```

### 3. Start the FastAPI Development Server
```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Interactive Documentation
Open your browser and navigate to:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
