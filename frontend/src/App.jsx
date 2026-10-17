import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import SingleDocAnalyzer from './components/SingleDocAnalyzer';
import CaseWorkspaces from './components/CaseWorkspaces';
import LegalSearch from './components/LegalSearch';
import LegalChatAssistant from './components/LegalChatAssistant';
import Footer from './components/Footer';
import { getEngineStatus } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentLang, setCurrentLang] = useState('en');
  const [engineStatus, setEngineStatus] = useState(null);

  useEffect(() => {
    fetchEngineStatus();
  }, []);

  const fetchEngineStatus = async () => {
    try {
      const status = await getEngineStatus();
      setEngineStatus(status);
    } catch (err) {
      console.warn('Backend not currently reachable or running in offline mode:', err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Header & Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentLang={currentLang}
        setCurrentLang={setCurrentLang}
        engineStatus={engineStatus}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {activeTab === 'dashboard' && (
          <Dashboard
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'analyzer' && (
          <SingleDocAnalyzer
            currentLang={currentLang}
          />
        )}

        {activeTab === 'cases' && (
          <CaseWorkspaces
            currentLang={currentLang}
          />
        )}

        {activeTab === 'search' && (
          <LegalSearch />
        )}

        {activeTab === 'chat' && (
          <LegalChatAssistant
            currentLang={currentLang}
          />
        )}
      </main>

      {/* Global Judicial Footer */}
      <Footer />
    </div>
  );
}
