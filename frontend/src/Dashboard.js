import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { BackgroundShapes } from './components/dashboard/BackgroundShapes';
import { DashboardSidebar } from './components/dashboard/DashboardSidebar';
import { Hero } from './components/dashboard/Hero';
import { PortfolioOverview } from './components/dashboard/PortfolioOverview';
import { InvestmentRecommendations } from './components/dashboard/InvestmentRecommendations';
import { DashboardChatInterface } from './components/dashboard/DashboardChatInterface';
import { MarketOverview } from './components/dashboard/MarketOverview';
import HoldingsManager from './components/dashboard/HoldingsManager';
import { askQuestion } from './api';

// New robo-advisor components
import { GoalPlanSnapshot } from './components/dashboard/GoalPlanSnapshot';
import { PortfolioDriftAlert } from './components/dashboard/PortfolioDriftAlert';
import { MarketSentimentWidget } from './components/dashboard/MarketSentimentWidget';
import { EnhancedPortfolioPage } from './components/dashboard/EnhancedPortfolioPage';

function Dashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Check authentication on component mount
  useEffect(() => {
    const isAuthenticated = sessionStorage.getItem('isAuthenticated');
    if (!isAuthenticated) {
      navigate('/');
    }
  }, [navigate]);

  // Chat state - reusing your existing API logic
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (question) => {
    const timestamp = new Date().toLocaleTimeString();

    // Add user message
    const userMessage = { role: 'user', text: question, time: timestamp };
    setHistory((prev) => [...prev, userMessage]);

    setLoading(true);

    // Get previous assistant answer for contradiction detection
    let prevAnswer = null;
    for (let i = history.length - 1; i >= 0; i--) {
      if (history[i].role === 'assistant') {
        prevAnswer = history[i].text;
        break;
      }
    }

    // Call backend API with your existing configuration
    const payload = {
      text: question,
      provider: 'deepseek',
      k: 5,
      retrieval_mode: 'tfidf',
      use_entropy: true,
      use_nli: true,
      use_fhri: true,
    };

    if (prevAnswer) {
      payload.prev_assistant_turn = prevAnswer;
    }

    try {
      const backendRes = await askQuestion(payload);

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        text: backendRes.answer,
        time: timestamp,
        meta: {
          entropy: backendRes.entropy,
          is_hallucination: backendRes.is_hallucination,
          contradiction_score: backendRes.contradiction_score,
          fhri: backendRes.meta?.fhri,
        },
      };
      setHistory((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error submitting question:', error);
      const errorMessage = {
        role: 'assistant',
        text: 'Sorry, I encountered an error processing your request. Please try again.',
        time: timestamp,
      };
      setHistory((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      {/* Background Geometric Shapes */}
      <BackgroundShapes />

      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="lg:hidden fixed top-6 left-6 z-50 w-12 h-12 rounded-xl gradient-blue-button flex items-center justify-center shadow-lg"
      >
        {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm z-40"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div
            className="w-80 h-full"
            onClick={(e) => e.stopPropagation()}
          >
            <DashboardSidebar activeTab={activeTab} onTabChange={(tab) => {
              setActiveTab(tab);
              setMobileMenuOpen(false);
            }} />
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <DashboardSidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <main className="lg:ml-80 min-h-screen relative z-10">
        {/* Hero Section */}
        <Hero activeTab={activeTab} />

        {/* Content Area */}
        <div className={activeTab === 'advisor' ? '' : 'px-8 pb-12'}>
          {activeTab === 'dashboard' && (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              {/* Left Column - Portfolio & Market */}
              <div className="xl:col-span-2 space-y-6">
                <PortfolioOverview />
                <MarketOverview />

                {/* New Robo-Advisor Features */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <GoalPlanSnapshot />
                  <PortfolioDriftAlert />
                </div>
                <MarketSentimentWidget />
              </div>

              {/* Right Column - AI Advisor Chat */}
              <div className="xl:col-span-1">
                <div className="sticky top-6 h-[calc(100vh-8rem)] rounded-[20px] glass-card-strong overflow-hidden">
                  <DashboardChatInterface
                    history={history}
                    onSubmit={handleSubmit}
                    loading={loading}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'portfolio' && (
            <div className="space-y-6">
              <EnhancedPortfolioPage />
            </div>
          )}

          {activeTab === 'investments' && (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2">
                <InvestmentRecommendations />
              </div>
              <div className="xl:col-span-1">
                <div className="sticky top-6 h-[calc(100vh-8rem)] rounded-[20px] glass-card-strong overflow-hidden">
                  <DashboardChatInterface
                    history={history}
                    onSubmit={handleSubmit}
                    loading={loading}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'holdings' && (
            <div className="space-y-6">
              <HoldingsManager />
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="p-8 rounded-[20px] glass-card-strong text-center">
                <h2 className="text-2xl tracking-wider text-white mb-4" style={{ textTransform: 'uppercase' }}>
                  ANALYTICS DASHBOARD
                </h2>
                <p className="text-white text-opacity-70">Comprehensive analytics and performance metrics coming soon.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <PortfolioOverview />
                <MarketOverview />
              </div>
            </div>
          )}


          {activeTab === 'advisor' && (
            <div className="h-[calc(100vh-200px)] px-8 pb-8">
              <div className="h-full rounded-[20px] glass-card-strong overflow-hidden">
                <DashboardChatInterface
                  history={history}
                  onSubmit={handleSubmit}
                  loading={loading}
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
