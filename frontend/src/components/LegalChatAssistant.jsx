import React, { useState } from 'react';
import { 
  MessageSquare, 
  Send, 
  ShieldCheck, 
  BookOpen, 
  Scale, 
  AlertCircle, 
  FileText, 
  CheckCircle2, 
  HelpCircle,
  Paperclip,
  Trash2
} from 'lucide-react';
import { askRAG } from '../services/api';

const CHAT_PRESETS = [
  "What is the statutory deadline to respond to a Section 138 cheque bounce notice?",
  "Can an employer enforce a non-compete clause after termination in India?",
  "How much notice is mandatory for evicting a monthly tenant under Section 106?",
  "What are the essential elements required to establish cheating under Section 420 or BNS 318?"
];

export default function LegalChatAssistant({ currentLang }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: "Namaste! I am Advo टेक, your verified Indian legal document assistant. You can ask me questions about your legal notices, agreements, statutory deadlines, or Supreme Court precedents. Every answer is bounded by ground-truth evidence with verbatim citations.",
      citations: [],
      epistemic_check: null,
      confidence_score: 1.0,
      limitations: []
    }
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [documentContext, setDocumentContext] = useState('');
  const [showDocBox, setShowDocBox] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (queryText = inputQuery) => {
    const q = queryText.trim();
    if (!q) return;

    const userMsg = {
      id: `user_${Date.now()}`,
      role: 'user',
      text: q,
      doc_attached: Boolean(documentContext.trim())
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const resp = await askRAG(q, documentContext.trim() || null, currentLang);
      const assistantMsg = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        text: resp.answer,
        synthesis_engine: resp.synthesis_engine,
        citations: resp.citations || [],
        epistemic_check: resp.epistemic_check,
        confidence_score: resp.confidence_score,
        limitations: resp.limitations || [],
        advocate_questions: resp.suggested_advocate_questions || []
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        text: `Error processing query: ${err.message || 'Unable to retrieve grounded response.'}`,
        citations: []
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 font-serif">Verified Legal RAG Assistant</h2>
          <p className="text-sm text-slate-600 mt-1">
            Source-grounded legal question answering with epistemic separation and verifiable inline citations.
          </p>
        </div>

        <button
          onClick={() => setShowDocBox(!showDocBox)}
          className={`px-3.5 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors border ${
            showDocBox
              ? 'bg-amber-500/10 text-amber-900 border-amber-300'
              : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
          }`}
        >
          <Paperclip className="w-3.5 h-3.5" />
          <span>{showDocBox ? 'Hide Context Document' : 'Attach Context Document'}</span>
        </button>
      </div>

      {/* Optional Document Context Box */}
      {showDocBox && (
        <div className="bg-amber-50/50 p-5 rounded-xl border border-amber-200 space-y-2 text-xs">
          <div className="flex items-center justify-between font-bold text-amber-900">
            <span>Context Legal Document (Grounding Reference):</span>
            {documentContext && (
              <button
                onClick={() => setDocumentContext('')}
                className="text-rose-600 hover:text-rose-800 flex items-center space-x-1 text-[11px]"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear Context</span>
              </button>
            )}
          </div>
          <textarea
            rows={4}
            value={documentContext}
            onChange={(e) => setDocumentContext(e.target.value)}
            placeholder="Paste notice or contract text here to ask questions directly about it..."
            className="w-full p-3 bg-white border border-amber-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono text-xs"
          />
          <span className="text-[11px] text-amber-800 italic block">
            *When document context is attached, questions will be answered using both your document passages and the Indian Legal Knowledge Base.
          </span>
        </div>
      )}

      {/* Preset Queries */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] text-slate-400 font-medium">Sample Inquiries:</span>
        {CHAT_PRESETS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(p)}
            className="text-[11px] px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            "{p}"
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6 min-h-[400px]">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-3xl rounded-2xl p-5 text-xs leading-relaxed space-y-3 ${
                msg.role === 'user'
                  ? 'bg-slate-900 text-white rounded-br-none shadow-sm'
                  : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-bl-none shadow-xs'
              }`}
            >
              {/* Header Label */}
              <div className="flex items-center justify-between gap-4 pb-2 border-b border-slate-200/40 text-[10px] font-mono">
                <span className="font-bold uppercase tracking-wider text-amber-500">
                  {msg.role === 'user' ? 'You (Citizen)' : 'Advo टेक AI Assistant'}
                </span>
                {msg.synthesis_engine && (
                  <span className="text-slate-400">
                    Engine: {msg.synthesis_engine}
                  </span>
                )}
              </div>

              {/* Message Body */}
              <div className="whitespace-pre-line font-sans text-xs sm:text-[13px] leading-relaxed">
                {msg.text}
              </div>

              {/* Citations Footer */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-3 border-t border-slate-200/80 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-slate-500 font-mono tracking-wider flex items-center space-x-1">
                    <BookOpen className="w-3 h-3 text-amber-600" />
                    <span>Verifiable Inline Citations ({msg.citations.length}):</span>
                  </span>
                  <div className="space-y-1.5">
                    {msg.citations.map((c, i) => (
                      <div key={i} className="p-2 rounded bg-white border border-slate-200 text-[11px] space-y-0.5">
                        <div className="flex items-center justify-between text-[10px] font-mono">
                          <span className="font-bold text-amber-800">{c.citation_id}</span>
                          <span className="text-slate-400">{c.source_type}</span>
                        </div>
                        <p className="font-serif italic text-slate-600 line-clamp-2">"{c.quote_snippet}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Advocate Questions */}
              {msg.advocate_questions && msg.advocate_questions.length > 0 && (
                <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg space-y-1.5 text-[11px] text-amber-950">
                  <span className="font-bold uppercase text-[10px] text-amber-900 font-mono flex items-center space-x-1">
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span>Questions to Discuss With an Advocate:</span>
                  </span>
                  <ul className="list-disc pl-4 space-y-1">
                    {msg.advocate_questions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-xs text-slate-400 p-4">
            <span className="w-3.5 h-3.5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></span>
            <span>Retrieving legal authorities & synthesizing grounded response...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="flex gap-2">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Ask a legal question in plain language..."
          className="flex-1 text-xs p-3.5 bg-white border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500 shadow-sm"
        />
        <button
          onClick={() => handleSendMessage()}
          disabled={loading || !inputQuery.trim()}
          className="px-6 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all disabled:opacity-50 flex items-center space-x-2 shadow-sm"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Ask</span>
        </button>
      </div>

      {/* Mandatory Disclaimer */}
      <p className="text-[11px] text-slate-400 text-center italic">
        *Advo टेक provides educational and informational document intelligence. This does not constitute legal advice or create an advocate-client relationship. Please consult a licensed advocate for legal proceedings.
      </p>
    </div>
  );
}
