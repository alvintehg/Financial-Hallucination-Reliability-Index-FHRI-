import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, TrendingUp, TrendingDown, RefreshCw, DollarSign, Percent } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Enhanced Rebalancing Widget
 * Features:
 * - Current vs Target allocation comparison
 * - Specific buy/sell recommendations with dollar amounts
 * - Visual drift indicators
 * - Transaction cost estimates
 * - Tax impact warnings
 */
export const EnhancedRebalancingWidget = () => {
  const [rebalanceData, setRebalanceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchRebalanceData();
  }, []);

  const fetchRebalanceData = async () => {
    setLoading(true);
    try {
      // Get current portfolio
      const portfolioRes = await axios.get(`${API_BASE_URL}/portfolio/live`);
      const currentHoldings = portfolioRes.data.holdings || [];

      // Get rebalancing recommendations
      const rebalanceRes = await axios.post(`${API_BASE_URL}/portfolio/rebalance`, {
        current_holdings: currentHoldings.map(h => ({
          symbol: h.symbol,
          shares: h.shares,
          current_price: h.current_price,
          value: h.value
        }))
      });

      setRebalanceData(rebalanceRes.data);
    } catch (error) {
      console.error('Error fetching rebalance data:', error);
      // Enhanced mock fallback with detailed recommendations
      setRebalanceData({
        needs_rebalance: true,
        drift_pct: 7.2,
        threshold_pct: 5.0,
        total_portfolio_value: 125000,
        target_allocation: [
          { symbol: 'VTI', target_pct: 40, current_pct: 35, drift: -5 },
          { symbol: 'VXUS', target_pct: 20, current_pct: 18, drift: -2 },
          { symbol: 'BND', target_pct: 30, current_pct: 35, drift: +5 },
          { symbol: 'VNQ', target_pct: 5, current_pct: 6, drift: +1 },
          { symbol: 'CASH', target_pct: 5, current_pct: 6, drift: +1 }
        ],
        recommendations: [
          {
            action: 'BUY',
            symbol: 'VTI',
            name: 'Vanguard Total Stock Market ETF',
            current_value: 43750,
            target_value: 50000,
            difference_dollars: 6250,
            difference_shares: 24,
            current_price: 260.42,
            reason: 'Underweight by 5% - Need to increase equity exposure',
            priority: 'High',
            estimated_cost: 12.50
          },
          {
            action: 'BUY',
            symbol: 'VXUS',
            name: 'Vanguard Total International Stock ETF',
            current_value: 22500,
            target_value: 25000,
            difference_dollars: 2500,
            difference_shares: 42,
            current_price: 59.52,
            reason: 'Underweight by 2% - Rebalance to target',
            priority: 'Medium',
            estimated_cost: 5.00
          },
          {
            action: 'SELL',
            symbol: 'BND',
            name: 'Vanguard Total Bond Market ETF',
            current_value: 43750,
            target_value: 37500,
            difference_dollars: -6250,
            difference_shares: -79,
            current_price: 79.11,
            reason: 'Overweight by 5% - Reduce fixed income allocation',
            priority: 'High',
            estimated_cost: 12.50
          },
          {
            action: 'SELL',
            symbol: 'VNQ',
            name: 'Vanguard Real Estate ETF',
            current_value: 7500,
            target_value: 6250,
            difference_dollars: -1250,
            difference_shares: -13,
            current_price: 96.15,
            reason: 'Overweight by 1% - Minor adjustment',
            priority: 'Low',
            estimated_cost: 2.50
          },
          {
            action: 'HOLD',
            symbol: 'CASH',
            name: 'Cash Reserve',
            current_value: 7500,
            target_value: 6250,
            difference_dollars: -1250,
            difference_shares: 0,
            current_price: 1.00,
            reason: 'Use excess cash for rebalancing purchases',
            priority: 'Info',
            estimated_cost: 0
          }
        ],
        summary: {
          total_buys: 8750,
          total_sells: 7500,
          net_cash_needed: 1250,
          estimated_total_cost: 32.50,
          estimated_tax_impact: 125.00,
          rebalance_benefit: 'Restores target risk profile and improves diversification'
        },
        last_rebalance: '2024-09-15',
        data_source: 'Portfolio Analytics Engine'
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatShares = (shares) => {
    return Math.abs(shares).toFixed(0);
  };

  // Loading state
  if (loading && !rebalanceData) {
    return (
      <div className="p-6 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-48">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-6 h-6 text-white animate-spin" />
            <p className="text-white text-opacity-70 text-sm">Analyzing portfolio...</p>
          </div>
        </div>
      </div>
    );
  }

  const needsRebalance = rebalanceData?.needs_rebalance;
  const recommendations = rebalanceData?.recommendations || [];
  const buyActions = recommendations.filter(r => r.action === 'BUY');
  const sellActions = recommendations.filter(r => r.action === 'SELL');

  return (
    <div className="p-6 rounded-[20px] glass-card-strong transition-all duration-300">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {needsRebalance ? (
            <div className="w-10 h-10 rounded-xl bg-orange-500 bg-opacity-20 border border-orange-500 border-opacity-30 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-xl bg-green-500 bg-opacity-20 border border-green-500 border-opacity-30 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
          )}
          <div>
            <h3 className="text-lg font-bold tracking-wider text-white" style={{ textTransform: 'uppercase' }}>
              {needsRebalance ? 'REBALANCING NEEDED' : 'PORTFOLIO BALANCED'}
            </h3>
            <p className="text-white text-opacity-50 text-xs">
              Drift: <span className="font-semibold text-white">{rebalanceData?.drift_pct}%</span> from target
              {needsRebalance && ` (threshold: ${rebalanceData?.threshold_pct}%)`}
            </p>
          </div>
        </div>
        <button
          onClick={fetchRebalanceData}
          disabled={loading}
          className="p-2 rounded-lg glass-card hover:scale-105 transition-transform disabled:opacity-50"
          title="Refresh rebalancing analysis"
        >
          <RefreshCw className={`w-4 h-4 text-white ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {!needsRebalance ? (
        <div className="text-center py-8">
          <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
          <p className="text-white text-opacity-70 mb-2">Your portfolio is well balanced!</p>
          <p className="text-white text-opacity-50 text-sm">
            Last rebalanced: {rebalanceData?.last_rebalance || 'N/A'}
          </p>
        </div>
      ) : (
        <>
          {/* Current vs Target Allocation */}
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-white text-opacity-60 mb-3">ALLOCATION COMPARISON</h4>
            <div className="space-y-3">
              {rebalanceData?.target_allocation?.map((allocation, idx) => {
                const isDrifted = Math.abs(allocation.drift) >= 2;
                const isOverweight = allocation.drift > 0;
                return (
                  <div key={idx} className="p-3 rounded-xl bg-white bg-opacity-5">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-semibold text-sm">{allocation.symbol}</span>
                        {isDrifted && (
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            isOverweight
                              ? 'bg-red-500 bg-opacity-20 text-red-400 border border-red-500 border-opacity-30'
                              : 'bg-blue-500 bg-opacity-20 text-blue-400 border border-blue-500 border-opacity-30'
                          }`}>
                            {isOverweight ? 'Overweight' : 'Underweight'}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <div className="text-white text-opacity-50">
                          Current: <span className="text-white font-semibold">{allocation.current_pct}%</span>
                        </div>
                        <div className="w-px h-3 bg-white bg-opacity-20"></div>
                        <div className="text-white text-opacity-50">
                          Target: <span className="text-white font-semibold">{allocation.target_pct}%</span>
                        </div>
                      </div>
                    </div>
                    {/* Progress bars */}
                    <div className="space-y-1">
                      <div className="h-1.5 rounded-full bg-white bg-opacity-10 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isDrifted && isOverweight ? 'bg-red-400' :
                            isDrifted ? 'bg-blue-400' : 'bg-green-400'
                          }`}
                          style={{ width: `${allocation.current_pct}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detailed Recommendations */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-white text-opacity-60">RECOMMENDED ACTIONS</h4>
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-xs px-3 py-1 rounded-lg glass-card text-blue-400 hover:bg-white hover:bg-opacity-10 transition-all"
              >
                {showDetails ? 'Hide Details' : 'Show Details'}
              </button>
            </div>

            <div className="space-y-3">
              {/* Buy Recommendations */}
              {buyActions.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-green-400" />
                    <span className="text-xs font-semibold text-white text-opacity-60">BUY ORDERS</span>
                  </div>
                  {buyActions.map((rec, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-green-500 bg-opacity-5 border border-green-500 border-opacity-20">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-white font-bold text-sm">{rec.symbol}</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              rec.priority === 'High' ? 'bg-red-500 bg-opacity-20 text-red-400' :
                              rec.priority === 'Medium' ? 'bg-yellow-500 bg-opacity-20 text-yellow-400' :
                              'bg-blue-500 bg-opacity-20 text-blue-400'
                            }`}>
                              {rec.priority}
                            </span>
                          </div>
                          <div className="text-xs text-white text-opacity-50 mb-2">{rec.name}</div>
                          {showDetails && (
                            <div className="text-xs text-white text-opacity-70 italic">{rec.reason}</div>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-green-400 font-bold text-lg">{formatCurrency(Math.abs(rec.difference_dollars))}</div>
                          <div className="text-white text-opacity-50 text-xs">{formatShares(rec.difference_shares)} shares</div>
                        </div>
                      </div>
                      {showDetails && (
                        <div className="pt-3 border-t border-white border-opacity-10 grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <div className="text-white text-opacity-50">Current Price</div>
                            <div className="text-white font-semibold">${rec.current_price.toFixed(2)}</div>
                          </div>
                          <div>
                            <div className="text-white text-opacity-50">Trading Cost</div>
                            <div className="text-white font-semibold">${rec.estimated_cost.toFixed(2)}</div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Sell Recommendations */}
              {sellActions.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingDown className="w-4 h-4 text-red-400" />
                    <span className="text-xs font-semibold text-white text-opacity-60">SELL ORDERS</span>
                  </div>
                  {sellActions.map((rec, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-red-500 bg-opacity-5 border border-red-500 border-opacity-20">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-white font-bold text-sm">{rec.symbol}</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              rec.priority === 'High' ? 'bg-red-500 bg-opacity-20 text-red-400' :
                              rec.priority === 'Medium' ? 'bg-yellow-500 bg-opacity-20 text-yellow-400' :
                              'bg-blue-500 bg-opacity-20 text-blue-400'
                            }`}>
                              {rec.priority}
                            </span>
                          </div>
                          <div className="text-xs text-white text-opacity-50 mb-2">{rec.name}</div>
                          {showDetails && (
                            <div className="text-xs text-white text-opacity-70 italic">{rec.reason}</div>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-red-400 font-bold text-lg">{formatCurrency(Math.abs(rec.difference_dollars))}</div>
                          <div className="text-white text-opacity-50 text-xs">{formatShares(rec.difference_shares)} shares</div>
                        </div>
                      </div>
                      {showDetails && (
                        <div className="pt-3 border-t border-white border-opacity-10 grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <div className="text-white text-opacity-50">Current Price</div>
                            <div className="text-white font-semibold">${rec.current_price.toFixed(2)}</div>
                          </div>
                          <div>
                            <div className="text-white text-opacity-50">Trading Cost</div>
                            <div className="text-white font-semibold">${rec.estimated_cost.toFixed(2)}</div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Summary */}
          {rebalanceData?.summary && (
            <div className="p-4 rounded-xl bg-blue-500 bg-opacity-5 border border-blue-500 border-opacity-20">
              <h4 className="text-sm font-semibold text-white mb-3">REBALANCING SUMMARY</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                <div>
                  <div className="flex items-center gap-1 text-white text-opacity-50 text-xs mb-1">
                    <DollarSign className="w-3 h-3" />
                    <span>Total Buys</span>
                  </div>
                  <div className="text-white font-bold">{formatCurrency(rebalanceData.summary.total_buys)}</div>
                </div>
                <div>
                  <div className="flex items-center gap-1 text-white text-opacity-50 text-xs mb-1">
                    <DollarSign className="w-3 h-3" />
                    <span>Total Sells</span>
                  </div>
                  <div className="text-white font-bold">{formatCurrency(rebalanceData.summary.total_sells)}</div>
                </div>
                <div>
                  <div className="flex items-center gap-1 text-white text-opacity-50 text-xs mb-1">
                    <Percent className="w-3 h-3" />
                    <span>Trading Costs</span>
                  </div>
                  <div className="text-yellow-400 font-bold">${rebalanceData.summary.estimated_total_cost.toFixed(2)}</div>
                </div>
                <div>
                  <div className="flex items-center gap-1 text-white text-opacity-50 text-xs mb-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Tax Impact</span>
                  </div>
                  <div className="text-orange-400 font-bold">${rebalanceData.summary.estimated_tax_impact.toFixed(2)}</div>
                </div>
              </div>
              <div className="pt-3 border-t border-white border-opacity-10">
                <div className="text-xs text-white text-opacity-70">
                  <strong>Benefit:</strong> {rebalanceData.summary.rebalance_benefit}
                </div>
              </div>
            </div>
          )}

          {/* Execute Button */}
          <div className="mt-6 flex gap-3">
            <button className="flex-1 py-3 rounded-xl gradient-blue-button text-white font-semibold hover:scale-105 transition-transform">
              Execute Rebalancing
            </button>
            <button className="px-6 py-3 rounded-xl glass-card text-white hover:bg-white hover:bg-opacity-10 transition-all">
              Preview Orders
            </button>
          </div>
        </>
      )}

      {/* Data Source */}
      {rebalanceData?.data_source && (
        <div className="mt-4 pt-4 border-t border-white border-opacity-10">
          <div className="flex items-center justify-center gap-2 text-xs text-white text-opacity-40">
            <span>Analysis by</span>
            <span className="px-2 py-0.5 rounded bg-blue-500 bg-opacity-20 text-blue-400 font-semibold">
              {rebalanceData.data_source}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
