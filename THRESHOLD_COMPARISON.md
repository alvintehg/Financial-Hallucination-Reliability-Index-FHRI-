# Threshold Comparison: 0.65 vs 0.70

## ⚠️ **Current Status**

**0.65 Threshold (Phase 4 - Valid):**
- Accuracy: **64.0%**
- Macro F1: **0.6391**
- Logic: Original simple logic ✅
- Contradiction F1: **1.0** (17/17 caught)

**0.70 Threshold (Test - INVALID):**
- Accuracy: **27.0%**
- Macro F1: **0.1966**
- Logic: Improved logic (BUGGY) ❌
- Contradiction F1: **0.0** (0/17 caught)

---

## 🔍 **Why 0.70 Results Are Invalid**

The 0.70 test used the **improved logic** which was too strict:
- Required `fhri > threshold + 0.10` for high confidence
- Or `fhri > threshold` with additional conditions
- This caused **42 out of 57 accurate samples** to be flagged as hallucination

**The improved logic has been fixed (reverted to original), but 0.70 hasn't been re-tested yet.**

---

## 📊 **Valid Comparison Needed**

To properly compare 0.65 vs 0.70, we need to:

1. **Re-run 0.70** with the **fixed original logic**
2. **Compare metrics** side-by-side
3. **Check per-class performance** (accurate, hallucination, contradiction)

---

## 🎯 **Expected Differences**

### **0.65 Threshold (More Lenient)**
- **Pros:**
  - More accurate samples pass (higher recall for accurate)
  - Better overall accuracy
  - Fewer false positives on accurate samples
  
- **Cons:**
  - More hallucinations might pass (lower precision for hallucination)
  - Might miss some hallucinations

### **0.70 Threshold (More Strict)**
- **Pros:**
  - Better at catching hallucinations (higher precision for hallucination)
  - Fewer false positives on hallucinations
  
- **Cons:**
  - More accurate samples flagged as hallucination (lower recall for accurate)
  - Might reduce overall accuracy

---

## 🚀 **Next Steps**

**Run proper comparison:**

```bash
# Test 0.65 with fixed logic
python scripts/evaluate_detection.py \
    --dataset data/evaluation_dataset.json \
    --output results/test_0.65_fixed.json \
    --fhri_threshold 0.65

# Test 0.70 with fixed logic
python scripts/evaluate_detection.py \
    --dataset data/evaluation_dataset.json \
    --output results/test_0.70_fixed.json \
    --fhri_threshold 0.70
```

Then compare:
- Overall accuracy
- Macro F1-score
- Per-class F1 (accurate, hallucination, contradiction)
- False positive/negative rates

---

## 💡 **Recommendation**

**For now, stick with 0.65** because:
1. ✅ It's proven to work (0.6391 macro F1)
2. ✅ Contradiction detection works perfectly (1.0 F1)
3. ✅ Balanced performance across classes

**After re-testing 0.70 with fixed logic:**
- If 0.70 improves hallucination detection without hurting accurate samples too much → use 0.70
- If 0.70 causes too many false positives on accurate samples → stick with 0.65

---

## 📋 **Current Best Performance**

**Phase 4 (0.65 threshold, scenario-specific):**
- Overall Accuracy: **64.0%**
- Macro F1: **0.6391**
- Accurate F1: **0.70**
- Hallucination F1: **0.2174** (needs improvement)
- Contradiction F1: **1.0** (perfect!)

**Goal:** Improve hallucination F1 while maintaining accurate F1 and contradiction F1.














