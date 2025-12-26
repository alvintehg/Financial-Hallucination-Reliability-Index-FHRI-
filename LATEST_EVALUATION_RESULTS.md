# Latest Evaluation Results - 0.65 Threshold

## 📊 **Results Comparison**

| Metric | Phase 4 (Best) | Latest Run | Previous Run | Status |
|--------|----------------|------------|--------------|--------|
| **Accuracy** | 64.0% | 38.0% | 37.0% | ⚠️ Still Low |
| **Macro F1** | 0.6391 | 0.2489 | 0.2421 | ⚠️ Still Low |
| **Accurate F1** | 0.70 | 0.5439 | 0.5172 | ⚠️ Improving |
| **Hallucination F1** | 0.2174 | 0.2029 | 0.209 | ⚠️ Similar |
| **Contradiction F1** | 1.0 | 0.0 | 0.0 | ❌ Still Broken |
| **Time** | ~5-7 min | 20.51 min | 20.55 min | ⚠️ Still CPU |

---

## 🔍 **Analysis**

### **Slight Improvement:**
- Accuracy: 37% → 38% (+1%)
- Macro F1: 0.2421 → 0.2489 (+0.0068)
- Accurate F1: 0.5172 → 0.5439 (+0.0267)

### **Still Broken:**
- ❌ **Contradiction F1: 0.0** (should be 1.0)
  - NLI model not working or not loaded
  - All 17 contradiction samples missed
  
- ⚠️ **Still using CPU** (not GPU)
  - Time: ~20.5 minutes (should be ~5-7 min with GPU)
  - GPU available but not being used

- ⚠️ **Performance much worse than Phase 4**
  - Accuracy: 38% vs 64% (-26%)
  - Macro F1: 0.2489 vs 0.6391 (-0.3902)

---

## 🐛 **Issues**

1. **Contradiction Detection Broken**
   - All `contradiction_score` values are `null`
   - NLI model not computing contradictions
   - Need to check backend logs for NLI errors

2. **GPU Not Being Used**
   - Backend might not be loading models on GPU
   - Or evaluation script not detecting GPU usage
   - Check backend startup logs

3. **Performance Gap**
   - Something changed between Phase 4 and now
   - Need to compare evaluation scripts/logic
   - May need to check Phase 4's exact configuration

---

## ✅ **What's Working**

- Evaluation script runs successfully
- Accurate detection improved slightly (0.5439 F1)
- No crashes or errors
- Results are consistent between runs

---

## 🚀 **Next Steps**

1. **Check backend logs** for NLI model loading errors
2. **Verify GPU usage** in backend (check Task Manager during evaluation)
3. **Compare with Phase 4** evaluation script to see what's different
4. **Test contradiction detection** manually via API to see if it works

---

## 💡 **Recommendation**

**For now, use Phase 4 results (eval_100_samples_numeric_check.json)** as your baseline:
- ✅ 64% accuracy
- ✅ 0.6391 macro F1
- ✅ Perfect contradiction detection (1.0 F1)

The current runs are not matching Phase 4 performance, so something is different. Need to investigate what changed.














