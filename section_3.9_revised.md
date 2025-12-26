# 3.9 Experimental Design (REVISED FOR METHODOLOGY CHAPTER)

The study employs a factorial design within the Static Evaluation mode to determine the optimal configuration of the FHRI system. The evaluation is structured around **predetermined threshold defaults** that are subsequently validated and optimized through systematic threshold sweeps. This section describes the experimental conditions, task scenarios, and calibration procedures employed to answer the research questions.

---

## 3.9.1 Study Conditions

The experiment manipulates the **FHRI Threshold Configuration** and **Detection Method** across the defined Scenarios to comprehensively evaluate system performance.

**Table 3.3**: Study Conditions and Tasks

| Condition | Task Description | Independent Variable(s) | Expected Outcome Metrics |
|-----------|-----------------|------------------------|-------------------------|
| **A: Global Threshold Sweep** | Evaluate the full 8,000-sample dataset using a single global FHRI threshold applied uniformly across all scenarios | Global Threshold τ ∈ [0.50, 0.95] with step 0.05 | - Global Macro-F1 Score<br>- Overall Accuracy<br>- Class-specific Precision/Recall<br>- Optimal τ that maximizes global F1 |
| **B: Scenario-Specific Sweep** | Evaluate each scenario stratum independently (e.g., Crypto, Numeric KPI, Regulatory) with scenario-specific thresholds | Scenario Threshold τ_s ∈ [0.50, 0.95] per scenario s | - Per-scenario Precision-Recall curves<br>- Scenario-specific optimal τ*<br>- F1 variance across scenarios<br>- Identification of high-risk vs. lenient scenarios |
| **C: Baseline Comparison** | Compare FHRI (full 5-component system) against FHRI without Entropy component to isolate the contribution of MC-Dropout uncertainty | Detection Method:<br>1. FHRI-Full (G, N/D, T, C, E)<br>2. FHRI-NoEntropy (G, N/D, T, C only, renormalized) | - Comparative Macro-F1<br>- Confusion Matrices (3×3)<br>- McNemar's Test (p-value for significance)<br>- Entropy component contribution (ΔF1) |

**Experimental Control Variables**:
- Dataset: Fixed 8,000-sample corpus with stratified labels (60% Accurate, 20% Hallucination, 20% Contradiction)
- LLM backbone: DeepSeek-V3 (temperature=0.2) for answer generation
- Retrieval: Top-5 passages from FAISS hybrid search
- NLI model: DeBERTa-v3-base with bidirectional scoring
- Evaluation mode: Static (pre-generated answers to eliminate stochastic variance)

**Randomization**:
- Sample order shuffled prior to evaluation to prevent order effects
- Contradiction pair ordering preserved (accurate baseline must precede contradiction follow-up)

---

## 3.9.2 Predetermined Threshold Defaults

Prior to empirical optimization, initial FHRI acceptance thresholds were established based on domain knowledge, regulatory risk considerations, and the criticality of financial information accuracy. These predetermined defaults serve as the **starting configuration** for the system and represent conservative safety margins designed to minimize false negatives (missed hallucinations).

### 3.9.2.1 Threshold Selection Rationale

The initial thresholds were stratified into four tiers based on the **consequence severity** of potential hallucinations:

**Tier 1: High-Precision Scenarios (τ = 0.75)**
- **Scenarios**: `numeric_kpi`, `intraday`, `fundamentals`
- **Rationale**: Financial metrics (P/E ratios, stock prices, revenue figures) must be highly accurate to avoid misleading investors or violating regulatory guidance. Incorrect numeric claims can have direct financial consequences or erode user trust.
- **Risk Profile**: High regulatory exposure (SEC Rule 10b-5 anti-fraud provisions apply to material misstatements)
- **Example**: "What is Tesla's current P/E ratio?" → FHRI must exceed 0.75 to classify as accurate, ensuring strong grounding in verified data sources (Finnhub, SEC filings)

