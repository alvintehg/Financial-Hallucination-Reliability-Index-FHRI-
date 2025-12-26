# 3.10 Variables and Metrics

This section operationalizes the research questions by defining the independent variables (inputs to the FHRI system), dependent variables (performance outcomes), and control variables (factors held constant). Additionally, it specifies the quantitative metrics used to evaluate detection performance.

---

## 3.10.1 Independent Variables (IV)

Independent variables are the manipulated factors in the experimental design that are hypothesized to influence FHRI detection performance.

### **IV1: FHRI Acceptance Threshold (τ)**

**Definition**: The minimum FHRI composite score required to classify a generated response as "accurate." Responses with FHRI < τ are classified as "hallucination" (unless overridden by contradiction detection).

**Type**: Continuous numeric variable

**Range**: τ ∈ [0.50, 0.95]

**Levels Tested**: 10 discrete values {0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95}

**Manipulation Method**:
- **Global Threshold Sweep** (Condition A): Single τ applied uniformly across all scenarios
- **Scenario-Specific Sweep** (Condition B): Each scenario s has its own τ_s optimized independently

**Operationalization**:
```python
predicted_label = {
    "accurate"       if fhri_score >= τ AND nli_score < 0.40
    "contradiction"  if nli_score >= 0.40
    "hallucination"  otherwise
}
```

**Rationale**: Different financial scenarios have varying tolerance for uncertainty. For example, numeric KPI queries (e.g., "What is Apple's P/E ratio?") demand higher certainty (τ = 0.75) than subjective advice queries (e.g., "Should I rebalance?") which allow lower thresholds (τ = 0.50).

---

### **IV2: Detection Method**

**Definition**: The set of FHRI components used for hallucination detection.

**Type**: Categorical variable (2 levels)

**Levels**:
1. **FHRI-Full**: All five components (Grounding, Numerical/Directional, Temporal, Citation, Entropy)
   - Weight vector: w = [0.25, 0.25, 0.20, 0.15, 0.15]
   - FHRI = 0.25G + 0.25N + 0.20T + 0.15C + 0.15E

2. **FHRI-NoEntropy**: Four components (G, N, T, C) with renormalized weights
   - Weight vector: w = [0.294, 0.294, 0.235, 0.177, 0.00]
   - FHRI = 0.294G + 0.294N + 0.235T + 0.177C

**Manipulation Method**: Experimental Condition C (Baseline Comparison)

**Operationalization**:
- Both methods evaluate the same 8,000-sample dataset
- Same scenario thresholds (τ_scenario) applied for fair comparison
- Difference isolates the incremental contribution of MC-Dropout entropy

**Hypothesis**: FHRI-Full outperforms FHRI-NoEntropy, demonstrating that uncertainty quantification adds value beyond fact-based validation alone.

---

### **IV3: Financial Scenario Type**

**Definition**: The semantic category of the user's financial query, which determines context-specific FHRI component weights and acceptance thresholds.

**Type**: Categorical variable (10 levels)

**Levels**:

| Scenario ID | Description | Example Query | Expected FHRI Emphasis |
|-------------|-------------|---------------|------------------------|
| `numeric_kpi` | Numeric financial metrics | "What is Tesla's current P/E ratio?" | High N/D weight (0.50), strict τ (0.75) |
| `intraday` | Real-time market data | "What's the S&P 500 at right now?" | High T weight (0.20), strict τ (0.75) |
| `directional` | Trend analysis | "Did Apple's revenue grow last quarter?" | Balanced N/D (0.45) and T (0.20) |
| `fundamentals` | Company fundamentals | "What is Microsoft's market cap?" | Balanced G (0.25) and N (0.40) |
| `regulatory` | Compliance/legal queries | "What are SEC disclosure requirements?" | High C weight (0.40), moderate τ (0.70) |
| `advice` | Investment recommendations | "Should I invest in bonds?" | Low τ (0.50), higher E weight (0.20) |
| `portfolio_advice` | Portfolio strategy | "How should I allocate my 401k?" | Lowest τ (0.50), subjective |
| `multi_ticker` | Comparative analysis | "Compare TSLA and AAPL revenue" | Moderate G (0.30), τ (0.65) |
| `news` | News summarization | "What happened at the latest Fed meeting?" | High G weight (0.45), moderate τ (0.65) |
| `crypto` | Cryptocurrency queries | "Is Ethereum proof-of-stake?" | Moderate τ (0.65), emerging domain |
| `default` | Unclassified queries | Generic financial questions | Conservative τ (0.70) |

