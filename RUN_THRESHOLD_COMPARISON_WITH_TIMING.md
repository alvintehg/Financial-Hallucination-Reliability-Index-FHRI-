# How to Run Threshold Comparison WITH TIMING

## ⚠️ **Important: Run Commands ONE AT A TIME**

Each evaluation takes **several minutes** (100 samples). Run them **sequentially**, not all at once.

---

## 📋 **Step-by-Step Instructions WITH TIMING**

### **Step 1: Test 0.65 Threshold (with timing)**

Open terminal and run:
```bash
python scripts/evaluate_with_timing.py --dataset data/evaluation_dataset.json --output results/test_0.65_fixed.json --fhri_threshold 0.65
```

**What you'll see:**
- Start time
- GPU info
- Progress updates
- End time
- **Total time (seconds)**
- **Time per sample (seconds)**

**Wait for it to finish** (you'll see "Evaluation complete!" and timing summary)

---

### **Step 2: Test 0.70 Threshold (with timing)**

After Step 1 finishes, run:
```bash
python scripts/evaluate_with_timing.py --dataset data/evaluation_dataset.json --output results/test_0.70_fixed.json --fhri_threshold 0.70
```

**What you'll see:**
- Start time
- GPU info
- Progress updates
- End time
- **Total time (seconds)**
- **Time per sample (seconds)**
- **Comparison with previous run** (if available)

**Wait for it to finish**

---

### **Step 3: Compare Results**

After Step 2 finishes, run:
```bash
python scripts/compare_thresholds.py --result1 results/test_0.65_fixed.json --result2 results/test_0.70_fixed.json --name1 "0.65" --name2 "0.70"
```

This will show a side-by-side comparison instantly (takes seconds).

---

## 📊 **Timing Data Saved**

Timing data is automatically saved to:
- `results/evaluation_timings.json`

This file contains:
- Start/end times for each run
- Total elapsed time
- Time per sample
- GPU usage info
- Comparison with previous runs

---

## 🚀 **Quick Version (All in One Terminal)**

You can run them in sequence in the same terminal:

```bash
# Step 1: Test 0.65 (with timing)
python scripts/evaluate_with_timing.py --dataset data/evaluation_dataset.json --output results/test_0.65_fixed.json --fhri_threshold 0.65

# Step 2: Test 0.70 (with timing) - wait for Step 1 to finish first!
python scripts/evaluate_with_timing.py --dataset data/evaluation_dataset.json --output results/test_0.70_fixed.json --fhri_threshold 0.70

# Step 3: Compare - wait for Step 2 to finish first!
python scripts/compare_thresholds.py --result1 results/test_0.65_fixed.json --result2 results/test_0.70_fixed.json --name1 "0.65" --name2 "0.70"
```

**But you still need to wait for each one to finish before running the next!**

---

## ⏱️ **Expected Time (Rough Estimate)**

- **Each evaluation:** ~5-10 minutes (100 samples)
  - With GPU: ~5-7 minutes
  - Without GPU: ~8-12 minutes
- **Total time:** ~10-20 minutes for both evaluations
- **Comparison:** Instant (seconds)

**Actual time will be shown after each evaluation completes!**

---

## 📈 **What Timing Shows**

After each evaluation, you'll see:
```
[END] Evaluation completed at: 2025-12-09 12:30:45
Total time: 342.5 seconds (5.7 minutes)
Time per sample: 3.4 seconds
```

And if you run multiple times, it will compare:
```
Previous run: 380.2 seconds (6.3 minutes)
Time difference: -37.7 seconds (faster!)
```

---

## 💡 **Tip**

You'll know each evaluation is done when you see:
```
[OK] Evaluation complete!
Total samples evaluated: 100
Overall accuracy: XX.XX%
Macro F1-Score: X.XXXX
Total time: XXX.X seconds
```

Then you can run the next command.














