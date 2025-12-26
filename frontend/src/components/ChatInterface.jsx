import React, { useState } from 'react';
import MessageDisplay from './MessageDisplay';

const ChatInterface = ({
  history,
  onSubmit,
  loading,
}) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !loading) {
      onSubmit(question.trim());
      setQuestion('');
    }
  };

  return (
    <div className="chat-container overflow-x-hidden">
      <div className="mx-auto max-w-[960px] px-4 sm:px-6 lg:px-8">
        <h3 className="chat-title">💬 Chat Interface</h3>

        <div className="messages-container overflow-y-auto overflow-x-hidden" style={{ height: 'calc(100vh - 220px)' }}>
          {history.length > 0 ? (
            <>
              <h4 className="messages-title">📜 Conversation History</h4>
              {[...history].reverse().slice(0, 10).map((msg, idx) => (
                <MessageDisplay key={idx} message={msg} />
              ))}
            </>
          ) : (
            <div className="empty-state">
              <div className="empty-state-content">
                <h3>👋 Welcome to your AI Financial Assistant!</h3>
                <p>Ask about portfolios, market analysis, or investment strategy.</p>
                <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                  Now with FHRI reliability scoring for enhanced trust!
                </p>
              </div>
            </div>
          )}
        </div>

        <form className="chat-form sticky bottom-0 bg-[#0A0A0A]/80 backdrop-blur border-t border-white/10" onSubmit={handleSubmit} style={{ padding: '1rem 0' }}>
          <textarea
            className="chat-textarea w-full overflow-x-hidden"
            placeholder="Try: 'What was our Q3 performance vs the S&P 500?'"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            style={{ resize: 'vertical', maxWidth: '100%' }}
          />
          <button
            type="submit"
            className="chat-submit"
            disabled={loading || !question.trim()}
          >
            {loading ? (
              <>
                <span className="spinner" />
                AI is thinking...
              </>
            ) : (
              <>🚀 Ask AI Assistant</>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
