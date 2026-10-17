import React, { useState } from 'react';
import { 
  Search, 
  Sliders, 
  ExternalLink, 
  BookOpen, 
  Scale, 
  ShieldCheck, 
  Sparkles,
  GitCompare,
  AlertCircle
} from 'lucide-react';
import { searchLegalKB, compareSearchMethods } from '../services/api';

const PRESETS = [
  "My landlord asked me to vacate within 30 days",
  "My employer terminated me without giving notice",
  "Cheque bounce for insufficient funds and notice period",
  "Section 138 Negotiable Instruments Act",
  "Compensation for breach of contract and damages"
];

export default function LegalSearch() {
  const [query, setQuery] = useState(PRESETS[0]);
  const [alpha, setAlpha] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [compareData, setCompareData] = useState(null);
  const [isCompareMode, setIsCompareMode] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      if (isCompareMode) {
        const comp = await compareSearchMethods(query);
        setCompareData(comp);
      } else {
        const res = await searchLegalKB(query, alpha, 5);
        setResults(res.results || []);
      }
    } catch (err) {
      setError(err.message || 'Search execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 font-serif">Indian Legal Knowledge Base & Hybrid Search</h2>
          <p className="text-sm text-slate-600 mt-1">
            Query Central Acts, statutory provisions, and landmark Supreme Court ratios using plain English language.
          </p>
        </div>

        {/* Query Input Box */}
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search factual scenario (e.g. 'employer fired me without notice')..."
              className="w-full text-xs pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            />
          </div>

          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-3 rounded-lg bg-amber-500 text-slate-950 font-bold text-xs uppercase tracking-wider hover:bg-amber-400 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2 shadow-sm"
          >
            {loading ? <span>Searching...</span> : <span>Execute Search</span>}
          </button>
        </div>

        {/* Presets */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] text-slate-400 font-medium">Try Scenario:</span>
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => { setQuery(p); }}
              className="text-[11px] px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              "{p}"
            </button>
          ))}
        </div>

        {/* Controls: Alpha Slider & Benchmark Mode */}
        <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
          {/* Alpha Slider */}
          <div className="flex items-center space-x-3">
            <Sliders className="w-4 h-4 text-slate-500" />
            <span className="font-semibold text-slate-700">Ensemble Weight (α):</span>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              value={alpha}
              disabled={isCompareMode}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="w-28 accent-amber-500"
            />
            <span className="font-mono text-slate-500 font-bold">
              {alpha === 1.0 ? '1.0 (Dense Semantic)' : alpha === 0.0 ? '0.0 (Lexical BM25)' : `${alpha} (Balanced Hybrid)`}
            </span>
          </div>

          {/* Compare Toggle */}
          <button
            onClick={() => { setIsCompareMode(!isCompareMode); setResults(null); setCompareData(null); }}
            className={`px-3 py-1.5 rounded-lg border font-semibold flex items-center space-x-1.5 transition-colors ${
              isCompareMode
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Benchmark Comparison Mode</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {error}
        </div>
      )}

      {/* Standard Results List */}
      {!isCompareMode && results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Retrieved <strong>{results.length}</strong> legal authorities matching query</span>
            <span className="font-mono">Ranking: Hybrid Score (α={alpha})</span>
          </div>

          <div className="space-y-4">
            {results.map((item, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-slate-200 p-6 space-y-3 shadow-xs">
                {/* Title & Metadata Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                        item.doc_type === 'STATUTE' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      }`}>
                        {item.doc_type}
                      </span>
                      <span className="text-xs font-mono text-slate-500">
                        {item.court_or_authority || item.citation}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 font-serif">
                      {item.title}
                    </h3>
                  </div>

                  {/* Provenance Link */}
                  {item.source_url && (
                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors self-start"
                    >
                      <span>India Code / Source</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>

                {/* Score Pills */}
                <div className="flex items-center space-x-3 text-[11px] font-mono">
                  <span className="text-amber-800 font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Hybrid Score: {item.hybrid_score.toFixed(3)}
                  </span>
                  <span className="text-slate-500">
                    Semantic: {item.semantic_score.toFixed(3)}
                  </span>
                  <span className="text-slate-500">
                    Keyword: {item.keyword_score.toFixed(3)}
                  </span>
                </div>

                {/* Retrieval Rationale */}
                <div className="p-3 bg-amber-50/50 rounded-lg border border-amber-200/60 text-xs text-slate-800 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-amber-800 tracking-wider font-mono">
                    Retrieval Rationale (Explainability):
                  </span>
                  <p className="italic font-serif">"{item.retrieval_rationale}"</p>
                </div>

                {/* Ratio Decidendi or Statute Excerpt */}
                {item.ratio_decidendi ? (
                  <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-900 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 font-mono">
                      Supreme Court Ratio Decidendi (Binding Holding):
                    </span>
                    <p className="font-serif leading-relaxed">"{item.ratio_decidendi}"</p>
                  </div>
                ) : (
                  <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-800 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 font-mono">
                      Statutory Provision Excerpt:
                    </span>
                    <p className="font-serif leading-relaxed line-clamp-3">"{item.content_snippet}"</p>
                  </div>
                )}

                {/* Guardrail Disclaimer */}
                <p className="text-[10px] text-slate-400 italic pt-1">
                  *{item.legal_guardrail_notice}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Side-by-Side Comparison Benchmark Mode */}
      {isCompareMode && compareData && (
        <div className="space-y-6">
          <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-950 font-medium">
            <strong>Benchmark Analysis:</strong> {compareData.benchmark_analysis}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Column 1: Keyword Only */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-3">
              <span className="block font-bold text-slate-800 uppercase font-mono tracking-wider pb-2 border-b">
                1. Pure Keyword / BM25 (α = 0.0)
              </span>
              <div className="space-y-3">
                {compareData.keyword_only_results.map((r, i) => (
                  <div key={i} className="p-2.5 bg-slate-50 rounded border border-slate-200 space-y-1">
                    <p className="font-bold text-slate-900">{r.title}</p>
                    <span className="text-[10px] font-mono text-slate-500">Score: {r.keyword_score.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Column 2: Semantic Only */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-3">
              <span className="block font-bold text-slate-800 uppercase font-mono tracking-wider pb-2 border-b">
                2. Pure Semantic Vectors (α = 1.0)
              </span>
              <div className="space-y-3">
                {compareData.semantic_only_results.map((r, i) => (
                  <div key={i} className="p-2.5 bg-slate-50 rounded border border-slate-200 space-y-1">
                    <p className="font-bold text-slate-900">{r.title}</p>
                    <span className="text-[10px] font-mono text-slate-500">Score: {r.semantic_score.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Column 3: Balanced Hybrid */}
            <div className="bg-white p-4 rounded-xl border border-amber-300 bg-amber-50/20 space-y-3 shadow-xs">
              <span className="block font-bold text-amber-900 uppercase font-mono tracking-wider pb-2 border-b border-amber-200">
                3. Balanced Hybrid (α = 0.6)
              </span>
              <div className="space-y-3">
                {compareData.hybrid_results.map((r, i) => (
                  <div key={i} className="p-2.5 bg-white rounded border border-amber-200 space-y-1">
                    <p className="font-bold text-slate-900">{r.title}</p>
                    <span className="text-[10px] font-mono text-amber-700 font-bold">Hybrid: {r.hybrid_score.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
