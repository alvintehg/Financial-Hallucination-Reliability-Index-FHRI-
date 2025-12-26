# New Features Documentation

This document describes all the new features added to the LLM-FIN-CHATBOT robo-advisor.

## Overview

All new features are **backend-only** with minimal client integration. The existing UI layout and styling remain unchanged. Features are accessible via new API endpoints and can be called from the chat flow or existing components.

---

## 1. Risk Profiling & Portfolio Allocation

### Risk Profiling (`POST /advice/risk-profile`)

Analyzes questionnaire responses to determine investor risk profile.

**Request:**
```json
{
  "answers": [
    {
      "question_id": "time_horizon",
      "answer": "10+ years",
      "score": 80
    },
    {
      "question_id": "risk_tolerance",
      "answer": "Very comfortable with volatility",
      "score": 85
    }
  ]
}
```

**Response:**
```json
{
  "risk_label": "Aggressive",
  "score": 82.5,
  "breakdown": {
    "time_horizon": 80,
    "risk_tolerance": 85
  },
  "answers_processed": 2
}
```

**Risk Labels:**
- **Conservative** (0-35): Capital preservation, low volatility
- **Balanced** (35-65): Growth and stability balance
- **Aggressive** (65-100): Maximum growth, high volatility tolerance

---

### Portfolio Allocation (`POST /advice/allocation`)

Provides ETF-based portfolio allocation based on risk profile.

**Request:**
```json
{
  "risk_label": "Balanced"
}
```

**Response:**
```json
{
  "allocation": [
    {
      "ticker": "VTI",
      "weight": 0.40,
      "role": "Total Stock Market",
      "name": "Vanguard Total Stock Market ETF"
    },
    {
      "ticker": "VXUS",
      "weight": 0.20,
      "role": "International Equities",
      "name": "Vanguard Total International Stock ETF"
    },
    {
      "ticker": "BND",
      "weight": 0.30,
      "role": "Core Bonds",
      "name": "Vanguard Total Bond Market ETF"
    }
  ],
  "asset_mix": {
    "equities": 60,
    "bonds": 35,
    "cash": 5
  },
  "notes": "This allocation balances growth and stability...",
  "sources": ["Vanguard Asset Allocation Models", "Academic research"]
}
```

**Allocation Templates:**
- **Conservative**: 30% equities / 60% bonds / 10% cash
- **Balanced**: 60% equities / 35% bonds / 5% cash
- **Aggressive**: 85% equities / 10% bonds / 5% cash

---

## 2. Goal-Based Planning

### Goal Planning (`POST /planning/goal`)

Computes projections for financial goals with required monthly contributions.

**Request:**
```json
{
  "target_amount": 100000,
  "years": 10,
  "init_capital": 5000,
  "monthly_contrib": null,
  "expected_return": 0.07
}
```

**Response:**
```json
{
  "target_amount": 100000,
  "years": 10,
  "init_capital": 5000,
  "monthly_contrib": 512.34,
  "required_monthly": 512.34,
  "expected_return": 0.07,
  "final_value": 100123.45,
  "will_reach_goal": true,
  "shortfall": 0,
  "projection": [
    {"date": "2025-11-09", "value": 5000, "year": 0},
    {"date": "2026-11-09", "value": 12456.78, "year": 1},
    {"date": "2027-11-09", "value": 20345.67, "year": 2}
  ]
}
```

**Use Cases:**
- Retirement planning
- College savings
- Down payment savings
- Emergency fund targets

---

## 3. Fee & Tax Impact Analysis

### Fee Impact Simulator (`POST /planning/fee-impact`)

Analyzes the impact of fees and taxes on portfolio growth over time.

**Request:**
```json
{
  "principal": 100000,
  "horizon_years": 20,
  "annual_fee_pct": 1.0,
  "exp_return_pct": 7.0,
  "dividend_withholding_pct": 15.0
}
```

**Response:**
```json
{
  "principal": 100000,
  "horizon_years": 20,
  "annual_fee_pct": 1.0,
  "exp_return_pct": 7.0,
  "dividend_withholding_pct": 15.0,
  "final_with_fee": 298765.43,
  "final_no_fee": 386968.45,
  "delta": 88203.02,
  "delta_pct": 22.79,
  "total_fees_paid": 45678.90,
  "breakdown_with_fee": [
    {"year": 0, "value": 100000, "fee_paid": 0},
    {"year": 1, "value": 105930, "fee_paid": 1070}
  ]
}
```

