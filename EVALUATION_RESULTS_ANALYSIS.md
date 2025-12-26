# Evaluation Results Analysis - 0.65 Threshold

## ⚠️ **Concerning Results**

**0.65 Threshold Test (Just Completed):**
- **Accuracy:** 37.0% (37/100 correct)
- **Macro F1:** 0.2421
- **Time:** 20.55 minutes (CPU, not GPU)
- **Contradiction F1:** 0.0 (0/17 caught) ❌

**Phase 4 (Previous Best):**
- **Accuracy:** 64.0% (64/100 correct)
- **Macro F1:** 0.6391
- **Contradiction F1:** 1.0 (17/17 caught) ✅

---

## 🔍 **Issues Identified**

### **1. Contradiction Detection Still Broken**
- **Current:** 0.0 F1 (0/17 caught)
- **Expected:** 1.0 F1 (17/17 caught)
- **Problem:** Contradiction scores are still `null` (NLI not working)

### **2. Overall Performance Much Worse**
- **Accuracy dropped:** 64% → 37% (-27%)
- **Macro F1 dropped:** 0.6391 → 0.2421 (-0.397)
- **Problem:** Something is wrong with the evaluation or backend

### **3. GPU Not Being Used**
- **Current:** CPU only (20.55 minutes)
- **Expected:** GPU (should be ~5-7 minutes)
- **Problem:** Backend might not be using GPU, or models not loaded on GPU

---

## 🐛 **Possible Causes**

1. **Backend not restarted** after fixing the improved logic
2. **NLI model not loaded** (contradiction detection broken)
3. **Backend using CPU** instead of GPU
4. **Evaluation script issue** (though logic was fixed)

---

## ✅ **What We Know Works**

**Phase 4 Results (eval_100_samples_numeric_check.json):**
- Used 0.65 threshold with scenario-specific thresholds
- Original simple logic
- Contradiction detection working (1.0 F1)
- Good overall performance (0.6391 macro F1)

---

## 🚀 **Next Steps**

1. **Check if backend is running and using GPU**
2. **Restart backend** to ensure NLI model is loaded
3. **Re-run evaluation** with backend properly configured
4. **Compare with Phase 4** to see if we can match those results

---

## 📊 **Per-Class Performance (0.65 Test)**

- **Accurate:** F1 = 0.5172 (30/57 correct)
- **Hallucination:** F1 = 0.209 (7/26 correct)
- **Contradiction:** F1 = 0.0 (0/17 correct) ❌

**All classes are performing poorly compared to Phase 4.**














