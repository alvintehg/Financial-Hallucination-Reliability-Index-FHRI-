import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react';
import { getMarketOverview } from '../../api';

export const MarketOverview = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getMarketOverview();
      setMarketData(data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Error fetching market data:', err);
      setError(err.message || 'Failed to load market data');
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchMarketData();

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      fetchMarketData();
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const formatPrice = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  // Company name mapping
  const companyNames = {
    'NVDA': 'NVIDIA Corp',
    'TSLA': 'Tesla Inc',
    'AAPL': 'Apple Inc',
    'META': 'Meta Platforms',
    'GOOGL': 'Alphabet Inc',
    'AMZN': 'Amazon.com Inc'
  };

  // Loading state
  if (loading && !marketData) {
    return (
      <div className="p-8 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-white animate-spin" />
            <p className="text-white text-opacity-70">Loading market data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !marketData) {
    return (
      <div className="p-8 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3 text-center">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <p className="text-white text-opacity-70">Failed to load market data</p>
            <p className="text-white text-opacity-50 text-sm">{error}</p>
            <button
              onClick={fetchMarketData}
              className="mt-4 px-6 py-2 rounded-lg gradient-blue-button text-white font-semibold hover:scale-105 transition-transform"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const indices = marketData?.indices || [];
  const topMovers = marketData?.top_movers || [];

  return (
    <div className="p-8 rounded-[20px] glass-card-strong transition-all duration-300">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-wider text-white mb-2" style={{ textTransform: 'uppercase' }}>
            MARKET OVERVIEW
          </h2>
          <p className="text-white text-opacity-70 text-sm">
            Real-time market indices and top movers
            {lastUpdated && (
              <span className="ml-2 text-white text-opacity-50">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchMarketData}
          disabled={loading}
          className="p-3 rounded-xl glass-card hover:scale-105 transition-transform disabled:opacity-50"
          title="Refresh market data"
        >
          <RefreshCw className={`w-5 h-5 text-white ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Market Indices */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold tracking-wider text-white mb-4" style={{ textTransform: 'uppercase' }}>
          MAJOR INDICES
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {indices.map((index, idx) => {
            const isPositive = (index.change_pct || 0) >= 0;
            return (
              <div
                key={idx}
                className="p-5 rounded-[20px] glass-card transition-all duration-300 hover:scale-105 text-center"
              >
                <div className="text-white text-opacity-60 text-xs font-semibold tracking-wider mb-3">
                  {index.name}
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {formatPrice(index.price)}
                </div>
                <div className={`text-sm font-semibold flex items-center justify-center gap-1 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {formatPercent(index.change_pct)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Movers */}
      {topMovers.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold tracking-wider text-white mb-4" style={{ textTransform: 'uppercase' }}>
            TOP MOVERS TODAY
          </h3>
          <div className="space-y-3">
            {topMovers.slice(0, 4).map((stock, idx) => {
              const isPositive = (stock.change_pct || 0) >= 0;
              const displayName = companyNames[stock.symbol] || stock.name;
              return (
                <div
                  key={idx}
                  className="flex items-center gap-4 p-5 rounded-[20px] glass-card transition-all duration-300 hover:scale-[1.02] cursor-pointer group"
                >
                  {/* Symbol Badge */}
                  <div className="w-12 h-12 rounded-xl gradient-blue-button flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-bold text-sm">{stock.symbol}</span>
                  </div>

                  {/* Name */}
                  <div className="flex-1">
                    <div className="font-semibold text-white">{displayName}</div>
                    <div className="text-white text-opacity-50 text-sm">{stock.symbol}</div>
                  </div>

                  {/* Change */}
                  <div className={`text-lg font-bold flex items-center gap-2 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                    {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                    {formatPercent(stock.change_pct)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Data Source Attribution */}
          {topMovers.length > 0 && topMovers[0].source && (
            <div className="mt-4 text-center">
              <p className="text-white text-opacity-40 text-xs">
                Market data provided by {topMovers[0].source}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