**Tier 2: Moderate-Precision Scenarios (τ = 0.70)**
- **Scenarios**: `directional`, `regulatory`
- **Rationale**:
  - `directional`: Trend claims ("revenue increased 12% YoY") require strong temporal and numeric grounding but allow minor rounding or period approximation
  - `regulatory`: Legal/compliance language must be precise, but multiple valid interpretations exist (e.g., "substantially compliant" vs. "fully compliant")
- **Risk Profile**: Medium regulatory exposure; directional errors can mislead but are less critical than absolute numeric errors
- **Example**: "Did Apple's revenue grow last quarter?" → FHRI ≥ 0.70 ensures direction is verified against SEC filings

**Tier 3: Standard-Precision Scenarios (τ = 0.65)**
- **Scenarios**: `multi_ticker`, `news`, `crypto`
- **Rationale**:
  - `multi_ticker`: Comparative analysis across multiple stocks allows minor variance in individual metrics as long as relative ordering is correct
  - `news`: News summarization tolerates paraphrasing and stylistic variation; factual core must be preserved
  - `crypto`: Emerging asset class with less regulatory standardization; allows more interpretation
- **Risk Profile**: Low-to-medium regulatory exposure; errors are concerning but less likely to trigger compliance issues
- **Example**: "Compare TSLA and AAPL revenue growth" → FHRI ≥ 0.65 allows minor numeric drift if comparative direction is correct

**Tier 4: Lenient Scenarios (τ = 0.50-0.55)**
- **Scenarios**: `advice`, `portfolio_advice`
- **Rationale**: Investment advice is inherently subjective and qualitative. Different advisors may provide conflicting but equally valid recommendations (e.g., "rebalance quarterly" vs. "rebalance annually"). Lower threshold reduces false positives that would flag legitimate strategic differences as hallucinations.
- **Risk Profile**: Subjective domain; no single "correct" answer exists
- **Regulatory Note**: System includes separate refusal logic for high-risk advice (e.g., margin trading, penny stocks) independent of FHRI scoring
- **Example**: "Should I rebalance my 60/40 portfolio?" → FHRI ≥ 0.50 allows diverse but reasonable advice

**Global Default (τ = 0.70)**:
- Applied to queries that do not match any of the 10 predefined scenarios
- Conservative fallback to prioritize safety over permissiveness

### 3.9.2.2 Initial Threshold Configuration

**Table 3.3.1**: Predetermined FHRI Thresholds (Pre-Optimization)

| Scenario | Initial τ | Tier | Primary Justification |
|----------|-----------|------|----------------------|
| `numeric_kpi` | 0.75 | High-Precision | Numeric accuracy is critical; regulatory exposure to SEC anti-fraud rules |
| `intraday` | 0.75 | High-Precision | Real-time market data must be current; temporal misalignment is high-risk |
| `fundamentals` | 0.75 | High-Precision | Company fundamentals (revenue, P/E, market cap) are material facts |
| `directional` | 0.70 | Moderate-Precision | Trend direction must be accurate; minor numeric variance tolerated |
| `regulatory` | 0.70 | Moderate-Precision | Legal language requires precision but allows interpretation |
| `multi_ticker` | 0.65 | Standard-Precision | Comparative metrics allow minor individual variance |
| `news` | 0.65 | Standard-Precision | News paraphrasing acceptable; factual core must be preserved |
| `crypto` | 0.65 | Standard-Precision | Emerging asset class with less standardization |
| `advice` | 0.50 | Lenient | Subjective investment strategy; diverse valid approaches exist |
| `portfolio_advice` | 0.50 | Lenient | Qualitative recommendations; no single correct answer |
| `default` | 0.70 | Moderate-Precision | Conservative fallback for unclassified queries |

**Design Philosophy**:
- **Conservative by Default**: Higher thresholds (0.70-0.75) for most scenarios minimize false negatives (undetected hallucinations) at the cost of increased false positives (accurate answers incorrectly flagged)
- **Scenario Specificity**: Thresholds reflect domain-specific risk profiles rather than uniform enforcement
- **Empirical Validation**: These predetermined values serve as hypotheses to be tested via threshold sweeps (Section 3.9.3)

