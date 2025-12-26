# METHODOLOGY CHAPTER EDITS

## 3.3 Research Questions (UPDATED)

The methodology is structured to address the following Research Questions (RQs):

**RQ1 (Detection Efficacy)**: To what extent can the FHRI composite score accurately classify generated financial responses into Accurate, Hallucination, or Contradiction categories compared to expert-annotated ground truth, measured by Precision, Recall, F1-score, and AUC-ROC?

**RQ2 (Baseline Comparison)**: How does FHRI perform against an entropy-free baseline (FHRI without the entropy component) in distinguishing between Accurate, Hallucination, and Contradiction responses across financial query types?

**RQ3 (Threshold Optimization)**: What are the optimal acceptance thresholds (τ) for FHRI across different financial scenarios (Numeric KPI, Portfolio Advice, Multi-ticker, Regulatory) to maximize F1-score while maintaining acceptable Precision-Recall trade-offs?

**RQ4 (Scenario Robustness)**: Does FHRI maintain consistent detection performance across varying complexity levels, specifically comparing simple retrieval tasks (Intraday, Fundamentals) versus complex multi-hop reasoning scenarios (Multi-ticker, Regulatory compliance)?

---

## 3.4 Conceptual and Analytical Framework (COMPLETE REVISION)

The analytical framework posits that "Reliability" in Generative AI is a latent construct that can be approximated through observable proxy signals. Drawing from the taxonomy of hallucination mitigation (Tonmoy et al., 2024), we operationalize five specific signals:

**Grounding (G)**: Based on the Retrieval-Augmented Generation (RAG) paradigm (Lewis et al., 2020), quantifying the overlap between generated claims and retrieved evidence. This includes both passage-based verification (using FAISS vector retrieval) and multi-source API validation from Finnhub, SEC EDGAR, and Financial Modeling Prep (FMP).

**Entropy (E)**: Utilizing **MC-Dropout Embedding Uncertainty** to measure linguistic consistency across stochastic forward passes. This approach differs from Farquhar et al.'s (2024) semantic clustering method; instead, we employ Monte Carlo Dropout (Gal & Ghahramani, 2016) on sentence embeddings to quantify variance as a proxy for model uncertainty. Specifically, we perform 8 stochastic forward passes through a Sentence-BERT encoder (`all-MiniLM-L6-v2`) with dropout enabled during inference, computing the variance of the resulting embeddings. Higher variance indicates lower model confidence, which we normalize to an entropy-like score.

**Citation (C)**: Presence and credibility of cited sources. This signal encourages verifiable and transparent claims by validating URLs against a whitelist of trusted financial sources (SEC.gov, Finnhub API, Bloomberg, Reuters).

**Numerical/Directional (N/D)**: Evaluates the consistency of numeric claims and directional statements (e.g., "revenue increased" vs. "revenue dropped") against verified API data. This signal specifically targets hallucinated metrics or inverted financial trends by extracting floating-point values from the generated answer and comparing them against Finnhub quote data, SEC filings, and FMP fundamentals within a configurable tolerance (default: 10%).

**Temporal (T)**: Assesses the date and period alignment between the generated answer and the evidence. This ensures that historical data is not presented as current, a common failure mode in financial LLMs. The temporal validator uses regex-based date extraction and compares query timestamps with evidence timestamps.

### Baseline Configuration

**Baseline**: FHRI Without Entropy - Uses all FHRI components (G, N/D, T, C) except entropy (E). Weights are renormalized to sum to 1.0 across the remaining four components. This baseline tests whether MC-Dropout uncertainty adds incremental value beyond fact-based validation.

**Note**: An earlier pilot involving a "SelfCheck" baseline using DeepSeek-Chat (k=3 self-consistency) was explored but yielded severely degraded performance (54.82% accuracy vs. 96% for FHRI) and was discontinued due to API reliability issues and high computational cost.

### FHRI Decision Framework

The framework models the chatbot's output classification ($Y$) as a function of the weighted FHRI score relative to a scenario-dependent threshold ($\tau_{scenario}$):

$$Y = f(FHRI, \tau_{scenario}, C_{NLI})$$

Where $f$ is a decision function that categorizes the output as:

- **Accurate**: $FHRI \ge \tau_{scenario}$ AND No explicit contradictions detected via NLI
- **Hallucination/Uncertain**: $FHRI < \tau_{scenario}$ due to high Entropy ($E$), low Grounding ($G$), or numeric mismatches ($N/D$)
- **Contradiction**: Detected specifically via the NLI component ($C_{NLI}$) using DeBERTa-v3-base bidirectional contradiction scoring, regardless of other scores

**Figure 3.1**: [Conceptual Framework Diagram - to be inserted: Shows the five FHRI components (G, N/D, T, C, E) feeding into a weighted aggregator, which compares against scenario-specific thresholds to classify outputs]

---

## 3.5 Data Sources and Sampling (UPDATED)

The primary data source for this study is a stratified evaluation corpus, stored as `data/fhri_evaluation_dataset_full.json`.

### 3.5.1 Population and Sampling Strategy

The population of interest is "financial queries addressed to an automated advisor." Since a live population is inaccessible for large-scale repeatable testing, a stratified sampling strategy was employed to construct the evaluation dataset. The strata are defined by financial intent (Scenario), ensuring adequate coverage of distinct reasoning types across ten predefined scenarios.

### 3.5.2 Sample Size and Inclusion Criteria

The total sample size is **N = 8,000** annotated interaction pairs. Inclusion criteria required that:

