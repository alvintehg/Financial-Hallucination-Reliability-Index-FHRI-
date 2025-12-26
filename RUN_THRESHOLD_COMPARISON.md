# How to Run Threshold Comparison

## ⚠️ **Important: Run Commands ONE AT A TIME**

Each evaluation takes **several minutes** (100 samples). Run them **sequentially**, not all at once.

---

## 📋 **Step-by-Step Instructions**

### **Step 1: Test 0.65 Threshold**

Open terminal and run:
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.65_fixed.json --fhri_threshold 0.65
```

**Wait for it to finish** (you'll see "Evaluation complete!" message)
- Takes ~5-10 minutes depending on your system
- Don't close terminal or run next command yet

---

### **Step 2: Test 0.70 Threshold**

After Step 1 finishes, run:
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.70_fixed.json --fhri_threshold 0.70
```

**Wait for it to finish** (you'll see "Evaluation complete!" message)
- Takes ~5-10 minutes
- Don't close terminal or run next command yet

---

### **Step 3: Compare Results**

After Step 2 finishes, run:
```bash
python scripts/compare_thresholds.py --result1 results/test_0.65_fixed.json --result2 results/test_0.70_fixed.json --name1 "0.65" --name2 "0.70"
```

This will show a side-by-side comparison instantly (takes seconds).

---

## 🚀 **Quick Version (If You Want to Run All)**

You can run them in sequence in the same terminal:

```bash
# Step 1: Test 0.65
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.65_fixed.json --fhri_threshold 0.65

# Step 2: Test 0.70 (wait for Step 1 to finish first!)
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/test_0.70_fixed.json --fhri_threshold 0.70

# Step 3: Compare (wait for Step 2 to finish first!)
python scripts/compare_thresholds.py --result1 results/test_0.65_fixed.json --result2 results/test_0.70_fixed.json --name1 "0.65" --name2 "0.70"
```

**But you still need to wait for each one to finish before running the next!**

---

## ⏱️ **Expected Time**

- **Each evaluation:** ~5-10 minutes (100 samples)
- **Total time:** ~10-20 minutes for both evaluations
- **Comparison:** Instant (seconds)

---

## 💡 **Tip**

You'll know each evaluation is done when you see:
```
[OK] Evaluation complete!
Total samples evaluated: 100
Overall accuracy: XX.XX%
Macro F1-Score: X.XXXX
```

Then you can run the next command.