---

## 3.9.3 Threshold Calibration Procedure

The predetermined thresholds represent an initial conservative configuration. To validate and optimize these defaults, a systematic grid search calibration procedure was designed to empirically determine the **optimal operating point** for each scenario.

### 3.9.3.1 Calibration Objectives

The calibration process aims to:
1. **Validate Initial Hypotheses**: Determine if predetermined thresholds (0.50-0.75) are empirically justified or overly conservative
2. **Maximize Detection Performance**: Identify τ* that maximizes Macro-F1 for each scenario
3. **Balance Precision-Recall Trade-off**: Find thresholds that maintain high hallucination recall (≥ 80%) while minimizing false positive rates
4. **Quantify Scenario Variance**: Assess whether uniform thresholds are sufficient or scenario-specific tuning is necessary

### 3.9.3.2 Grid Search Methodology

**Search Space Definition**:
- **Threshold Range**: τ ∈ [0.50, 0.95]
- **Step Size**: Δτ = 0.05
- **Total Candidates per Scenario**: 10 thresholds {0.50, 0.55, 0.60, ..., 0.95}

**Rationale for Range Selection**:
- **Lower Bound (0.50)**: Below this threshold, hallucination recall falls below acceptable levels (< 60% based on pilot testing), creating unacceptable safety risks
- **Upper Bound (0.95)**: Above this threshold, false positive rate exceeds 30%, flagging too many legitimate accurate responses and degrading user experience
- **Step Size (0.05)**: Provides sufficient granularity to identify performance peaks while limiting computational cost (10 evaluations per scenario)

**Implementation Pipeline**:

The threshold sweep is implemented via `scripts/run_scenario_sweeps.py` with the following procedure:

**Algorithm: Per-Scenario Threshold Sweep**
```
Input: Dataset D, Scenario s, Threshold range T = {0.50, 0.55, ..., 0.95}
Output: Optimal threshold τ*, Performance metrics M

1. Filter dataset to scenario:
   D_s ← {sample ∈ D : sample.scenario = s}

2. For each candidate threshold τ ∈ T:
   a. Initialize confusion matrix C[3×3] = zeros
   b. For each sample x_i ∈ D_s:
      i.  Retrieve stored FHRI score: fhri_i ← x_i.fhri_spec.fhri
      ii. Classify based on threshold:
          y_pred ← {
              "accurate"       if fhri_i ≥ τ AND no_contradiction
              "hallucination"  if fhri_i < τ
              "contradiction"  if NLI_score > 0.40
          }
      iii. Update confusion matrix: C[y_true, y_pred] += 1

   c. Calculate performance metrics:
      - Precision_c, Recall_c, F1_c for each class c ∈ {accurate, hallucination, contradiction}
      - Macro-F1 ← mean(F1_accurate, F1_hallucination, F1_contradiction)
      - Overall Accuracy ← trace(C) / sum(C)

   d. Store results: M[τ] ← {Macro-F1, Precision, Recall, Accuracy, Confusion Matrix}
   e. Log to file: results/threshold_sweep_per_scenario/{s}/sweep_static_fhri_{τ}.json

3. Select optimal threshold:
   τ* ← argmax_τ (Macro-F1(τ)) subject to Recall_hallucination(τ) ≥ 0.80

4. Generate Precision-Recall curve for scenario s
5. Return τ*, M[τ*]
```

**Example Execution Command** (PowerShell):
```powershell
python scripts/run_scenario_sweeps.py `
  --dataset data/fhri_evaluation_dataset_full.json `
  --thresholds "0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90,0.95" `
  --output_base results/threshold_sweep_per_scenario `
  --scenarios "numeric_kpi,intraday,directional,regulatory,advice"
```

**Computational Efficiency**:
- **Static Mode**: Evaluation uses pre-computed FHRI scores stored in dataset, avoiding redundant LLM generation
- **Parallelization**: Scenarios processed independently; can be parallelized across CPU cores
- **Total Runtime**: ~8 minutes for all 10 scenarios × 10 thresholds = 100 evaluations on consumer hardware (Intel i7)