**Key Insights:**
- Shows exact dollar cost of fees over time
- Compares scenarios with/without fees
- Accounts for dividend withholding tax
- Helps investors understand fee drag on returns

---

## 4. Portfolio Backtesting

### Backtest (`POST /portfolio/backtest`)

Backtests portfolio performance with historical data or simulations.

**Request:**
```json
{
  "weights": {
    "AAPL": 0.5,
    "MSFT": 0.3,
    "GOOGL": 0.2
  },
  "start": "2020-01-01",
  "end": "2024-12-31",
  "rebalance_freq": "quarterly"
}
```

**Response:**
```json
{
  "cagr": 18.45,
  "volatility": 22.35,
  "max_drawdown": 15.67,
  "sharpe_ratio": 0.82,
  "final_value": 15678.90,
  "total_return": 56.79,
  "equity_curve": [
    {"date": "2020-01-03", "value": 10000},
    {"date": "2020-01-10", "value": 10123.45}
  ],
  "summary": "Portfolio returned 18.45% CAGR with 22.35% volatility over 5.0 years...",
  "note": "Simulated backtest (not real historical data)"
}
```

**Metrics:**
- **CAGR**: Compound Annual Growth Rate (annualized return)
- **Volatility**: Annualized standard deviation of returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return (assumes 2% risk-free rate)

**Note:** Currently uses simulated data. Can be extended to fetch real historical prices from yfinance or similar APIs.

---

## 5. Thematic & ESG Portfolios

### Thematic Recommendations (`POST /advice/themes`)

Suggests ETFs based on thematic interests (ESG, clean energy, tech, etc.).

**Request:**
```json
{
  "interest_keywords": ["esg", "clean energy", "technology"]
}
```

**Response:**
```json
{
  "etfs": [
    {
      "ticker": "ESGU",
      "name": "iShares ESG Aware MSCI USA ETF",
      "theme": "ESG",
      "why": "Broad ESG screening with strong corporate governance",
      "source": "Thematic database (esg)"
    },
    {
      "ticker": "ICLN",
      "name": "iShares Global Clean Energy ETF",
      "theme": "Clean Energy",
      "why": "Global renewable energy exposure",
      "source": "Thematic database (clean_energy)"
    },
    {
      "ticker": "QQQ",
      "name": "Invesco QQQ Trust",
      "theme": "Technology",
      "why": "Top NASDAQ-100 tech companies",
      "source": "Thematic database (technology)"
    }
  ],
  "summary": "Found 3 ETF(s) matching themes: esg, clean_energy, technology.",
  "themes_matched": ["esg", "clean_energy", "technology"],
  "keywords_processed": ["esg", "clean energy", "technology"]
}
```

**Supported Themes:**
- **ESG**: Environmental, Social, Governance
- **Clean Energy**: Solar, wind, renewable energy
- **Technology**: Software, semiconductors, innovation
- **Healthcare**: Biotech, pharma, medical devices
- **Dividend**: High dividend yield, dividend growth
- **Emerging Markets**: Developing economies
- **Crypto**: Bitcoin, blockchain-related

---

## 6. Human-in-the-Loop Escalation

### Escalate to Advisor (`POST /advice/escalate`)

Provides escalation message and contact link for regulated advice.

**Request:**
```json
{
  "topic": "tax planning"
}
```

**Response:**
```json
{
  "message": "The topic 'tax planning' may require personalized advice from a licensed financial planner. This chatbot provides general information only and does not constitute financial, legal, or tax advice. For regulated advice tailored to your specific situation, please connect with a licensed professional.",
  "contact_link": "mailto:advisor@example.com?subject=Financial Advice Request: tax planning",
  "topic": "tax planning",
  "disclaimer": "This is an automated response. No fiduciary relationship is established."
}
```

**Use Cases:**
- Tax planning
- Estate planning
- Insurance needs
- Legal advice
- Complex financial situations

**Configuration:**
Set `ADVISOR_CONTACT_EMAIL` in `.env` to customize the contact email.

---

## 7. Behavioral Insights

### Behavior Analysis (`POST /insights/behavior`)

Analyzes user actions and provides behavioral nudges.

**Request:**
```json
{
  "actions": [
    {
      "timestamp": "2025-11-09T10:30:00Z",
      "action": "trade",
      "details": {"ticker": "AAPL", "type": "sell"}
    },
    {
      "timestamp": "2025-11-09T10:35:00Z",
      "action": "query",
      "details": {"query": "should I sell now?"}
    },
    {
      "timestamp": "2025-11-09T10:40:00Z",
      "action": "trade",
      "details": {"ticker": "TSLA", "type": "buy"}
    }
  ]
}
```

