# Improving FHRI Performance - Action Plan

## 🎯 **Good News: Phase 4 Already Beats Baselines!**

Your **Phase 4 (Numeric Check)** results show:
- **Macro F1: 0.6391** (vs 0.5518 in comparative baseline)
- **This is HIGHER than all baselines!**

The comparative baseline was likely run with **suboptimal settings**. Let's fix this!

---

## 📊 **Current Situation**

| Method | Macro F1 (Comparative) | Macro F1 (Phase 4) | Status |
|--------|------------------------|-------------------|--------|
| Entropy-Only | 0.242 | - | Baseline |
| NLI-Only | 0.5474 | - | Baseline |
| RAG-Only | 0.242 | - | Baseline |
| **FHRI-Full** | **0.5518** | **0.6391** | ✅ **Already Better!** |

**Phase 4 FHRI (0.6391) beats:**
- ✅ NLI-Only (0.5474) by **+16.8%**
- ✅ Entropy-Only (0.242) by **+164%**
- ✅ RAG-Only (0.242) by **+164%**

---

## 🚀 **Step 1: Re-run Comparative Baseline with Phase 4 Settings**

The comparative baseline was run with default settings. Phase 4 uses optimized settings:

**Phase 4 Optimal Settings:**
- **FHRI Thresholds:** Moderate (numeric_kpi: 0.80, high-risk floor: 0.85)
- **Numeric Check:** Enabled (10% tolerance)
- **Contradiction:** Two-tier (soft: 0.15, hard: 0.40)

**Action:** Re-run comparative baseline with Phase 4 settings to get fair comparison.

---

## 🔧 **Step 2: Further Improvements (Optional)**

### **Option A: Threshold Tuning**

**Current Phase 4 Settings:**
```python
SCENARIO_FHRI_THRESHOLDS = {
    "numeric_kpi": 0.80,
    "intraday": 0.80,
    "directional": 0.75,
    "regulatory": 0.75,
    "fundamentals": 0.70,
    "default": 0.65,
}
HIGH_RISK_FHRI_FLOOR = 0.85
```

**Tuning Strategy:**
1. **Grid Search:** Try different threshold combinations
2. **Per-Scenario Optimization:** Optimize each scenario threshold separately
3. **Balance Precision/Recall:** Adjust thresholds to maximize macro F1

**Expected Improvement:** +2-5% macro F1

---

### **Option B: Component Weight Optimization**

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
1. **Ablation Study Results:** Use component contribution data to adjust weights
2. **Finance-Specific:** Increase weights for numeric/grounding (finance is data-heavy)
3. **Machine Learning:** Use optimization algorithm (Optuna) to find best weights

**Expected Improvement:** +1-3% macro F1

---

### **Option C: Enhanced Numeric Checks**

**Current:** Only checks prices with 10% tolerance

**Enhancements:**
1. **Expand to More Metrics:**
   - P/E ratios
   - Market cap
   - Revenue
   - EPS
   - Dividend yield

2. **Tighter Tolerance:**
   - Current: 10% tolerance
   - Try: 5% tolerance for critical metrics

3. **Multi-Source Verification:**
   - Cross-check across multiple APIs (Finnhub, yfinance, Alpha Vantage)
   - Flag if sources disagree

**Expected Improvement:** +3-8% hallucination recall

---

### **Option D: Ensemble with Baselines**

**Idea:** Combine FHRI with best baseline (NLI-Only) for hybrid approach

**Strategy:**
```python
if contradiction_score >= 0.15:
    # Use NLI (best at contradictions)
    predicted = "contradiction"
elif fhri < threshold or entropy > 2.0:
    # Use FHRI (best at hallucinations)
    predicted = "hallucination"
else:
    predicted = "accurate"
```

**Expected Improvement:** +2-4% macro F1

---

### **Option E: Rule-Based Fact Verification**

**Current:** Relies on ML models only

**Enhancements:**
1. **Binary Facts Database:**
   - Market holidays
   - Dow 30 membership
   - S&P 500 constituents
   - Exchange listings

2. **Temporal Rules:**
   - Market hours (9:30 AM - 4:00 PM ET)
   - Trading days (not weekends/holidays)

3. **Numeric Ranges:**
   - P/E ratios (typically 10-30 for S&P 500)
   - Dividend yields (typically 1-5%)
   - Flag outliers

**Expected Improvement:** +5-10% precision on numeric questions

---

## 📝 **Implementation Plan**

### **Priority 1: Re-run with Phase 4 Settings (Quick Win)**

**Command:**
```bash
# Make sure backend uses Phase 4 settings (numeric check enabled)
# Then re-run comparative baseline
python scripts/evaluate_comparative_baselines.py \
    --dataset data/evaluation_dataset.json \
    --output results/comparative_baselines_phase4.json
```

**Expected Result:** FHRI macro F1 should be ~0.6391 (matching Phase 4)

---

### **Priority 2: Threshold Tuning (Medium Effort)**

**Create script:** `scripts/tune_fhri_thresholds.py`

**Approach:**
1. Grid search over threshold ranges
2. Evaluate on validation set
3. Select best combination

**Time:** 2-3 hours
**Expected Gain:** +2-5% macro F1

---

### **Priority 3: Enhanced Numeric Checks (Medium Effort)**

**Modify:** `src/fhri_scoring.py`

**Add:**
- P/E ratio checks
- Market cap checks
- Revenue checks
- Multi-source verification

**Time:** 3-4 hours
**Expected Gain:** +3-8% hallucination recall

---

### **Priority 4: Ensemble Approach (Low Effort)**

**Modify:** `scripts/evaluate_comparative_baselines.py`

**Add:** Hybrid detection logic combining FHRI + NLI

**Time:** 1-2 hours
**Expected Gain:** +2-4% macro F1

---

## 🎯 **Realistic Expectations**

### **Current Best (Phase 4):**
- Macro F1: **0.6391**
- Accuracy: **64.0%**
- Hallucination F1: **0.2174**

### **With All Improvements:**
- Macro F1: **0.68-0.72** (realistic target)
- Accuracy: **68-72%** (realistic target)
- Hallucination F1: **0.30-0.40** (realistic target)

**This would beat all baselines convincingly!**

---

## 🚀 **Quick Start: Re-run with Phase 4 Settings**

**Step 1: Verify Backend Settings**

Check that your backend is using Phase 4 configuration:
- Numeric check enabled
- Moderate thresholds (numeric_kpi: 0.80, high-risk floor: 0.85)

**Step 2: Re-run Comparative Baseline**

```bash
python scripts/evaluate_comparative_baselines.py \
    --dataset data/evaluation_dataset.json \
    --output results/comparative_baselines_phase4.json
```

**Step 3: Compare Results**

You should see FHRI macro F1 around **0.6391** (matching Phase 4), which already beats all baselines!

---

## 💡 **Key Insight**

**You already have better results (Phase 4: 0.6391) than the comparative baseline (0.5518)!**

The issue is that the comparative baseline was run with **different (worse) settings**. Re-running with Phase 4 settings should show FHRI outperforming all baselines.

---

## ✅ **Next Steps**

1. **Re-run comparative baseline** with Phase 4 settings (quick win)
2. **If needed:** Implement threshold tuning (medium effort, +2-5% gain)
3. **If needed:** Add enhanced numeric checks (medium effort, +3-8% hallucination recall)

**You're already close to beating all baselines - just need to use the right settings!** 🚀




















