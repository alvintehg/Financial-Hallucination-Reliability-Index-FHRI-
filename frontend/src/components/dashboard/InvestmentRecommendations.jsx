import React, { useState, useEffect } from 'react';
import { Zap, Shield, Target, TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import { getInvestmentRecommendations } from '../../api';

export const InvestmentRecommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [riskProfile, setRiskProfile] = useState('moderate');
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getInvestmentRecommendations(riskProfile, true);

      // Map recommendations to component format
      const mappedRecs = data.recommendations.map(rec => ({
        icon: getIconForType(rec.type),
        type: rec.type,
        title: rec.name,
        description: rec.description,
        risk: rec.risk,
        riskColor: getRiskColor(rec.risk),
        confidence: rec.confidence,
        allocation: rec.allocation,
        symbol: rec.symbol,
        currentPrice: rec.current_price,
        priceChangePct: rec.price_change_pct,
        insights: rec.insights || []
      }));

      setRecommendations(mappedRecs);

      // Map metrics
      const portfolioMetrics = data.portfolio_metrics;
      setMetrics([
        {
          label: 'Expected Return',
          value: `${portfolioMetrics.expected_return}%`,
          sublabel: 'annual'
        },
        {
          label: 'Volatility',
          value: `${portfolioMetrics.volatility}%`,
          sublabel: 'standard deviation'
        },
        {
          label: 'Sharpe Ratio',
          value: portfolioMetrics.sharpe_ratio.toFixed(2),
          sublabel: 'risk-adjusted'
        },
        {
          label: 'Max Drawdown',
          value: `${portfolioMetrics.max_drawdown}%`,
          sublabel: 'historical'
        }
      ]);

      setLastUpdated(new Date(data.last_updated));
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
      setError('Failed to load recommendations. Please check if the backend is running.');
      setLoading(false);

      // Fallback to demo data
      loadDemoData();
    }
  };

  const loadDemoData = () => {
    const demoRecs = [
      {
        icon: Zap,
        type: 'HIGH GROWTH',
        title: 'Emerging Tech Sector',
        description: 'AI, quantum computing, and biotech opportunities with strong momentum.',
        risk: 'HIGH',
        riskColor: 'red',
        confidence: 87,
        allocation: 12,
        insights: []
      },
      {
        icon: Shield,
        type: 'BALANCED',
        title: 'Dividend Aristocrats',
        description: 'Stable companies with consistent dividend growth over 25+ years.',
        risk: 'MEDIUM',
        riskColor: 'amber',
        confidence: 92,
        allocation: 18,
        insights: []
      },
      {
        icon: Target,
        type: 'STRATEGIC',
        title: 'ESG Sustainable Fund',
        description: 'Environmental, social, and governance-focused investment portfolio.',
        risk: 'LOW',
        riskColor: 'green',
        confidence: 78,
        allocation: 8,
        insights: []
      },
    ];

    const demoMetrics = [
      { label: 'Expected Return', value: '12.4%', sublabel: 'annual' },
      { label: 'Volatility', value: '8.2%', sublabel: 'standard deviation' },
      { label: 'Sharpe Ratio', value: '1.85', sublabel: 'risk-adjusted' },
      { label: 'Max Drawdown', value: '-12.1%', sublabel: 'historical' },
    ];

    setRecommendations(demoRecs);
    setMetrics(demoMetrics);
  };

  useEffect(() => {
    fetchRecommendations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [riskProfile]);

  const getIconForType = (type) => {
    switch (type) {
      case 'HIGH GROWTH':
        return Zap;
      case 'BALANCED':
        return Shield;
      case 'STRATEGIC':
        return Target;
      default:
        return TrendingUp;
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'HIGH':
        return 'red';
      case 'MEDIUM':
        return 'amber';
      case 'LOW':
        return 'green';
      default:
        return 'amber';
    }
  };

  const getRiskBadgeClass = (color) => {
    if (color === 'red') return 'gradient-danger';
    if (color === 'amber') return 'gradient-warning';
    return 'gradient-success';
  };

  return (
    <div className="p-8 rounded-[20px] glass-card-strong transition-all duration-300">
      {/* Header with Risk Profile Selector */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wider text-white mb-2" style={{ textTransform: 'uppercase' }}>
            AI INVESTMENT RECOMMENDATIONS
          </h2>
          <p className="text-white text-opacity-70 text-sm">
            Personalized opportunities based on your risk profile and market analysis
          </p>
          {lastUpdated && (
            <p className="text-white text-opacity-50 text-xs mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>

        <div className="flex gap-2 items-center">
          {/* Risk Profile Selector */}
          <select
            value={riskProfile}
            onChange={(e) => setRiskProfile(e.target.value)}
            className="px-4 py-2 rounded-xl bg-white bg-opacity-10 text-white text-sm font-semibold tracking-wide transition-all duration-300 hover:bg-opacity-20 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="conservative" className="bg-gray-800">Conservative</option>
            <option value="moderate" className="bg-gray-800">Moderate</option>
            <option value="aggressive" className="bg-gray-800">Aggressive</option>
          </select>

          {/* Refresh Button */}
          <button
            onClick={fetchRecommendations}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-white bg-opacity-10 text-white text-sm font-semibold tracking-wide transition-all duration-300 hover:bg-opacity-20 disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500 bg-opacity-20 border border-red-500 border-opacity-30 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-200 text-sm font-semibold">Error Loading Recommendations</p>
            <p className="text-red-300 text-xs mt-1">{error}</p>
            <p className="text-red-400 text-xs mt-1">Showing demo data instead.</p>
          </div>
        </div>
      )}

      {/* Recommendation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {recommendations.map((rec, idx) => {
          const Icon = rec.icon;
          return (
            <div
              key={idx}
              className="p-6 rounded-[20px] glass-card transition-all duration-300 hover:scale-105 group cursor-pointer"
            >
              {/* Icon */}
              <div className="w-14 h-14 rounded-xl gradient-blue-button flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <Icon className="w-7 h-7 text-white" />
              </div>

              {/* Type & Risk Badges */}
              <div className="flex gap-2 mb-3 flex-wrap">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-white bg-opacity-10 text-white tracking-wide">
                  {rec.type}
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold text-white tracking-wide ${getRiskBadgeClass(rec.riskColor)}`}>
                  {rec.risk}
                </span>
              </div>

              {/* Title & Symbol */}
              <div className="mb-2">
                <h3 className="text-lg font-bold text-white">{rec.title}</h3>
                {rec.symbol && (
                  <p className="text-white text-opacity-50 text-xs">{rec.symbol}</p>
                )}
              </div>

              {/* Real-time Price Data */}
              {rec.currentPrice && (
                <div className="mb-3 flex items-baseline gap-2">
                  <span className="text-white font-bold text-xl">
                    ${rec.currentPrice.toFixed(2)}
                  </span>
                  {rec.priceChangePct !== null && (
                    <span className={`text-sm font-semibold ${rec.priceChangePct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {rec.priceChangePct >= 0 ? '+' : ''}{rec.priceChangePct.toFixed(2)}%
                    </span>
                  )}
                </div>
              )}

              {/* Description */}
              <p className="text-white text-opacity-70 text-sm mb-4 leading-relaxed">
                {rec.description}
              </p>

              {/* AI Insights */}
              {rec.insights && rec.insights.length > 0 && (
                <div className="mb-4 p-3 rounded-lg bg-black bg-opacity-20 border border-white border-opacity-10">
                  <p className="text-white text-opacity-60 text-xs font-semibold mb-2">AI INSIGHTS</p>
                  <ul className="space-y-1">
                    {rec.insights.slice(0, 2).map((insight, i) => (
                      <li key={i} className="text-white text-opacity-80 text-xs flex items-start gap-2">
                        <span className="text-blue-400 mt-0.5">•</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confidence Bar */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white text-opacity-60 text-xs font-semibold">CONFIDENCE</span>
                  <span className="text-white font-bold text-sm">{rec.confidence}%</span>
                </div>
                <div className="h-2 bg-black bg-opacity-30 rounded-full overflow-hidden">
                  <div
                    className="h-full gradient-blue-button transition-all duration-500"
                    style={{ width: `${rec.confidence}%` }}
                  />
                </div>
              </div>

              {/* Allocation */}
              <div className="mb-4">
                <div className="text-white text-opacity-60 text-xs font-semibold mb-1">SUGGESTED ALLOCATION</div>
                <div className="text-2xl font-bold text-white">{rec.allocation}%</div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button className="flex-1 px-4 py-2 rounded-xl bg-white bg-opacity-10 text-white text-xs font-semibold tracking-wide transition-all duration-300 hover:bg-opacity-20">
                  DETAILS
                </button>
                <button className="flex-1 px-4 py-2 rounded-xl gradient-blue-button text-white text-xs font-semibold tracking-wide transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
                  INVEST NOW
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Performance Metrics */}
      <div>
        <h3 className="text-lg font-semibold tracking-wider text-white mb-4 flex items-center gap-2" style={{ textTransform: 'uppercase' }}>
          <TrendingUp className="w-5 h-5 text-green-400" />
          PERFORMANCE METRICS
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, idx) => (
            <div
              key={idx}
              className="p-5 rounded-[20px] glass-card transition-all duration-300 hover:scale-105 text-center"
            >
              <div className="text-white text-opacity-60 text-xs font-semibold tracking-wider mb-2">
                {metric.label}
              </div>
              <div className="text-2xl font-bold text-white mb-1">{metric.value}</div>
              <div className="text-white text-opacity-50 text-xs">{metric.sublabel}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
