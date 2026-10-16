import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Portfolio Drift Alert - Shows when portfolio deviates >5% from target
 * Displays rebalancing needed status
 */
export const PortfolioDriftAlert = () => {
  const [driftData, setDriftData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDriftData();
  }, []);

  const fetchDriftData = async () => {
    setLoading(true);
    try {
      // Get current holdings
      const holdingsRes = await axios.get(`${API_BASE_URL}/portfolio/live`);
      const currentHoldings = holdingsRes.data.holdings || [];

      // Define target allocation (example: balanced portfolio)
      const targetAllocation = [
        { symbol: 'VTI', weight: 0.40 },
        { symbol: 'VXUS', weight: 0.20 },
        { symbol: 'BND', weight: 0.30 },
        { symbol: 'VNQ', weight: 0.05 },
        { symbol: 'SHY', weight: 0.05 }
      ];

      // Analyze drift
      const driftRes = await axios.post(`${API_BASE_URL}/portfolio/drift`, {
        current_holdings: currentHoldings.map(h => ({
          symbol: h.symbol,
          value: h.value,
          shares: h.shares
        })),
        target_allocation: targetAllocation
      });

      setDriftData(driftRes.data);
    } catch (error) {
      console.error('Error fetching drift data:', error);
      // Mock fallback
      setDriftData({
        drift_pct: 3.5,
        needs_rebalance: false,
        threshold_pct: 5.0,
        actions: []
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !driftData) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-white bg-opacity-5">
        <div className="w-8 h-8 rounded-full bg-white bg-opacity-10 animate-pulse"></div>
        <div className="flex-1">
          <div className="h-4 bg-white bg-opacity-10 rounded mb-2 animate-pulse"></div>
          <div className="h-2 bg-white bg-opacity-10 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  const needsRebalance = driftData.needs_rebalance;

  return (
    <div className={`p-4 rounded-xl border ${needsRebalance ? 'bg-orange-500 bg-opacity-10 border-orange-500 border-opacity-30' : 'bg-green-500 bg-opacity-10 border-green-500 border-opacity-30'}`}>
      <div className="flex items-center gap-3">
        {needsRebalance ? (
          <AlertTriangle className="w-8 h-8 text-orange-400" />
        ) : (
          <CheckCircle className="w-8 h-8 text-green-400" />
        )}
        <div className="flex-1">
          <h4 className="font-semibold text-white text-sm mb-1">
            {needsRebalance ? 'Rebalancing Needed' : 'Portfolio Balanced'}
          </h4>
          <p className="text-xs text-white text-opacity-70">
            Drift: <span className="font-semibold">{driftData.drift_pct}%</span> from target
            {needsRebalance && ` (threshold: ${driftData.threshold_pct}%)`}
          </p>
        </div>
        {needsRebalance && (
          <button className="px-3 py-1 rounded-lg bg-orange-500 bg-opacity-20 text-orange-400 text-xs font-semibold hover:bg-opacity-30 transition-all">
            View Actions
          </button>
        )}
      </div>

      {needsRebalance && driftData.actions && driftData.actions.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white border-opacity-10">
          <div className="text-xs text-white text-opacity-60 mb-2">Quick Actions</div>
          <div className="space-y-1">
            {driftData.actions.slice(0, 2).map((action, idx) => (
              <div key={idx} className="text-xs text-white text-opacity-80 flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${action.action === 'BUY' ? 'bg-green-400' : 'bg-red-400'}`}></span>
                <span className="font-semibold">{action.action}</span>
                <span>{action.symbol}</span>
                <span className="text-white text-opacity-60">({action.amount_pct}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
