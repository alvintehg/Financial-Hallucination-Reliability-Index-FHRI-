# Results Comparison - Improved Logic vs Baseline

## ⚠️ **WARNING: Improved Logic Made It Worse!**

### Performance Comparison

| Metric | Baseline (0.65) | Improved Logic (0.65) | Change |
|--------|----------------|----------------------|--------|
| **Macro F1** | 0.2787 | **0.1858** | ❌ **-33% worse** |
| **Accurate F1** | 0.6207 | **0.1311** | ❌ **-79% worse** |
| **Hallucination F1** | 0.2154 | **0.4262** | ✅ **+98% better** |
| **Contradiction F1** | 0.0 | **0.0** | ⚠️ Still broken |
| **Overall Accuracy** | 43.4% | **30.0%** | ❌ **-31% worse** |

### What Went Wrong

**The improved logic is TOO STRICT:**
- **53 out of 57 accurate samples** flagged as hallucination (93% false positive rate!)
- **0 out of 17 contradictions** caught (still broken)
- **26 out of 26 hallucinations** caught (100% recall, but too many false positives)

**Problem:** The confidence zones are too conservative - almost everything falls into the "hallucination" category.

---

## 🚀 **Speed Comparison**

**File timestamps:**
- Comparative baseline: 19:01:36 (ran 4 methods)
- Improved logic: 19:04:09 (ran 1 method)
- **Time difference:** ~2.5 minutes (but this was only 1 method vs 4)

**GPU Impact:**
- Hard to compare directly (different number of methods)
- GPU should make individual queries faster
- Check Task Manager GPU usage during evaluation to confirm

---

## ✅ **What to Do Next**

### **Option 1: Revert Improved Logic** (Recommended)

The improved logic made things worse. Revert to original:

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

### **Option 2: Fix Improved Logic** (Adjust Parameters)

The logic is too strict. Make it more lenient:

**Change confidence zones:**
- Increase threshold buffer (0.10 → 0.15 or 0.20)
- Lower grounding requirement (0.7 → 0.6)
- Lower entropy requirement (1.8 → 2.0)

---

## 📊 **Recommendation**

**Revert to original logic** - it performed better (0.2787 macro F1 vs 0.1858).

Then try:
1. **Different thresholds** (0.70, 0.68, 0.63) with original logic
2. **Component weight tuning** (increase grounding/numeric weights)
3. **Enhanced numeric checks** (expand beyond prices)

**The improved logic needs more tuning - it's too strict right now.**














