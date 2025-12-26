# Commands to Restart Backend and Re-Run Evaluation

## 🔄 **Step 1: Restart Backend**

**Open a NEW terminal window** (keep this one open for evaluation) and run:

```bash
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
uvicorn src.server:app --port 8000
```

**Wait for it to show:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal open** - don't close it!

---

## ✅ **Step 2: Verify Backend is Running**

In your **original terminal** (where you'll run evaluation), test the backend:

```bash
curl http://localhost:8000/health
```

You should see a response like `{"status":"ok"}` or similar.

---

## 🚀 **Step 3: Re-Run 0.65 Evaluation (with timing)**

In your **original terminal**, run:

```bash
python scripts/evaluate_with_timing.py --dataset data/evaluation_dataset.json --output results/test_0.65_fixed.json --fhri_threshold 0.65
```

**Wait for it to complete** (~5-10 minutes with GPU, ~20 minutes with CPU)

---

## 📊 **Step 4: Check Results**

After evaluation completes, check if:
- ✅ Contradiction F1 > 0 (should be ~1.0)
- ✅ Accuracy > 50% (should be ~64%)
- ✅ Time < 10 minutes (if using GPU)

---

## 🔍 **If Still Having Issues**

If contradiction detection is still broken (F1 = 0.0), check backend logs in the terminal where you started uvicorn. Look for:
- NLI model loading messages
- Any error messages
- GPU usage indicators














