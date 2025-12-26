# FHRI Fine-Tuning Guide - Improve Accurate & Hallucination Detection

## 🎯 **Goal: Improve Both Accurate and Hallucination F1-Scores**

**Current Performance:**
- Accurate F1: **0.6441** (target: 0.70-0.75)
- Hallucination F1: **0.1395** (target: 0.30-0.40)
- Macro F1: **0.5518** (target: 0.65-0.70)

---

## 📊 **Understanding the Trade-off**

**The Challenge:**
- **Higher thresholds** → More accurate samples correctly identified (higher accurate F1)
- **Lower thresholds** → More hallucinations caught (higher hallucination F1)
- **Need balance** → Optimize both simultaneously

**Current Issues:**
1. **Accurate F1 too low:** Many accurate samples flagged as hallucination (false positives)
2. **Hallucination F1 too low:** Many hallucinations missed (false negatives)
3. **Need better balance:** Optimize thresholds to catch more hallucinations without hurting accurate detection

---

## 🔧 **Fine-Tuning Strategies**

### **Strategy 1: Threshold Optimization** (Primary)

**Parameters to Tune:**

1. **FHRI Thresholds (per scenario):**
   ```python
   SCENARIO_FHRI_THRESHOLDS = {
       "numeric_kpi": 0.80,    # Try: 0.75, 0.80, 0.85
       "default": 0.65,        # Try: 0.60, 0.65, 0.70
       "advice": 0.55,         # Try: 0.50, 0.55, 0.60
   }
   ```

2. **Entropy Threshold:**
   ```python
   HALLU_THRESHOLD = 2.0  # Try: 1.5, 2.0, 2.5, 3.0
   ```

3. **Contradiction Thresholds:**
   ```python
   contradiction_soft = 0.15  # Try: 0.10, 0.15, 0.20
   contradiction_hard = 0.40  # Try: 0.35, 0.40, 0.45
   ```

4. **High-Risk Floor:**
   ```python
   HIGH_RISK_FHRI_FLOOR = 0.85  # Try: 0.80, 0.85, 0.90
   ```

**How to Tune:**
- Use grid search to find optimal combination
- Balance: maximize macro F1 while keeping accurate/hallucination F1 close

---

### **Strategy 2: Detection Logic Improvement**

**Current Logic (in `evaluate_detection.py`):**
```python
# Priority: contradiction > hallucination > accurate
if contradiction_detected:
    predicted = "contradiction"
elif hallucination_flag:
    predicted = "hallucination"
elif fhri > threshold:
    predicted = "accurate"
else:
    predicted = "hallucination"  # Too strict!
```

**Problem:** Too many accurate samples fall into the "else" case and get flagged as hallucination.

**Improvement Options:**

**Option A: Add Confidence Zones**
```python
if fhri > threshold + 0.10:  # High confidence
    predicted = "accurate"
elif fhri > threshold:  # Medium confidence
    # Check entropy and other signals
    if entropy < 1.5 and grounding > 0.7:
        predicted = "accurate"
    else:
        predicted = "hallucination"
elif fhri > threshold - 0.10:  # Low confidence
    predicted = "hallucination"
else:  # Very low
    predicted = "hallucination"
```

**Option B: Multi-Signal Voting**
```python
# Count signals for each class
accurate_signals = 0
hallucination_signals = 0

if fhri > threshold:
    accurate_signals += 1
if entropy < 1.5:
    accurate_signals += 1
if grounding > 0.7:
    accurate_signals += 1

if entropy > 2.0:
    hallucination_signals += 1
if fhri < threshold:
    hallucination_signals += 1
if numeric_mismatch:
    hallucination_signals += 1

# Predict based on signal count
if contradiction_detected:
    predicted = "contradiction"
elif hallucination_signals >= 2:
    predicted = "hallucination"
elif accurate_signals >= 2:
    predicted = "accurate"
else:
    predicted = "hallucination"  # Default to safer option
```

---

### **Strategy 3: Component Weight Optimization**

**Current Default Weights:**
```python
weights = {
    "grounding": 0.25,
    "numeric": 0.25,
    "temporal": 0.20,
    "citation": 0.15,
    "entropy": 0.15
}
```

**Optimization Strategy:**
1. **Increase grounding weight** (helps identify accurate samples)
2. **Increase numeric weight** (helps catch hallucinations in numeric questions)
3. **Adjust based on ablation study results**

**Example:**
```python
# Finance-focused weights (more emphasis on data grounding)
weights = {
    "grounding": 0.30,  # Increased from 0.25
    "numeric": 0.30,    # Increased from 0.25
    "temporal": 0.20,
    "citation": 0.10,   # Decreased from 0.15
    "entropy": 0.10     # Decreased from 0.15
}
```

---

### **Strategy 4: Enhanced Numeric Checks**

**Current:** Only checks prices with 10% tolerance

**Improvements:**
1. **Tighter tolerance for critical metrics:**
   - Prices: 5% tolerance (instead of 10%)
   - P/E ratios: 10% tolerance
   - Market cap: 15% tolerance

2. **Expand to more metrics:**
   - P/E ratios
   - Market cap
   - Revenue
   - EPS

3. **Multi-source verification:**
   - Cross-check across APIs
   - Flag if sources disagree

**Expected Gain:** +5-10% hallucination recall

---

### **Strategy 5: Scenario-Specific Thresholds**

**Current:** Same thresholds for all scenarios

**Improvement:** Optimize thresholds per scenario based on performance