**Manipulation Method**: Stratified sampling ensures 800 samples per scenario in the evaluation dataset

**Detection Logic**: Implemented via regex-based pattern matching in `scenario_detection.py`:
- Keyword matching (e.g., "P/E" → numeric_kpi, "Fed" → regulatory)
- Contextual patterns (e.g., "proof-of-stake" → crypto)
- Fallback to `default` if no pattern matches

**Hypothesis**: Scenario-specific thresholds (τ_s) outperform a global uniform threshold (τ_global) by adapting to domain-specific risk profiles.

---

### **IV4: Contradiction Pair Structure**

**Definition**: Whether a sample is part of a sequential contradiction pair (baseline + follow-up) or a standalone sample.

**Type**: Binary categorical variable (2 levels)

**Levels**:
1. **Standalone Sample**: No `contradiction_pair_id`; evaluated independently
2. **Contradiction Pair**: Two linked samples sharing a `contradiction_pair_id`:
   - Sample A (baseline): Labeled "accurate"
   - Sample B (follow-up): Labeled "contradiction"

**Manipulation Method**:
- 20% of dataset (1,600 samples) organized into 800 contradiction pairs
- Each pair tests whether the system detects when the LLM reverses its prior claim

**Operationalization**:
- Baseline sample answer stored as `prev_answer`
- Follow-up sample includes `prev_answer` in NLI scoring:
  ```python
  nli_score = contradiction_score_bidirectional(
      premise=prev_answer,
      hypothesis=current_answer,
      question=query_text
  )
  ```

**Hypothesis**: NLI-based contradiction detection (using DeBERTa-v3-base with τ_hard = 0.40) achieves ≥ 70% recall on contradiction pairs.

---

## 3.10.2 Dependent Variables (DV)

Dependent variables are the measured outcomes that quantify FHRI system performance. These metrics operationalize the concept of "detection efficacy" across the three classification categories.

### **DV1: Classification Accuracy**

**Definition**: The proportion of samples correctly classified across all three categories (Accurate, Hallucination, Contradiction).

**Formula**:
$$\text{Accuracy} = \frac{\text{TP}_{\text{all}} + \text{TN}_{\text{all}}}{N}$$

Where:
- TP_all = Sum of true positives across all classes
- TN_all = Sum of true negatives across all classes
- N = Total number of samples (8,000)

**Alternative Formulation** (for multi-class):
$$\text{Accuracy} = \frac{\sum_{i=1}^{N} \mathbb{1}[y_i = \hat{y}_i]}{N}$$

Where $y_i$ is the true label and $\hat{y}_i$ is the predicted label for sample $i$.

**Range**: [0, 1] or [0%, 100%]

**Interpretation**:
- 1.0 (100%): Perfect classification; all predictions match ground truth
- 0.5 (50%): Random guessing performance for balanced 3-class problem
- < 0.60: Unacceptable; worse than simple majority-class baseline

**Reporting**: Rounded to 4 decimal places (e.g., 0.9600 = 96.00%)

**Data Source**: Calculated from confusion matrix diagonal

---

### **DV2: Per-Class Precision**

**Definition**: The proportion of positive predictions for a class that are truly positive.

**Formula** (for class $c$):
$$\text{Precision}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}$$

Where:
- TP_c = True Positives for class $c$ (predicted $c$ AND true label is $c$)
- FP_c = False Positives for class $c$ (predicted $c$ BUT true label is NOT $c$)

**Class-Specific Formulations**:

1. **Hallucination Precision**:
   $$P_{\text{hall}} = \frac{\text{# correctly flagged hallucinations}}{\text{# all samples flagged as hallucinations}}$$
   - **Interpretation**: Of all responses the system flagged as hallucinations, what percentage were actually hallucinations?
   - **Critical for**: Avoiding false alarms that erode user trust

2. **Accurate Precision**:
   $$P_{\text{acc}} = \frac{\text{# correctly classified accurate}}{\text{# all samples classified as accurate}}$$
   - **Interpretation**: Of all responses the system passed as accurate, what percentage were truly accurate?
   - **Critical for**: Ensuring reliable information delivery

3. **Contradiction Precision**:
   $$P_{\text{contr}} = \frac{\text{# correctly detected contradictions}}{\text{# all samples flagged as contradictions}}$$
   - **Interpretation**: Of all responses flagged as contradictions, what percentage were genuine contradictions?
   - **Critical for**: Maintaining coherence across multi-turn conversations

**Range**: [0, 1]

**Threshold Dependency**: Precision typically increases with higher FHRI thresholds (fewer false positives) but decreases recall

**Reporting**: Rounded to 4 decimal places

---

### **DV3: Per-Class Recall (Sensitivity)**

**Definition**: The proportion of true instances of a class that are correctly identified.

**Formula** (for class $c$):
$$\text{Recall}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}$$

Where:
- FN_c = False Negatives for class $c$ (true label is $c$ BUT predicted NOT $c$)

**Class-Specific Formulations**:

1. **Hallucination Recall**:
   $$R_{\text{hall}} = \frac{\text{# correctly detected hallucinations}}{\text{# all true hallucinations in dataset}}$$
   - **Interpretation**: Of all actual hallucinations, what percentage did the system detect?
   - **Critical for**: User safety; missed hallucinations (false negatives) are dangerous
   - **Minimum Acceptable**: ≥ 80% (per constraint in RQ3)

2. **Accurate Recall**:
   $$R_{\text{acc}} = \frac{\text{# correctly passed accurate}}{\text{# all true accurate responses}}$$
   - **Interpretation**: Of all truly accurate responses, what percentage passed the FHRI check?
   - **Critical for**: System usability; low recall → excessive false positives

3. **Contradiction Recall**:
   $$R_{\text{contr}} = \frac{\text{# correctly detected contradictions}}{\text{# all true contradictions}}$$
   - **Interpretation**: Of all actual contradictions, what percentage were caught?
   - **Critical for**: Multi-turn conversation coherence
   - **Minimum Acceptable**: ≥ 70% (per constraint in RQ3)

**Range**: [0, 1]

**Threshold Dependency**: Recall typically decreases with higher FHRI thresholds (more false negatives)

**Reporting**: Rounded to 4 decimal places

---

### **DV4: Per-Class F1-Score**

**Definition**: The harmonic mean of precision and recall, balancing both metrics into a single score.

**Formula** (for class $c$):
$$F1_c = 2 \cdot \frac{P_c \cdot R_c}{P_c + R_c}$$

**Alternative Formulation**:
$$F1_c = \frac{2 \cdot \text{TP}_c}{2 \cdot \text{TP}_c + \text{FP}_c + \text{FN}_c}$$

**Properties**:
- **Harmonic Mean**: Penalizes extreme imbalances (e.g., P=1.0, R=0.1 → F1=0.18, not 0.55)
- **Range**: [0, 1]
- **Maximum**: F1 = 1.0 when P = R = 1.0 (perfect precision and recall)
- **Minimum**: F1 = 0.0 when either P or R = 0

**Class-Specific Importance**:

1. **Hallucination F1**: Most critical metric for safety
   - Balances avoiding false alarms (precision) with catching real hallucinations (recall)

2. **Accurate F1**: Indicates system usability
   - High F1 → system reliably passes good answers and flags bad ones

3. **Contradiction F1**: Measures coherence maintenance
   - High F1 → system detects self-contradictions without over-flagging paraphrases

**Threshold Selection**: Optimal τ* is chosen to maximize per-class F1 scores (or Macro-F1)

**Reporting**: Rounded to 4 decimal places

---

### **DV5: Macro-Averaged F1 Score**

**Definition**: The unweighted average of F1 scores across all three classes.

**Formula**:
$$\text{Macro-F1} = \frac{1}{3}\left(F1_{\text{hallucination}} + F1_{\text{accurate}} + F1_{\text{contradiction}}\right)$$

**Rationale for Macro-Averaging**:
- Treats all three classes as **equally important** regardless of sample size
- Prevents optimization bias toward the majority class (Accurate = 60% of dataset)
- Standard metric for imbalanced multi-class problems

**Alternative: Micro-F1** (NOT used in this study):
$$\text{Micro-F1} = \frac{2 \cdot \sum_{c} \text{TP}_c}{2 \cdot \sum_{c} \text{TP}_c + \sum_{c} \text{FP}_c + \sum_{c} \text{FN}_c}$$
- Micro-F1 would bias toward the Accurate class due to its larger support
- Macro-F1 ensures minority classes (Hallucination, Contradiction) have equal weight

**Range**: [0, 1]

**Primary Optimization Criterion**: Threshold sweeps maximize Macro-F1 subject to safety constraints (Hallucination Recall ≥ 80%)

**Reporting**: Rounded to 4 decimal places

**Interpretation**:
- Macro-F1 > 0.90: Excellent detection across all classes
- Macro-F1 ∈ [0.75, 0.90]: Good detection; acceptable for deployment
- Macro-F1 < 0.75: Insufficient; requires threshold recalibration or system redesign

---

### **DV6: Confusion Matrix**

**Definition**: A 3×3 matrix tabulating predicted labels against true labels for all samples.

**Structure**:

|                  | **Predicted: Hallucination** | **Predicted: Accurate** | **Predicted: Contradiction** |
|------------------|------------------------------|-------------------------|------------------------------|
| **True: Hallucination** | TP_hall (correct)     | FN_hall → Acc (missed)  | FN_hall → Contr (misclassified) |
| **True: Accurate**      | FP_acc → Hall (false alarm) | TP_acc (correct)        | FN_acc → Contr (misclassified) |
| **True: Contradiction** | FP_contr → Hall (misclassified) | FN_contr → Acc (missed) | TP_contr (correct) |

**Notation**:
- Rows: True labels (ground truth)
- Columns: Predicted labels (system output)
- Diagonal elements: Correct classifications (TP)
- Off-diagonal elements: Errors (FP, FN)

**Data Type**: 3×3 integer matrix

**Derived Metrics**:
- Row sums: Support (number of samples per true class)
- Column sums: Predicted class frequencies
- Diagonal sum: Total correct predictions
- Off-diagonal analysis: Common error patterns (e.g., "Hallucinations misclassified as Accurate")

**Reporting**:
- Absolute counts (integer values)
- Percentage heatmap (cell value / row total) for visualization

**Error Analysis Use Case**:
```
Example Confusion Matrix (hypothetical):
                  Pred_Hall  Pred_Acc  Pred_Contr
True_Hall            1600       300        100
True_Acc              0        5900       100
True_Contr            50        50        1900

Error Pattern: 300 hallucinations misclassified as accurate (FN_hall → Acc)
→ Indicates FHRI threshold may be too lenient (need higher τ)
```

---

### **DV7: True Positives, False Positives, False Negatives, True Negatives**

**Definition**: Standard binary classification metrics extended to multi-class via **One-vs-Rest** decomposition.

For each class $c$, we compute:

**True Positives (TP_c)**:
- Count of samples where **true label = $c$** AND **predicted label = $c$**
- Example (Hallucination): System correctly flagged a hallucination

**False Positives (FP_c)**:
- Count of samples where **true label ≠ $c$** AND **predicted label = $c$**
- Example (Hallucination): System flagged an accurate response as hallucination (false alarm)

**False Negatives (FN_c)**:
- Count of samples where **true label = $c$** AND **predicted label ≠ $c$**
- Example (Hallucination): System missed a hallucination (dangerous!)

**True Negatives (TN_c)**:
- Count of samples where **true label ≠ $c$** AND **predicted label ≠ $c$**
- Example (Hallucination): System correctly did NOT flag a non-hallucination

**Computation** (for class $c$):
```python
TP_c = sum(1 for i in samples if true[i] == c and pred[i] == c)
FP_c = sum(1 for i in samples if true[i] != c and pred[i] == c)
FN_c = sum(1 for i in samples if true[i] == c and pred[i] != c)
TN_c = sum(1 for i in samples if true[i] != c and pred[i] != c)
```

**Verification Constraint**:
$$\text{TP}_c + \text{FP}_c + \text{FN}_c + \text{TN}_c = N$$

**Data Type**: Integer counts

**Reporting**: Absolute values (not percentages) in detailed results JSON

**Use Case**: Diagnostic analysis to identify systematic biases (e.g., high FP_contradiction → NLI threshold too low)

---

### **DV8: Support (Class Frequency)**

**Definition**: The number of samples in the dataset with a given true label.

**Formula** (for class $c$):
$$\text{Support}_c = \text{TP}_c + \text{FN}_c$$

**Alternative**: Count of samples where true label = $c$

**Values in Evaluation Dataset**:
- Support_hallucination = 1,600 (20% of 8,000)
- Support_accurate = 4,800 (60% of 8,000)
- Support_contradiction = 1,600 (20% of 8,000)

**Purpose**:
- **Context for Metrics**: Precision/Recall have different implications for high-support vs. low-support classes
- **Stratification Validation**: Confirms dataset follows intended 60/20/20 distribution
- **Weighted Metrics**: (Not used in this study, but support enables weighted-F1 calculation)

**Data Type**: Integer count

**Reporting**: Included in per-class metric tables

---

## 3.10.3 Control Variables

Control variables are factors held constant across all experimental conditions to isolate the effects of independent variables.

### **CV1: LLM Backbone**

**Fixed Value**: DeepSeek-V3 (via OpenRouter API)

**Configuration**:
- Temperature: 0.2 (low stochasticity for factual consistency)
- Max tokens: 256
- Top-p: 1.0
- Frequency penalty: 0.0

**Rationale**: Using a single LLM eliminates confounding from model capability variance. Different LLMs (e.g., GPT-4-Turbo vs. DeepSeek-V3) may produce answers of varying quality, making it unclear whether performance differences stem from FHRI logic or LLM quality.

---

### **CV2: Retrieval Configuration**

**Fixed Value**: Top-5 passages from FAISS hybrid search

**Configuration**:
- Dense retrieval: `sentence-transformers/all-MiniLM-L6-v2` embeddings
- Sparse retrieval: BM25 re-ranking
- Index: FAISS IVF1024_HNSW32
- Retrieval cutoff: k=5 (top-5 most relevant passages)

**Rationale**: Retrieval quality directly affects grounding score (G). Holding k=5 constant ensures fair comparison across scenarios.

---

### **CV3: NLI Model**

**Fixed Value**: DeBERTa-v3-base (`cross-encoder/nli-deberta-v3-base`)

**Configuration**:
- Bidirectional scoring (max of forward and backward directions)
- Hard threshold: 0.40
- Soft threshold: 0.15

**Rationale**: Contradiction detection must be consistent across all samples to isolate FHRI threshold effects.

---

### **CV4: Dataset Composition**

**Fixed Value**: 8,000 samples with stratified 60/20/20 label distribution

**Stratification**:
- Scenarios: 800 samples per scenario (10 scenarios)
- Labels: 4,800 Accurate / 1,600 Hallucination / 1,600 Contradiction

**Rationale**: Ensures representative coverage of financial domains and prevents label imbalance from confounding results.

---

### **CV5: Ground Truth Annotation Protocol**

**Fixed Value**: Hybrid automated + manual annotation with Cohen's κ = 0.87

**Configuration**:
- Stage 1: Automated pre-labeling (70% of samples)
- Stage 2: Manual expert review (30% of samples)
- Stage 3: Inter-rater reliability check (5% cross-annotation)

**Rationale**: Consistent annotation quality ensures that performance metrics reflect FHRI efficacy, not label noise.

---

### **CV6: Evaluation Mode**

**Fixed Value**: Static evaluation (pre-generated answers)

**Configuration**:
- Answers and FHRI scores pre-computed during dataset construction
- No live API calls during threshold sweeps
- Deterministic classification logic

**Rationale**: Eliminates stochastic variance from LLM generation and API latency, enabling reproducible threshold optimization.

**Exception**: Dynamic evaluation (Section 3.13) uses live mode for 200 samples to validate ecological validity, but this is a **separate validation phase**, not part of threshold optimization.

---

## 3.10.4 Summary of Variables

**Table 3.4.1**: Variable Summary

| Variable | Type | Role | Levels/Range | Manipulation/Measurement |
|----------|------|------|--------------|--------------------------|
| **Independent Variables** |
| FHRI Threshold (τ) | Continuous | IV1 | [0.50, 0.95], step 0.05 | Grid search sweep (Conditions A, B) |
| Detection Method | Categorical | IV2 | FHRI-Full, FHRI-NoEntropy | Experimental condition (Condition C) |
| Scenario Type | Categorical | IV3 | 10 scenarios | Stratified sampling |
| Contradiction Pair | Binary | IV4 | Standalone, Paired | Dataset structure (20% paired) |
| **Dependent Variables** |
| Classification Accuracy | Continuous | DV1 | [0, 1] | (TP+TN)/N |
| Per-Class Precision | Continuous | DV2 | [0, 1] | TP/(TP+FP) per class |
| Per-Class Recall | Continuous | DV3 | [0, 1] | TP/(TP+FN) per class |
| Per-Class F1-Score | Continuous | DV4 | [0, 1] | 2PR/(P+R) per class |
| Macro-F1 | Continuous | DV5 | [0, 1] | Mean of class F1 scores |
| Confusion Matrix | Integer Matrix | DV6 | 3×3 counts | Tabulation of predictions |
| TP/FP/FN/TN | Integer | DV7 | [0, N] | One-vs-Rest decomposition |
| Support | Integer | DV8 | [0, N] | Count per true label |
| **Control Variables** |
| LLM Backbone | Categorical | CV1 | DeepSeek-V3 | Fixed |
| Retrieval Config | Numeric | CV2 | k=5, FAISS | Fixed |
| NLI Model | Categorical | CV3 | DeBERTa-v3-base | Fixed |
| Dataset Size | Integer | CV4 | N=8,000 | Fixed |
| Annotation Protocol | Categorical | CV5 | Hybrid (κ=0.87) | Fixed |
| Evaluation Mode | Categorical | CV6 | Static | Fixed (except Section 3.13) |

---

## 3.10.5 Metric Reporting Standards

To ensure transparency and reproducibility, all quantitative results are reported according to the following standards:

**Rounding Precision**:
- **Accuracy, Precision, Recall, F1**: 4 decimal places (e.g., 0.9600)
- **Percentage Format**: 2 decimal places when expressed as % (e.g., 96.00%)
- **Counts (TP, FP, FN, TN)**: Integer values (no rounding)
- **FHRI Scores**: 2 decimal places (e.g., 0.75)
- **NLI Scores**: 2 decimal places (e.g., 0.68)

**Confidence Intervals** (where applicable):
- 95% confidence intervals calculated using normal approximation for proportions:
  $$\text{CI}_{95} = \hat{p} \pm 1.96 \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$
- Example: Accuracy = 0.96 ± 0.004 (95% CI: [0.956, 0.964])

**Statistical Significance**:
- **McNemar's Test**: p-value reported to 4 decimal places (e.g., p=0.0023)
- **Significance Level**: α = 0.05
- **Notation**: * p < 0.05, ** p < 0.01, *** p < 0.001

**Visualization Standards**:
- **Confusion Matrices**: Heatmap with row normalization (percentage of true class)
- **PR Curves**: Precision on y-axis, Recall on x-axis, F1 contours overlaid
- **Bar Charts**: Error bars show ±1 standard deviation (when applicable)

**Data Provenance**:
- All reported metrics include metadata:
  - Evaluation script version (Git commit SHA)
  - Dataset file (with MD5 checksum)
  - Timestamp of evaluation run
  - Threshold configuration used

**Example Metric Report** (from JSON output):
```json
{
  "evaluation_metadata": {
    "backend_url": "http://localhost:8000",
    "hallucination_threshold": 2.0,
    "fhri_threshold": 0.70,
    "total_samples": 8000,
    "evaluation_date": "2025-12-15 03:52:18",
    "git_commit": "a3f2c1d",
    "dataset_md5": "8f4e3a2b..."
  },
  "metrics": {
    "hallucination": {
      "precision": 0.9600,
      "recall": 0.8000,
      "f1_score": 0.8727,
      "support": 1600
    },
    "overall": {
      "accuracy": 0.9600,
      "macro_f1": 0.9522
    }
  }
}
```

---

This concludes Section 3.10, providing a comprehensive operationalization of all variables and metrics used to evaluate the FHRI system. The actual empirical values of these metrics (e.g., "Hallucination Recall = 80%") will be reported in Chapter 4 (Results).