### 3.9.3.3 Optimization Criterion

The threshold selection employs a **constrained optimization** approach balancing multiple objectives:

**Primary Objective Function**:
$$\tau^* = \arg\max_{\tau \in T} \text{Macro-F1}(\tau)$$

Where Macro-F1 is the unweighted average F1 score across all three classes:
$$\text{Macro-F1} = \frac{1}{3}\left(F1_{\text{accurate}} + F1_{\text{hallucination}} + F1_{\text{contradiction}}\right)$$

**Hard Constraints**:
1. **Safety Constraint**: $\text{Recall}_{\text{hallucination}}(\tau) \geq 0.80$
   - Ensures at least 80% of true hallucinations are detected
   - Prevents selecting overly permissive thresholds that miss safety-critical errors

2. **Usability Constraint**: $\text{Precision}_{\text{accurate}}(\tau) \geq 0.90$
   - Ensures at least 90% of "accurate" classifications are truly accurate
   - Prevents excessive false positives that degrade user trust

3. **Contradiction Constraint**: $\text{Recall}_{\text{contradiction}}(\tau) \geq 0.70$
   - Ensures contradictions are detected independently of FHRI threshold
   - Validates that NLI-based detection is functioning correctly

**Selection Rule**:
If multiple thresholds satisfy all constraints, the tie-breaker prioritizes:
1. Highest Macro-F1 (primary)
2. Highest Hallucination Recall (secondary, for safety)
3. Lowest threshold value (tertiary, favors permissiveness when F1 is equal)

**Rationale**: Macro-F1 ensures balanced performance across all three classes, avoiding optimization bias toward the majority class (Accurate = 60% of dataset). The constraints ensure that optimization does not sacrifice critical safety (hallucination detection) or usability (false positive control).

### 3.9.3.4 Validation and Robustness Analysis

To assess the stability of the selected thresholds, two validation procedures are employed:

**1. Perturbation Analysis**:
- For each optimized threshold τ*, evaluate performance at τ* ± 0.05
- Calculate ΔF1 = |F1(τ*) - F1(τ* ± 0.05)|
- If ΔF1 < 0.02, the threshold is considered **robust** (small perturbations do not significantly degrade performance)
- If ΔF1 ≥ 0.05, the threshold is **sensitive** and may require scenario-specific tuning

**2. Cross-Scenario Generalization**:
- Apply the global optimal threshold (τ_global*) to each individual scenario
- Measure performance degradation: ΔF1_scenario = F1(τ_scenario*) - F1(τ_global*)
- Quantifies the benefit of scenario-specific tuning over a one-size-fits-all approach
- Expected result: Scenarios with ΔF1 > 0.10 benefit significantly from custom thresholds

**Evaluation Outputs**:
1. **Per-Threshold JSON Reports**: Detailed confusion matrices and metrics for each τ
   - Location: `results/threshold_sweep_per_scenario/{scenario}/sweep_static_fhri_{τ}.json`

2. **Summary CSV**: Aggregated results for quick comparison
   - Location: `results/threshold_sweep_per_scenario/{scenario}/sweep_static_summary.csv`
   - Columns: threshold, accuracy, macro_f1, hall_precision, hall_recall, hall_f1, accurate_f1, contradiction_f1

3. **Precision-Recall Curves**: Visualization of threshold trade-offs
   - Generated via: `python scripts/plot_scenario_sweeps.py`
   - Shows P-R frontier for each scenario with τ* annotated

---

## 3.9.4 Contradiction Pair Handling

Contradiction detection operates **independently** of FHRI thresholds using NLI-based scoring. However, the experimental design must account for the sequential dependency between contradiction pairs.

**Pair Structure**:
- Each contradiction pair consists of:
  1. **Baseline Sample** (label: "accurate"): Establishes factual ground truth
  2. **Follow-up Sample** (label: "contradiction"): Requests reversal of prior claim