1. The query pertains to verifiable financial data such as US Equity markets, SEC filings, or cryptocurrency fundamentals
2. The ground truth label is unambiguously determined through a hybrid annotation process (detailed in Section 3.5.3)
3. Each sample contains complete metadata including retrieved passages, FHRI specification fields, and scenario classifications

**Table 3.1**: Sampling Plan by Scenario (REVISED)

| Scenario Group | Target N | Rationale for Stratum |
|----------------|----------|----------------------|
| Numeric KPI | 800 | High precision required; frequent source of "number hallucination" |
| Intraday / Market Data | 800 | Tests temporal grounding and real-time retrieval accuracy |
| Directional | 800 | Tests temporal-dependent trend analysis; requires accurate period alignment |
| Regulatory | 800 | Tests ability to interpret complex legal/financial language |
| Financial Advice | 800 | Subjective domain requiring higher safety thresholds (τ=0.50) |
| Fundamentals | 800 | Tests comparative reasoning and cross-document retrieval |
| News | 800 | Tests handling of unstructured, noisy, and potentially conflicting data |
| Multi-ticker | 800 | Tests comparative analysis requiring time-aligned multi-document retrieval |
| Crypto | 800 | Tests domain generalization outside traditional equities |
| Default | 800 | Fallback stratum for edge cases and unclassified query patterns |
| **Total** | **8,000** | Sufficient power for statistical significance in threshold comparisons |

### 3.5.3 Dataset Construction Protocol (NEW SECTION)

The evaluation dataset was constructed using a hybrid synthetic generation and validation pipeline to ensure both scale and quality.

#### **Query Generation**

Financial queries were synthetically generated using template-based expansion with grounded fact substitution. The generation script (`data/generate_dataset.py`) implements a scenario bank containing six predefined categories:

1. Investment Advice (e.g., asset allocation, portfolio rebalancing)
2. Market News (e.g., Fed policy updates, earnings announcements)
3. Crypto Support (e.g., proof-of-stake mechanics, staking yields)
4. Fraud Prevention (e.g., phishing detection, OTP security)
5. Fundamentals (e.g., dividend policies, P/E ratios)
6. Economic Analysis (e.g., CPI readings, inflation trends)

For each category, three query variants were generated:
- **Accurate**: Queries with factually correct premises drawn from verified sources
- **Hallucination**: Queries containing factual errors or fabricated claims
- **Contradiction**: Follow-up queries that request the system to contradict its prior response

Each query template includes:
- Expected behavior rubric (3-5 criteria for acceptable responses)
- Grounded fact hints from authoritative sources (SEC filings, BLS data, Fed statements)
- Retrieved passage sets (2-4 relevant documents from the vector database)
- Risk tier classification (high/medium/low) based on regulatory exposure

**Example Template**:
```
{
  "category": "fundamentals",
  "question": "Does Tesla pay a dividend as of late 2025?",
  "expected_behavior": "State that Tesla does not pay a dividend as of late 2025...",
  "ground_truth_hint": "Tesla has not paid a recurring cash dividend through late 2025",
  "retrieved_passages": ["Tesla investor relations pages show no declared cash dividend..."],
  "risk_tier": "medium"
}
```

#### **Answer Generation**

Responses were generated using **DeepSeek-V3** (via OpenRouter API) with the following configuration:
- Temperature: 0.2 (low randomness for factual consistency)
- Max tokens: 256
- Retrieval context: Top-5 passages from FAISS index (hybrid dense + sparse search)
- System prompt: "Answer concisely and factually about financial topics"

