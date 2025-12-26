import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, ArrowRight, RefreshCw, AlertCircle } from 'lucide-react';
import { getLivePortfolio } from '../../api';

export const PortfolioOverview = () => {
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLivePortfolio();
      setPortfolioData(data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Error fetching portfolio:', err);
      setError(err.message || 'Failed to load portfolio');
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchPortfolio();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchPortfolio();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value, includeSign = true) => {
    const sign = includeSign && value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  // Loading state
  if (loading && !portfolioData) {
    return (
      <div className="p-8 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-white animate-spin" />
            <p className="text-white text-opacity-70">Loading portfolio data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !portfolioData) {
    return (
      <div className="p-8 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3 text-center">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <p className="text-white text-opacity-70">Failed to load portfolio</p>
            <p className="text-white text-opacity-50 text-sm">{error}</p>
            <button
              onClick={fetchPortfolio}
              className="mt-4 px-6 py-2 rounded-lg gradient-blue-button text-white font-semibold hover:scale-105 transition-transform"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const summary = portfolioData?.summary || {};
  const holdings = portfolioData?.holdings || [];

  const stats = [
    {
      label: 'TOTAL PORTFOLIO VALUE',
      value: formatCurrency(summary.total_value || 0),
      change: formatPercent(summary.total_pnl_pct || 0),
      changeAmount: formatCurrency(summary.total_pnl || 0),
      positive: (summary.total_pnl || 0) >= 0,
    },
    {
      label: 'DAILY CHANGE',
      value: formatCurrency(summary.daily_change || 0),
      change: formatPercent(summary.daily_change_pct || 0),
      changeAmount: 'today',
      positive: (summary.daily_change || 0) >= 0,
    },
    {
      label: 'ACTIVE POSITIONS',
      value: summary.positions_count || 0,
      change: holdings.length > 0 ? `${holdings.length} holdings` : 'No holdings',
      changeAmount: 'managed',
      positive: true,
    },
  ];

  return (
    <div className="p-8 rounded-[20px] glass-card-strong transition-all duration-300">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-wider text-white mb-2" style={{ textTransform: 'uppercase' }}>
            LIVE PORTFOLIO
          </h2>
          <p className="text-white text-opacity-70 text-sm">
            Real-time performance metrics and asset allocation
            {lastUpdated && (
              <span className="ml-2 text-white text-opacity-50">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={fetchPortfolio}
          disabled={loading}
          className="p-3 rounded-xl glass-card hover:scale-105 transition-transform disabled:opacity-50"
          title="Refresh portfolio"
        >
          <RefreshCw className={`w-5 h-5 text-white ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="p-6 rounded-[20px] glass-card transition-all duration-300 hover:scale-105"
          >
            <div className="text-white text-opacity-60 text-xs font-semibold tracking-wider mb-3">
              {stat.label}
            </div>
            <div className="text-3xl font-bold text-white mb-2">{stat.value}</div>
            <div className="flex items-center gap-2">
              <span className={`text-sm font-semibold ${stat.positive ? 'text-green-400' : 'text-red-400'}`}>
                {stat.change}
              </span>
              <span className="text-white text-opacity-50 text-xs">{stat.changeAmount}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Holdings Table */}
      {holdings.length > 0 ? (
        <div>
          <h3 className="text-lg font-semibold tracking-wider text-white mb-4" style={{ textTransform: 'uppercase' }}>
            TOP HOLDINGS
          </h3>
          <div className="space-y-3">
            {holdings.map((holding, idx) => (
              <div
                key={idx}
                className="group p-5 rounded-[20px] glass-card transition-all duration-300 hover:scale-[1.02] cursor-pointer relative"
              >
                <div className="flex items-center gap-4">
                  {/* Symbol Badge */}
                  <div className="w-12 h-12 rounded-xl gradient-blue-button flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-bold text-sm">{holding.symbol}</span>
                  </div>

                  {/* Name & Ticker */}
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-white">{holding.name}</div>
                    <div className="text-white text-opacity-50 text-sm">
                      {holding.shares} shares @ {formatCurrency(holding.current_price)}
                    </div>
                  </div>

                  {/* Allocation Bar */}
                  <div className="flex-1 hidden md:block">
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-2 bg-black bg-opacity-30 rounded-full overflow-hidden">
                        <div
                          className="h-full gradient-blue-button"
                          style={{ width: `${holding.allocation_pct}%` }}
                        />
                      </div>
                      <span className="text-white text-opacity-70 text-sm font-semibold w-12 text-right">
                        {holding.allocation_pct.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Value & P&L */}
                  <div className="text-right">
                    <div className="font-semibold text-white">{formatCurrency(holding.market_value)}</div>
                    <div className={`text-sm font-semibold flex items-center gap-1 justify-end ${holding.daily_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {holding.daily_change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {formatPercent(holding.daily_change_pct)}
                    </div>
                    <div className={`text-xs ${holding.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'} text-opacity-70`}>
                      P&L: {formatCurrency(holding.unrealized_pnl)} ({formatPercent(holding.unrealized_pnl_pct)})
                    </div>
                  </div>

                  {/* Hover Arrow */}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <ArrowRight className="w-5 h-5 text-white text-opacity-50" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Data Source Attribution */}
          {holdings.length > 0 && holdings[0].source && (
            <div className="mt-4 text-center">
              <p className="text-white text-opacity-40 text-xs">
                Market data provided by {holdings[0].source}
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-white text-opacity-50">No holdings found. Add your first holding to get started!</p>
        </div>
      )}
    </div>
  );
};