- Both samples share a unique `contradiction_pair_id` in their `fhri_spec` metadata

**Evaluation Protocol**:
1. **Preserve Sample Order**: Baseline sample must be processed before its paired contradiction
2. **Context Propagation**: The LLM answer from the baseline is passed as `prev_answer` when evaluating the follow-up
3. **Bidirectional NLI Scoring**: Compute contradiction score in both directions:
   - Forward: P(contradiction | premise=baseline_answer, hypothesis=followup_answer)
   - Backward: P(contradiction | premise=followup_answer, hypothesis=baseline_answer)
   - Final score: max(forward, backward)
4. **Threshold Application**:
   - If NLI score ≥ 0.40 (hard threshold) → classify as "contradiction"
   - If NLI score ∈ [0.15, 0.40) (soft threshold) → flag for manual review
   - If NLI score < 0.15 → classify based on FHRI threshold

**Threshold Sweep Interaction**:
- Contradiction classification is **orthogonal** to FHRI threshold sweeps
- Even if FHRI > τ (would normally classify as "accurate"), a high NLI score overrides to "contradiction"
- This ensures contradictions are detected regardless of grounding/numeric quality

---

## 3.9.5 Baseline Comparison Protocol (Condition C)

To isolate the contribution of the **Entropy component** (MC-Dropout uncertainty), a controlled comparison is conducted between:

**1. FHRI-Full**: All five components (G, N/D, T, C, E) with standard weights
$$FHRI_{\text{full}} = 0.25G + 0.25N + 0.20T + 0.15C + 0.15E$$

**2. FHRI-NoEntropy**: Four components (G, N/D, T, C) with renormalized weights
$$FHRI_{\text{no-entropy}} = 0.294G + 0.294N + 0.235T + 0.177C$$
*(Weights renormalized to sum to 1.0 after removing E)*

**Comparison Methodology**:

1. **Matched Sample Pairs**: Both methods evaluate the identical 8,000-sample dataset with identical:
   - Retrieved passages
   - Multi-source API data
   - NLI contradiction scores
   - Ground truth labels

2. **Threshold Alignment**: Both use the same scenario-specific thresholds (τ_scenario) for fair comparison

3. **Statistical Significance Testing**:
   - **McNemar's Test**: Tests if FHRI-Full and FHRI-NoEntropy make systematically different errors
     - Null hypothesis (H0): P(error_A ∧ correct_B) = P(correct_A ∧ error_B)
     - If p < 0.05, reject H0 → methods are significantly different

   - **Paired t-test on F1 scores**: Tests if mean F1 difference across scenarios is significant
     - Computes: ΔF1_s = F1_full(s) - F1_no-entropy(s) for each scenario s
     - Tests if mean(ΔF1) ≠ 0

4. **Confusion Matrix Comparison**:
   - Generate 3×3 confusion matrices for both methods
   - Compute difference matrix: Δ = C_full - C_no-entropy
   - Identify systematic error patterns (e.g., does removing entropy increase false positives?)

**Evaluation Metrics**:
- **ΔAccuracy** = Accuracy_full - Accuracy_no-entropy
- **ΔMacro-F1** = Macro-F1_full - Macro-F1_no-entropy
- **Entropy Contribution** = % improvement in Hallucination Recall attributable to entropy component

**Expected Outcome**:
- If ΔMacro-F1 > 0.05 and p < 0.05 → Entropy provides significant incremental value
- If ΔMacro-F1 < 0.02 → Entropy is redundant; fact-based components (G, N/D, T) suffice
- Results will be reported in Chapter 4 (Results)

---

## 3.9.6 Evaluation Modes: Static vs. Dynamic

The study employs **two evaluation modes** to balance reproducibility (static) with ecological validity (dynamic).

### Static Evaluation (Primary Mode)

**Purpose**: Deterministic, reproducible assessment of FHRI detection logic

