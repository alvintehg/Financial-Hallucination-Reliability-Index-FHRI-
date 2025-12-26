import React, { useState, useMemo } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const MessageDisplay = ({ message }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [collapsed, setCollapsed] = useState(window.innerWidth < 1024);
  const [copied, setCopied] = useState(false);
  const [showRiskAllocation, setShowRiskAllocation] = useState(false);
  const [showGoalPlan, setShowGoalPlan] = useState(false);
  const [showBacktest, setShowBacktest] = useState(false);
  const [showThematic, setShowThematic] = useState(false);
  const [showBehavioral, setShowBehavioral] = useState(false);

  // Configure marked to open links in new tab
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  // Parse markdown to HTML with sanitization
  const messageHtml = useMemo(() => {
    if (message.role === 'assistant' && message.text) {
      const rawHtml = marked.parse(message.text);
      const cleanHtml = DOMPurify.sanitize(rawHtml, {
        ADD_ATTR: ['target', 'rel'],
      });
      // Add target="_blank" and rel="noopener noreferrer" to all links
      return cleanHtml.replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" ');
    }
    return null;
  }, [message.text, message.role]);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (message.role === 'user') {
    return (
      <div className="message message-user max-w-[860px] w-full mx-auto">
        <div className="message-content overflow-x-hidden">
          <div className="message-header">
            <div className="message-author">👤 You</div>
            <div className="message-time">{message.time}</div>
          </div>
          <div className="whitespace-pre-wrap break-words overflow-wrap-anywhere">{message.text}</div>
        </div>
      </div>
    );
  }

  const meta = message.meta || {};
  const fhri = meta.fhri;
  const scenarioName = meta.scenario_name || 'Default';
  const subscores = meta.fhri_subscores || {};
  const scenarioWeights = meta.scenario_weights || {};
  const dataSources = meta.data_sources_used || [];
  const passages = meta.passages || [];

  // Extract robo-advisor data from meta (if present)
  const riskProfile = meta.risk_profile || null;
  const allocation = meta.allocation || null;
  const goalPlan = meta.goal_plan || null;
  const feeImpact = meta.fee_impact || null;
  const backtest = meta.backtest || null;
  const thematicIdeas = meta.thematic_ideas || null;
  const behavioralNudges = meta.behavioral_nudges || null;
  const escalation = meta.escalation || null;

  // Determine FHRI pill class
  let fhriClass = 'fhri-pill';
  let fhriIcon = '✅';
  if (fhri !== null && fhri !== undefined) {
    if (fhri > 0.75) {
      fhriClass = 'fhri-pill';
      fhriIcon = '✅';
    } else if (fhri > 0.50) {
      fhriClass = 'fhri-pill medium';
      fhriIcon = '⚠️';
    } else {
      fhriClass = 'fhri-pill low';
      fhriIcon = '❌';
    }
  }

  // Calculate metrics
  const confidence = meta.entropy !== null && meta.entropy !== undefined
    ? Math.max(0, 1 - meta.entropy)
    : 0;
  const consistency = meta.contradiction_score !== null && meta.contradiction_score !== undefined
    ? Math.max(0, 1 - meta.contradiction_score)
    : 1;
  const latency = meta.latency || 0;

  const scoreLabels = {
    G: 'Grounding',
    N_or_D: 'Numerical/Dir',
    T: 'Temporal',
    C: 'Citation',
    E: 'Entropy',
  };

  return (
    <div className="message message-assistant max-w-[860px] w-full mx-auto">
      <div className="message-content overflow-x-hidden">
        <div className="message-header">
          <div>
            <div className="message-author">🤖 AI Assistant</div>
            <div className="message-time">{message.time}</div>
          </div>
          <div className="message-badges">
            <button
              onClick={handleCopy}
              className="copy-button"
              title="Copy message"
              style={{
                padding: '0.25rem 0.5rem',
                fontSize: '0.875rem',
                background: copied ? '#10B981' : 'rgba(64, 180, 229, 0.2)',
                border: '1px solid rgba(64, 180, 229, 0.3)',
                borderRadius: '0.375rem',
                color: '#fff',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {copied ? '✓ Copied' : '📋 Copy'}
            </button>
            {fhri !== null && fhri !== undefined && (
              <>
                <span className={`badge ${fhriClass}`}>
                  {fhriIcon} FHRI: {fhri.toFixed(2)}
                </span>
                <span className="badge badge-chip" title="Detected Scenario">
                  🎯 {scenarioName}
                </span>
              </>
            )}
            {meta.is_hallucination === true && (
              <span className="badge badge-warning">⚠️ Needs Verification</span>
            )}
            {meta.is_hallucination === false && (
              <span className="badge badge-safe">✅ Fact-Checked</span>
            )}
          </div>
        </div>

        <div
          className="message-text prose prose-invert max-w-none overflow-x-hidden whitespace-pre-wrap break-words"
          style={{
            lineHeight: '1.6',
            fontSize: '16px',
          }}
          dangerouslySetInnerHTML={{ __html: messageHtml }}
        />

        {/* Collapsible section for mobile */}
        <div className="lg:hidden" style={{ marginTop: '1rem' }}>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="details-toggle"
            style={{
              width: '100%',
              padding: '0.5rem',
              background: 'rgba(64, 180, 229, 0.1)',
              border: '1px solid rgba(64, 180, 229, 0.3)',
              borderRadius: '0.375rem',
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            {collapsed ? '▼ Show Details' : '▲ Hide Details'}
          </button>
        </div>

        {/* FHRI Sub-scores */}
        {Object.keys(subscores).length > 0 && (
          <div className={`message-subscores ${collapsed && window.innerWidth < 1024 ? 'hidden lg:block' : ''}`}>
            <div className="subscores-title">FHRI Components:</div>
            <div className="subscores-chips">
              {Object.entries(scoreLabels).map(([key, label]) => {
                const score = subscores[key];
                const weight = scenarioWeights[key] || 0.0;
                if (score !== null && score !== undefined) {
                  return (
                    <span
                      key={key}
                      className="subscore-chip"
                      title={`${label} (weight: ${weight.toFixed(2)})`}
                    >
                      {label}: {score.toFixed(2)} (w:{weight.toFixed(2)})
                    </span>
                  );
                }
                return (
                  <span key={key} className="subscore-chip" title={label}>
                    {label}: N/A
                  </span>
                );
              })}
            </div>
            {meta.fhri_renormalized && (
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
                ⚠️ FHRI renormalized (some components unavailable)
              </div>
            )}
          </div>
        )}

        {/* Verified Data Sources */}
        {dataSources.length > 0 && (
          <div className={`data-sources ${collapsed && window.innerWidth < 1024 ? 'hidden lg:block' : ''}`}>
            <div className="subscores-title">✅ Verified with:</div>
            <div className="sources-chips">
              {dataSources.map((source, idx) => (
                <span key={idx} className="source-chip">
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Metrics Cards */}
        <div className={`message-metrics ${collapsed && window.innerWidth < 1024 ? 'hidden lg:block' : ''}`}>
          <div className="metric-card-small">
            <div className="metric-value">{(confidence * 100).toFixed(0)}%</div>
            <div className="metric-label">Confidence</div>
          </div>
          <div className="metric-card-small">
            <div className="metric-value">{(consistency * 100).toFixed(0)}%</div>
            <div className="metric-label">Consistency</div>
          </div>
          <div className="metric-card-small">
            <div className="metric-value">{meta.passages_used || 0}</div>
            <div className="metric-label">Sources</div>
          </div>
          <div className="metric-card-small">
            <div className="metric-value">{latency.toFixed(1)}s</div>
            <div className="metric-label">Response</div>
          </div>
        </div>

        {/* Risk Profile & Allocation */}
        {(riskProfile || allocation) && (
          <div className="message-details" style={{ marginTop: '1rem' }}>
            <button
              className="details-toggle"
              onClick={() => setShowRiskAllocation(!showRiskAllocation)}
            >
              📊 {showRiskAllocation ? 'Hide' : 'View'} Risk Profile & Allocation
            </button>
            {showRiskAllocation && (
              <div className="details-content">
                {riskProfile && (
                  <>
                    <div><strong>Risk Profile:</strong> {riskProfile.risk_label} (Score: {riskProfile.score})</div>
                  </>
                )}
                {allocation && (
                  <>
                    <div style={{ marginTop: '0.5rem' }}><strong>Recommended ETF Mix:</strong></div>
                    <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                      {allocation.allocation && allocation.allocation.map((etf, idx) => (
                        <li key={idx} style={{ marginBottom: '0.25rem' }}>
                          {etf.ticker} ({(etf.weight * 100).toFixed(0)}%) - {etf.role}
                        </li>
                      ))}
                    </ul>
                    {allocation.notes && <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#9ca3af' }}>{allocation.notes}</div>}
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* Goal Plan Summary */}
        {goalPlan && (
          <div className="message-details" style={{ marginTop: '1rem' }}>
            <button
              className="details-toggle"
              onClick={() => setShowGoalPlan(!showGoalPlan)}
            >
              🎯 {showGoalPlan ? 'Hide' : 'View'} Goal Plan Summary
            </button>
            {showGoalPlan && (
              <div className="details-content">
                <div>Target: ${goalPlan.target_amount?.toLocaleString()}</div>
                <div>Time Horizon: {goalPlan.years} years</div>
                {goalPlan.required_monthly && (
                  <div>Required Monthly: ${goalPlan.required_monthly.toFixed(2)}</div>
                )}
                <div>Projected Final Value: ${goalPlan.final_value?.toLocaleString()}</div>
                <div>Will Reach Goal: {goalPlan.will_reach_goal ? '✅ Yes' : '❌ No'}</div>
              </div>
            )}
          </div>
        )}

        {/* Fee & Tax Impact */}
        {feeImpact && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', padding: '0.5rem', background: 'rgba(255, 193, 7, 0.1)', borderRadius: '0.375rem' }}>
            <strong>💰 Fee Impact:</strong> Fees reduce final value by ${feeImpact.delta?.toLocaleString()} ({feeImpact.delta_pct?.toFixed(1)}%) over {feeImpact.horizon_years} years
          </div>
        )}

        {/* Backtest Results */}
        {backtest && (
          <div className="message-details" style={{ marginTop: '1rem' }}>
            <button
              className="details-toggle"
              onClick={() => setShowBacktest(!showBacktest)}
            >
              📈 {showBacktest ? 'Hide' : 'View'} Backtest Results
            </button>
            {showBacktest && (
              <div className="details-content">
                <div className="metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#40B4E5' }}>{backtest.cagr?.toFixed(2)}%</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>CAGR</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#40B4E5' }}>{backtest.volatility?.toFixed(2)}%</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Volatility</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#40B4E5' }}>{backtest.max_drawdown?.toFixed(2)}%</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Max Drawdown</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#40B4E5' }}>{backtest.sharpe_ratio?.toFixed(2)}</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Sharpe Ratio</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Thematic Ideas */}
        {thematicIdeas && thematicIdeas.etfs && thematicIdeas.etfs.length > 0 && (
          <div className="message-details" style={{ marginTop: '1rem' }}>
            <button
              className="details-toggle"
              onClick={() => setShowThematic(!showThematic)}
            >
              🌱 {showThematic ? 'Hide' : 'View'} Thematic Ideas
            </button>
            {showThematic && (
              <div className="details-content">
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                  {thematicIdeas.etfs.map((etf, idx) => (
                    <li key={idx} style={{ marginBottom: '0.5rem' }}>
                      <strong>{etf.ticker}</strong> - {etf.name}: {etf.why}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Behavioral Insights */}
        {behavioralNudges && behavioralNudges.nudges && behavioralNudges.nudges.length > 0 && (
          <div className="message-details" style={{ marginTop: '1rem' }}>
            <button
              className="details-toggle"
              onClick={() => setShowBehavioral(!showBehavioral)}
            >
              🧠 {showBehavioral ? 'Hide' : 'View'} Behavioral Insights
            </button>
            {showBehavioral && (
              <div className="details-content">
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                  {behavioralNudges.nudges.map((nudge, idx) => (
                    <li key={idx} style={{ marginBottom: '0.5rem' }}>
                      {nudge}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Escalate to Planner */}
        {escalation && (
          <div style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
            <a
              href={escalation.contact_link}
              style={{ color: '#40B4E5', textDecoration: 'none', borderBottom: '1px solid rgba(64, 180, 229, 0.5)' }}
              target="_blank"
              rel="noopener noreferrer"
            >
              📧 Escalate to Human Planner
            </a>
          </div>
        )}

        {/* Multi-Source Verification Note */}
        {dataSources.length > 0 && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#6b7280' }}>
            Verified with: {dataSources.join(', ')}
          </div>
        )}

        {/* Details Toggle */}
        <div className="message-details">
          <button
            className="details-toggle"
            onClick={() => setShowDetails(!showDetails)}
          >
            🔍 {showDetails ? 'Hide' : 'View'} Detailed Metrics & Citations
          </button>
          {showDetails && (
            <div className="details-content">
              <div><strong>Raw Scores:</strong></div>
              <div>Hallucination: {String(meta.is_hallucination)}</div>
              <div>Contradiction: {meta.contradiction_score !== null && meta.contradiction_score !== undefined ? meta.contradiction_score.toFixed(3) : 'N/A'}</div>
              <div>Provider: {meta.provider || 'N/A'}</div>
              <div>Model: {meta.model || 'N/A'}</div>
              <div>FHRI Score: {fhri !== null && fhri !== undefined ? fhri.toFixed(3) : 'N/A'}</div>
              {meta.scenario_detected !== undefined && (
                <div>Scenario: {scenarioName} (Auto-detected: {String(meta.scenario_detected)})</div>
              )}
              <div style={{ marginTop: '1rem' }}><strong>Citations ({passages.length} sources):</strong></div>
              {passages.length > 0 ? (
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                  {passages.slice(0, 5).map((passage, idx) => (
                    <li key={idx} style={{ marginBottom: '0.5rem' }}>
                      {passage.substring(0, 200)}{passage.length > 200 ? '...' : ''}
                    </li>
                  ))}
                </ul>
              ) : (
                <div>No sources retrieved.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageDisplay;
