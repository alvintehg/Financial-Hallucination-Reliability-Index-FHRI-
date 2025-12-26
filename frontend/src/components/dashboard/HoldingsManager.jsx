import { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, RefreshCw, AlertCircle, Check, X } from 'lucide-react';
import { getPortfolioHoldings, addHolding, updateHolding, removeHolding } from '../../api';

const HoldingsManager = () => {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingHolding, setEditingHolding] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    symbol: '',
    name: '',
    shares: '',
    cost_basis: '',
  });

  useEffect(() => {
    fetchHoldings();
  }, []);

  // Auto-dismiss messages after 5 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const fetchHoldings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPortfolioHoldings();
      setHoldings(data.holdings || []);
    } catch (err) {
      setError('Failed to load holdings');
      console.error('Error fetching holdings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (holding = null) => {
    if (holding) {
      setEditingHolding(holding);
      setFormData({
        symbol: holding.symbol,
        name: holding.name,
        shares: holding.shares.toString(),
        cost_basis: holding.cost_basis.toString(),
      });
    } else {
      setEditingHolding(null);
      setFormData({ symbol: '', name: '', shares: '', cost_basis: '' });
    }
    setShowDialog(true);
  };

  const handleCloseDialog = () => {
    setShowDialog(false);
    setEditingHolding(null);
    setFormData({ symbol: '', name: '', shares: '', cost_basis: '' });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setError(null);
      setSuccess(null);

      if (!formData.symbol || !formData.shares || !formData.cost_basis) {
        setError('Please fill in all required fields');
        return;
      }

      const shares = parseFloat(formData.shares);
      const costBasis = parseFloat(formData.cost_basis);

      if (isNaN(shares) || shares <= 0) {
        setError('Shares must be a positive number');
        return;
      }

      if (isNaN(costBasis) || costBasis <= 0) {
        setError('Cost basis must be a positive number');
        return;
      }

      if (editingHolding) {
        await updateHolding(formData.symbol, shares, costBasis);
        setSuccess(`Updated ${formData.symbol} successfully`);
      } else {
        await addHolding(
          formData.symbol.toUpperCase(),
          shares,
          costBasis,
          formData.name || formData.symbol.toUpperCase(),
          'equity'
        );
        setSuccess(`Added ${formData.symbol.toUpperCase()} successfully`);
      }

      handleCloseDialog();
      fetchHoldings();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save holding');
      console.error('Error saving holding:', err);
    }
  };

  const handleDelete = async (symbol) => {
    if (!window.confirm(`Are you sure you want to remove ${symbol}?`)) {
      return;
    }

    try {
      setError(null);
      setSuccess(null);
      await removeHolding(symbol);
      setSuccess(`Removed ${symbol} successfully`);
      fetchHoldings();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove holding');
      console.error('Error removing holding:', err);
    }
  };

  if (loading) {
    return (
      <div className="p-8 rounded-[20px] glass-card-strong">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-white animate-spin" />
            <p className="text-white text-opacity-70">Loading holdings...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="p-8 rounded-[20px] glass-card-strong">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl tracking-wider text-white" style={{ textTransform: 'uppercase' }}>
            Manage Holdings
          </h2>
          <button
            onClick={() => handleOpenDialog()}
            className="px-4 py-2 rounded-lg gradient-blue-button text-white font-semibold hover:scale-105 transition-transform flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Holding
          </button>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 rounded-lg bg-red-500 bg-opacity-20 border border-red-500 border-opacity-50 flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 rounded-lg bg-green-500 bg-opacity-20 border border-green-500 border-opacity-50 flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-400">
              <Check className="w-5 h-5" />
              <span>{success}</span>
            </div>
            <button onClick={() => setSuccess(null)} className="text-green-400 hover:text-green-300">
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Holdings Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white border-opacity-10">
                <th className="text-left py-3 px-4 text-white text-opacity-70 font-semibold tracking-wide">SYMBOL</th>
                <th className="text-left py-3 px-4 text-white text-opacity-70 font-semibold tracking-wide">NAME</th>
                <th className="text-right py-3 px-4 text-white text-opacity-70 font-semibold tracking-wide">SHARES</th>
                <th className="text-right py-3 px-4 text-white text-opacity-70 font-semibold tracking-wide">COST BASIS</th>
                <th className="text-right py-3 px-4 text-white text-opacity-70 font-semibold tracking-wide">TOTAL COST</th>
                <th className="text-center py-3 px-4 text-white text-opacity-70 font-semibold tracking-wide">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {holdings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12">
                    <div className="flex flex-col items-center gap-3">
                      <AlertCircle className="w-8 h-8 text-white text-opacity-40" />
                      <p className="text-white text-opacity-60">No holdings yet. Click "Add Holding" to get started.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                holdings.map((holding) => (
                  <tr
                    key={holding.symbol}
                    className="border-b border-white border-opacity-5 hover:bg-white hover:bg-opacity-5 transition-colors"
                  >
                    <td className="py-4 px-4">
                      <span className="text-white font-semibold tracking-wide">{holding.symbol}</span>
                    </td>
                    <td className="py-4 px-4 text-white text-opacity-80">{holding.name}</td>
                    <td className="py-4 px-4 text-right text-white">{holding.shares.toLocaleString()}</td>
                    <td className="py-4 px-4 text-right text-white">
                      ${holding.cost_basis.toFixed(2)}
                    </td>
                    <td className="py-4 px-4 text-right text-white font-semibold">
                      ${(holding.shares * holding.cost_basis).toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleOpenDialog(holding)}
                          className="p-2 rounded-lg bg-blue-500 bg-opacity-20 hover:bg-opacity-30 text-blue-400 transition-colors"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(holding.symbol)}
                          className="p-2 rounded-lg bg-red-500 bg-opacity-20 hover:bg-opacity-30 text-red-400 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Info Box */}
        <div className="mt-6 p-4 rounded-lg bg-blue-500 bg-opacity-10 border border-blue-500 border-opacity-30">
          <p className="text-blue-300 font-semibold mb-2">How to use:</p>
          <ul className="text-white text-opacity-70 text-sm space-y-1 ml-4">
            <li>• Add your Moomoo holdings manually using the "Add Holding" button</li>
            <li>• Enter the stock symbol, number of shares, and your average cost per share</li>
            <li>• The dashboard will automatically fetch live prices and calculate your P&L</li>
            <li>• You can edit or remove holdings anytime</li>
          </ul>
        </div>
      </div>

      {/* Add/Edit Dialog */}
      {showDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card-strong rounded-[20px] p-8 max-w-md w-full">
            <h3 className="text-2xl tracking-wider text-white mb-6" style={{ textTransform: 'uppercase' }}>
              {editingHolding ? `Edit ${editingHolding.symbol}` : 'Add New Holding'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-white text-opacity-70 mb-2 text-sm tracking-wide">
                  Stock Symbol *
                </label>
                <input
                  type="text"
                  name="symbol"
                  value={formData.symbol}
                  onChange={handleInputChange}
                  disabled={!!editingHolding}
                  placeholder="e.g., AAPL"
                  className="w-full px-4 py-3 rounded-lg bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:border-opacity-50 disabled:opacity-50"
                  required
                />
                <p className="text-white text-opacity-50 text-xs mt-1">Required. Use the ticker symbol from Moomoo.</p>
              </div>

              <div>
                <label className="block text-white text-opacity-70 mb-2 text-sm tracking-wide">
                  Company Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Apple Inc."
                  className="w-full px-4 py-3 rounded-lg bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:border-opacity-50"
                />
                <p className="text-white text-opacity-50 text-xs mt-1">Optional. Will use symbol if not provided.</p>
              </div>

              <div>
                <label className="block text-white text-opacity-70 mb-2 text-sm tracking-wide">
                  Number of Shares *
                </label>
                <input
                  type="number"
                  name="shares"
                  value={formData.shares}
                  onChange={handleInputChange}
                  placeholder="e.g., 100"
                  step="0.01"
                  min="0.01"
                  className="w-full px-4 py-3 rounded-lg bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:border-opacity-50"
                  required
                />
                <p className="text-white text-opacity-50 text-xs mt-1">Required. Total shares you own.</p>
              </div>

              <div>
                <label className="block text-white text-opacity-70 mb-2 text-sm tracking-wide">
                  Cost Basis (per share) *
                </label>
                <input
                  type="number"
                  name="cost_basis"
                  value={formData.cost_basis}
                  onChange={handleInputChange}
                  placeholder="e.g., 150.00"
                  step="0.01"
                  min="0.01"
                  className="w-full px-4 py-3 rounded-lg bg-white bg-opacity-5 border border-white border-opacity-20 text-white placeholder-white placeholder-opacity-40 focus:outline-none focus:border-blue-500 focus:border-opacity-50"
                  required
                />
                <p className="text-white text-opacity-50 text-xs mt-1">Required. Your average purchase price per share.</p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleCloseDialog}
                  className="flex-1 px-4 py-3 rounded-lg bg-white bg-opacity-5 hover:bg-opacity-10 text-white font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-3 rounded-lg gradient-blue-button text-white font-semibold hover:scale-105 transition-transform"
                >
                  {editingHolding ? 'Update' : 'Add'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default HoldingsManager;
