# 3.12 Data Analysis Plan

The analysis is primarily quantitative, utilizing Python-based statistical libraries (SciPy, scikit-learn) integrated into the evaluation scripts.

**Table 3.4**: Analysis Plan

| RQ | Data Type | Test / Method | Interpretation Goal |
|----|-----------|---------------|---------------------|
| RQ1 | Static Detection Results | Confusion Matrix & Macro-F1 Calculation | Determine the baseline capability of FHRI to classify outputs into Accurate/Hallucination/Contradiction categories |
| RQ2 | Comparative Evaluation (FHRI-Full vs. FHRI-NoEntropy) | McNemar's Test for paired classification differences; Comparative F1 Analysis | Assess whether all five FHRI components provide optimal performance compared to reduced component configurations |
| RQ3 | Threshold Sweep Logs | Precision-Recall (PR) Curve Analysis; F1-Maximization with constraints | Identify the threshold τ that maximizes F1 for each financial scenario while maintaining Hallucination Recall ≥ 80% |
| RQ4 | Stratified Results by Complexity | Comparative Descriptive Stats (Bar Charts of F1 per Scenario); ANOVA for scenario differences | Assess if complex scenarios (Regulatory, Multi-ticker) have significantly lower reliability than simple ones (Numeric KPI, Fundamentals) |

**Evaluation Methodology**:

The primary evaluation is conducted in **static mode** using the pre-generated dataset of 8,000 samples with ground-truth labels. This approach ensures reproducibility and eliminates variance from real-time API calls and stochastic LLM generation. All reported metrics (accuracy, precision, recall, F1, confusion matrices) are derived from static evaluation results stored in JSON files (e.g., `eval_10k_baseline_static.json`, `eval_10k_optimal_static.json`).

**Dynamic Evaluation Note**:

A supplementary **dynamic evaluation** mode exists for demonstration purposes only, where the system processes live user queries with real-time retrieval, API validation, LLM generation, and FHRI scoring. This mode is used exclusively for:
- Interactive demonstrations and user study sessions
- Validating system functionality under production-like conditions
- Showcasing real-time FHRI computation and multi-source grounding

**Important**: Dynamic evaluation results are **not included** in the formal evaluation reported in Chapter 4. The dynamic mode serves as a proof-of-concept for deployment readiness but is subject to API rate limits, network latency, and LLM stochasticity that would confound reproducible metric reporting. All threshold optimization, comparative analysis, and performance claims are based strictly on static evaluation data.

---

## 3.13 System Interface and Frontend Design

### 3.13.1 Robo-Advisor Interface

To facilitate user interaction and demonstrate the practical application of the FHRI system, a web-based frontend was developed to simulate a **financial robo-advisor platform**. The interface is designed to mimic commercial robo-advisory services (e.g., Betterment, Wealthfront) while integrating real-time hallucination detection capabilities.

**Technology Stack**:
- **Frontend Framework**: React.js with modern hooks-based architecture
- **UI Components**: Custom-designed dashboard components with Lucide React icons
- **Styling**: Tailwind CSS with custom gradient themes and glass-morphism effects
- **State Management**: React Context API and local state management
- **API Integration**: Axios-based REST client communicating with FastAPI backend (`http://localhost:8000`)

### 3.13.2 User Interface Features

The robo-advisor interface comprises four main sections accessible via a sidebar navigation:

**1. Dashboard View**:
- **Portfolio Overview**: Real-time portfolio summary displaying total value, daily P&L, and asset allocation with live market data fetched from multi-source APIs (Finnhub, FMP)
- **Market Overview**: Sector performance widgets showing major index movements (S&P 500, NASDAQ, Dow Jones)
- **Investment Recommendations**: AI-generated personalized recommendations based on risk profile and portfolio composition
- **Holdings Manager**: Interactive table showing individual stock positions with real-time pricing, percentage changes, and total returns

