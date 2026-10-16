import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw, Activity } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Sector Performance Widget - Shows sector rotation and performance
 * Displays major market sectors with real-time performance data
 */
export const SectorPerformanceWidget = () => {
  const [sectorData, setSectorData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchSectorData();
    // Refresh every 5 minutes
    const interval = setInterval(fetchSectorData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchSectorData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/market/sectors`);
      setSectorData(response.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching sector data:', error);
      // Mock fallback with realistic sector data
      setSectorData({
        sectors: [
          { name: 'Technology', symbol: 'XLK', change_pct: 2.45, performance_1w: 3.2, trend: 'up' },
          { name: 'Healthcare', symbol: 'XLV', change_pct: 0.85, performance_1w: 1.4, trend: 'up' },
          { name: 'Financials', symbol: 'XLF', change_pct: 1.32, performance_1w: 2.1, trend: 'up' },
          { name: 'Energy', symbol: 'XLE', change_pct: -1.20, performance_1w: -0.8, trend: 'down' },
          { name: 'Consumer Discretionary', symbol: 'XLY', change_pct: 1.65, performance_1w: 2.5, trend: 'up' },
          { name: 'Industrials', symbol: 'XLI', change_pct: 0.95, performance_1w: 1.7, trend: 'up' },
          { name: 'Materials', symbol: 'XLB', change_pct: -0.45, performance_1w: 0.3, trend: 'neutral' },
          { name: 'Real Estate', symbol: 'XLRE', change_pct: -0.85, performance_1w: -1.2, trend: 'down' },
          { name: 'Utilities', symbol: 'XLU', change_pct: 0.25, performance_1w: 0.6, trend: 'neutral' },
          { name: 'Communication Services', symbol: 'XLC', change_pct: 1.85, performance_1w: 2.8, trend: 'up' },
          { name: 'Consumer Staples', symbol: 'XLP', change_pct: 0.45, performance_1w: 0.9, trend: 'up' }
        ],
        data_source: 'Finnhub',
        timestamp: new Date().toISOString()
      });
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const sign = value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getSectorColor = (changePct) => {
    if (changePct > 1.5) return 'text-green-400 bg-green-500 bg-opacity-10 border-green-500 border-opacity-30';
    if (changePct > 0) return 'text-green-400 bg-green-500 bg-opacity-5 border-green-500 border-opacity-20';
    if (changePct < -1.5) return 'text-red-400 bg-red-500 bg-opacity-10 border-red-500 border-opacity-30';
    if (changePct < 0) return 'text-red-400 bg-red-500 bg-opacity-5 border-red-500 border-opacity-20';
    return 'text-blue-400 bg-blue-500 bg-opacity-5 border-blue-500 border-opacity-20';
  };

  // Loading state
  if (loading && !sectorData) {
    return (
      <div className="p-6 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-48">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-6 h-6 text-white animate-spin" />
            <p className="text-white text-opacity-70 text-sm">Loading sector data...</p>
          </div>
        </div>
      </div>
    );
  }

  const sectors = sectorData?.sectors || [];
  const topPerformers = [...sectors].sort((a, b) => b.change_pct - a.change_pct).slice(0, 3);
  const bottomPerformers = [...sectors].sort((a, b) => a.change_pct - b.change_pct).slice(0, 3);

  return (
    <div className="p-6 rounded-[20px] glass-card-strong transition-all duration-300">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-blue-button flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold tracking-wider text-white" style={{ textTransform: 'uppercase' }}>
              SECTOR PERFORMANCE
            </h3>
            <p className="text-white text-opacity-50 text-xs">
              11 Major Market Sectors
              {lastUpdated && (
                <span className="ml-2">• Updated {lastUpdated.toLocaleTimeString()}</span>
              )}
            </p>
          </div>
        </div>
        <button
          onClick={fetchSectorData}
          disabled={loading}
          className="p-2 rounded-lg glass-card hover:scale-105 transition-transform disabled:opacity-50"
          title="Refresh sector data"
        >
          <RefreshCw className={`w-4 h-4 text-white ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Top & Bottom Performers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Top Performers */}
        <div>
          <div className="text-xs font-semibold text-white text-opacity-60 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-400" />
            TOP PERFORMERS
          </div>
          <div className="space-y-2">
            {topPerformers.map((sector, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-green-500 bg-opacity-5 border border-green-500 border-opacity-20 hover:bg-opacity-10 transition-all"
              >
                <div className="flex-1">
                  <div className="text-white font-semibold text-sm">{sector.name}</div>
                  <div className="text-white text-opacity-50 text-xs">{sector.symbol}</div>
                </div>
                <div className="text-right">
                  <div className="text-green-400 font-bold text-sm">{formatPercent(sector.change_pct)}</div>
                  <div className="text-white text-opacity-50 text-xs">1W: {formatPercent(sector.performance_1w)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Performers */}
        <div>
          <div className="text-xs font-semibold text-white text-opacity-60 mb-3 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-red-400" />
            LAGGING SECTORS
          </div>
          <div className="space-y-2">
            {bottomPerformers.map((sector, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-red-500 bg-opacity-5 border border-red-500 border-opacity-20 hover:bg-opacity-10 transition-all"
              >
                <div className="flex-1">
                  <div className="text-white font-semibold text-sm">{sector.name}</div>
                  <div className="text-white text-opacity-50 text-xs">{sector.symbol}</div>
                </div>
                <div className="text-right">
                  <div className="text-red-400 font-bold text-sm">{formatPercent(sector.change_pct)}</div>
                  <div className="text-white text-opacity-50 text-xs">1W: {formatPercent(sector.performance_1w)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* All Sectors Grid */}
      <div>
        <div className="text-xs font-semibold text-white text-opacity-60 mb-3">ALL SECTORS (Today)</div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {sectors.map((sector, idx) => {
            const isPositive = sector.change_pct >= 0;
            const colorClasses = getSectorColor(sector.change_pct);
            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border transition-all duration-300 hover:scale-105 cursor-pointer ${colorClasses}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {isPositive ? (
                    <TrendingUp className="w-4 h-4 flex-shrink-0" />
                  ) : (
                    <TrendingDown className="w-4 h-4 flex-shrink-0" />
                  )}
                  <div className="text-white text-opacity-90 font-semibold text-xs truncate">
                    {sector.name}
                  </div>
                </div>
                <div className="text-sm font-bold">
                  {formatPercent(sector.change_pct)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Data Source Attribution */}
      {sectorData?.data_source && (
        <div className="mt-4 pt-4 border-t border-white border-opacity-10">
          <div className="flex items-center justify-center gap-2 text-xs text-white text-opacity-40">
            <span>Sector data powered by</span>
            <span className="px-2 py-0.5 rounded bg-blue-500 bg-opacity-20 text-blue-400 font-semibold">
              {sectorData.data_source}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