**Characteristics**:
- Uses **pre-generated LLM answers** stored in `fhri_evaluation_dataset_full.json`
- FHRI component scores (G, N/D, T, C, E) pre-computed and cached
- No API calls during evaluation (all data retrieved during dataset construction)
- Eliminates stochastic variance from LLM generation and API latency

**Advantages**:
1. **Reproducibility**: Identical results across multiple runs
2. **Computational Efficiency**: Threshold sweeps complete in minutes vs. hours
3. **Deterministic Threshold Optimization**: No confounding from API failures or network issues
4. **Focused Testing**: Isolates FHRI scoring logic from retrieval/generation components

**Limitations**:
- Does not capture real-time API failures, rate limits, or network latency
- Cannot assess degradation from stochastic LLM temperature variation

**Use Cases**:
- Threshold calibration (Condition A, B)
- Baseline comparison (Condition C)
- Confusion matrix generation
- Precision-Recall curve plotting

### Dynamic Evaluation (Secondary Mode)

**Purpose**: Validate system performance under realistic deployment conditions

**Characteristics**:
- Queries submitted to **live chatbot backend** (`http://localhost:8000/ask`)
- Full pipeline executed: retrieval → API calls → LLM generation → FHRI scoring
- Subject to network latency, API rate limits, and stochastic generation variance

**Sample Selection**:
- Random subsample of 200 queries (25 per scenario) from the 8,000-sample corpus
- Stratified sampling ensures proportional representation of scenarios

**Validation Objectives**:
1. Confirm FHRI maintains high performance (> 90% accuracy) with real-time data
2. Measure latency distribution (P50, P95, P99)
3. Assess API failure handling (graceful degradation when Finnhub/SEC APIs timeout)
4. Validate end-to-end system integration

**Evaluation Protocol**:
1. Submit each query via POST request to `/ask` endpoint
2. Timeout: 90 seconds per query (to accommodate slow API calls)
3. Log response time breakdown: retrieval_time, api_time, generation_time, fhri_time
4. Compare dynamic classifications against ground truth labels

**Results Reporting**:
- Dynamic evaluation results summarized in Section 3.13
- Detailed latency analysis reported in Chapter 4 (Results)

---

## 3.9.7 Summary of Experimental Design

**Table 3.3.2**: Summary of Experimental Conditions

| Aspect | Configuration |
|--------|--------------|
| **Evaluation Dataset** | 8,000 samples (stratified: 60% Accurate, 20% Hallucination, 20% Contradiction) |
| **Scenarios Evaluated** | 10 scenarios (800 samples each) |
| **Threshold Range** | τ ∈ [0.50, 0.95], step 0.05 |
| **Baseline Methods** | FHRI-Full vs. FHRI-NoEntropy |
| **NLI Model** | DeBERTa-v3-base (bidirectional scoring) |
| **Contradiction Thresholds** | Soft: 0.15, Hard: 0.40 |
| **Evaluation Mode** | Static (primary, N=8,000) + Dynamic (secondary, N=200) |
| **Optimization Criterion** | Maximize Macro-F1 subject to Hallucination Recall ≥ 80% |
| **Statistical Tests** | McNemar's Test, Paired t-test, Confusion Matrix Analysis |
| **Output Artifacts** | 100+ JSON reports, PR curves, summary CSVs |

**Experimental Timeline**:
- Threshold sweeps (Condition A, B): ~2 hours total compute time
- Baseline comparison (Condition C): ~15 minutes per method
- Dynamic evaluation: ~6 hours (200 queries × 90s timeout with retries)
- Data analysis and visualization: ~4 hours

**Quality Assurance**:
- All evaluation scripts version-controlled (Git commit SHA logged with results)
- Random seed fixed (seed=42) for reproducible sample shuffling
- Intermediate results checksummed to detect data corruption
- Results independently validated on separate hardware to ensure reproducibility

---

**This concludes Section 3.9**. The actual threshold optimization **results** (i.e., the specific optimal τ* values, performance metrics, and PR curves) will be presented in Chapter 4 (Results), while this section establishes the **methodology** for how those results were obtained.