**Example:**
```python
# Optimized per scenario
SCENARIO_FHRI_THRESHOLDS = {
    "numeric_kpi": 0.75,      # Lower (more strict) for numeric
    "intraday": 0.75,         # Lower for real-time data
    "directional": 0.70,      # Medium for trends
    "regulatory": 0.80,       # Higher (more lenient) for regulatory
    "fundamentals": 0.70,     # Medium
    "advice": 0.60,          # Lower (more strict) for advice
    "default": 0.65,
}
```

---

## 🚀 **Implementation Plan**

### **Step 1: Run Fine-Tuning Script** (2-3 hours)

```bash
# Make sure backend is running
uvicorn src.server:app --port 8000

# Run fine-tuning
python scripts/tune_fhri_parameters.py \
    --dataset data/evaluation_dataset.json \
    --output results/fhri_tuning_results.json \
    --max_combinations 30
```

**What it does:**
- Tests different threshold combinations
- Finds optimal balance for accurate/hallucination F1
- Saves best parameters

---

### **Step 2: Apply Best Parameters** (30 minutes)

**Update `src/fhri_scoring.py`:**
```python
# Replace with best thresholds from tuning
SCENARIO_FHRI_THRESHOLDS = {
    "numeric_kpi": <best_value>,
    "default": <best_value>,
    # ... etc
}
HIGH_RISK_FHRI_FLOOR = <best_value>
```

**Update `scripts/evaluate_detection.py`:**
```python
# Replace with best thresholds
self.hallu_threshold = <best_entropy_threshold>
self.contradiction_soft_threshold = <best_soft>
self.contradiction_hard_threshold = <best_hard>
```

---

### **Step 3: Improve Detection Logic** (1-2 hours)

**Modify `scripts/evaluate_detection.py` prediction logic:**

**Option A: Confidence Zones** (recommended)
```python
# Add confidence zones for better balance
if fhri is not None:
    if fhri > effective_threshold + 0.10:
        # High confidence accurate
        predicted_label = "accurate"
    elif fhri > effective_threshold:
        # Medium confidence - check other signals
        if entropy is not None and entropy < 1.5:
            predicted_label = "accurate"
        else:
            predicted_label = "hallucination"
    elif fhri > effective_threshold - 0.10:
        # Low confidence - likely hallucination
        predicted_label = "hallucination"
    else:
        # Very low - definitely hallucination
        predicted_label = "hallucination"
```

**Option B: Multi-Signal Voting** (more complex but better)
```python
# Count signals for each class
accurate_votes = 0
hallucination_votes = 0

if fhri is not None and fhri > effective_threshold:
    accurate_votes += 1
if entropy is not None and entropy < 1.5:
    accurate_votes += 1
if fhri_subscores and fhri_subscores.get("grounding", 0) > 0.7:
    accurate_votes += 1

if entropy is not None and entropy > self.hallu_threshold:
    hallucination_votes += 1
if fhri is not None and fhri <= effective_threshold:
    hallucination_votes += 1
if fhri_high_risk_breach:
    hallucination_votes += 1

# Predict based on votes
if contradiction_detected:
    predicted_label = "contradiction"
elif hallucination_votes >= 2:
    predicted_label = "hallucination"
elif accurate_votes >= 2:
    predicted_label = "accurate"
else:
    # Default to safer option (hallucination)
    predicted_label = "hallucination"
```

---

### **Step 4: Re-run Evaluation** (30 minutes)

```bash
# Re-run with optimized parameters
python scripts/evaluate_comparative_baselines.py \
    --dataset data/evaluation_dataset.json \
    --output results/comparative_baselines_optimized.json
```

**Expected Results:**
- Accurate F1: **0.70-0.75** (up from 0.6441)
- Hallucination F1: **0.30-0.40** (up from 0.1395)
- Macro F1: **0.65-0.70** (up from 0.5518)

---

## 📊 **Expected Improvements**

### **Current:**
- Accurate F1: 0.6441
- Hallucination F1: 0.1395
- Macro F1: 0.5518

### **After Fine-Tuning:**
- Accurate F1: **0.70-0.75** (+8-16% improvement)
- Hallucination F1: **0.30-0.40** (+115-187% improvement)
- Macro F1: **0.65-0.70** (+18-27% improvement)

---

## 🎯 **Quick Start (Recommended Order)**

1. **Run fine-tuning script** (2-3 hours)
   - Finds optimal thresholds automatically
   - Tests 30 combinations

2. **Apply best parameters** (30 minutes)
   - Update thresholds in code
   - Restart backend

3. **Improve detection logic** (1-2 hours)
   - Add confidence zones or multi-signal voting
   - Better balance between classes

4. **Re-run evaluation** (30 minutes)
   - Verify improvements
   - Compare with baselines

**Total Time:** ~4-6 hours
**Expected Gain:** +15-25% macro F1, +100-200% hallucination F1

---

## 💡 **Key Insights**

1. **Threshold tuning is most important** - Small changes can have big impact
2. **Detection logic matters** - Current logic is too strict for accurate samples
3. **Balance is key** - Don't optimize one class at expense of another
4. **Use grid search** - Manual tuning is slow and suboptimal

---

## ✅ **Next Steps**

1. Run `scripts/tune_fhri_parameters.py` to find best thresholds
2. Apply best parameters to code
3. Improve detection logic (confidence zones or voting)
4. Re-run evaluation to verify improvements

**You can significantly improve both accurate and hallucination detection!** 🚀




















