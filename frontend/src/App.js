import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import MetricsPanel from './components/MetricsPanel';
import { askQuestion } from './api';

function App() {
  // Configuration state
  const [retrievalMode, setRetrievalMode] = useState('tfidf');
  const [k, setK] = useState(5);
  const [useEntropy, setUseEntropy] = useState(true);
  const [useNli, setUseNli] = useState(true);
  const [useFhri, setUseFhri] = useState(true);
  const [scenarioMode, setScenarioMode] = useState('auto');
  const [scenarioOverride, setScenarioOverride] = useState(null);
  const [showRaw, setShowRaw] = useState(false);

  // Chat state
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionMetrics, setSessionMetrics] = useState({
    queries: 0,
    avg_confidence: 0,
    avg_fhri: 0,
    total_time: 0,
  });

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

    // Call backend API
    const payload = {
      text: question,
      provider: 'deepseek',
      k,
      retrieval_mode: retrievalMode,
      use_entropy: useEntropy,
      use_nli: useNli,
      use_fhri: useFhri,
    };

    if (prevAnswer) {
      payload.prev_assistant_turn = prevAnswer;
    }

    if (scenarioOverride) {
      payload.scenario_override = scenarioOverride;
    }

    try {
      const backendRes = await askQuestion(payload);

      // Extract metadata
      const backendMeta = backendRes.meta || {};
      const meta = {
        entropy: backendRes.entropy,
        is_hallucination: backendRes.is_hallucination,
        contradiction_score: backendRes.contradiction_score,
        passages_used: backendRes.passages_used,
        latency: backendRes._latency || backendMeta.latency_s,
        raw_error: backendRes._error,
        provider: backendMeta.provider,
        model: backendMeta.model,
        retrieval_mode: backendMeta.retrieval_mode,
        fhri: backendMeta.fhri,
        fhri_subscores: backendMeta.fhri_subscores || {},
        fhri_components: backendMeta.fhri_components || [],
        fhri_renormalized: backendMeta.fhri_renormalized || false,
        scenario_name: backendMeta.scenario_name,
        scenario_weights: backendMeta.scenario_weights || {},
        data_sources_used: backendMeta.data_sources_used || [],
        passages: backendRes.passages || [],
      };

      // Update session metrics
      const newQueries = sessionMetrics.queries + 1;
      let newAvgConfidence = sessionMetrics.avg_confidence;
      let newAvgFhri = sessionMetrics.avg_fhri;
      let newTotalTime = sessionMetrics.total_time;

      if (meta.entropy !== null && meta.entropy !== undefined) {
        const confidence = Math.max(0, 1 - meta.entropy);
        newAvgConfidence =
          (sessionMetrics.avg_confidence * sessionMetrics.queries + confidence) / newQueries;
      }

      if (meta.fhri !== null && meta.fhri !== undefined) {
        newAvgFhri =
          (sessionMetrics.avg_fhri * sessionMetrics.queries + meta.fhri) / newQueries;
      }

      if (meta.latency) {
        newTotalTime += meta.latency;
      }

      setSessionMetrics({
        queries: newQueries,
        avg_confidence: newAvgConfidence,
        avg_fhri: newAvgFhri,
        total_time: newTotalTime,
      });

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        text: backendRes.answer,
        time: timestamp,
        meta,
      };
      setHistory((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error submitting question:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    setSessionMetrics({
      queries: 0,
      avg_confidence: 0,
      avg_fhri: 0,
      total_time: 0,
    });
  };

  return (
    <div className="App">
      <Sidebar
        retrievalMode={retrievalMode}
        setRetrievalMode={setRetrievalMode}
        k={k}
        setK={setK}
        useEntropy={useEntropy}
        setUseEntropy={setUseEntropy}
        useNli={useNli}
        setUseNli={setUseNli}
        useFhri={useFhri}
        setUseFhri={setUseFhri}
        scenarioMode={scenarioMode}
        setScenarioMode={setScenarioMode}
        scenarioOverride={scenarioOverride}
        setScenarioOverride={setScenarioOverride}
        showRaw={showRaw}
        setShowRaw={setShowRaw}
        onClearHistory={handleClearHistory}
      />

      <div className="main-content">
        <div className="hero-header">
          <div>
            <h1 className="hero-title">Robo-Advisor</h1>
            <p className="hero-subtitle">
              Intelligent Financial Assistant with FHRI Reliability Scoring
            </p>
          </div>
        </div>

        <div className="content-wrapper">
          <ChatInterface
            history={history}
            onSubmit={handleSubmit}
            loading={loading}
          />

          <MetricsPanel
            sessionMetrics={sessionMetrics}
            history={history}
            onExportChat={() => {}}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
