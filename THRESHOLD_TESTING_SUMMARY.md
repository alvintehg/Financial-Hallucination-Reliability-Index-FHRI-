# Threshold Testing Summary

## ✅ **What You've Tested**

### **1. Phase Evaluations (from EVALUATION_RESULTS_SUMMARY.md)**
- **Phase 1 (Baseline):** Default thresholds → Macro F1: **0.6194**
- **Phase 2 (Strict):** Very strict thresholds → Macro F1: **0.6201**
- **Phase 3 (Moderate):** Moderate thresholds → Macro F1: **0.6266**
- **Phase 4 (Numeric Check):** Moderate + numeric check → Macro F1: **0.6391** ⭐ **BEST**

### **2. Single Threshold Tests**
- **0.60** (test.json): Macro F1: **0.2648** ❌ (too strict)
- **0.65** (test_improved_logic.json): Macro F1: **0.1858** ❌ (improved logic made it worse)
- **0.65** (comparative_baselines.json - FHRI-full): Macro F1: **0.2787** (but this was with old logic)

---

## 📊 **Best Result So Far**

**Phase 4 (Numeric Check):** Macro F1 = **0.6391**
- Uses scenario-specific thresholds (numeric_kpi: 0.80, default: 0.65, etc.)
- Has numeric price check enabled
- This is your **current best baseline**

---

## 🎯 **What to Test Next**

### **Priority 1: Test Different Single Thresholds** (with ORIGINAL logic, not improved)

**First, revert the improved logic** (it made things worse), then test:

1. **0.70** (more lenient - should reduce false positives)
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.70.json --fhri_threshold 0.70
   ```

2. **0.68** (slightly more lenient)
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.68.json --fhri_threshold 0.68
   ```

3. **0.63** (slightly more strict)
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.63.json --fhri_threshold 0.63
   ```

4. **0.62** (more strict)
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.62.json --fhri_threshold 0.62
   ```

**Goal:** Find threshold that beats Phase 4's 0.6391 macro F1

---

### **Priority 2: Revert Improved Logic First**

**The improved logic made things worse** (0.1858 vs 0.2787). Revert it:

**File:** `scripts/evaluate_detection.py` around line 238

**Revert to original:**
```python
elif fhri is not None and fhri > effective_threshold:
    predicted_label = "accurate"
else:
    if entropy is not None and entropy > self.hallu_threshold:
        predicted_label = "hallucination"
    elif fhri is not None and fhri <= effective_threshold:
        predicted_label = "hallucination"
    else:
        predicted_label = "accurate"
```

---

## 📋 **Testing Checklist**

- [ ] Revert improved logic (it made things worse)
- [ ] Test 0.70 threshold
- [ ] Test 0.68 threshold  
- [ ] Test 0.63 threshold
- [ ] Test 0.62 threshold
- [ ] Compare all results
- [ ] Pick best threshold

---

## 🎯 **Expected Best Threshold**

Based on your results:
- **0.60:** Too strict (0.2648 macro F1)
- **0.65:** Baseline (Phase 4: 0.6391 with scenario-specific thresholds)
- **0.70:** Likely best (more lenient, should improve accurate F1)

**Try 0.70 first** - it's most likely to improve results!