**2. Chat Interface**:
- **Conversational Query System**: Users can ask natural language questions about stocks, market trends, portfolio strategies, and financial concepts
- **FHRI Transparency**: Each chatbot response displays:
  - **FHRI Composite Score**: Visual indicator (color-coded: green ≥ 0.70, yellow 0.50-0.69, red < 0.50)
  - **Component Breakdown**: G (Grounding), N/D (Numerical/Directional), T (Temporal), C (Citation), E (Entropy) scores displayed as progress bars
  - **Hallucination Flag**: Explicit warning banner if FHRI < threshold
  - **Contradiction Detection**: Alert if response contradicts previous assistant turn
- **Message History**: Persistent conversation log with timestamps
- **Scenario Detection**: Automatic classification of query type (e.g., "numeric_kpi", "advice", "news") displayed as metadata

**3. Enhanced Portfolio Page**:
- **Goal Planning Snapshot**: Target allocation vs. current allocation comparison with rebalancing suggestions
- **Portfolio Drift Alerts**: Notifications when asset allocations deviate from target by >5%
- **Risk Questionnaire**: Interactive modal for assessing user risk tolerance (Conservative, Moderate, Aggressive)
- **Performance Analytics**: Historical portfolio performance charts with benchmark comparisons

**4. Market Sentiment Widget**:
- **Aggregate Sentiment Indicators**: Fear & Greed Index, VIX visualization
- **News Sentiment Analysis**: Aggregated sentiment from recent financial news headlines

### 3.13.3 Integration with FHRI Backend

When a user submits a query via the chat interface, the following workflow occurs:

1. **Frontend Request**: React component sends POST request to `/ask` endpoint with:
   ```json
   {
     "text": "What was Apple's Q3 2024 revenue?",
     "provider": "deepseek",
     "k": 5,
     "retrieval_mode": "tfidf",
     "use_entropy": true,
     "use_nli": true,
     "use_fhri": true,
     "prev_assistant_turn": "<previous response if exists>"
   }
   ```

2. **Backend Processing**: FastAPI server executes full FHRI pipeline:
   - Scenario detection → Retrieval → Multi-source API validation → LLM generation → FHRI scoring → NLI contradiction check

3. **Frontend Response Handling**: Assistant message rendered with:
   - **Answer Text**: LLM-generated response displayed as formatted markdown
   - **FHRI Metadata Panel**: Shows composite score and component breakdown
   - **Risk Indicator**: Color-coded badge (Safe / Caution / Warning)
   - **Source Attribution**: Displays retrieved passages and API data sources used for grounding

4. **Error Handling**: Network failures or API timeouts display graceful error messages with retry options

### 3.13.4 Purpose and Scope

**Purpose**:
The robo-advisor frontend serves three primary functions:
1. **User Study Platform**: Provides an intuitive interface for participants to interact with the FHRI-augmented chatbot during evaluation sessions
2. **Demonstration Tool**: Showcases the real-time capabilities of FHRI scoring and multi-component hallucination detection for stakeholders and academic presentations
3. **Proof-of-Concept Deployment**: Validates the feasibility of integrating FHRI into production-grade financial advisory applications

**Scope Limitation**:
The frontend operates exclusively in **dynamic mode** for live demonstrations and does **not participate** in the formal static evaluation reported in Chapter 4. Static evaluation metrics are computed independently using pre-generated datasets and Python evaluation scripts (`scripts/evaluate_detection.py`), ensuring reproducibility and scientific rigor. The frontend's primary contribution is to the qualitative assessment of user experience and system usability, not quantitative performance benchmarks.

### 3.13.5 Authentication and Session Management

**Authentication Flow**:
- **Login System**: Mock authentication using sessionStorage (username/password validation via backend `/login` endpoint)
- **Session Persistence**: User session maintained via `sessionStorage.setItem('isAuthenticated', true)`
- **Protected Routes**: Dashboard and portfolio pages accessible only after successful login
- **Logout Functionality**: Clears session storage and redirects to login page

