# Why Contradiction Detection Failed

## 🔍 **The Problem**

**Phase 4 Results (Working):**
- Contradiction F1: **1.0** (17/17 caught)
- Contradiction scores: **Present** (e.g., 0.463)

**Test 0.70 Results (Broken):**
- Contradiction F1: **0.0** (0/17 caught)
- Contradiction scores: **All `null`**

---

## 🐛 **Root Cause**

The backend requires **`use_nli: true`** to compute contradiction scores, but the evaluation script might not be passing it correctly.

**Backend Code (src/server.py:999):**
```python
if req.use_nli and req.prev_assistant_turn and isinstance(answer, str) and answer.strip():
    # Compute contradiction score
    result = nli_detector.compute_contradiction(...)
```

**Required Conditions:**
1. ✅ `req.use_nli` = `True` (might be missing!)
2. ✅ `req.prev_assistant_turn` = Previous answer (evaluation script passes this)
3. ✅ `answer` = Non-empty string (should be fine)

---

## ✅ **Solution**

Check if `use_nli` is being passed in `query_chatbot()`:

**Current Code (scripts/evaluate_detection.py:78-91):**
```python
def query_chatbot(self, question: str, prev_answer: str = None, ...):
    payload = {
        "text": question,
        "k": k,
        "provider": "auto",
        "use_entropy": use_entropy,
        "use_nli": use_nli,  # ← Check if this defaults to True
        "use_fhri": use_fhri
    }
```

**Check:**
- Does `use_nli` default to `True`?
- Is it being set correctly when calling `query_chatbot()`?

---

## 🔧 **Quick Fix**

If `use_nli` is not being passed or defaults to `False`, add it explicitly:

```python
response = self.query_chatbot(
    question, 
    prev_answer=prev_answer, 
    prev_question=prev_question, 
    k=5, 
    use_fhri=use_fhri, 
    use_nli=True,  # ← Add this explicitly
    scenario_override=scenario_override
)
```

---

## 📊 **Why This Happened**

You didn't change contradiction detection code, but:
- The improved logic might have affected how `query_chatbot()` is called
- Or `use_nli` parameter might not be defaulting correctly
- Or backend needs restart to load NLI model

**Most likely:** `use_nli` is not being passed as `True` to the backend!














