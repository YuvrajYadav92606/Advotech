import React, { useState, useEffect } from 'react';
import { 
  FolderKanban, 
  Plus, 
  Upload, 
  Calendar, 
  AlertTriangle, 
  FileCheck, 
  MessageSquare, 
  FileText, 
  ShieldAlert,
  ArrowRight,
  Sparkles,
  HelpCircle
} from 'lucide-react';
import { 
  listCases, 
  createCase, 
  uploadCaseDocument, 
  addCaseTextDocument, 
  analyzeCaseWorkspace, 
  askCaseWorkspace 
} from '../services/api';

export default function CaseWorkspaces({ currentLang }) {
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [caseAnalysis, setCaseAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // New Case Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newCategory, setNewCategory] = useState('CHEQUE_BOUNCE_DISPUTE');

  // Cross-doc Q&A State
  const [qaQuestion, setQaQuestion] = useState('Does the agreement between the parties require arbitration before going to court?');
  const [qaLoading, setQaLoading] = useState(false);
  const [qaResponse, setQaResponse] = useState(null);

  useEffect(() => {
    fetchCaseList();
  }, []);

  const fetchCaseList = async () => {
    try {
      const res = await listCases();
      setCases(res.cases || []);
      if (res.cases && res.cases.length > 0 && !selectedCaseId) {
        handleSelectCase(res.cases[0].case_id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectCase = async (caseId) => {
    setSelectedCaseId(caseId);
    setLoading(true);
    setError(null);
    setQaResponse(null);
    try {
      const analysis = await analyzeCaseWorkspace(caseId);
      setCaseAnalysis(analysis);
    } catch (err) {
      setError(err.message || 'Failed to load case workspace details.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewCase = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const res = await createCase(newTitle, newDesc, newCategory);
      setShowCreateModal(false);
      setNewTitle('');
      setNewDesc('');
      await fetchCaseList();
      handleSelectCase(res.case_id);
    } catch (err) {
      setError(err.message || 'Failed to create case workspace.');
    }
  };

  const handleDocumentUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedCaseId) return;
    setLoading(true);
    try {
      await uploadCaseDocument(selectedCaseId, file);
      const updatedAnalysis = await analyzeCaseWorkspace(selectedCaseId);
      setCaseAnalysis(updatedAnalysis);
      await fetchCaseList();
    } catch (err) {
      setError(err.message || 'Failed to upload document into case.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemoDispute = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Create a demo case
      const res = await createCase(
        'Sharma Traders v. Kumar Enterprises - Commercial Cheque Dispute',
        'Multi-document matter with Legal Notice, Bank Return Memo, and Commercial Supply Agreement',
        'CHEQUE_BOUNCE_DISPUTE'
      );
      const cId = res.case_id;

      // 2. Add Notice
      await addCaseTextDocument(
        cId,
        'Legal_Notice_Sec138.txt',
        `LEGAL NOTICE UNDER SECTION 138 NEGOTIABLE INSTRUMENTS ACT.
To: Sh. Rajesh Kumar, Kumar Enterprises.
My client states that Cheque No. 458921 dated 15th January 2024 for Rs. 2,50,000/- was dishonoured with remarks "Funds Insufficient" vide Bank Return Memo dated 20th January 2024.
You are hereby required to remit Rs. 2,50,000/- within 15 days, failing which criminal proceedings shall be initiated.
Dated: 25th January 2024.`
      );

      // 3. Add Bank Memo
      await addCaseTextDocument(
        cId,
        'Bank_Return_Memo_SBI.txt',
        `STATE BANK OF INDIA - CHEQUE RETURN MEMO
Date: 20th January 2024
Cheque No: 458921 | Amount: Rs. 2,50,000/-
Reason for Dishonour: Funds Insufficient.
Account: Kumar Enterprises.`
      );

      // 4. Add Supply Agreement with Arbitration clause
      await addCaseTextDocument(
        cId,
        'Supply_Agreement_2023.txt',
        `COMMERCIAL SUPPLY AGREEMENT executed on 10th January 2023.
Between: M/s Sharma Traders and M/s Kumar Enterprises.
Clause 14. Dispute Resolution: All disputes arising out of this agreement shall be settled through mandatory binding arbitration in New Delhi under the Arbitration and Conciliation Act, 1996, before any court action.`
      );

      await fetchCaseList();
      await handleSelectCase(cId);
    } catch (err) {
      setError(err.message || 'Failed to initialize demo dispute.');
    } finally {
      setLoading(false);
    }
  };

  const handleAskCaseQA = async () => {
    if (!qaQuestion.trim() || !selectedCaseId) return;
    setQaLoading(true);
    try {
      const resp = await askCaseWorkspace(selectedCaseId, qaQuestion, currentLang);
      setQaResponse(resp);
    } catch (err) {
      setError(err.message || 'Cross-document Q&A failed.');
    } finally {
      setQaLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Case Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900 font-serif">Case-Aware Multi-Document Workspaces</h2>
          <p className="text-sm text-slate-600 mt-1">
            Connect notices, agreements, and bank memos for cross-document discrepancy auditing and timeline alignment.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleLoadDemoDispute}
            className="px-3.5 py-2 text-xs rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 font-bold hover:bg-indigo-100 transition-colors flex items-center space-x-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Load 3-Doc Commercial Dispute</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2 text-xs rounded-lg bg-amber-500 text-slate-950 font-bold hover:bg-amber-400 transition-colors flex items-center space-x-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Case Workspace</span>
          </button>
        </div>
      </div>

      {/* Case Selector Tabs */}
      {cases.length > 0 && (
        <div className="flex overflow-x-auto space-x-2 pb-2">
          {cases.map((c) => (
            <button
              key={c.case_id}
              onClick={() => handleSelectCase(c.case_id)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center space-x-2 border ${
                selectedCaseId === c.case_id
                  ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
              }`}
            >
              <FolderKanban className="w-3.5 h-3.5 text-amber-400" />
              <span>{c.title}</span>
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300 font-mono">
                {c.total_documents} docs
              </span>
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {error}
        </div>
      )}

      {/* Case Workspace Dashboard */}
      {caseAnalysis && (
        <div className="space-y-6">
          {/* Case Overview & Document Attachments Bar */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-amber-700 font-mono">
                  {caseAnalysis.dispute_category}
                </span>
                <h3 className="text-lg font-bold text-slate-900 font-serif mt-0.5">
                  {caseAnalysis.title}
                </h3>
              </div>

              {/* Upload Document to Case */}
              <label className="cursor-pointer inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs border border-slate-200 transition-colors">
                <input type="file" accept=".pdf,.docx,.txt" onChange={handleDocumentUpload} className="hidden" />
                <Upload className="w-3.5 h-3.5" />
                <span>Attach Document to Case</span>
              </label>
            </div>

            {/* Document Pills */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                Attached Files in Case ({caseAnalysis.documents.length}):
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {caseAnalysis.documents.map((doc, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800 truncate">{doc.filename}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-800 border border-amber-500/20">
                        {doc.role}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 font-mono">
                      {doc.segment_count} segments • {doc.char_count} chars
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cross-Document Conflicts & Discrepancies Alerts */}
          {caseAnalysis.cross_document_discrepancies.length > 0 && (
            <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 space-y-3">
              <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>Cross-Document Evidentiary Conflicts Detected ({caseAnalysis.cross_document_discrepancies.length})</span>
              </h4>

              <div className="space-y-2.5">
                {caseAnalysis.cross_document_discrepancies.map((disc, idx) => (
                  <div key={idx} className="p-4 bg-white rounded-lg border border-rose-200 space-y-1.5 shadow-2xs">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-rose-800 font-mono">
                        [{disc.issue_type}] - Severity: {disc.severity}
                      </span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        Between: {disc.involved_documents.join(' & ')}
                      </span>
                    </div>
                    <p className="text-xs text-slate-800 font-medium leading-relaxed">
                      {disc.description}
                    </p>
                    <div className="pt-1 text-xs text-indigo-900 flex items-start space-x-1.5 font-medium">
                      <ArrowRight className="w-3.5 h-3.5 text-indigo-600 mt-0.5 flex-shrink-0" />
                      <span><strong>Advocate Strategy:</strong> {disc.advocate_action}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chronological Timeline & Missing Evidence Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Interactive Chronological Timeline */}
            <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-indigo-600" />
                <span>Unified Chronological Case Timeline ({caseAnalysis.chronological_timeline.length} Events)</span>
              </h4>

              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {caseAnalysis.chronological_timeline.map((ev, idx) => (
                  <div key={idx} className="relative space-y-1 text-xs">
                    <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-amber-500 border-2 border-white shadow-xs"></div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-900 font-mono">{ev.event_date}</span>
                      <span className="text-[10px] px-2 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200 font-mono truncate max-w-[200px]">
                        {ev.source_doc_filename} ({ev.citation_pointer})
                      </span>
                      <span className={`text-[9px] px-1.5 rounded font-mono font-bold ${
                        ev.epistemic_nature === 'ALLEGATION' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {ev.epistemic_nature}
                      </span>
                    </div>
                    <p className="text-slate-700 bg-slate-50 p-2.5 rounded border border-slate-100 font-serif leading-relaxed">
                      "{ev.event_description}"
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Missing Evidence & Advocate Checklist */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  <span>Missing Supporting Records</span>
                </h4>
                <ul className="space-y-2 text-xs">
                  {caseAnalysis.missing_supporting_documents.map((rec, i) => (
                    <li key={i} className="p-2.5 rounded-lg bg-amber-50 border border-amber-200/80 text-amber-950 font-medium">
                      • {rec}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="space-y-3 pt-3 border-t border-slate-100">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                  <HelpCircle className="w-4 h-4 text-slate-500" />
                  <span>Key Questions for Legal Counsel</span>
                </h4>
                <div className="space-y-2 text-xs">
                  {caseAnalysis.strategic_advocate_questions.map((q, i) => (
                    <div key={i} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 font-medium">
                      {q}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Cross-Document Contextual Q&A */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <MessageSquare className="w-4 h-4 text-indigo-600" />
              <span>Cross-Document Question Answering</span>
            </h4>

            <div className="flex gap-2">
              <input
                type="text"
                value={qaQuestion}
                onChange={(e) => setQaQuestion(e.target.value)}
                placeholder="Ask a question comparing documents..."
                className="flex-1 text-xs p-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/50"
              />
              <button
                onClick={handleAskCaseQA}
                disabled={qaLoading}
                className="px-5 py-2 rounded-lg bg-slate-900 text-amber-300 font-bold text-xs uppercase hover:bg-slate-800 transition-colors disabled:opacity-50 flex items-center space-x-2"
              >
                {qaLoading ? <span>Searching...</span> : <span>Ask Case</span>}
              </button>
            </div>

            {/* QA Response */}
            {qaResponse && (
              <div className="mt-4 p-5 rounded-xl bg-amber-50/40 border border-amber-200 space-y-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-amber-900 font-serif">Verified Cross-Document Synthesis:</span>
                  <span className="text-[11px] font-mono text-slate-500">
                    Confidence: {(qaResponse.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>

                <p className="text-xs text-slate-800 whitespace-pre-line leading-relaxed font-sans">
                  {qaResponse.answer}
                </p>

                {/* Multi-Doc Pinpoint Citations */}
                <div className="pt-3 border-t border-amber-200/60 space-y-2">
                  <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                    Pinpoint Citations ({qaResponse.multi_doc_citations.length}):
                  </span>
                  <div className="space-y-1.5">
                    {qaResponse.multi_doc_citations.map((c, i) => (
                      <div key={i} className="p-2.5 rounded bg-white border border-amber-200/80 text-[11px] space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-amber-800 font-mono">{c.citation_id}</span>
                          <span className="text-[10px] text-slate-500 font-mono">{c.source_type}</span>
                        </div>
                        <p className="text-slate-700 font-serif italic">"{c.quote_snippet}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 font-serif">Initialize Case Workspace</h3>
            <form onSubmit={handleCreateNewCase} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Case / Dispute Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Apex Corp v. Zenith Logistics"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Dispute Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                >
                  <option value="CHEQUE_BOUNCE_DISPUTE">Cheque Dishonour (Sec 138 NI Act)</option>
                  <option value="TENANCY_DISPUTE">Tenancy & Eviction (Sec 106 TPA)</option>
                  <option value="COMMERCIAL_CONTRACT_BREACH">Commercial Contract Breach (ICA 1872)</option>
                  <option value="CONSUMER_DEFICIENCY_DISPUTE">Consumer Deficiency (CPA 2019)</option>
                  <option value="GENERAL_LEGAL_DISPUTE">General Legal Matter</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Brief Description (Optional)</label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Summary of facts, background, or parties..."
                  className="w-full p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold shadow-sm"
                >
                  Create Workspace
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
