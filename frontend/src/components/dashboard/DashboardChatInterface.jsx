import React, { useState, useMemo } from 'react';
import { Bot, Send, User, Shield, AlertTriangle, CheckCircle, Copy, Check } from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

export const DashboardChatInterface = ({ history, onSubmit, loading }) => {
  const [question, setQuestion] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Configure marked to open links in new tab
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    });
  };

  // Helper function to get FHRI badge color
  const getFHRIBadgeColor = (fhri) => {
    if (!fhri) return 'bg-gray-500';
    if (fhri >= 0.7) return 'gradient-success';
    if (fhri >= 0.4) return 'gradient-warning';
    return 'gradient-danger';
  };

  // Helper function to get FHRI label
  const getFHRILabel = (fhri) => {
    if (!fhri) return 'N/A';
    if (fhri >= 0.7) return 'HIGH RELIABILITY';
    if (fhri >= 0.4) return 'MODERATE';
    return 'LOW RELIABILITY';
  };

  // Simple welcome message for first-time users
  const exampleMessages = history.length === 0 ? [
    {
      role: 'assistant',
      text: "Hello! I'm your AI financial advisor. How can I help you today?",
      time: new Date().toLocaleTimeString(),
    },
  ] : [];

  const allMessages = history.length > 0 ? history : exampleMessages;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !loading) {
      onSubmit(question.trim());
      setQuestion('');
    }
  };

  const quickActions = [
    'Portfolio Review',
    'Market Analysis',
    'Risk Assessment',
  ];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Messages Area - with max-width container */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="max-w-[960px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-4">
          {allMessages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] w-full p-4 overflow-x-hidden ${
                  msg.role === 'user'
                    ? 'gradient-blue-button text-white rounded-[20px_20px_5px_20px]'
                    : 'glass-card text-white rounded-[20px_20px_20px_5px]'
                }`}
                style={{
                  wordWrap: 'break-word',
                  overflowWrap: 'anywhere',
                  wordBreak: 'break-word',
                }}
              >
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  {msg.role === 'assistant' ? (
                    <Bot className="w-4 h-4 text-blue-400" />
                  ) : (
                    <User className="w-4 h-4" />
                  )}
                  <span className="text-xs font-semibold opacity-80">
                    {msg.role === 'assistant' ? 'AI Advisor' : 'You'}
                  </span>
                </div>
                {msg.role === 'assistant' && (
                  <button
                    onClick={() => handleCopy(msg.text, idx)}
                    className="p-1.5 rounded hover:bg-white hover:bg-opacity-10 transition-all"
                    title="Copy message"
                  >
                    {copiedIndex === idx ? (
                      <Check className="w-3.5 h-3.5 text-green-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 opacity-60" />
                    )}
                  </button>
                )}
              </div>

              {msg.role === 'assistant' ? (
                <div
                  className="text-sm leading-relaxed message-text prose prose-invert max-w-none"
                  style={{
                    lineHeight: '1.6',
                    fontSize: '14px',
                    overflowX: 'hidden',
                    whiteSpace: 'pre-wrap',
                  }}
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(
                      marked.parse(msg.text).replace(/<a /g, '<a target="_blank" rel="noopener noreferrer" '),
                      { ADD_ATTR: ['target', 'rel'] }
                    ),
                  }}
                />
              ) : (
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{msg.text}</p>
              )}

              {/* FHRI Score & Metadata Badges */}
              {msg.role === 'assistant' && msg.meta && (
                <div className="mt-3 pt-3 border-t border-white border-opacity-10">
                  <div className="flex flex-wrap gap-2">
                    {/* FHRI Score Badge */}
                    {msg.meta.fhri !== undefined && msg.meta.fhri !== null && (
                      <div className={`px-3 py-1.5 rounded-full text-xs font-bold text-white flex items-center gap-1.5 ${getFHRIBadgeColor(msg.meta.fhri)}`}>
                        <Shield className="w-3.5 h-3.5" />
                        FHRI: {(msg.meta.fhri * 100).toFixed(1)}%
                        <span className="text-[10px] opacity-80 ml-1">({getFHRILabel(msg.meta.fhri)})</span>
                      </div>
                    )}

                    {/* Hallucination Badge */}
                    {msg.meta.is_hallucination !== undefined && (
                      <div className={`px-3 py-1.5 rounded-full text-xs font-bold text-white flex items-center gap-1.5 ${msg.meta.is_hallucination ? 'gradient-danger' : 'gradient-success'}`}>
                        {msg.meta.is_hallucination ? (
                          <>
                            <AlertTriangle className="w-3.5 h-3.5" />
                            HALLUCINATION
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-3.5 h-3.5" />
                            VERIFIED
                          </>
                        )}
                      </div>
                    )}


                    {/* Contradiction Score Badge */}
                    {msg.meta.contradiction_score !== undefined && msg.meta.contradiction_score !== null && (
                      <div className="px-3 py-1.5 rounded-full text-xs font-semibold bg-white bg-opacity-10 text-white border border-white border-opacity-20">
                        Contradiction: {(msg.meta.contradiction_score * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                </div>
              )}

              {msg.time && (
                <div className="text-xs opacity-50 mt-2">{msg.time}</div>
              )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex-shrink-0 border-t border-white border-opacity-10 bg-[#0A0A0A]/80 backdrop-blur">
        <div className="max-w-[960px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-wrap gap-2">
            {quickActions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(action);
                }}
                className="px-4 py-2 rounded-full text-xs font-semibold bg-white bg-opacity-10 text-white hover:bg-opacity-20 transition-all duration-300"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="flex-shrink-0 sticky bottom-0 border-t border-white border-opacity-10 bg-[#0A0A0A]/80 backdrop-blur">
        <div className="max-w-[960px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask me anything about your portfolio..."
              disabled={loading}
              className="flex-1 px-4 py-3 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:bg-opacity-10 transition-all duration-300"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="w-12 h-12 rounded-xl gradient-blue-button flex items-center justify-center transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-5 h-5 text-white" />
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
