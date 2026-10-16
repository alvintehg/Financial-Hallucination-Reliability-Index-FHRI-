import React from 'react';

const Sidebar = ({
  retrievalMode,
  setRetrievalMode,
  k,
  setK,
  useEntropy,
  setUseEntropy,
  useNli,
  setUseNli,
  useFhri,
  setUseFhri,
  scenarioMode,
  setScenarioMode,
  scenarioOverride,
  setScenarioOverride,
  showRaw,
  setShowRaw,
  onClearHistory,
  // New robo-advisor settings
  enableRiskProfiling = true,
  setEnableRiskProfiling,
  enableGoalPlanning = true,
  setEnableGoalPlanning,
  enableBacktest = true,
  setEnableBacktest,
  enableBehavioralNudges = true,
  setEnableBehavioralNudges,
  advisorContactEmail = 'advisor@example.com',
  setAdvisorContactEmail,
}) => {
  const scenarioOptions = {
    'Default': 'default',
    'Numeric KPI / Ratios': 'numeric_kpi',
    'Directional Recap': 'directional',
    'Intraday / Real-time': 'intraday',
    'Fundamentals / Long Horizon': 'fundamentals',
    'Regulatory / Policy': 'regulatory',
    'Portfolio Advice / Suitability': 'advice',
    'Multi-Ticker Comparison': 'multi_ticker',
    'News Summarization': 'news',
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🚀 Control Panel</h2>
        <p>Fine-tune your AI assistant</p>
      </div>

      <div className="sidebar-section">
        <h4>📚 Retrieval Configuration</h4>
        <div className="form-group">
          <label>Retrieval Mode</label>
          <select
            value={retrievalMode}
            onChange={(e) => setRetrievalMode(e.target.value)}
          >
            <option value="tfidf">TF-IDF</option>
            <option value="faiss">FAISS</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>

        <div className="form-group">
          <label>📊 Retrieved Documents</label>
          <input
            type="range"
            min="1"
            max="15"
            value={k}
            onChange={(e) => setK(parseInt(e.target.value))}
          />
          <div className="slider-value">{k} documents</div>
        </div>
      </div>

      <div className="sidebar-section">
        <h4>🔬 Detection & Scoring</h4>
        <div
          className="checkbox-group"
          onClick={() => setUseEntropy(!useEntropy)}
        >
          <input type="checkbox" checked={useEntropy} readOnly />
          <label>🎯 Use Entropy Detection</label>
        </div>

        <div className="checkbox-group" onClick={() => setUseNli(!useNli)}>
          <input type="checkbox" checked={useNli} readOnly />
          <label>🔗 Use NLI Contradiction</label>
        </div>

        <div className="checkbox-group" onClick={() => setUseFhri(!useFhri)}>
          <input type="checkbox" checked={useFhri} readOnly />
          <label>✨ Use FHRI Scoring</label>
        </div>
      </div>

      <div className="sidebar-section">
        <h4>🎯 Scenario Detection</h4>
        <div className="radio-group">
          <div
            className={`radio-option ${scenarioMode === 'auto' ? 'active' : ''}`}
            onClick={() => {
              setScenarioMode('auto');
              setScenarioOverride(null);
            }}
          >
            Auto Detect
          </div>
          <div
            className={`radio-option ${scenarioMode === 'manual' ? 'active' : ''}`}
            onClick={() => setScenarioMode('manual')}
          >
            Manual
          </div>
        </div>

        {scenarioMode === 'manual' && (
          <div className="form-group">
            <label>Select Scenario</label>
            <select
              value={scenarioOverride || 'default'}
              onChange={(e) => setScenarioOverride(e.target.value)}
            >
              {Object.entries(scenarioOptions).map(([label, value]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="divider" />

      <div className="sidebar-section">
        <h4>🤖 Robo-Advisor Features</h4>
        {setEnableRiskProfiling && (
          <div
            className="checkbox-group"
            onClick={() => setEnableRiskProfiling(!enableRiskProfiling)}
          >
            <input type="checkbox" checked={enableRiskProfiling} readOnly />
            <label>📊 Enable Risk Profiling</label>
          </div>
        )}

        {setEnableGoalPlanning && (
          <div
            className="checkbox-group"
            onClick={() => setEnableGoalPlanning(!enableGoalPlanning)}
          >
            <input type="checkbox" checked={enableGoalPlanning} readOnly />
            <label>🎯 Enable Goal Planning</label>
          </div>
        )}

        {setEnableBacktest && (
          <div
            className="checkbox-group"
            onClick={() => setEnableBacktest(!enableBacktest)}
          >
            <input type="checkbox" checked={enableBacktest} readOnly />
            <label>📈 Enable Backtest</label>
          </div>
        )}

        {setEnableBehavioralNudges && (
          <div
            className="checkbox-group"
            onClick={() => setEnableBehavioralNudges(!enableBehavioralNudges)}
          >
            <input type="checkbox" checked={enableBehavioralNudges} readOnly />
            <label>🧠 Enable Behavioral Nudges</label>
          </div>
        )}

        {setAdvisorContactEmail && (
          <div className="form-group" style={{ marginTop: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem' }}>📧 Advisor Contact Email</label>
            <input
              type="email"
              value={advisorContactEmail}
              onChange={(e) => setAdvisorContactEmail(e.target.value)}
              placeholder="advisor@example.com"
              style={{
                width: '100%',
                padding: '0.5rem',
                marginTop: '0.25rem',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '0.375rem',
                color: '#fff',
                fontSize: '0.875rem',
              }}
            />
          </div>
        )}

        <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: '#9ca3af' }}>
          Note: Features are enabled by default. Disable to hide from responses.
        </div>
      </div>

      <div className="divider" />

      <div className="sidebar-section">
        <h4>⚡ Advanced Options</h4>
        <div className="checkbox-group" onClick={() => setShowRaw(!showRaw)}>
          <input type="checkbox" checked={showRaw} readOnly />
          <label>🔧 Debug Mode</label>
        </div>
      </div>

      <div className="divider" />

      <div className="sidebar-section">
        <h4>🔧 Maintenance</h4>
        <button className="btn btn-secondary" onClick={onClearHistory}>
          🗑️ Clear History
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
