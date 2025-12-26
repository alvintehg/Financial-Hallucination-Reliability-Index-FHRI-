# Why Lowering Threshold Made It Worse

## What Happened

**Lower threshold (0.60) = More strict = Flags more as hallucinations**

This causes:
- ✅ More hallucinations caught (good)
- ❌ More accurate samples flagged as hallucinations (bad - false positives)
- ❌ Accurate F1 drops significantly

## The Trade-off

| Threshold | Effect | Accurate F1 | Hallucination F1 |
|-----------|--------|-------------|------------------|
| **0.70** (higher) | More lenient | Higher | Lower |
| **0.65** (original) | Balanced | Medium | Medium |
| **0.60** (lower) | More strict | Lower | Higher |

**Your case:** 0.60 caught more hallucinations BUT hurt accurate detection too much.

---

## Better Solutions

### Option 1: Go Back to 0.65 or Try 0.70

**Change back:**
```python
# src/fhri_scoring.py line 46
"default": 0.65,  # Change back from 0.60
```

**Or try higher (0.70):**
```python
"default": 0.70,  # More lenient - fewer false positives
```

---

### Option 2: Improve Detection Logic (Better Approach)

Instead of just changing threshold, improve the logic in `scripts/evaluate_detection.py`:

**Current (too strict):**
```python
elif fhri is not None and fhri > effective_threshold:
    predicted_label = "accurate"
else:
    predicted_label = "hallucination"  # Too many accurate samples fall here!
```

**Improved (confidence zones):**
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
```

This gives you:
- Better balance between accurate and hallucination detection
- Uses multiple signals (not just threshold)
- Reduces false positives on accurate samples

---

## Recommended Action

1. **Change threshold back to 0.65** (or try 0.70)
2. **Improve detection logic** with confidence zones (Option 2)
3. **Test again** - should improve both accurate and hallucination F1

---

## Quick Fix: Change Back

Edit `src/fhri_scoring.py` line 46:
```python
"default": 0.65,  # Change back from 0.60
```

And `scripts/evaluate_detection.py` line 48 and 532:
```python
fhri_threshold: float = 0.65,  # Change back
default=0.65,  # Change back
```

Then test again!

















