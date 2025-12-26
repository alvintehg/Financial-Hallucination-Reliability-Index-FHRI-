# Quick Fix: Use New Threshold

## Problem
The evaluation script has its own default threshold (0.65). Even if you changed `src/fhri_scoring.py`, you need to tell the evaluation script to use the new value.

## Solution: Pass threshold as argument

```bash
python scripts/evaluate_detection.py \
    --dataset data/evaluation_dataset.json \
    --output results/test.json \
    --fhri_threshold 0.60
```

**This will use 0.60 instead of the default 0.65.**

## Or: Change the default in evaluation script

Edit `scripts/evaluate_detection.py` line 532:
```python
default=0.60,  # Change from 0.65 to 0.60
```

Then run normally:
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test.json
```

---

**Try the command-line argument first - it's faster!**




















