import React from 'react';
import { Scale, ShieldCheck, ExternalLink, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-xs mt-16 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Scale className="w-5 h-5 text-amber-400" />
              <span className="text-base font-bold text-white font-serif">Advo टेक</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">
                SIH 2024
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Verified AI for Judicial Knowledge & Legal Document Intelligence (India)
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs">
            <a
              href="https://www.indiacode.nic.in"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white flex items-center space-x-1"
            >
              <span>India Code Digital Repository</span>
              <ExternalLink className="w-3 h-3 text-slate-500" />
            </a>
            <a
              href="https://main.sci.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white flex items-center space-x-1"
            >
              <span>Supreme Court of India (eSCR)</span>
              <ExternalLink className="w-3 h-3 text-slate-500" />
            </a>
          </div>
        </div>

        {/* Disclaimer & Privacy Notice */}
        <div className="space-y-2 text-[11px] text-slate-500 leading-relaxed">
          <p>
            <strong>Mandatory Legal Disclaimer:</strong> Advo टेक is an assistive legal document intelligence system developed for educational, informational, and judicial literacy purposes. The platform does not provide legal representation, formulate formal attorney-client relationships, or guarantee judicial outcomes. Always engage a licensed advocate enrolled with the Bar Council for formal litigation or legal advice.
          </p>
          <p>
            <strong>Privacy & Data Safeguards:</strong> Uploaded documents are processed strictly in-memory for ephemeral NLP parsing and are not persisted to external LLM providers or used for training without consent.
          </p>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-slate-800/80 text-[11px]">
          <span>© 2024-2026 Advo टेक. All rights reserved.</span>
          <span className="flex items-center space-x-1">
            <span>Built with integrity for</span>
            <span className="text-amber-400 font-bold">Smart India Hackathon</span>
          </span>
        </div>
      </div>
    </footer>
  );
}
