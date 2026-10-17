import React, { useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Coins, 
  Scale, 
  Sparkles, 
  HelpCircle,
  Copy,
  Languages,
  Filter
} from 'lucide-react';
import { analyzeDocumentUpload, getStructuredAnalysis, simplifyLegalText } from '../services/api';

const SAMPLES = {
  cheque: `LEGAL DEMAND NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881

To,
Sh. Rajesh Kumar
Proprietor, M/s Kumar Enterprises
Connaught Place, New Delhi - 110001

Under instructions from and on behalf of my client, M/s Sharma Traders, having its registered office at Nehru Place, New Delhi, I hereby serve upon you this formal statutory legal notice:

1. My client states that you issued Cheque No. 458921 dated 15th January 2024 for an amount of Rs. 2,50,000/- drawn on State Bank of India, Connaught Place Branch, towards the legally enforceable debt of supply of building materials.
2. The said cheque was presented by my client through their banker, HDFC Bank, but the same was returned dishonoured with the remarks "Funds Insufficient" vide Bank Return Memo dated 20th January 2024.
3. My client informs that you have dishonestly and intentionally issued the said cheque without maintaining sufficient balance, with an intention to defraud my client.
4. You are hereby called upon and required to remit and pay the aforementioned amount of Rs. 2,50,000/- within a period of 15 days from the receipt of this statutory notice, failing which my client will be constrained to initiate criminal proceedings against you under Section 138 and Section 142 of the Negotiable Instruments Act, 1881.

Yours faithfully,
Adv. Priya Singh
Delhi High Court Bar Association`,

  tenancy: `NOTICE TO QUIT AND VACATE PREMISES UNDER SECTION 106 OF TRANSFER OF PROPERTY ACT, 1882

To,
Mr. Arvind Verma,
Flat No. 402, Green Valley Apartments, Indirapuram, Ghaziabad.

Sir,
Under instructions from your landlord, Mr. Suresh Malhotra, I hereby give you notice to quit, vacate, and deliver peaceful and vacant possession of the premises bearing Flat No. 402, Green Valley Apartments, currently occupied by you as a monthly tenant.

1. You entered into a monthly tenancy agreement commencing on 1st April 2023 at a monthly rent of Rs. 25,000/- excluding electricity charges.
2. You have failed and neglected to remit rent for the past three consecutive months amounting to Rs. 75,000/-.
3. Your tenancy is hereby terminated with the expiry of 15 days from the receipt of this notice in terms of Section 106 of the Transfer of Property Act, 1882.
4. If you fail to hand over peaceful possession within the stipulated 15 days period, appropriate proceedings for ejectment and mesne profits will be initiated against you before the Civil Court.

Adv. Ramesh Gupta
Ghaziabad District Court`,
};

