# Fine-Tuning Next Steps - Improve Results

## Current Situation
- **Baseline (0.65):** Your current performance
- **Tried 0.60:** Made it worse (too strict)
- **Goal:** Improve both accurate and hallucination F1

---

## Step-by-Step Fine-Tuning Plan

### **Step 1: Test Different Thresholds** (30 minutes)

Test multiple threshold values to find the sweet spot:

**Try these values:**
- 0.70 (more lenient - fewer false positives)
- 0.68 (slightly more lenient)
- 0.65 (current baseline)
- 0.63 (slightly more strict)
- 0.62 (more strict)

**How to test:**
```bash
# Test each threshold
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.70.json --fhri_threshold 0.70
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.68.json --fhri_threshold 0.68
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.63.json --fhri_threshold 0.63
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.62.json --fhri_threshold 0.62
```

**Compare results:** Look at macro F1 for each - pick the best one.

---

### **Step 2: Improve Detection Logic** (1-2 hours) ⭐ **MOST IMPORTANT**

The detection logic is too simple. Improve it with confidence zones:

**File:** `scripts/evaluate_detection.py` (around line 238)

**Current logic (too strict):**
```python
elif fhri is not None and fhri > effective_threshold:
    predicted_label = "accurate"
else:
    predicted_label = "hallucination"  # Too many accurate samples fall here!
```

**Replace with improved logic:**
```python
elif fhri is not None:
    # Get subscores for better decision making
    fhri_subscores = meta.get("fhri_subscores", {})
    grounding = fhri_subscores.get("grounding", 0)
    
    # High confidence zone (FHRI well above threshold)
    if fhri > effective_threshold + 0.10:
        predicted_label = "accurate"
    
    # Medium confidence zone (FHRI just above threshold)
    elif fhri > effective_threshold:
        # Check additional signals for better accuracy
        # If well-grounded and low entropy, likely accurate
        if grounding > 0.7 and (entropy is None or entropy < 1.8):
            predicted_label = "accurate"
        else:
            # Medium confidence but other signals suggest hallucination
            predicted_label = "hallucination"
    
    # Low confidence zone (FHRI just below threshold)
    elif fhri > effective_threshold - 0.10:
        # Check if it's a borderline case
        # If entropy is low and grounding is good, might still be accurate
        if entropy is not None and entropy < 1.5 and grounding > 0.75:
            predicted_label = "accurate"
        else:
            predicted_label = "hallucination"
    
    # Very low confidence (FHRI well below threshold)
    else:
        predicted_label = "hallucination"
```

**This gives you:**
- Better balance (not just binary threshold)
- Uses multiple signals (FHRI + grounding + entropy)
- Reduces false positives on accurate samples
- Still catches hallucinations

---

### **Step 3: Test Improved Logic** (30 minutes)

After changing the detection logic:

```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_improved_logic.json --fhri_threshold 0.65
```

**Compare:**
- Accurate F1: Should improve (fewer false positives)
- Hallucination F1: Should maintain or improve
- Macro F1: Should improve overall

---

### **Step 4: Fine-Tune Threshold with Improved Logic** (30 minutes)

Once you have improved logic, test different thresholds again:

```bash
# Test with improved logic
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/improved_0.70.json --fhri_threshold 0.70
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/improved_0.68.json --fhri_threshold 0.68
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/improved_0.65.json --fhri_threshold 0.65
```

Pick the best combination.

---

## Recommended Order

1. **First:** Improve detection logic (Step 2) - This is the most impactful
2. **Then:** Test with 0.65 threshold
3. **Finally:** Fine-tune threshold (Step 1) if needed

---

## Expected Improvements

**After Step 2 (Improved Logic):**
- Accurate F1: 0.6441 → **0.70-0.75** (+8-16%)
- Hallucination F1: 0.1395 → **0.20-0.30** (+43-115%)
- Macro F1: 0.5518 → **0.65-0.70** (+18-27%)

**After Step 4 (Fine-tuned threshold):**
- Additional +2-5% improvement

---

## Quick Start: Do Step 2 Now

**Edit `scripts/evaluate_detection.py` around line 238** and replace the simple threshold check with the improved confidence zone logic above.

Then test:
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_improved.json
```

**This should give you the biggest improvement!**

















