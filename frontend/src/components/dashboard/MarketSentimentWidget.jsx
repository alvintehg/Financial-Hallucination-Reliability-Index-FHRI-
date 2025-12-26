import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Market Sentiment Widget - Shows market outlook with FHRI reliability
 * Displays Bullish/Neutral/Bearish with confidence score
 */
export const MarketSentimentWidget = () => {
  const [sentiment, setSentiment] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSentiment();
    // Refresh every 5 minutes
    const interval = setInterval(fetchSentiment, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchSentiment = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/sentiment/market`);
      setSentiment(response.data);
    } catch (error) {
      console.error('Error fetching sentiment:', error);
      // Mock fallback
      setSentiment({
        outlook: 'Neutral',
        confidence: 72.5,
        summary: 'Mixed signals in the market with balanced risk/reward outlook.',
        fhri_reliability: 'Moderate'
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !sentiment) {
    return (
      <div className="p-4 rounded-xl bg-white bg-opacity-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white bg-opacity-10 animate-pulse"></div>
          <div className="flex-1">
            <div className="h-4 bg-white bg-opacity-10 rounded mb-2 animate-pulse"></div>
            <div className="h-2 bg-white bg-opacity-10 rounded animate-pulse"></div>
          </div>
        </div>
      </div>
    );
  }

  const outlookConfig = {
    'Bullish': {
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500 bg-opacity-10',
      borderColor: 'border-green-500 border-opacity-30'
    },
    'Bearish': {
      icon: TrendingDown,
      color: 'text-red-400',
      bgColor: 'bg-red-500 bg-opacity-10',
      borderColor: 'border-red-500 border-opacity-30'
    },
    'Neutral': {
      icon: Minus,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500 bg-opacity-10',
      borderColor: 'border-blue-500 border-opacity-30'
    }
  };

  const config = outlookConfig[sentiment.outlook] || outlookConfig['Neutral'];
  const Icon = config.icon;

  const fhriColorClass = {
    'High': 'text-green-400',
    'Moderate': 'text-yellow-400',
    'Low': 'text-red-400'
  }[sentiment.fhri_reliability] || 'text-gray-400';

  return (
    <div className={`p-4 rounded-xl border ${config.bgColor} ${config.borderColor}`}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl gradient-blue-button flex items-center justify-center flex-shrink-0">
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-white text-sm">Market Sentiment</h4>
            <span className={`text-xs px-2 py-0.5 rounded-full ${config.bgColor} ${config.color} border ${config.borderColor} font-semibold`}>
              {sentiment.outlook}
            </span>
          </div>

          <p className="text-xs text-white text-opacity-70 mb-2 line-clamp-2">
            {sentiment.summary}
          </p>

          {/* Confidence and FHRI */}
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1">
              <span className="text-white text-opacity-60">Confidence:</span>
              <span className="font-semibold text-white">{sentiment.confidence.toFixed(1)}%</span>
            </div>
            <div className="w-px h-3 bg-white bg-opacity-20"></div>
            <div className="flex items-center gap-1">
              <Info className={`w-3 h-3 ${fhriColorClass}`} />
              <span className="text-white text-opacity-60">FHRI:</span>
              <span className={`font-semibold ${fhriColorClass}`}>{sentiment.fhri_reliability}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