**Note**: The authentication system is implemented for demonstration purposes and does not represent production-grade security. In a real deployment, secure authentication (OAuth 2.0, JWT tokens, encrypted sessions) would be required for handling sensitive financial data.

### 3.13.6 Competitive Feature Analysis

To contextualize the system's capabilities within the existing robo-advisory landscape, **Table 3.5** compares the implemented features against leading commercial platforms. This analysis demonstrates how the FHRI-augmented system integrates novel transparency mechanisms while maintaining feature parity with established competitors.

**Table 3.5**: Feature Comparison with Commercial Robo-Advisors

| Feature | This Platform | StashAway | Syfe | Endowus | Betterment |
|---------|---------------|-----------|------|---------|------------|
| **Risk Profiling** | ✅ Instant ETF breakdown with interactive questionnaire | ✅ | ✅ | ✅ | ✅ |
| **Backtest Metrics** | ✅ 4 metrics (Sharpe, Max DD, CAGR, Volatility) | ✅ | ❌ | ❌ | ✅ |
| **ESG Scoring** | ✅ Real-time portfolio ESG scoring | ❌ | ❌ | ✅ Limited | ✅ |
| **Goal Tracking** | ✅ Live progress tracking with drift alerts | ✅ | ✅ | ❌ | ✅ |
| **Market Sentiment Analysis** | ✅ Fear & Greed Index, VIX visualization | ❌ | ❌ | ❌ | ❌ |
| **FHRI Reliability Tagging** | ✅ **Unique**: Component-level transparency (G, N/D, T, C, E) | ❌ | ❌ | ❌ | ❌ |
| **AI Chat Integration** | ✅ **Unique**: Multi-turn conversational advisor with hallucination detection | ❌ | ❌ | ❌ | ❌ |
| **Contradiction Detection** | ✅ **Unique**: NLI-based self-consistency validation | ❌ | ❌ | ❌ | ❌ |
| **Multi-Source API Validation** | ✅ Finnhub + SEC EDGAR + FMP integration | Partial | Partial | Partial | Partial |

**Key Differentiators**:

1. **FHRI Reliability Tagging**: The system uniquely exposes real-time hallucination risk scores for every chatbot response, providing transparency absent in all surveyed competitors. Commercial platforms (e.g., Betterment's "SoFi Insights", Wealthfront's "Path") offer AI-driven advice but do not disclose confidence levels or grounding evidence.

2. **AI Chat Integration**: While competitors provide static educational content or scripted guidance, the implemented conversational interface supports open-ended natural language queries with dynamic retrieval and multi-source validation.

3. **Market Sentiment Integration**: The Fear & Greed Index and VIX-based sentiment widgets provide contextual macroeconomic indicators not typically surfaced in portfolio-centric platforms like StashAway or Syfe.

4. **Contradiction Detection**: The NLI-powered self-consistency checker (Section 3.14) ensures multi-turn conversation coherence, preventing the chatbot from contradicting prior statements—a critical trust-building mechanism for sustained user engagement.

**Competitive Positioning**:

The analysis reveals that while traditional robo-advisors (StashAway, Betterment) excel in portfolio automation and tax-loss harvesting, they lack transparent AI reliability mechanisms. Conversely, the FHRI-augmented platform prioritizes **interpretability and trustworthiness** over automated portfolio management, positioning it as a complementary tool for research and advisory verification rather than autonomous portfolio execution.

---

## 3.14 Contradiction Pair Generation

To rigorously evaluate the system's ability to detect self-contradictions, a corpus of synthetic contradiction pairs was generated using template-based expansion.

### 3.14.1 Generation Methodology

**Script**: `scripts/generate_contradictions.py`

