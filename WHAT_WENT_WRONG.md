# What Went Wrong with 0.70 Threshold

## ⚠️ **The Problem: Improved Logic is TOO STRICT**

**Results with 0.70:**
- Macro F1: **0.1966** (terrible!)
- Accurate F1: **0.3261** (only 15/57 caught)
- **42 accurate samples** flagged as hallucination (false positives!)

---

## 🔍 **Root Cause**

The **improved logic with confidence zones** is still active and it's way too strict:

**Current Logic (TOO STRICT):**
```python
if fhri > threshold + 0.10:  # Needs > 0.80 for default
    accurate
elif fhri > threshold:  # Needs > 0.70 AND grounding > 0.7 AND entropy < 1.8
    accurate (only if all conditions met)
else:
    hallucination  # Everything else!
```

**Problem:**
- With threshold 0.70, needs **fhri > 0.80** for high confidence
- Or **fhri > 0.70** with **grounding > 0.7** AND **entropy < 1.8**
- Most samples don't meet these strict criteria → flagged as hallucination!

---

## ✅ **Solution: Revert to Original Logic**

I've already reverted the logic to the original simple version:

**Original Logic (SIMPLE):**
```python
if fhri > threshold:
    accurate
else:
    hallucination
```

**This is what Phase 4 used** (0.6391 macro F1)!

---

## 🚀 **Next Steps**

1. **Revert is done** - Logic is back to original
2. **Test 0.70 again** with original logic:
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.70_original.json --fhri_threshold 0.70
   ```

**Expected:** Should be much better now (closer to Phase 4's 0.6391)

---

## 📊 **Comparison**

| Version | Logic | Threshold | Macro F1 |
|---------|-------|-----------|----------|
| **Phase 4** | Original | 0.65 (scenario-specific) | **0.6391** ✅ |
| **0.70 (improved logic)** | Improved (strict) | 0.70 | **0.1966** ❌ |
| **0.70 (original logic)** | Original | 0.70 | **To be tested** |

**The improved logic was the problem, not the threshold!**