**Response:**
```json
{
  "nudges": [
    "🔄 **Over-trading detected**: You've made 12 trades recently. Frequent trading can increase costs and reduce returns. Consider a buy-and-hold strategy for long-term wealth building.",
    "⚠️ **Loss aversion pattern**: Multiple queries about selling or cutting losses. Remember: short-term volatility is normal. Avoid panic selling during market dips unless your investment thesis has fundamentally changed.",
    "⏰ **Market timing risk**: Several queries about optimal timing. Research shows that timing the market is extremely difficult, even for professionals. Consider dollar-cost averaging instead of trying to time entry/exit points."
  ],
  "metrics": {
    "trade_count": 12,
    "loss_aversion_queries": 5,
    "timing_queries": 3,
    "portfolio_checks": 25
  },
  "risk_flags": ["over_trading", "loss_aversion", "timing_risk"],
  "actions_analyzed": 42
}
```

**Behavioral Patterns Detected:**
- **Over-trading**: Excessive trading frequency
- **Loss aversion**: Panic selling during downturns
- **Market timing**: Attempting to time the market
- **Recency bias**: Overreacting to recent price movements

---

## 8. Trust Feedback Loop (FHRI Calibration)

### Submit Feedback (`POST /eval/feedback`)

Collects user feedback to calibrate FHRI weights over time.

**Request:**
```json
{
  "turn_id": "turn_12345",
  "user_rating_1to5": 5
}
```

**Response:**
```json
{
  "ok": true,
  "turn_id": "turn_12345",
  "rating": 5,
  "message": "Feedback received and logged for FHRI calibration"
}
```

**How It Works:**
1. User rates the quality of an LLM response (1-5 stars)
2. Feedback is logged with the corresponding FHRI subscores
3. Over time, the system learns which FHRI components correlate with high user ratings
4. FHRI weights are adjusted via EMA (Exponential Moving Average) smoothing
5. This creates a feedback loop where user trust improves FHRI accuracy

**Privacy:**
- Only anonymous session IDs are stored
- No PII (Personally Identifiable Information) is logged
- Feedback is stored in `logs/fhri_eval/feedback.jsonl`

---

## Multi-Source Data Verification

All endpoints leverage the existing multi-source data aggregator for enhanced reliability:

**Data Sources:**
- **Finnhub**: Primary stock + crypto data
- **Twelve Data**: Stock data fallback
- **yfinance**: Final fallback for stock data
- **FinancialModelingPrep (FMP)**: Fundamentals (P/E, ROE, debt ratios)
- **SEC EDGAR**: Regulatory filings (10-K, 10-Q)
- **CoinGecko**: Cryptocurrency data (free, no API key)

**Caching:**
- In-memory TTL cache (30-60s default)
- Prevents rate limiting
- On-demand fetching (no startup overhead)

---

## Scenario-Aware FHRI

The existing FHRI system now supports **scenario-aware weighting** for all new features:

**Scenarios:**
- `numeric_kpi`: Numeric/directional queries (increased weight on N/D subscore)
- `intraday`: Intraday trading queries (increased weight on temporal subscore)
- `fundamentals`: Fundamental analysis queries (increased weight on grounding)
- `regulatory`: Regulatory/compliance queries (increased weight on citation)
- `advice`: Investment advice queries (balanced weights)
- `multi_ticker`: Multi-asset comparisons (increased grounding weight)
- `news`: News-driven queries (increased temporal weight)
- `default`: General queries (default weights)

**Auto-Detection:**
The system automatically detects the scenario from the query text. Manual override is available via the `scenario_override` parameter in `/ask` endpoint settings.

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/advice/risk-profile` | POST | Compute risk profile from questionnaire |
| `/advice/allocation` | POST | Get ETF allocation by risk profile |
| `/advice/themes` | POST | Get thematic/ESG ETF recommendations |
| `/advice/escalate` | POST | Escalate to human advisor |
| `/planning/goal` | POST | Compute goal-based projections |
| `/planning/fee-impact` | POST | Analyze fee and tax impact |
| `/portfolio/backtest` | POST | Backtest portfolio performance |
| `/insights/behavior` | POST | Analyze user behavior and provide nudges |
| `/eval/feedback` | POST | Submit user feedback for FHRI calibration |

---

## Frontend Integration

All new API functions are exported from `frontend/src/api.js`:

```javascript
import {
  getRiskProfile,
  getPortfolioAllocation,
  getThematicRecommendations,
  escalateToAdvisor,
  planGoal,
  analyzeFeeImpact,
  backtestPortfolio,
  analyzeBehavior,
  submitFeedback
} from './api';