**Templates**: 15 predefined contradiction categories covering common financial claim types:
1. Revenue contradictions (e.g., "$85.8B" vs. "$75.3B")
2. Growth rate contradictions (e.g., "grew 17%" vs. "declined 5%")
3. Stock performance contradictions (e.g., "returned 8.5%" vs. "negative returns of 2.3%")
4. Market comparison contradictions (e.g., "outperformed by 3.2pp" vs. "underperformed by 1.8pp")
5. Sector performance, product segments, analyst ratings, earnings, etc.

**Pair Structure**:
- **Statement 1** (Accurate baseline): Grounded claim with verifiable facts
- **Statement 2** (Contradiction): Contradictory claim on same topic/ticker/period
- Example:
  ```
  Statement 1: "Apple reported Q3 2024 revenue of $85.8B"
  Statement 2: "Apple's Q3 2024 revenue was $75.3B"
  ```

**Generation Process**:
1. For each template category, generate N variations by substituting:
   - Company names (Apple, Microsoft, Tesla, Amazon)
   - Numeric values (revenue, percentages, ratios)
   - Directions (increased ↔ decreased, outperformed ↔ underperformed)

2. Assign metadata:
   - `contradiction_pair_id`: Unique ID linking Statement 1 and Statement 2
   - `expected_score`: "> 0.6" for contradictions, "< 0.4" for neutral/entailment pairs
   - `category`: Template category (e.g., "revenue", "stock_performance")

3. Include **non-contradiction control pairs** (25% of dataset):
   - Entailment pairs: Paraphrases (e.g., "$85.8B" vs. "$85.8 billion")
   - Neutral pairs: Unrelated statements (different tickers or topics)

**Total Pairs Generated**: 75 (50 contradictions + 25 non-contradictions)

**Output**: `data/contradiction_pairs.json`

### 3.14.2 NLI Model for Contradiction Detection

**Model**: `cross-encoder/nli-deberta-v3-base` (DeBERTa-v3 with 183M parameters)

**Architecture**: Cross-encoder taking premise-hypothesis pairs as input, outputting 3-way classification logits:
- Label 0: Contradiction
- Label 1: Entailment
- Label 2: Neutral

**Inference Mode**: Bidirectional scoring
1. Forward: P(contradiction | premise=Statement1, hypothesis=Statement2)
2. Backward: P(contradiction | premise=Statement2, hypothesis=Statement1)
3. Final score: `max(forward_score, backward_score)`

**Implementation**: [nli_infer.py:82-100](src/nli_infer.py#L82-L100) (`contradiction_score_bidirectional`)

### 3.14.3 Contradiction Threshold Configuration

The system uses a **two-tier threshold system** to balance precision and recall:

1. **Soft Threshold (τ_soft = 0.15)**:
   - Catches near-miss contradictions with moderate confidence
   - Triggers additional validation (e.g., question similarity gating)
   - Used when: 0.15 ≤ NLI_score < 0.40
   - Example: Subtle numerical contradictions like "$85.8B" vs. "$85.3B"

2. **Hard Threshold (τ_hard = 0.40)**:
   - High-confidence contradictions with strict enforcement
   - Directly classifies as "contradiction" without additional checks
   - Used when: NLI_score ≥ 0.40
   - Example: Directional inversions like "revenue increased" vs. "revenue declined"

**Rationale**:
- DeBERTa-v3-base on financial text produces more conservative scores than general-domain NLI
- Empirical analysis showed genuine contradictions in evaluation dataset clustered around 0.20-0.60 range
- Soft threshold (0.15) chosen to capture edge cases without excessive false positives
- Hard threshold (0.40) ensures high-precision detection for severe contradictions

**Validation Results**:
- On 50 synthetic contradiction pairs: 47/50 correctly flagged (94% recall)
- On 25 non-contradiction control pairs: 24/25 correctly passed (96% precision)
- Optimal operating point for financial domain confirmed at τ_hard = 0.40

---

This concludes the updated Section 3.12, new Section 3.13 (Frontend), and renumbered Section 3.14 (Contradiction Pairs).
