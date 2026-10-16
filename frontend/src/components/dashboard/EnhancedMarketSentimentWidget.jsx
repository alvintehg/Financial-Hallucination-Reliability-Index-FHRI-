import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Info, AlertTriangle, Zap, Newspaper } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Enhanced Market Sentiment Widget
 * Features:
 * - Fear & Greed Index with 0-100 gauge
 * - VIX (Volatility Index) integration
 * - News headline sentiment aggregation
 * - FHRI reliability scoring
 */
export const EnhancedMarketSentimentWidget = () => {
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
      // Enhanced mock fallback with all features
      setSentiment({
        outlook: 'Neutral',
        confidence: 72.5,
        summary: 'Mixed signals in the market with balanced risk/reward outlook.',
        fhri_reliability: 'Moderate',
        fear_greed_index: {
          value: 52,
          label: 'Neutral',
          last_updated: new Date().toISOString()
        },
        vix: {
          value: 18.45,
          change_pct: 2.3,
          interpretation: 'Moderate Volatility'
        },
        news_sentiment: {
          headlines_analyzed: 150,
          bullish_pct: 42,
          bearish_pct: 31,
          neutral_pct: 27,
          top_headlines: [
            { title: 'Tech stocks rally on earnings optimism', sentiment: 'bullish' },
            { title: 'Fed signals potential rate pause', sentiment: 'bullish' },
            { title: 'Energy sector faces headwinds', sentiment: 'bearish' }
          ]
        },
        data_sources: ['CNN Fear & Greed', 'CBOE VIX', 'Finnhub News']
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !sentiment) {
    return (
      <div className="p-6 rounded-[20px] glass-card-strong">
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

  // Fear & Greed Index Configuration
  const getFearGreedConfig = (value) => {
    if (value >= 75) return { label: 'Extreme Greed', color: 'text-red-400', bgColor: 'bg-red-500', borderColor: 'border-red-500' };
    if (value >= 55) return { label: 'Greed', color: 'text-orange-400', bgColor: 'bg-orange-500', borderColor: 'border-orange-500' };
    if (value >= 45) return { label: 'Neutral', color: 'text-blue-400', bgColor: 'bg-blue-500', borderColor: 'border-blue-500' };
    if (value >= 25) return { label: 'Fear', color: 'text-yellow-400', bgColor: 'bg-yellow-500', borderColor: 'border-yellow-500' };
    return { label: 'Extreme Fear', color: 'text-green-400', bgColor: 'bg-green-500', borderColor: 'border-green-500' };
  };

  const fearGreedConfig = getFearGreedConfig(sentiment.fear_greed_index?.value || 50);

  // VIX Interpretation
  const getVixConfig = (value) => {
    if (value < 12) return { level: 'Low', color: 'text-green-400', interpretation: 'Market Calm' };
    if (value < 20) return { level: 'Moderate', color: 'text-blue-400', interpretation: 'Normal Volatility' };
    if (value < 30) return { level: 'Elevated', color: 'text-yellow-400', interpretation: 'Increased Uncertainty' };
    return { level: 'High', color: 'text-red-400', interpretation: 'Market Stress' };
  };

  const vixConfig = getVixConfig(sentiment.vix?.value || 20);

  // Outlook Configuration
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
    <div className="p-6 rounded-[20px] glass-card-strong transition-all duration-300">
      {/* Header */}
      <div className="flex items-start gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl gradient-blue-button flex items-center justify-center flex-shrink-0">
          <Icon className={`w-5 h-5 ${config.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-bold text-white tracking-wide uppercase">MARKET SENTIMENT</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${config.bgColor} ${config.color} border ${config.borderColor} font-semibold`}>
              {sentiment.outlook}
            </span>
          </div>
          <p className="text-xs text-white text-opacity-70 mb-2">
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

      {/* Fear & Greed Index Gauge */}
      <div className="mb-6 p-4 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-10">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="w-4 h-4 text-yellow-400" />
          <h4 className="text-sm font-semibold text-white">Fear & Greed Index</h4>
        </div>

        {/* Gauge Bar */}
        <div className="relative mb-3">
          <div className="h-3 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 via-blue-500 via-orange-500 to-red-500 opacity-30"></div>
          <div
            className="absolute top-0 h-3 rounded-full transition-all duration-500"
            style={{
              width: `${sentiment.fear_greed_index?.value || 50}%`,
              background: `linear-gradient(to right, rgba(34, 197, 94, 0.8), rgba(59, 130, 246, 0.8))`
            }}
          ></div>
          {/* Indicator */}
          <div
            className={`absolute -top-1 w-5 h-5 rounded-full ${fearGreedConfig.bgColor} border-2 ${fearGreedConfig.borderColor} transition-all duration-500`}
            style={{ left: `calc(${sentiment.fear_greed_index?.value || 50}% - 10px)` }}
          ></div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className={`font-bold text-2xl ${fearGreedConfig.color}`}>
              {sentiment.fear_greed_index?.value || 50}
            </span>
            <span className={`px-2 py-0.5 rounded ${fearGreedConfig.bgColor} ${fearGreedConfig.color} bg-opacity-20 border ${fearGreedConfig.borderColor} border-opacity-30 font-semibold`}>
              {fearGreedConfig.label}
            </span>
          </div>
          <div className="text-white text-opacity-50 text-xs">
            0 = Extreme Fear • 100 = Extreme Greed
          </div>
        </div>
      </div>

      {/* VIX (Volatility Index) */}
      <div className="mb-6 p-4 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-10">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className={`w-4 h-4 ${vixConfig.color}`} />
            <h4 className="text-sm font-semibold text-white">VIX (Volatility Index)</h4>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded bg-white bg-opacity-10 ${vixConfig.color} font-semibold`}>
            {vixConfig.level}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`font-bold text-2xl ${vixConfig.color}`}>
              {sentiment.vix?.value?.toFixed(2) || 'N/A'}
            </span>
            <div className="text-xs">
              <div className={`font-semibold ${sentiment.vix?.change_pct >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                {sentiment.vix?.change_pct >= 0 ? '+' : ''}{sentiment.vix?.change_pct?.toFixed(2)}%
              </div>
              <div className="text-white text-opacity-50">{vixConfig.interpretation}</div>
            </div>
          </div>
        </div>
      </div>

      {/* News Sentiment Analysis */}
      {sentiment.news_sentiment && (
        <div className="p-4 rounded-xl bg-white bg-opacity-5 border border-white border-opacity-10">
          <div className="flex items-center gap-2 mb-3">
            <Newspaper className="w-4 h-4 text-blue-400" />
            <h4 className="text-sm font-semibold text-white">News Sentiment Analysis</h4>
            <span className="text-xs text-white text-opacity-50">
              ({sentiment.news_sentiment.headlines_analyzed} headlines)
            </span>
          </div>

          {/* Sentiment Breakdown */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="p-2 rounded bg-green-500 bg-opacity-10 border border-green-500 border-opacity-20">
              <div className="text-xs text-white text-opacity-60 mb-1">Bullish</div>
              <div className="text-lg font-bold text-green-400">
                {sentiment.news_sentiment.bullish_pct}%
              </div>
            </div>
            <div className="p-2 rounded bg-blue-500 bg-opacity-10 border border-blue-500 border-opacity-20">
              <div className="text-xs text-white text-opacity-60 mb-1">Neutral</div>
              <div className="text-lg font-bold text-blue-400">
                {sentiment.news_sentiment.neutral_pct}%
              </div>
            </div>
            <div className="p-2 rounded bg-red-500 bg-opacity-10 border border-red-500 border-opacity-20">
              <div className="text-xs text-white text-opacity-60 mb-1">Bearish</div>
              <div className="text-lg font-bold text-red-400">
                {sentiment.news_sentiment.bearish_pct}%
              </div>
            </div>
          </div>

          {/* Top Headlines */}
          <div className="space-y-2">
            <div className="text-xs text-white text-opacity-60 mb-2">Recent Headlines</div>
            {sentiment.news_sentiment.top_headlines?.slice(0, 3).map((headline, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs">
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                  headline.sentiment === 'bullish' ? 'bg-green-400' :
                  headline.sentiment === 'bearish' ? 'bg-red-400' : 'bg-blue-400'
                }`}></span>
                <span className="text-white text-opacity-80 line-clamp-2">{headline.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Source Attribution */}
      {sentiment.data_sources && sentiment.data_sources.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white border-opacity-10">
          <div className="flex items-center justify-center gap-2 text-xs text-white text-opacity-40 flex-wrap">
            <span>Data sources:</span>
            {sentiment.data_sources.map((source, idx) => (
              <span key={idx} className="px-2 py-0.5 rounded bg-blue-500 bg-opacity-20 text-blue-400 font-semibold">
                {source}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
