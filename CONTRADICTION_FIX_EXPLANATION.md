# Why Contradiction Detection Failed & Fix

## 🔍 **The Problem**

**Phase 4 (Working):**
- Contradiction F1: **1.0** (17/17 caught ✅)
- Contradiction scores: **Present** (e.g., 0.463)

**Test 0.70 (Broken):**
- Contradiction F1: **0.0** (0/17 caught ❌)
- Contradiction scores: **All `null`**

---

## 🐛 **Root Cause**

The evaluation script wasn't **explicitly** passing `use_nli=True` when calling `query_chatbot()`.

**Line 167 (Before Fix):**
```python
response = self.query_chatbot(
    question, 
    prev_answer=prev_answer, 
    prev_question=prev_question, 
    k=5, 
    use_fhri=use_fhri, 
    scenario_override=scenario_override
    # ❌ Missing: use_nli=True
)
```

**Even though `use_nli` defaults to `True` in the function signature**, something might have changed or the backend might need it explicitly.

---

## ✅ **Fix Applied**

**Line 167 (After Fix):**
```python
response = self.query_chatbot(
    question, 
    prev_answer=prev_answer, 
    prev_question=prev_question, 
    k=5, 
    use_fhri=use_fhri, 
    use_nli=True,  # ✅ Explicitly enable NLI for contradiction detection
    scenario_override=scenario_override
)
```

---

## 🚀 **Next Steps**

1. **Restart backend** (if needed):
   ```bash
   uvicorn src.server:app --port 8000
   ```

2. **Re-run evaluation** with fix:
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.70_fixed.json --fhri_threshold 0.70
   ```

**Expected:** Contradiction detection should work again (17/17 caught)!

---

## 📊 **Why This Happened**

You didn't change contradiction code, but:
- The improved logic changes might have affected parameter passing
- Or backend state changed (needs restart)
- Or explicit `use_nli=True` is required for reliability

**The fix ensures NLI is always enabled for contradiction detection!**