// Example: Risk profiling
const result = await getRiskProfile([
  { question_id: "time_horizon", answer: "10+ years", score: 80 }
]);

// Example: Goal planning
const goalPlan = await planGoal(100000, 10, 5000);

// Example: Submit feedback
await submitFeedback("turn_12345", 5);
```

**Integration Pattern:**
- Call from chat flow when user asks relevant questions
- Display results in existing answer blocks (Markdown)
- No new UI components required
- Fits within current "Analysis / Recommendation" sections

---

## Environment Variables

Add to your `.env` file:

```bash
# Multi-Source Data APIs (optional, for enhanced data verification)
TWELVEDATA_API_KEY=
FMP_API_KEY=
EDGAR_CONTACT_EMAIL=

# Advisory Services
ADVISOR_CONTACT_EMAIL=advisor@example.com  # Email for human advisor escalation
```

---

## Logging & Evaluation

All new features automatically log metrics to the existing evaluation system:

**Logged Metrics:**
- Risk profile distribution (Conservative/Balanced/Aggressive)
- Average fee impact across queries
- Backtest statistics (CAGR, Sharpe, volatility)
- Behavioral risk flags frequency
- User feedback ratings (1-5)
- FHRI scores before/after user feedback

**Log Locations:**
- FHRI evaluation: `logs/fhri_eval/fhri_eval_*.csv`
- User feedback: `logs/fhri_eval/feedback.jsonl`
- Server logs: Standard Python logging (INFO level)

**Evaluation Scripts:**
Use existing evaluation scripts to aggregate data:

```bash
# Generate correlation plots
python scripts/analyze_fhri.py

# Export metrics
python scripts/export_metrics.py
```

---

## Acceptance Criteria

✅ **No visual layout or navigation changes** to current interface
✅ **All features callable from chat** (Markdown summaries fit inside existing answer blocks)
✅ **Settings page gets only minimal toggles** (no new pages)
✅ **Live data remains on-demand** (app startup unaffected)
✅ **FHRI and contradiction remain visible** as today; internal calibration updated
✅ **Backend-only implementation** (minimal client hooks)
✅ **Existing UI components reused** (panels/accordions/tabs)

---

## Testing

### Quick API Tests

```bash
# Start server
uvicorn src.server:app --port 8000

# Test risk profiling
curl -X POST http://127.0.0.1:8000/advice/risk-profile \
  -H "Content-Type: application/json" \
  -d '{"answers": [{"question_id": "risk", "answer": "high", "score": 80}]}'

# Test goal planning
curl -X POST http://127.0.0.1:8000/planning/goal \
  -H "Content-Type: application/json" \
  -d '{"target_amount": 100000, "years": 10, "init_capital": 5000}'

# Test backtest
curl -X POST http://127.0.0.1:8000/portfolio/backtest \
  -H "Content-Type: application/json" \
  -d '{"weights": {"AAPL": 0.5, "MSFT": 0.5}, "start": "2020-01-01", "end": "2024-12-31"}'

# Test feedback
curl -X POST http://127.0.0.1:8000/eval/feedback \
  -H "Content-Type: application/json" \
  -d '{"turn_id": "test_123", "user_rating_1to5": 5}'
```

### Interactive Testing

Visit API docs: http://127.0.0.1:8000/docs

All endpoints are documented with OpenAPI/Swagger for interactive testing.

---

## Future Enhancements

Potential improvements (not implemented):

1. **Real Historical Data for Backtesting**: Integrate yfinance or Alpha Vantage for actual price history
2. **Monte Carlo Simulations**: Add probabilistic projections for goal planning
3. **Tax-Loss Harvesting**: Identify opportunities to offset capital gains
4. **Portfolio Rebalancing Alerts**: Notify when allocation drifts from target
5. **ESG Scoring Integration**: Fetch real-time ESG scores from data providers
6. **Robo-Advisor Autopilot**: Automated portfolio management based on risk profile

---

## Support

For questions or issues:
- Check server logs: Look for errors in console output
- Review API docs: http://127.0.0.1:8000/docs
- Verify environment variables: Ensure all required keys are set in `.env`
- Test endpoints individually: Use curl or Postman to isolate issues

---

## License

Same as the main llm-fin-chatbot project.