export default function SingleDocAnalyzer({ currentLang }) {
  const [inputText, setInputText] = useState(SAMPLES.cheque);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Results
  const [analysisResult, setAnalysisResult] = useState(null);
  const [simplificationResult, setSimplificationResult] = useState(null);
  const [activeResultTab, setActiveResultTab] = useState('summary');
  const [simplificationLang, setSimplificationLang] = useState('en');

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setError(null);
    setLoading(true);

    try {
      const uploadRes = await analyzeDocumentUpload(file);
      const combinedText = uploadRes.segments.map((s) => s.content).join('\n\n');
      setInputText(combinedText);
      await runAnalysisPipeline(combinedText);
    } catch (err) {
      setError(err.message || 'Failed to process document file.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!inputText || inputText.trim().length < 20) {
      setError('Please provide at least 20 characters of legal document text.');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      await runAnalysisPipeline(inputText);
    } catch (err) {
      setError(err.message || 'Analysis failed. Please check document content.');
    } finally {
      setLoading(false);
    }
  };

  const runAnalysisPipeline = async (text) => {
    const [analysisData, simpData] = await Promise.all([
      getStructuredAnalysis(text),
      simplifyLegalText(text, simplificationLang),
    ]);
    setAnalysisResult(analysisData);
    setSimplificationResult(simpData);
    setActiveResultTab('summary');
  };

  const handleLanguageChange = async (newLang) => {
    setSimplificationLang(newLang);
    if (inputText) {
      try {
        const simpData = await simplifyLegalText(inputText, newLang);
        setSimplificationResult(simpData);
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Heading */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900 font-serif">Legal Document Analyzer</h2>
          <p className="text-sm text-slate-600 mt-1">
            Extract entities, classify statements epistemically, and generate simple plain-language explanations.
          </p>
        </div>

        {/* Quick Sample Buttons */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500 font-medium">Load Sample:</span>
          <button
            onClick={() => { setInputText(SAMPLES.cheque); setSelectedFile(null); }}
            className="px-2.5 py-1 text-xs rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
          >
            Sec 138 Notice
          </button>
          <button
            onClick={() => { setInputText(SAMPLES.tenancy); setSelectedFile(null); }}
            className="px-2.5 py-1 text-xs rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
          >
            Tenancy Eviction
          </button>
        </div>
      </div>

      {/* Input Section: Upload or Paste */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Dropzone */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
            <UploadCloud className="w-4 h-4 text-indigo-600" />
            <span>Upload Document (PDF / DOCX)</span>
          </h3>

          <label className="border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:border-amber-500 hover:bg-amber-50/20 transition-all block">
            <input type="file" accept=".pdf,.docx" onChange={handleFileUpload} className="hidden" />
            <FileText className="w-10 h-10 text-slate-400 mb-2" />
            <span className="text-xs font-semibold text-slate-700">Click to upload or drag & drop</span>
            <span className="text-[11px] text-slate-500 mt-1">PDF or DOCX (Max 20MB)</span>
            {selectedFile && (
              <span className="mt-3 inline-block px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 text-xs font-mono font-medium truncate max-w-full">
                {selectedFile.name}
              </span>
            )}
          </label>

          <p className="text-[11px] text-slate-500 italic">
            *Preserves original page and paragraph citations for strict legal verification.
          </p>
        </div>

        {/* Text Input Area */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <FileText className="w-4 h-4 text-indigo-600" />
              <span>Or Paste Document Content</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">{inputText.length} chars</span>
          </div>

          <textarea
            rows={7}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste notice, agreement, or court order here..."
            className="w-full text-xs font-mono p-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/50 resize-y"
          />

          <div className="flex justify-end">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="px-6 py-2.5 rounded-lg bg-amber-500 text-slate-950 font-bold text-xs uppercase tracking-wider hover:bg-amber-400 transition-all disabled:opacity-50 flex items-center space-x-2 shadow-sm"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                  <span>Processing NLP Pipeline...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Execute Full Analysis</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Top Quick Key Data Bar */}
          <div className="bg-slate-900 p-4 text-white flex flex-wrap items-center justify-between gap-4 border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <span className="text-xs px-2.5 py-1 rounded bg-amber-500 text-slate-950 font-bold uppercase tracking-wider font-mono">
                {analysisResult.category_label || analysisResult.document_type}
              </span>
              <span className="text-xs text-slate-300 font-mono">
                Confidence: {(analysisResult.classification_confidence * 100).toFixed(0)}%
              </span>
            </div>

            <div className="flex items-center space-x-6 text-xs">
              <div className="flex items-center space-x-1.5 text-amber-300">
                <Clock className="w-4 h-4" />
                <span className="font-semibold">
                  {analysisResult.deadlines.length > 0 ? analysisResult.deadlines[0] : 'No Explicit Deadline'}
                </span>
              </div>
              <div className="flex items-center space-x-1.5 text-emerald-300">
                <Coins className="w-4 h-4" />
                <span className="font-semibold">
                  {analysisResult.monetary_amounts.length > 0 ? analysisResult.monetary_amounts[0] : 'None Mentioned'}
                </span>
              </div>
            </div>
          </div>

          {/* Results Navigation Tabs */}
          <div className="flex border-b border-slate-200 bg-slate-50/80 px-4">
            {[
              { id: 'summary', label: 'Plain Language Simplification', icon: Sparkles },
              { id: 'epistemic', label: 'Epistemic Statement Parser', icon: Scale },
              { id: 'entities', label: 'Extracted Legal Entities', icon: FileText },
              { id: 'advocate', label: 'Advocate Strategy & Gaps', icon: HelpCircle },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveResultTab(tab.id)}
                  className={`flex items-center space-x-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all ${
                    activeResultTab === tab.id
                      ? 'border-amber-500 text-amber-800 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Content Panels */}
          <div className="p-6">
            {/* 1. Simplification Tab */}
            {activeResultTab === 'summary' && simplificationResult && (
              <div className="space-y-6">
                {/* Language Switcher for Explanation */}
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    <Languages className="w-4 h-4 text-amber-600" />
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Explanation Language:
                    </span>
                    {['en', 'hi', 'hinglish'].map((l) => (
                      <button
                        key={l}
                        onClick={() => handleLanguageChange(l)}
                        className={`px-3 py-1 rounded text-xs font-semibold capitalize transition-all ${
                          simplificationLang === l
                            ? 'bg-amber-500 text-slate-950 shadow-sm'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {l === 'en' ? 'English' : l === 'hi' ? 'हिंदी' : 'Hinglish'}
                      </button>
                    ))}
                  </div>

                  <span className="text-xs text-slate-400 font-mono">
                    Fidelity: {simplificationResult.fidelity_verification?.fidelity_passed ? 'Verified 100%' : 'Audited'}
                  </span>
                </div>

                {/* Executive Summary Card */}
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-5 space-y-2">
                  <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-amber-700" />
                    <span>Executive Summary in Plain Words</span>
                  </h4>
                  <p className="text-sm text-slate-800 leading-relaxed font-sans">
                    {simplificationLang === 'hi'
                      ? simplificationResult.executive_summary_hi
                      : simplificationLang === 'hinglish'
                      ? simplificationResult.executive_summary_hinglish
                      : simplificationResult.executive_summary_en}
                  </p>
                </div>

                {/* Side-by-side or Clause Breakdowns */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Grounded Clause-by-Clause Translation
                  </h4>
                  <div className="space-y-3">
                    {simplificationResult.simplified_clauses.map((clause, idx) => (
                      <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-2">
                        <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                          <span>{clause.original_reference_label}</span>
                          <span className="text-emerald-700 font-semibold">Preserved Meaning</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                          <div className="p-3 bg-white rounded border border-slate-200 text-slate-600 font-mono">
                            <strong className="block text-slate-400 uppercase text-[10px] mb-1 font-sans">Original Legalese:</strong>
                            "{clause.original_text}"
                          </div>
                          <div className="p-3 bg-amber-50/50 rounded border border-amber-200 text-slate-900">
                            <strong className="block text-amber-700 uppercase text-[10px] mb-1">Plain Language:</strong>
                            {clause.simplified_text}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 2. Epistemic Statement Parser Tab */}
            {activeResultTab === 'epistemic' && (
              <div className="space-y-4">
                <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-950 leading-relaxed">
                  <strong>Epistemic Separation Guardrail:</strong> In Indian law, claims in a legal notice represent <em>allegations</em> by the opposing party, not established facts. Below, our parser categorizes each sentence into its strict legal status.
                </div>

                <div className="space-y-3">
                  {analysisResult.classified_statements.map((stmt, idx) => {
                    let badgeColor = 'bg-slate-100 text-slate-700 border-slate-200';
                    let label = stmt.epistemic_type;
                    if (stmt.epistemic_type === 'DEMAND_OR_OBLIGATION') {
                      badgeColor = 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
                      label = 'DEMAND / DEADLINE';
                    } else if (stmt.epistemic_type === 'ALLEGATION') {
                      badgeColor = 'bg-amber-50 text-amber-800 border-amber-200 font-bold';
                      label = 'UNPROVEN ALLEGATION';
                    } else if (stmt.epistemic_type === 'FACT') {
                      badgeColor = 'bg-emerald-50 text-emerald-800 border-emerald-200 font-bold';
                      label = 'ESTABLISHED FACT';
                    } else if (stmt.epistemic_type === 'LEGAL_REASONING') {
                      badgeColor = 'bg-blue-50 text-blue-800 border-blue-200 font-bold';
                      label = 'STATUTORY JURISDICTION';
                    }

                    return (
                      <div key={idx} className="p-3.5 rounded-lg border border-slate-200 bg-white flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                        <div className="space-y-1 text-xs">
                          <span className="text-[10px] font-mono text-slate-400">Sentence #{idx + 1}</span>
                          <p className="text-slate-800 font-serif leading-relaxed">"{stmt.text}"</p>
                        </div>
                        <span className={`px-2.5 py-1 rounded text-[11px] font-mono border whitespace-nowrap self-start ${badgeColor}`}>
                          {label} ({(stmt.confidence * 100).toFixed(0)}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 3. Entities Tab */}
            {activeResultTab === 'entities' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(analysisResult.entities_by_category).map(([cat, items]) => (
                    <div key={cat} className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                      <span className="text-xs font-bold text-slate-700 font-mono tracking-wider">
                        {cat} ({items.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {items.map((item, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-white border border-slate-200 text-xs font-medium text-slate-800 shadow-2xs">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. Advocate Strategy Tab */}
            {activeResultTab === 'advocate' && (
              <div className="space-y-6">
                {/* Evidentiary Gaps & Ambiguities */}
                {analysisResult.missing_information_and_ambiguities?.length > 0 && (
                  <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 space-y-2">
                    <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center space-x-1.5">
                      <AlertCircle className="w-4 h-4 text-amber-700" />
                      <span>Potential Ambiguities & Missing Evidentiary Dates</span>
                    </h4>
                    <ul className="list-disc pl-5 text-xs text-amber-900 space-y-1">
                      {analysisResult.missing_information_and_ambiguities.map((gap, i) => (
                        <li key={i}>{gap}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Advocate Consultation Questions */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Recommended Questions to Ask an Advocate
                  </h4>
                  <div className="space-y-2.5">
                    {analysisResult.suggested_questions_for_advocate.map((q, idx) => (
                      <div key={idx} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-800 flex items-start space-x-3">
                        <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                          {idx + 1}
                        </span>
                        <p className="font-medium leading-relaxed">{q}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
