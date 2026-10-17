import React from 'react';
import { 
  FileText, 
  FolderKanban, 
  Search, 
  MessageSquare, 
  ShieldAlert, 
  BookOpen, 
  CheckCircle2, 
  Clock, 
  Scale, 
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function Dashboard({ setActiveTab, onLoadSample }) {
  const stats = [
    { label: 'Statutory Provisions Indexed', value: '7 Sections', subtext: 'NI Act, Contract Act, TPA, CPA, IPC/BNS', icon: BookOpen },
    { label: 'Supreme Court Precedents', value: '5 Rulings', subtext: 'Verifiable Ratios & Citations', icon: Scale },
    { label: 'Epistemic Segmentation', value: '4 Classes', subtext: 'Facts, Allegations, Demands, Reasoning', icon: ShieldAlert },
    { label: 'Multilingual Simplification', value: '3 Languages', subtext: 'English, Hindi, Hinglish', icon: Sparkles },
  ];

  const features = [
    {
      id: 'analyzer',
      title: 'Legal Document Analyzer',
      description: 'Upload PDF or DOCX legal notices. Automatically extract monetary claims, deadlines, and convert complex legalese into clear, simple language.',
      badge: 'Core Feature',
      icon: FileText,
      color: 'blue',
    },
    {
      id: 'cases',
      title: 'Case Workspaces & Timeline',
      description: 'Connect multiple documents (Notice + Agreement + Bank Return Memo). Detect cross-document monetary conflicts, limitation breaches, and bypassed arbitration clauses.',
      badge: 'Multi-Document',
      icon: FolderKanban,
      color: 'amber',
    },
    {
      id: 'search',
      title: 'Hybrid Semantic Legal Search',
      description: 'Search Indian legislation and case laws using ordinary words like "my landlord asked me to vacate". Combines dense Sentence-Transformers with sparse TF-IDF.',
      badge: 'Dual Retrieval',
      icon: Search,
      color: 'emerald',
    },
    {
      id: 'chat',
      title: 'Source-Grounded Legal RAG',
      description: 'Ask questions with zero hallucination. Answers are strictly bounded by uploaded document excerpts and verified statutes, complete with inline citations.',
      badge: 'Anti-Hallucination',
      icon: MessageSquare,
      color: 'purple',
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 p-8 sm:p-10 text-white shadow-xl border border-slate-700/60">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Smart India Hackathon (SIH) 2024 Project</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight font-serif text-white">
            Demystifying Indian Legal Documents for Ordinary Citizens
          </h1>
          <p className="text-slate-300 text-base sm:text-lg leading-relaxed">
            <strong className="text-amber-400">Advo टेक</strong> is an NLP-driven judicial intelligence platform. 
            We analyze notices and agreements, segregate unproven allegations from facts, pinpoint statutory deadlines, 
            and retrieve binding court rulings—grounded entirely in verifiable legal sources.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => setActiveTab('analyzer')}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-amber-500 text-slate-950 font-semibold text-sm hover:bg-amber-400 transition-all shadow-md hover:shadow-amber-500/20"
            >
              <span>Analyze a Notice Now</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveTab('cases')}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-slate-800/90 text-slate-200 border border-slate-700 font-semibold text-sm hover:bg-slate-700 hover:text-white transition-all"
            >
              <span>Explore Multi-Document Cases</span>
            </button>
          </div>
        </div>

        {/* Decorative Background Elements */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 pointer-events-none hidden md:flex items-center justify-center">
          <Scale className="w-96 h-96 text-white" />
        </div>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div key={idx} className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-start space-x-4">
              <div className="p-2.5 rounded-lg bg-slate-100 text-slate-700">
                <Icon className="w-5 h-5 text-indigo-700" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{s.label}</p>
                <p className="text-xl font-bold text-slate-900 mt-0.5">{s.value}</p>
                <p className="text-xs text-slate-500 mt-1">{s.subtext}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Core Capability Cards */}
      <div>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-slate-900 font-serif">Platform Capabilities</h2>
          <p className="text-sm text-slate-600">Select a module below to process legal documents or explore Indian case law.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div
                key={f.id}
                onClick={() => setActiveTab(f.id)}
                className="group cursor-pointer bg-white rounded-xl p-6 border border-slate-200/80 shadow-sm hover:shadow-md hover:border-slate-400/80 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-lg bg-amber-500/10 text-amber-700 border border-amber-500/20 group-hover:bg-amber-500/20 transition-colors">
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {f.badge}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 group-hover:text-amber-700 transition-colors">
                    {f.title}
                  </h3>
                  <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                    {f.description}
                  </p>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-amber-700">
                  <span>Launch Tool</span>
                  <ArrowRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SIH Evaluation & Trust Architecture */}
      <div className="rounded-xl bg-slate-50 border border-slate-200 p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <span>Why Advo टेक is Not Just Another Chatbot</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-600 leading-relaxed">
          <div className="p-3.5 bg-white rounded-lg border border-slate-200/80">
            <strong className="block text-slate-900 mb-1">1. Epistemic Integrity</strong>
            We never convert an unproven allegation made in a legal notice into a judicial fact. Allegations and demands are segregated through grammatical parsing.
          </div>
          <div className="p-3.5 bg-white rounded-lg border border-slate-200/80">
            <strong className="block text-slate-900 mb-1">2. Zero-Cost Offline Fallback</strong>
            Operates completely offline with deterministic legal synthesizers and local Sentence Transformers if internet or API keys are unavailable during evaluation.
          </div>
          <div className="p-3.5 bg-white rounded-lg border border-slate-200/80">
            <strong className="block text-slate-900 mb-1">3. Pinpoint Source Citations</strong>
            Every legal conclusion cites verbatim document lines, India Code statutory sections, and landmark Supreme Court ratios.
          </div>
        </div>
      </div>
    </div>
  );
}
