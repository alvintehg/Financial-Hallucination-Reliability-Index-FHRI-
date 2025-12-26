# 3.10 Variables and Metrics

This section defines the independent variables (manipulated inputs), dependent variables (measured outcomes), and control variables (factors held constant) used in the FHRI evaluation.

---

## 3.10.1 Independent Variables (IV)

### **IV1: FHRI Acceptance Threshold (τ)**

The minimum FHRI composite score required to classify a response as "accurate." Responses with FHRI < τ are classified as "hallucination."

- **Type**: Continuous
- **Range**: τ ∈ [0.50, 0.95], step 0.05 (10 values tested)
- **Levels**: Global threshold (Condition A) vs. Scenario-specific thresholds (Condition B)

### **IV2: Detection Method**

The set of FHRI components used for classification.

- **Type**: Categorical (2 levels)
- **Levels**:
  1. **FHRI-Full**: All 5 components (G, N/D, T, C, E) with weights [0.25, 0.25, 0.20, 0.15, 0.15]
  2. **FHRI-NoEntropy**: 4 components (G, N/D, T, C) with renormalized weights [0.294, 0.294, 0.235, 0.177]

### **IV3: Financial Scenario Type**

The semantic category of the query, determining component weights and thresholds.

- **Type**: Categorical (10 levels)
- **Scenarios**: `numeric_kpi`, `intraday`, `directional`, `fundamentals`, `regulatory`, `advice`, `portfolio_advice`, `multi_ticker`, `news`, `crypto`, `default`
- **Distribution**: 800 samples per scenario (stratified sampling)

### **IV4: Contradiction Pair Structure**

Whether a sample is standalone or part of a sequential contradiction pair.

- **Type**: Binary (Standalone vs. Paired)
- **Paired Samples**: 20% of dataset (1,600 samples = 800 pairs)
- **Structure**: Each pair has baseline (accurate) + follow-up (contradiction) sharing `contradiction_pair_id`

---

## 3.10.2 Dependent Variables (DV)

Performance is measured using standard multi-class classification metrics:

### **Primary Metrics**

**1. Classification Accuracy**
$$\text{Accuracy} = \frac{\text{Correct Predictions}}{N} = \frac{\sum_{i=1}^{N} \mathbb{1}[y_i = \hat{y}_i]}{N}$$
- Range: [0, 1]
- Interpretation: Overall proportion of correct classifications

**2. Per-Class Precision**
$$\text{Precision}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FP}_c}$$
- Interpretation: Of all samples predicted as class $c$, what % were correct?
- Critical for: Avoiding false positives (e.g., wrongly flagging accurate responses)

**3. Per-Class Recall**
$$\text{Recall}_c = \frac{\text{TP}_c}{\text{TP}_c + \text{FN}_c}$$
- Interpretation: Of all true class $c$ samples, what % were detected?
- Critical for: Safety (must detect ≥80% of hallucinations per RQ3 constraint)

**4. Per-Class F1-Score**
$$F1_c = 2 \cdot \frac{P_c \cdot R_c}{P_c + R_c} = \frac{2 \cdot \text{TP}_c}{2 \cdot \text{TP}_c + \text{FP}_c + \text{FN}_c}$$
- Harmonic mean balancing precision and recall
- Primary metric for per-class performance

**5. Macro-Averaged F1 Score** (Primary Optimization Criterion)
$$\text{Macro-F1} = \frac{1}{3}\left(F1_{\text{hallucination}} + F1_{\text{accurate}} + F1_{\text{contradiction}}\right)$$
- Unweighted average across all three classes
- Prevents bias toward majority class (Accurate = 60% of dataset)
- **Optimization Target**: Maximize Macro-F1 subject to Hallucination Recall ≥ 80%

### **Secondary Metrics**

**6. Confusion Matrix** (3×3)
- Rows: True labels | Columns: Predicted labels
- Diagonal: Correct classifications (TP)
- Off-diagonal: Misclassifications (FP, FN)
- Used for error pattern analysis

**7. True Positives/False Positives/False Negatives/True Negatives**
- Computed per class using One-vs-Rest decomposition
- Reported as integer counts
- Used for diagnostic analysis

**8. Support**
- Number of samples per true label
- Dataset distribution: 4,800 Accurate / 1,600 Hallucination / 1,600 Contradiction

---

## 3.10.3 Control Variables

Factors held constant across all experimental conditions:

| Variable | Fixed Value | Rationale |
|----------|-------------|-----------|
| **LLM Backbone** | DeepSeek-V3 (temp=0.2, max_tokens=256) | Eliminates variance from model capability |
| **Retrieval Config** | Top-5 passages, FAISS hybrid search | Ensures consistent grounding context |
| **NLI Model** | DeBERTa-v3-base (τ_hard=0.40, τ_soft=0.15) | Consistent contradiction detection |
| **Dataset Size** | 8,000 samples (60/20/20 label distribution) | Representative coverage of scenarios |
| **Annotation Quality** | Hybrid protocol (Cohen's κ=0.87) | Reliable ground truth labels |
| **Evaluation Mode** | Static (pre-generated answers) | Reproducible, deterministic results |

---

## 3.10.4 Metric Reporting Standards

**Rounding Precision**:
- Accuracy, Precision, Recall, F1: **4 decimal places** (e.g., 0.9600)
- Percentages: **2 decimal places** (e.g., 96.00%)
- Counts (TP, FP, FN, TN): **Integer values** (no rounding)

**Statistical Significance**:
- McNemar's Test for paired comparison (FHRI-Full vs. NoEntropy)
- Significance level: **α = 0.05**
- Notation: * p < 0.05, ** p < 0.01, *** p < 0.001

**Data Provenance**:
All reported metrics include:
- Evaluation script version (Git commit SHA)
- Dataset file with MD5 checksum
- Timestamp and threshold configuration

---

**Table 3.4**: Summary of Variables

| Variable | Type | Role | Range/Levels |
|----------|------|------|--------------|
| **Independent Variables** ||||
| FHRI Threshold (τ) | Continuous | IV1 | [0.50, 0.95], step 0.05 |
| Detection Method | Categorical | IV2 | FHRI-Full, FHRI-NoEntropy |
| Scenario Type | Categorical | IV3 | 10 scenarios |
| Contradiction Pair | Binary | IV4 | Standalone, Paired |
| **Dependent Variables** ||||
| Accuracy | Continuous | DV1 | [0, 1] |
| Precision (per class) | Continuous | DV2 | [0, 1] |
| Recall (per class) | Continuous | DV3 | [0, 1] |
| F1-Score (per class) | Continuous | DV4 | [0, 1] |
| Macro-F1 | Continuous | DV5 | [0, 1] |
| Confusion Matrix | Integer Matrix | DV6 | 3×3 counts |
| TP/FP/FN/TN | Integer | DV7 | [0, 8000] |
| Support | Integer | DV8 | [0, 8000] |
| **Control Variables** ||||
| LLM, Retrieval, NLI, Dataset, Annotation, Eval Mode | Various | CV1-CV6 | Fixed (see table above) |

---

This concludes Section 3.10. All variable definitions and metric formulas are provided; actual empirical values (e.g., "Accuracy = 96%") will be reported in Chapter 4 (Results).
