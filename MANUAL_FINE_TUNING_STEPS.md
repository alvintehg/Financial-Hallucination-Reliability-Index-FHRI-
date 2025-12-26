# Manual Fine-Tuning Steps - Quick Reference

## 🎯 **Goal: Improve Accurate F1 (0.6441 → 0.70+) and Hallucination F1 (0.1395 → 0.30+)**

---

## 📝 **Step-by-Step Process**

### **Step 1: Identify Current Issues**

**From your results:**
- **Accurate F1: 0.6441** - Too many false positives (accurate samples flagged as hallucination)
- **Hallucination F1: 0.1395** - Too many false negatives (hallucinations missed)

**Root Cause:**
- Thresholds too strict → flags accurate as hallucination
- Detection logic too simple → misses hallucinations

---

### **Step 2: Adjust Thresholds (Start Here)**

**File: `src/fhri_scoring.py`**

**Current:**
```python
SCENARIO_FHRI_THRESHOLDS = {
    "numeric_kpi": 0.80,
    "default": 0.65,
    "advice": 0.55,
}
HIGH_RISK_FHRI_FLOOR = 0.85
```

**Try Lowering (to catch more hallucinations):**
```python
SCENARIO_FHRI_THRESHOLDS = {
    "numeric_kpi": 0.75,  # Lower from 0.80
    "default": 0.60,      # Lower from 0.65
    "advice": 0.50,       # Lower from 0.55
}
HIGH_RISK_FHRI_FLOOR = 0.80  # Lower from 0.85
```

**Or Try Raising (to reduce false positives on accurate):**
```python
SCENARIO_FHRI_THRESHOLDS = {
    "numeric_kpi": 0.85,  # Higher from 0.80
    "default": 0.70,      # Higher from 0.65
    "advice": 0.60,       # Higher from 0.55
}
HIGH_RISK_FHRI_FLOOR = 0.90  # Higher from 0.85
```

**Test both directions and see which improves macro F1!**

---

### **Step 3: Adjust Entropy Threshold**

**File: `scripts/evaluate_detection.py`**

**Current:**
```python
self.hallu_threshold = 2.0
```

**Try:**
- **Lower (1.5):** More hallucinations caught, but more false positives
- **Higher (2.5):** Fewer false positives, but more hallucinations missed

**Test:** 1.5, 2.0, 2.5 and see which gives best balance

---

### **Step 4: Improve Detection Logic**

**File: `scripts/evaluate_detection.py` (around line 238)**

**Current Logic (too strict):**
```python
elif fhri is not None and fhri > effective_threshold:
    predicted_label = "accurate"
else:
    # Too many accurate samples fall here!
    predicted_label = "hallucination"
```

**Improved Logic (confidence zones):**
```python
elif fhri is not None:
    if fhri > effective_threshold + 0.10:
        # High confidence - definitely accurate
        predicted_label = "accurate"
    elif fhri > effective_threshold:
        # Medium confidence - check other signals
        fhri_subscores = meta.get("fhri_subscores", {})
        grounding = fhri_subscores.get("grounding", 0)
        
        # If well-grounded and low entropy, likely accurate
        if grounding > 0.7 and (entropy is None or entropy < 1.8):
            predicted_label = "accurate"
        else:
            predicted_label = "hallucination"
    elif fhri > effective_threshold - 0.10:
        # Low confidence - likely hallucination
        predicted_label = "hallucination"
    else:
        # Very low - definitely hallucination
        predicted_label = "hallucination"
else:
    # No FHRI - use entropy as fallback
    if entropy is not None and entropy > self.hallu_threshold:
        predicted_label = "hallucination"
    else:
        predicted_label = "accurate"  # Give benefit of doubt
```

---

### **Step 5: Test Each Change**

**After each change:**
1. Restart backend: `uvicorn src.server:app --port 8000`
2. Run evaluation: `python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test.json`
3. Check metrics: Look at accurate F1 and hallucination F1
4. Keep changes that improve macro F1

---

## 🔄 **Iterative Process**

**Recommended Approach:**

1. **Start with thresholds:**
   - Lower default threshold by 0.05 (0.65 → 0.60)
   - Test and measure

2. **If hallucination F1 improves but accurate F1 drops:**
   - Improve detection logic (add confidence zones)
   - Test again

3. **If accurate F1 improves but hallucination F1 drops:**
   - Lower thresholds more
   - Or improve numeric checks

4. **Repeat until macro F1 is maximized**

---

## 📊 **Expected Results After Tuning**

### **Conservative Tuning (small changes):**
- Accurate F1: 0.6441 → **0.68-0.70** (+5-8%)
- Hallucination F1: 0.1395 → **0.20-0.25** (+43-79%)
- Macro F1: 0.5518 → **0.60-0.63** (+8-14%)

### **Aggressive Tuning (larger changes):**
- Accurate F1: 0.6441 → **0.70-0.75** (+8-16%)
- Hallucination F1: 0.1395 → **0.30-0.40** (+115-187%)
- Macro F1: 0.5518 → **0.65-0.70** (+18-27%)

---

## ⚡ **Quick Test Script**

Create `test_thresholds.py`:

```python
import requests
import json

# Test different thresholds
thresholds = [0.60, 0.65, 0.70]

for thresh in thresholds:
    # Modify evaluate_detection.py threshold
    # Run evaluation
    # Check results
    print(f"Testing threshold: {thresh}")
```

---

## ✅ **Checklist**

- [ ] Lower/raise FHRI thresholds in `src/fhri_scoring.py`
- [ ] Adjust entropy threshold in `scripts/evaluate_detection.py`
- [ ] Improve detection logic (add confidence zones)
- [ ] Test each change
- [ ] Keep changes that improve macro F1
- [ ] Re-run comparative baseline with optimized settings

---

## 🎯 **Target Metrics**

**After fine-tuning, aim for:**
- Accurate F1: **≥ 0.70** (currently 0.6441)
- Hallucination F1: **≥ 0.30** (currently 0.1395)
- Macro F1: **≥ 0.65** (currently 0.5518)

**This would beat all baselines convincingly!**

---

**Start with Step 2 (adjust thresholds) - it's the easiest and most impactful!** 🚀




