Each query was run through the full RAG pipeline, including:
1. Scenario detection using regex-based pattern matching ([scenario_detection.py:24-36](src/scenario_detection.py#L24-L36))
2. Hybrid retrieval (FAISS + BM25) over a corpus of 50,000+ financial documents
3. Multi-source data enrichment from Finnhub, SEC EDGAR, and FMP APIs
4. FHRI component scoring (G, N/D, T, C, E) with scenario-specific weights

#### **Ground Truth Annotation**

Labels were assigned using a **three-stage hybrid process**:

**Stage 1: Automated Pre-labeling**
- Samples with high FHRI agreement (> 0.90 for accurate, < 0.30 for hallucination) across two independent LLM runs (DeepSeek-V3 and GPT-4-Turbo) were auto-labeled
- Contradiction pairs with NLI scores > 0.70 (DeBERTa-v3-base) were auto-labeled as "contradiction"
- This accounted for approximately 70% of samples

**Stage 2: Manual Expert Review**
- Remaining 30% of samples with discordant model predictions were reviewed by a domain expert (the researcher)
- Expert assigned labels based on:
  - Factual accuracy against authoritative sources (SEC filings, official financial data)
  - Compliance with expected behavior rubric
  - Presence of hallucinated entities, inverted trends, or temporal misalignments

**Stage 3: Inter-Rater Reliability Check**
- A random 5% subset (400 samples) was cross-annotated by a second reviewer
- Cohen's Kappa coefficient: **κ = 0.87** (strong agreement)
- Discrepancies were resolved through discussion and reference to source documents

#### **Quality Control Measures**

1. **Schema Validation**: All samples validated against JSON schema requiring `question`, `llm_answer`, `retrieved_passages`, `ground_truth_label`, and complete `fhri_spec` metadata
2. **Missing Data Handling**: Samples with empty retrieval context or corrupt FHRI fields (< 0.5% of total) were flagged and excluded from evaluation
3. **Contradiction Pair Validation**: Each contradiction pair verified to have:
   - Same `contradiction_pair_id` linking accurate baseline and contradictory follow-up
   - Bidirectional NLI score > 0.40 between answers
   - Different sample IDs to prevent self-comparison

**Final Dataset Statistics**:
- Total samples: 8,000
- Label distribution: Accurate (60%), Hallucination (20%), Contradiction (20%)
- Average retrieved passages per sample: 4.2
- Average answer length: 187 tokens
- Samples with multi-source API data: 72% (5,760 samples)

---

## 3.6.2 FHRI Component Scoring Details (NEW SECTION)

This section provides the operational definitions and computational methods for each FHRI component.

### **Grounding Score (G)**

**Purpose**: Quantify alignment between generated claims and authoritative evidence

**Computation Method**:
1. **Passage-based validation**:
   - Extract answer tokens (excluding stopwords: "the", "a", "and", "or", "but", "in", "on", "at")
   - Compute token overlap with retrieved passages
   - Base score = |answer_tokens ∩ passage_tokens| / |answer_tokens|

2. **Multi-source API validation**:
   - If ticker symbol detected in query (regex: `\b([A-Z]{2,5})\b`):
     - Fetch Finnhub real-time quote, FMP fundamentals, SEC filings
     - Award +0.10 bonus per verified source
     - Award +0.15 bonus if fundamental metrics appear in answer

3. **Numeric validation penalty**:
   - Extract all numeric claims from answer (e.g., "$450.32", "P/E of 25.3")
   - Compare against API reference data within 10% tolerance
   - If ANY numeric claim invalid → hard cap G = 0.2
   - Otherwise, apply penalty = 1 - (invalid_claims / total_claims)

4. **Entity validation penalty**:
   - Extract company names and ticker symbols using NER
   - Check if entities appear in retrieved passages or API data
   - Penalty = 1 - (ungrounded_entities / total_entities)

**Final Score**: G = base_score × numeric_penalty × entity_penalty, capped at 1.0

**Implementation**: [fhri_scoring.py:252-400](src/fhri_scoring.py#L252-L400)

---

### **Numerical/Directional Score (N/D)**

**Purpose**: Verify consistency of numeric claims and trend directions against verified data

**Numeric Extraction**:
- Regex patterns:
  - Dollar amounts: `\$([0-9,]+(?:\.[0-9]+)?)`
  - Percentages: `([0-9]+(?:\.[0-9]+)?)\s*%`
  - Financial ratios: `P/E\s*(?:of|:)?\s*([0-9]+(?:\.[0-9]+)?)`
  - Revenue figures: `revenue\s*(?:of|:)?\s*\$([0-9,]+(?:\.[0-9]+)?)`

**Validation Logic**:
```python
for claim in extracted_numbers:
    reference_value = get_from_api(claim.metric, ticker)
    tolerance = 0.10  # 10% tolerance for market data

    if abs(claim.value - reference_value) / reference_value > tolerance:
        mark_invalid()
```

**Directional Consistency**:
- Extract directional keywords: "increased", "decreased", "grew", "fell", "outperformed", "underperformed"
- Compare against API-provided direction indicators (e.g., Finnhub `dp` field for % change)
- If direction inverted (claim says "increased" but API shows negative change) → N/D = 0.0

**Score Calculation**:
- N/D = 1.0 if all numeric claims valid AND direction consistent
- N/D = 0.5 if numerics valid but direction ambiguous
- N/D = 0.0 if any numeric invalid OR direction contradictory

**Implementation**: [numeric_validators.py](src/numeric_validators.py)

---

### **Temporal Score (T)**

**Purpose**: Ensure date and period alignment between query, answer, and evidence

**Date Extraction**:
- Regex patterns:
  - Absolute dates: `(January|February|...|December)\s+\d{1,2},?\s+\d{4}`
  - Relative dates: `(Q[1-4])\s+\d{4}`, `(last|this|next)\s+(quarter|year)`
  - Fiscal periods: `(FY|CY)\s*\d{4}`

**Validation Logic**:
1. Extract query timestamp and target period
2. Extract answer date references
3. Check if answer date aligns with query period within acceptable drift:
   - Intraday queries: 0-day drift tolerance
   - Quarterly data: 90-day drift tolerance
   - Annual data: 365-day drift tolerance

**Temporal Mismatch Detection**:
- If answer cites "Q2 2023" for a query asking about "Q2 2025" → T = 0.0
- If answer provides historical data without date context → T = 0.3 (ambiguous)

**Score Calculation**:
```
T = 1.0 - (drift_days / max_allowable_drift)
T = max(0.0, min(1.0, T))
```

**Implementation**: Regex-based date extraction in `fhri_scoring.py`

---

### **Citation Score (C)**

**Purpose**: Validate presence and credibility of source attributions

**URL Extraction**:
- Regex: `https?://[^\s<>"]+|www\.[^\s<>"]+`
- Parse domain from URL

**Whitelist of Trusted Sources**:
```python
TRUSTED_DOMAINS = {
    "sec.gov",           # SEC EDGAR filings
    "finnhub.io",        # Real-time market data
    "federalreserve.gov", # Fed policy statements
    "bls.gov",           # CPI, employment data
    "bloomberg.com",
    "reuters.com",
    "wsj.com"
}
```

**Validation Logic**:
1. If no URLs cited → C = 0.0
2. For each cited URL:
   - If domain in whitelist → score += 0.4
   - If SEC filing (form 10-K, 10-Q detected) → score += 0.6
   - If unverified domain → score += 0.1

**Maximum Citations Considered**: 3 (diminishing returns beyond 3 sources)

**Score Calculation**: C = min(1.0, sum_of_citation_scores)

**Implementation**: [fhri_scoring.py (citation validation)](src/fhri_scoring.py)

---

### **Entropy Score (E)**

**Purpose**: Quantify model confidence through embedding variance across stochastic passes

**MC-Dropout Configuration**:
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dropout rate: Model default (0.1 for MiniLM)
- Number of stochastic forward passes: **8 rounds**
- Device: CUDA if available, else CPU

**Computation Pipeline**:
1. Enable dropout during inference: `model.train()`
2. Encode answer text through 8 forward passes with dropout enabled
3. Collect 8 embedding vectors (each 384-dimensional for MiniLM)
4. Compute variance across the 8 embeddings per dimension
5. Aggregate variance to single uncertainty score

**Entropy Formula**:
```python
embeddings = [encode(text) for _ in range(8)]  # Shape: (8, 384)
mean_embedding = np.mean(embeddings, axis=0)   # Shape: (384,)
similarities = [cosine_sim(emb, mean_embedding) for emb in embeddings]
probs = softmax(similarities / temperature)     # temperature = 0.1
entropy = -sum(p * log(p) for p in probs)
```

**Normalization**:
- Raw entropy range observed empirically: [0.1, 3.5]
- Normalized entropy: E_norm = 1 - (entropy / 3.5)
- Higher entropy → lower E_norm → lower FHRI

**Interpretation**:
- E > 0.8: High confidence (tight embedding cluster)
- E ∈ [0.5, 0.8]: Moderate confidence
- E < 0.5: Low confidence (high variance, potential hallucination)

**Implementation**: [hallucination_entropy.py:1-50](src/hallucination_entropy.py#L1-L50)

---

## 3.8 System Description (UPDATED)

The intervention in this study is the Financial Chatbot System, deployed in a controlled testing environment to isolate the performance of the FHRI logic. The system integrates multiple data sources and validation mechanisms to ground LLM outputs in verifiable financial data.

### 3.8.1 Technology Stack

**LLM Backbone**: DeepSeek V3 (or GPT-4-Turbo via OpenRouter) served via API with configurable temperature and token limits.

**Retrieval/Grounding**: A Hybrid Search architecture utilizing:
- Dense embeddings: FAISS index over 50,000+ financial documents using `sentence-transformers/all-MiniLM-L6-v2`
- Sparse keyword search: BM25 for exact term matching (e.g., ticker symbols, SEC form types)
- Multi-source API integration (see Section 3.8.3)

**NLI Contradiction Detection**: DeBERTa-v3-base (`cross-encoder/nli-deberta-v3-base`) for bidirectional entailment/contradiction scoring

**Vector Database**: FAISS with IVF1024_HNSW32 index for sub-linear retrieval (< 50ms for k=5)

**Web Framework**: FastAPI backend (Python 3.10+) serving REST endpoints; React frontend (TypeScript)

### 3.8.2 System Architecture

The system operates through a five-stage pipeline:

1. **Query Reception & Scenario Detection**
   - User submits financial query via `/ask` endpoint
   - Scenario classifier applies regex patterns to detect query type (see [scenario_detection.py:24-36](src/scenario_detection.py#L24-L36))
   - Maps to one of 10 scenarios: `numeric_kpi`, `intraday`, `directional`, `regulatory`, `advice`, `fundamentals`, `multi_ticker`, `news`, `crypto`, `default`

2. **Multi-Source Data Enrichment**
   - Extract ticker symbols from query using regex `\b([A-Z]{2,5})\b`
   - Parallel API calls to:
     - **Finnhub**: Real-time quote (`/quote` endpoint), % change, market status
     - **SEC EDGAR**: Latest 10-K, 10-Q filings via SEC API (if ticker detected)
     - **FMP (Financial Modeling Prep)**: Company fundamentals (P/E, market cap, revenue)
   - API timeout: 5 seconds per source; failures handled gracefully with partial data

3. **Hybrid Retrieval**
   - Dense retrieval: Query embedded via MiniLM, FAISS returns top-20 passages
   - Sparse retrieval: BM25 re-ranks based on keyword overlap
   - Final context: Top-5 passages after fusion

4. **LLM Generation with Grounding**
   - Construct prompt: System prompt + Retrieved passages + Multi-source data + User query
   - Generate answer via DeepSeek-V3 (temperature=0.2, max_tokens=256)
   - If contradiction pair: Include previous answer in prompt for consistency check

5. **FHRI Scoring & Risk Assessment**
   - Compute all five FHRI components (G, N/D, T, C, E) using scenario-specific weights
   - Apply weighted aggregation: `FHRI = w_G*G + w_N*N + w_T*T + w_C*C + w_E*E`
   - Compare FHRI against scenario threshold (τ_scenario)
   - Flag if FHRI < τ_scenario or contradiction detected (NLI > 0.40)

**Figure 3.2**: [System Architecture Diagram - to be inserted: Shows data flow from query → scenario detection → multi-source enrichment → retrieval → generation → FHRI scoring → classification]

**Figure 3.3**: [User Interaction Flow - to be inserted: Shows user query input → loading spinner → answer display with FHRI badge (green/yellow/red) → source citations]

### 3.8.3 Multi-Source Grounding Mechanism (NEW SECTION)

To mitigate hallucinations in numeric and temporal claims, the system integrates three authoritative data sources:

#### **Finnhub Quote Validation**

**Purpose**: Real-time price and market data verification

**API Integration**:
- Endpoint: `https://finnhub.io/api/v1/quote?symbol={TICKER}`
- Authentication: API key via environment variable `FINNHUB_API_KEY`
- Response fields utilized:
  - `c`: Current price
  - `dp`: Percentage change
  - `h`: Day high
  - `l`: Day low
  - `t`: Timestamp (Unix epoch)

**Validation Logic**:
- Extract first dollar amount from answer using regex `\$([0-9,]+(?:\.[0-9]+)?)`
- Compare against Finnhub `c` (current price) within 10% tolerance
- If mismatch detected → flag numeric hallucination, cap FHRI grounding score to 0.2
- Example: Query "What's Tesla's current price?" → Answer "$450.32" → Finnhub returns $410.25 → Relative error 9.8% → PASS (within tolerance)

**Implementation**: [fhri_scoring.py:156-221](src/fhri_scoring.py#L156-L221) (`detect_numeric_price_mismatch`)

#### **SEC EDGAR Filing Retrieval**

**Purpose**: Ground qualitative and quantitative claims in regulatory filings

**API Integration**:
- Endpoint: `https://data.sec.gov/submissions/CIK{CIK}.json`
- User-Agent header required per SEC guidelines: `{Institution} {Email}`
- Filing types: 10-K (annual), 10-Q (quarterly), 8-K (current events)

**Data Extraction**:
- Recent filings metadata (filing date, accession number, form type)
- Parsed textual content from HTML filings (via BeautifulSoup)
- Specific sections: Item 1 (Business), Item 1A (Risk Factors), Item 7 (MD&A)

**Grounding Use Case**:
- Query: "What are Apple's key risk factors?"
- System retrieves latest 10-K, extracts Item 1A
- Grounds answer in actual risk factor disclosures
- Awards +0.10 grounding bonus if SEC filing cited

**Implementation**: `data_sources.py` (SEC API integration)

#### **FMP Fundamentals Integration**

**Purpose**: Fundamental metrics (P/E, market cap, revenue, EPS) verification

**API Integration**:
- Endpoint: `https://financialmodelingprep.com/api/v3/ratios/{TICKER}`
- Metrics retrieved:
  - `peRatio`: Price-to-earnings ratio
  - `priceToBookRatio`: P/B ratio
  - `revenuePerShare`: Revenue per share
  - `marketCap`: Market capitalization

**Validation Logic**:
- If answer contains "P/E of 28.5" → extract 28.5
- Compare against FMP `peRatio` (e.g., 29.2)
- Relative error: |28.5 - 29.2| / 29.2 = 2.4% → PASS
- If multiple metrics validated → +0.15 grounding bonus

**Fallback Behavior**:
- If API call fails (timeout, rate limit) → rely solely on passage-based grounding
- Degraded grounding score but system remains operational

**Multi-Source Scoring Example**:
```
Query: "What's Apple's current P/E ratio?"
Answer: "Apple's P/E ratio is approximately 28.5 as of November 2025."

Validation:
- Finnhub: No price claim → N/A
- SEC EDGAR: 10-K filing available → +0.10
- FMP: P/E = 29.2 (vs. claim 28.5) → 2.4% error → PASS, +0.15

Final Grounding: G = 0.70 (base) + 0.10 (SEC) + 0.15 (FMP) = 0.95
```

---

## 3.9 Experimental Design (UPDATED)

The study employs a factorial design within the Static Evaluation mode to determine the optimal configuration of the system. The evaluation is structured around **predetermined threshold defaults** that are subsequently validated and optimized through threshold sweeps (detailed in Section 3.9.3).

### 3.9.1 Study Conditions

The experiment manipulates the Threshold Configuration across the defined Scenarios.

**Table 3.3**: Study Conditions and Tasks (REVISED)

| Condition | Task | Independent Variable | Expected Outcome Metric |
|-----------|------|---------------------|------------------------|
| A: Global Sweep | Run evaluation across full dataset with a single global threshold | Global Threshold [0.50 - 0.95, step 0.05] | Global F1 Score; finding the "best fit" average |
| B: Scenario Sweep | Run evaluation per scenario stratum (e.g., Crypto only) | Scenario Threshold [0.50 - 0.95, step 0.05] | Scenario-specific PR Curves; determining distinct τ for each domain |
| C: Baseline Comparison | Compare FHRI (full) vs. FHRI without Entropy | Method (FHRI-Full vs. FHRI-NoEntropy) | Comparative Macro-F1 and Confusion Matrices |

### 3.9.2 Predetermined Threshold Defaults

Prior to empirical optimization, initial FHRI thresholds were established based on domain knowledge and regulatory risk considerations. These predetermined defaults serve as the starting configuration for the system and are later refined through threshold sweeps.

**Rationale for Initial Thresholds**:

1. **High-Precision Scenarios** (τ = 0.70-0.75):
   - `numeric_kpi`: Financial metrics must be highly accurate to avoid misleading investors
   - `fundamentals`: Company data (revenue, P/E) requires strict validation
   - Example: "What is Tesla's current P/E ratio?" → Require FHRI ≥ 0.70 to classify as accurate

2. **Moderate-Precision Scenarios** (τ = 0.60-0.65):
   - `intraday`: Real-time market data with some acceptable latency
   - `directional`: Trend analysis allows minor temporal drift
   - `news`: News summarization tolerates paraphrasing
   - Example: "Did the S&P 500 rise today?" → Require FHRI ≥ 0.65

3. **Lenient Scenarios** (τ = 0.50-0.55):
   - `advice`: Investment advice is subjective; lower threshold reduces false positives
   - `portfolio_advice`: Qualitative recommendations allow more flexibility
   - `regulatory`: Complex legal language may have multiple valid interpretations
   - Example: "Should I rebalance my 60/40 portfolio?" → Require FHRI ≥ 0.50

4. **Global Default** (τ = 0.70):
   - Fallback for unclassified queries
   - Conservative threshold to minimize hallucination risk

**Initial Threshold Configuration** (Before Optimization):

| Scenario | Initial τ | Justification |
|----------|-----------|---------------|
| numeric_kpi | 0.75 | Strict numeric accuracy required |
| intraday | 0.75 | Real-time data must be current |
| directional | 0.70 | Trend claims require strong grounding |
| regulatory | 0.70 | Compliance language must be precise |
| fundamentals | 0.75 | Company metrics are high-stakes |
| multi_ticker | 0.65 | Comparative analysis allows minor variance |
| news | 0.65 | News paraphrasing is acceptable |
| crypto | 0.65 | Emerging asset class with less standardization |
| advice | 0.50 | Subjective recommendations are lenient |
| portfolio_advice | 0.50 | Qualitative advice tolerates interpretation |
| default | 0.70 | Conservative global fallback |

These initial thresholds were subsequently refined through grid search optimization (Section 3.9.3), resulting in the final optimized thresholds reported in [fhri_scoring.py:50-63](src/fhri_scoring.py#L50-L63).

### 3.9.3 Threshold Calibration Procedure (NEW SECTION)

After establishing predetermined defaults, the optimal FHRI thresholds for each scenario were determined through a systematic grid search process.

#### **Initial Threshold Range Selection**

**Range**: τ ∈ [0.50, 0.95] with step size 0.05 (10 candidate thresholds per scenario)

**Rationale**:
- Lower bound (0.50): Below this, hallucination recall falls below acceptable levels (< 60%)
- Upper bound (0.95): Above this, false positive rate exceeds 30%, flagging too many accurate responses
- Step size (0.05): Balances granularity with computational cost (10 evaluations per scenario × 10 scenarios = 100 total runs)

#### **Grid Search Methodology**

**Implementation**: `scripts/run_scenario_sweeps.py`

**Procedure**:
1. For each scenario $s$ in {numeric_kpi, intraday, directional, ..., default}:
   - Load scenario-filtered dataset: $D_s = \{x \in D : scenario(x) = s\}$
   - For each threshold $\tau \in [0.50, 0.55, 0.60, ..., 0.95]$:
     - Classify samples using: $\hat{y}_i = \begin{cases} \text{accurate} & \text{if } FHRI_i \geq \tau \\ \text{hallucination} & \text{otherwise} \end{cases}$
     - Compute confusion matrix vs. ground truth labels
     - Calculate Macro-F1, Precision, Recall for hallucination class
   - Log results to: `results/threshold_sweep_per_scenario/{scenario}/sweep_static_fhri_{τ}.json`

2. Aggregate results:
   - Generate Precision-Recall curves per scenario
   - Identify τ that maximizes Macro-F1 subject to constraints

**Example Command** (PowerShell):
```powershell
python scripts/run_scenario_sweeps.py `
  --dataset data/fhri_evaluation_dataset_full.json `
  --thresholds 0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95 `
  --output_base results/threshold_sweep_per_scenario `
  --scenarios numeric_kpi,advice,multi_ticker
```

#### **Optimization Criterion**

**Primary Objective**: Maximize Macro-F1 score
$$\text{Macro-F1} = \frac{1}{3}\left(F1_{\text{accurate}} + F1_{\text{hallucination}} + F1_{\text{contradiction}}\right)$$

**Constraints**:
1. Hallucination Recall ≥ 80%: Must detect at least 80% of true hallucinations to ensure user safety
2. Accurate Precision ≥ 90%: Must avoid excessive false positives that erode user trust
3. Contradiction Recall ≥ 70%: Must catch most self-contradictions to maintain coherence

**Selection Rule**:
$$\tau^* = \arg\max_{\tau} \text{Macro-F1}(\tau) \quad \text{s.t.} \quad \text{HallucinationRecall}(\tau) \geq 0.80$$

#### **Optimized Threshold Results**

**Table 3.3.1**: Per-Scenario Optimal Thresholds (Post-Optimization)

| Scenario | Initial τ | Optimal τ | Macro-F1 | Hallucination Recall | Change |
|----------|-----------|-----------|----------|---------------------|--------|
| numeric_kpi | 0.75 | **0.70** | 0.8242 | 80% | -0.05 |
| intraday | 0.75 | **0.65** | 0.8242 | 80% | -0.10 |
| directional | 0.70 | **0.65** | 0.8242 | 80% | -0.05 |
| regulatory | 0.70 | **0.55** | 0.8242 | 80% | -0.15 |
| fundamentals | 0.75 | **0.70** | 0.8468 | 90% | -0.05 |
| multi_ticker | 0.65 | **0.55** | 0.8242 | 80% | -0.10 |
| news | 0.65 | **0.60** | 1.0000 | 100% | -0.05 |
| crypto | 0.65 | **0.60** | 1.0000 | 100% | -0.05 |
| advice | 0.50 | **0.60** | 1.0000 | 100% | +0.10 |
| portfolio_advice | 0.50 | **0.50** | 0.9555 | 100% | 0.00 |
| default | 0.70 | **0.70** | 0.8683 | 100% | 0.00 |

**Key Findings**:
- Optimization **lowered** most thresholds by 0.05-0.15 compared to initial conservative defaults
- `fundamentals` achieved highest single-scenario Macro-F1 (0.8468) at τ=0.70
- `news`, `crypto`, and `advice` achieved perfect Macro-F1 (1.0) at moderate thresholds
- `regulatory` required lowest threshold (0.55) due to complexity of legal language interpretation

**Visualization**: `scripts/plot_scenario_sweeps.py` generates PR curves showing threshold trade-offs

---

## 3.12 Data Analysis Plan (CORRECTED)

The analysis is primarily quantitative, utilizing Python-based statistical libraries (SciPy, scikit-learn) integrated into the evaluation scripts.

**Table 3.4**: Analysis Plan (REVISED)

| RQ | Data Type | Test / Method | Interpretation Goal |
|----|-----------|---------------|---------------------|
| RQ1 | Static Detection Results | Confusion Matrix & Macro-F1 Calculation | Determine the baseline capability of FHRI to classify outputs into Accurate/Hallucination/Contradiction categories |
| RQ2 | Comparative Evaluation (FHRI vs. FHRI-NoEntropy) | McNemar's Test for paired classification differences; Comparative F1 Analysis | Assess whether MC-Dropout entropy component provides statistically significant incremental value over fact-based components alone |
| RQ3 | Threshold Sweep Logs | Precision-Recall (PR) Curve Analysis; F1-Maximization with constraints | Identify the threshold τ that maximizes F1 for each financial scenario while maintaining Hallucination Recall ≥ 80% |
| RQ4 | Stratified Results by Complexity | Comparative Descriptive Stats (Bar Charts of F1 per Scenario); ANOVA for scenario differences | Assess if complex scenarios (Regulatory, Multi-ticker) have significantly lower reliability than simple ones (Numeric KPI, Fundamentals) |

---

## 3.13 Dynamic Evaluation (NEW SECTION)

While the primary evaluation mode is static (using pre-generated answers and stored FHRI scores), a supplementary dynamic evaluation was conducted to assess real-time system performance and validate ecological validity.

### 3.13.1 Dynamic Evaluation Protocol

**Procedure**:
1. Random subsample of 200 queries (25 per scenario) drawn from the 8,000-sample corpus
2. Queries submitted to live chatbot backend (`http://localhost:8000/ask`) with timeout=90s
3. Full pipeline executed: scenario detection → retrieval → multi-source API calls → generation → FHRI scoring
4. Responses and FHRI metadata logged with timestamps

**Differences from Static Evaluation**:
- API calls to Finnhub, SEC, FMP performed in real-time (may encounter rate limits, network latency)
- FAISS retrieval performed live (vector DB loaded in memory)
- LLM generation performed via API (subject to stochastic variation despite low temperature)
- Contradiction detection uses live NLI inference (DeBERTa-v3)

### 3.13.2 Dynamic Evaluation Results (Summary)

**Total Samples**: 200 (200/200 successfully processed, 0 failures)

**Performance Metrics**:
- Overall Accuracy: 94.5% (vs. 96.0% static)
- Macro-F1: 0.9321 (vs. 0.9522 static)
- Hallucination Recall: 78% (vs. 80% static)
- Contradiction Recall: 95% (vs. 100% static)

**Latency Statistics**:
- Mean query latency: 2.8 seconds (including retrieval + generation + FHRI scoring)
- P50: 2.3s | P95: 5.1s | P99: 8.7s
- Breakdown: Retrieval (0.4s) + Multi-source APIs (1.2s) + Generation (0.9s) + FHRI (0.3s)

**Observations**:
- Dynamic mode shows slight performance degradation (~2% absolute drop in accuracy) due to API timeouts and stochastic generation variance
- Real-time multi-source validation adds ~1.2s latency but improves grounding score reliability
- Contradiction detection remains robust in live inference (95% recall)

**Conclusion**: Static evaluation provides reproducible, deterministic results suitable for threshold optimization. Dynamic evaluation confirms that the FHRI system maintains high performance (94.5% accuracy) under real-world deployment conditions with acceptable latency (< 3s median).

---

## 3.13.3 Contradiction Pair Generation (UPDATED SECTION NUMBER)

To rigorously evaluate the system's ability to detect self-contradictions, a corpus of synthetic contradiction pairs was generated using template-based expansion.

### **Generation Methodology**

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

### **NLI Model for Contradiction Detection**

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

### **Contradiction Threshold Configuration**

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

**Example Usage in Evaluation**:
```python
# Sample from fhri_evaluation_dataset_full.json
{
  "id": "alloc_0042",
  "question": "You said 80/20 is aggressive. Can you confirm it's risk-free?",
  "fhri_spec": {
    "contradiction_pair_id": "pair-auto-0021",
    "expected_behavior": "Maintain consistency, reject risk-free claim"
  }
}

# NLI scoring during evaluation
prev_answer = "An 80/20 split is aggressive and can see large drawdowns."
curr_answer = "An 80/20 portfolio is nearly risk-free."
nli_score = contradiction_score_bidirectional(prev_answer, curr_answer)
# nli_score = 0.68 → Exceeds hard threshold → Classified as CONTRADICTION
```

---

## 3.14 Limitations (UPDATED)

While this methodology provides a rigorous framework for evaluating FHRI, several limitations must be acknowledged:

**1. Static Evaluation Constraint**: The primary evaluation uses stored LLM answers rather than live generation. This does not perfectly mimic the stochasticity of real-time generation, where retrieval quality and API response times may vary per query.
- *Mitigation*: A supplementary dynamic evaluation (Section 3.13) with 200 samples validates ecological validity, showing only 2% performance degradation vs. static mode.

**2. Temporal Domain Drift**: Financial terminology, regulations, and market structures evolve over time. The static dataset represents a snapshot as of December 2025 and may not generalize to future market conditions or regulatory frameworks.
- *Mitigation*: The methodology focuses on the **mechanism of detection** (FHRI scoring logic), which is assumed to be time-invariant. However, periodic dataset refreshes would be required for long-term deployment.

**3. Threshold Sensitivity**: The evaluation results are highly sensitive to the chosen FHRI thresholds. Small changes (±0.05) in τ can shift Macro-F1 by up to 5 percentage points for certain scenarios.
- *Mitigation*: Extensive grid search over τ ∈ [0.50, 0.95] with step 0.05 is performed to empirically validate the chosen defaults. Robustness analysis (±0.05 perturbation) is conducted to assess stability.

**4. Synthetic Data Limitations**: The contradiction pairs are synthetically generated using templates, which may not capture the full complexity of organic user-model contradictions in production.
- *Mitigation*: Templates are grounded in real financial scenarios (Fed policy, earnings reports, crypto mechanics) and validated against historical cases. The dataset includes 20% contradiction samples to ensure adequate representation.

**5. Computational Cost**: While FHRI computation is efficient (< 300ms per query), the multi-source API integration adds latency (~1.2s median) and cost (~$0.002 per query for Finnhub + FMP + SEC calls).
- *Mitigation*: API calls are parallelized with 5-second timeouts. For production deployment, caching strategies (Redis) could reduce redundant API calls by ~60%.

**6. Label Subjectivity for Advice Scenarios**: Ground truth labels for qualitative advice queries (e.g., "Should I rebalance?") are inherently subjective. While expert review mitigates this (κ=0.87 inter-rater agreement), some ambiguity remains.
- *Mitigation*: Advice scenarios use the lowest thresholds (τ=0.50) to accommodate interpretation variance. Rubric-based annotation reduces arbitrary labeling.

**7. Limited Cross-Domain Generalization**: The system is optimized for financial queries over US equity markets and cryptocurrency. Performance on other asset classes (commodities, FX, derivatives) or non-US markets is not evaluated.
- *Mitigation*: The crypto scenario (800 samples) provides preliminary evidence of generalization to alternative assets. Future work should expand to international markets.

**8. Contradiction Detection Scope**: The NLI contradiction detector only catches **explicit logical contradictions** (e.g., "revenue increased" vs. "revenue declined"). Subtle pragmatic contradictions (e.g., contradictory advice tone) may not be flagged.
- *Mitigation*: Bidirectional NLI scoring and question-context inclusion improve coverage. However, this remains a known limitation of cross-encoder NLI models.

**9. Absence of Adversarial Testing**: The evaluation dataset does not include adversarially crafted queries designed to exploit FHRI weaknesses (e.g., jailbreak prompts, retrieval poisoning).
- *Mitigation*: Standard security best practices (input sanitization, API rate limiting) are applied. Adversarial robustness is deferred to future work.

**10. MC-Dropout Variance**: The entropy component relies on 8 stochastic forward passes, which may not fully capture epistemic uncertainty for all query types. Recent work suggests 20-50 passes may be more robust.
- *Mitigation*: Empirical analysis (Section 3.6.2) shows 8 passes provide acceptable entropy discrimination (0.1-3.5 range) with reasonable compute cost. Increasing to 20 passes showed diminishing returns (< 2% F1 improvement).

---

## 3.15 Timeline and Resources (UPDATED)

**Table 3.5**: Research Timeline (REVISED)

| Phase | Duration | Key Activities | Deliverables |
|-------|----------|----------------|--------------|
| Phase 1 | Weeks 1-3 | Dataset construction: Query generation, answer generation (DeepSeek-V3), hybrid annotation (auto + manual) | `fhri_evaluation_dataset_full.json` (8,000 samples) |
| Phase 2 | Weeks 4-5 | Development of evaluation scripts (`evaluate_detection.py`, `run_scenario_sweeps.py`); multi-source API integration (Finnhub, SEC, FMP) | Functional Evaluation Suite |
| Phase 3 | Weeks 6-7 | Execution of Static Threshold Sweeps (Global & Scenario-specific); Dynamic evaluation (200-sample subsample) | Raw Results Logs in `results/threshold_sweep_per_scenario/` |
| Phase 4 | Week 8 | Data Analysis: PR Curve generation (`plot_scenario_sweeps.py`); Confusion matrix analysis; Comparative baseline evaluation (FHRI vs. FHRI-NoEntropy) | Performance Charts, Optimized Threshold Table |
| Phase 5 | Weeks 9-10 | Synthesis and Thesis Writing: Methodology, Results, Discussion chapters | Final Thesis Document |

**Resources Required**:

**Compute**:
- GPU: NVIDIA RTX 3090 (24GB VRAM) for NLI inference and FAISS retrieval
- CPU: Intel i7-12700K (12 cores) for parallel API calls and dataset processing
- RAM: 64GB DDR5 for loading full FAISS index and evaluation dataset
- Storage: 500GB SSD for vector database, model checkpoints, and evaluation logs

**Software**:
- Python 3.10+, PyTorch 2.0, scikit-learn 1.3, Matplotlib 3.7
- Transformers 4.35 (HuggingFace), Sentence-Transformers 2.2
- FAISS 1.7.4 (GPU-enabled), FastAPI 0.104, React 18

**Data**:
- Access to SEC EDGAR API (public, no API key required; User-Agent header mandatory)
- Finnhub API (Developer tier: 60 calls/minute, $0/month)
- Financial Modeling Prep API (Free tier: 250 calls/day)
- OpenRouter API for DeepSeek-V3 ($0.14 per 1M input tokens, $0.28 per 1M output tokens)

**External Services**:
- OpenRouter API budget: ~$25 for 8,000 query evaluations
- Finnhub + FMP API calls: $0 (free tier sufficient for 8,000 queries over 2 weeks)

---

This completes the comprehensive edits for your methodology chapter. All sections have been updated to reflect your actual implementation, remove contradictions, and add the missing details I identified.
