const API_BASE = '/api/v1';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function getEngineStatus() {
  const res = await fetch(`${API_BASE}/rag/engine-status`);
  if (!res.ok) throw new Error('Failed to retrieve engine status');
  return res.json();
}

// ----------------------------------------------------------------------
// Phase 1 - 4: NLP, Extraction, Analysis & Simplification
// ----------------------------------------------------------------------

export async function analyzeDocumentUpload(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload and extract document');
  }
  return res.json();
}

export async function analyzeTextNLP(text) {
  const res = await fetch(`${API_BASE}/nlp/analyze-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to run NLP analysis');
  return res.json();
}

export async function getStructuredAnalysis(text) {
  const res = await fetch(`${API_BASE}/analysis/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to generate structured legal analysis');
  return res.json();
}

export async function simplifyLegalText(text, targetLanguage = 'en') {
  const res = await fetch(`${API_BASE}/simplification/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, target_language: targetLanguage }),
  });
  if (!res.ok) throw new Error('Failed to simplify legal text');
  return res.json();
}

// ----------------------------------------------------------------------
// Phase 5 & 6: Indian Legal Knowledge Base & Hybrid Search
// ----------------------------------------------------------------------

export async function searchLegalKB(query, alpha = 0.7, limit = 5) {
  const res = await fetch(`${API_BASE}/search/hybrid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, alpha, limit }),
  });
  if (!res.ok) throw new Error('Hybrid search failed');
  return res.json();
}

export async function compareSearchMethods(query, limit = 3) {
  const res = await fetch(`${API_BASE}/search/compare?query=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error('Comparison benchmark failed');
  return res.json();
}

export async function getKBStats() {
  const res = await fetch(`${API_BASE}/kb/stats`);
  if (!res.ok) throw new Error('Failed to fetch KB statistics');
  return res.json();
}

// ----------------------------------------------------------------------
// Phase 7: Grounded Legal RAG & Q&A
// ----------------------------------------------------------------------

export async function askRAG(question, documentText = null, language = 'en') {
  const res = await fetch(`${API_BASE}/rag/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      document_text: documentText,
      language,
      max_sources: 4,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'RAG query failed');
  }
  return res.json();
}

export async function askDocumentFile(file, question, language = 'en') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('question', question);
  formData.append('language', language);
  formData.append('max_sources', '4');

  const res = await fetch(`${API_BASE}/rag/ask-document`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'File Q&A failed');
  }
  return res.json();
}

// ----------------------------------------------------------------------
// Phase 8: Case-Aware Multi-Document Workspaces
// ----------------------------------------------------------------------

export async function listCases() {
  const res = await fetch(`${API_BASE}/cases/`);
  if (!res.ok) throw new Error('Failed to list cases');
  return res.json();
}

export async function createCase(title, description = '', category = 'GENERAL_LEGAL_DISPUTE') {
  const res = await fetch(`${API_BASE}/cases/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, category }),
  });
  if (!res.ok) throw new Error('Failed to create case');
  return res.json();
}

export async function getCaseDetails(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}`);
  if (!res.ok) throw new Error('Failed to get case details');
  return res.json();
}

export async function uploadCaseDocument(caseId, file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/cases/${caseId}/upload-document`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to upload document to case');
  }
  return res.json();
}

export async function addCaseTextDocument(caseId, filename, textContent) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/add-text-document`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, text_content: textContent }),
  });
  if (!res.ok) throw new Error('Failed to add text document to case');
  return res.json();
}

export async function analyzeCaseWorkspace(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/analysis`);
  if (!res.ok) throw new Error('Failed to analyze case workspace');
  return res.json();
}

export async function askCaseWorkspace(caseId, question, language = 'en') {
  const res = await fetch(`${API_BASE}/cases/${caseId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, language, max_sources: 4 }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Cross-document Q&A failed');
  }
  return res.json();
}
