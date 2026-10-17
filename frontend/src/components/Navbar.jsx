import React from 'react';
import { Scale, FileText, FolderKanban, Search, MessageSquare, ShieldCheck, Globe } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, currentLang, setCurrentLang, engineStatus }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Scale },
    { id: 'analyzer', label: 'Document Analyzer', icon: FileText },
    { id: 'cases', label: 'Case Workspaces', icon: FolderKanban },
    { id: 'search', label: 'Legal Search', icon: Search },
    { id: 'chat', label: 'RAG Assistant', icon: MessageSquare },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Branding */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-sm">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white font-serif">Advo टेक</span>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-medium">SIH 2024</span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">Verified AI for Judicial Knowledge & Document Intelligence</p>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-inner'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Controls: Language Selector & Engine Badge */}
          <div className="flex items-center space-x-3">
            {/* Language Switcher */}
            <div className="flex items-center bg-slate-800 border border-slate-700 rounded-lg p-0.5 text-xs">
              <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1" />
              {[
                { id: 'en', label: 'English' },
                { id: 'hi', label: 'हिंदी' },
                { id: 'hinglish', label: 'Hinglish' },
              ].map((lang) => (
                <button
                  key={lang.id}
                  onClick={() => setCurrentLang(lang.id)}
                  className={`px-2 py-1 rounded font-medium transition-all ${
                    currentLang === lang.id
                      ? 'bg-amber-500 text-slate-950 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {lang.label}
                </button>
              ))}
            </div>

            {/* Offline/Online Engine Status Pill */}
            <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-[11px] text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-mono">
                {engineStatus?.gemini_api_configured ? 'Gemini 1.5' : 'Offline Verified Engine'}
              </span>
            </div>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="flex md:hidden overflow-x-auto py-2 space-x-2 border-t border-slate-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1 px-2.5 py-1.5 rounded text-xs whitespace-nowrap ${
                  isActive
                    ? 'bg-amber-500/20 text-amber-300 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
