// API service for backend communication
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const askQuestion = async (payload) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/ask`, payload, {
      timeout: 60000, // Increased to 60 seconds for ML model loading and data fetching
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    // Return demo response on error
    return {
      answer: `💡 **Demo Response**: Backend offline (error: ${error.message.substring(0, 50)}). Please start the server with: uvicorn src.server:app --port 8000`,
      entropy: Math.random() * 1.5 + 0.2,
      is_hallucination: Math.random() > 0.5,
      contradiction_score: Math.random() * 0.8 + 0.1,
      passages_used: Math.floor(Math.random() * 5),
      meta: {
        fhri: Math.random() * 0.6 + 0.3,
        provider: 'demo',
      },
      _error: error.message,
    };
  }
};

export const getLivePortfolio = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/portfolio/live`, {
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    console.error('Portfolio API Error:', error);
    throw error;
  }
};

export const getPortfolioHoldings = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/portfolio/holdings`, {
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    console.error('Get Holdings Error:', error);
    throw error;
  }
};

export const addHolding = async (symbol, shares, costBasis, name, assetType = 'equity') => {
  try {
    const response = await axios.post(`${API_BASE_URL}/portfolio/holdings/add`, {
      symbol,
      shares,
      cost_basis: costBasis,
      name,
      asset_type: assetType,
    });
    return response.data;
  } catch (error) {
    console.error('Add Holding Error:', error);
    throw error;
  }
};

export const updateHolding = async (symbol, shares, costBasis) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/portfolio/holdings/update`, {
      symbol,
      shares,
      cost_basis: costBasis,
    });
    return response.data;
  } catch (error) {
    console.error('Update Holding Error:', error);
    throw error;
  }
};

export const removeHolding = async (symbol) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/portfolio/holdings/remove`, {
      symbol,
    });
    return response.data;
  } catch (error) {
    console.error('Remove Holding Error:', error);
    throw error;
  }
};

export const getMarketOverview = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/market/overview`, {
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    console.error('Market Overview API Error:', error);
    throw error;
  }
};

export const getInvestmentRecommendations = async (riskProfile = 'moderate', useAiInsights = true) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/recommendations`, {
      risk_profile: riskProfile,
      use_ai_insights: useAiInsights,
    }, {
      timeout: 45000, // Allow time for AI insights generation
    });
    return response.data;
  } catch (error) {
    console.error('Recommendations API Error:', error);
    throw error;
  }
};

// ============================================================================
// Advisory API (Risk Profiling, Allocation, Themes, Escalation)
// ============================================================================

export const getRiskProfile = async (answers) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/advice/risk-profile`, {
      answers,
    }, {
      timeout: 10000,
    });
    return response.data;
  } catch (error) {
    console.error('Risk Profile API Error:', error);
    throw error;
  }
};

export const getPortfolioAllocation = async (riskLabel) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/advice/allocation`, {
      risk_label: riskLabel,
    }, {
      timeout: 10000,
    });
    return response.data;
  } catch (error) {
    console.error('Allocation API Error:', error);
    throw error;
  }
};

export const getThematicRecommendations = async (interestKeywords) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/advice/themes`, {
      interest_keywords: interestKeywords,
    }, {
      timeout: 15000,
    });
    return response.data;
  } catch (error) {
    console.error('Thematic API Error:', error);
    throw error;
  }
};

export const escalateToAdvisor = async (topic) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/advice/escalate`, {
      topic,
    }, {
      timeout: 5000,
    });
    return response.data;
  } catch (error) {
    console.error('Escalation API Error:', error);
    throw error;
  }
};

// ============================================================================
// Planning API (Goal Planning, Fee Impact)
// ============================================================================

export const planGoal = async (targetAmount, years, initCapital = 0, monthlyContrib = null, expectedReturn = 0.07) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/planning/goal`, {
      target_amount: targetAmount,
      years,
      init_capital: initCapital,
      monthly_contrib: monthlyContrib,
      expected_return: expectedReturn,
    }, {
      timeout: 10000,
    });
    return response.data;
  } catch (error) {
    console.error('Goal Planning API Error:', error);
    throw error;
  }
};

export const analyzeFeeImpact = async (principal, horizonYears, annualFeePct, expReturnPct, dividendWithholdingPct = 0) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/planning/fee-impact`, {
      principal,
      horizon_years: horizonYears,
      annual_fee_pct: annualFeePct,
      exp_return_pct: expReturnPct,
      dividend_withholding_pct: dividendWithholdingPct,
    }, {
      timeout: 10000,
    });
    return response.data;
  } catch (error) {
    console.error('Fee Impact API Error:', error);
    throw error;
  }
};

// ============================================================================
// Portfolio Analytics API (Backtesting, Behavioral Insights)
// ============================================================================

export const backtestPortfolio = async (weights, start, end, rebalanceFreq = 'quarterly') => {
  try {
    const response = await axios.post(`${API_BASE_URL}/portfolio/backtest`, {
      weights,
      start,
      end,
      rebalance_freq: rebalanceFreq,
    }, {
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    console.error('Backtest API Error:', error);
    throw error;
  }
};

export const analyzeBehavior = async (actions) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/insights/behavior`, {
      actions,
    }, {
      timeout: 10000,
    });
    return response.data;
  } catch (error) {
    console.error('Behavior Analysis API Error:', error);
    throw error;
  }
};

// ============================================================================
// Feedback API (Trust Feedback Loop for FHRI)
// ============================================================================

export const submitFeedback = async (turnId, rating) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/eval/feedback`, {
      turn_id: turnId,
      user_rating_1to5: rating,
    }, {
      timeout: 5000,
    });
    return response.data;
  } catch (error) {
    console.error('Feedback API Error:', error);
    throw error;
  }
};

export default {
  askQuestion,
  getLivePortfolio,
  getPortfolioHoldings,
  addHolding,
  updateHolding,
  removeHolding,
  getMarketOverview,
  getInvestmentRecommendations,
  getRiskProfile,
  getPortfolioAllocation,
  getThematicRecommendations,
  escalateToAdvisor,
  planGoal,
  analyzeFeeImpact,
  backtestPortfolio,
  analyzeBehavior,
  submitFeedback
};
