import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const MetricsPanel = ({ sessionMetrics, history, onExportChat }) => {
  const [moomooHoldings, setMoomooHoldings] = useState(null);
  const [showHoldings, setShowHoldings] = useState(false);
  const [holdingsError, setHoldingsError] = useState(null);
  // Get FHRI scores for chart
  const assistantMessages = history.filter((h) => h.role === 'assistant' && h.meta);
  const fhriScores = assistantMessages
    .slice(-10)
    .map((h, idx) => ({
      index: idx + 1,
      fhri: h.meta.fhri || 0,
    }));

  // Fetch Moomoo holdings on demand
  const fetchMoomooHoldings = async () => {
    try {
      setHoldingsError(null);
      const response = await axios.get('http://127.0.0.1:8000/moomoo/positions', {
        timeout: 10000,
      });
      if (response.data.status === 'success') {
        setMoomooHoldings(response.data.positions);
      } else {
        setHoldingsError(response.data.message || 'Failed to fetch holdings');
      }
    } catch (error) {
      console.error('Moomoo holdings error:', error);
      setHoldingsError('Moomoo integration not available');
    }
  };

  useEffect(() => {
    if (showHoldings && !moomooHoldings && !holdingsError) {
      fetchMoomooHoldings();
    }
  }, [showHoldings, moomooHoldings, holdingsError]);

  const handleExport = () => {
    if (history.length === 0) return;

    const rows = history.map((h) => {
      const meta = h.meta || {};
      return {
        timestamp: h.time,
        role: h.role,
        message: h.text,
        confidence: meta.entropy !== null && meta.entropy !== undefined
          ? Math.max(0, 1 - meta.entropy)
          : null,
        fhri: meta.fhri || null,
        is_verified: meta.is_hallucination !== null && meta.is_hallucination !== undefined
          ? !meta.is_hallucination
          : null,
      };
    });

    const csvContent = [
      'timestamp,role,message,confidence,fhri,is_verified',
      ...rows.map((r) =>
        `"${r.timestamp}","${r.role}","${r.message.replace(/"/g, '""')}",${r.confidence},${r.fhri},${r.is_verified}`
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `roboadvisor_chat_${new Date().toISOString().replace(/:/g, '-')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="metrics-panel">
      <h3 className="metrics-title">📊 Live Analytics</h3>

      <div className="metrics-card">
        <h4>📈 Session Overview</h4>
        <div className="metrics-grid">
          <div className="metric-item">
            <div className="metric-value">{sessionMetrics.queries}</div>
            <div className="metric-label">Questions Asked</div>
          </div>
          <div className="metric-item">
            <div className="metric-value">
              {(sessionMetrics.avg_confidence * 100).toFixed(0)}%
            </div>
            <div className="metric-label">Avg Confidence</div>
          </div>
          <div className="metric-item">
            <div className="metric-value">
              {sessionMetrics.avg_fhri.toFixed(2)}
            </div>
            <div className="metric-label">Avg FHRI</div>
          </div>
          <div className="metric-item">
            <div className="metric-value">
              {sessionMetrics.total_time.toFixed(1)}s
            </div>
            <div className="metric-label">Total Time</div>
          </div>
        </div>
      </div>

      {/* FHRI Trend Chart */}
      {fhriScores.length > 1 && (
        <div className="metrics-card">
          <h4>FHRI Trend</h4>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fhriScores}>
                <XAxis dataKey="index" stroke="rgba(255,255,255,0.5)" />
                <YAxis domain={[0, 1]} stroke="rgba(255,255,255,0.5)" />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(0,0,0,0.9)',
                    border: '1px solid #40B4E5',
                    borderRadius: '8px',
                    color: 'white',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="fhri"
                  stroke="#40B4E5"
                  strokeWidth={3}
                  dot={{ fill: '#40B4E5', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="divider" />

      {/* Moomoo Holdings Section */}
      <div className="metrics-card">
        <h4
          onClick={() => setShowHoldings(!showHoldings)}
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <span>💼 My Holdings (Moomoo)</span>
          <span style={{ fontSize: '0.875rem' }}>{showHoldings ? '▼' : '▶'}</span>
        </h4>
        {showHoldings && (
          <div style={{ marginTop: '0.5rem' }}>
            {holdingsError ? (
              <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>{holdingsError}</div>
            ) : moomooHoldings === null ? (
              <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>Loading...</div>
            ) : moomooHoldings.length === 0 ? (
              <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>No holdings found</div>
            ) : (
              <div style={{ fontSize: '0.875rem' }}>
                {moomooHoldings.map((holding, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '0.25rem 0',
                      borderBottom: idx < moomooHoldings.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                    }}
                  >
                    <span><strong>{holding.symbol}</strong> ({holding.qty} shares)</span>
                    <span style={{ color: holding.pl >= 0 ? '#10B981' : '#EF4444' }}>
                      ${holding.market_value?.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="divider" />

      <button className="btn" onClick={handleExport}>
        📋 Export Chat
      </button>

      <div className="pro-tips">
        <h4>💡 Pro Tips</h4>
        <ul>
          <li>
            <strong>FHRI Score:</strong> Composite reliability (&gt;0.75 = high, 0.50-0.75 = medium, &lt;0.50 = low)
          </li>
          <li>
            <strong>Grounding (G):</strong> How well answer aligns with retrieved sources
          </li>
          <li>
            <strong>Numerical/Directional (N/D):</strong> Consistency of numeric claims and directions
          </li>
          <li>
            <strong>Temporal (T):</strong> Date/period alignment with question
          </li>
          <li>
            <strong>Citation (C):</strong> Presence and credibility of sources
          </li>
          <li>
            <strong>Entropy (E):</strong> Model uncertainty (lower = more confident)
          </li>
        </ul>
      </div>
    </div>
  );
};

export default MetricsPanel;
