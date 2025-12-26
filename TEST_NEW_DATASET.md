# How to Test the Expanded 100-Sample Dataset

## Prerequisites

1. **Backend must be running**:
   ```bash
   uvicorn src.server:app --reload --port 8000
   ```

2. **Verify backend is accessible**:
   - Open browser: http://localhost:8000/health
   - Should show: `{"status": "ok", ...}`

## Step 1: Quick Test (Contradiction Samples Only)

Test only the contradiction samples to verify NLI is working:

```bash
python test_contradiction_fix.py
```

**Expected output:**
- Should show all contradiction samples have NLI scores
- Should detect some contradictions (with threshold 0.15)

## Step 2: Full Evaluation (All 100 Samples)

Run the complete evaluation on your expanded dataset:

```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_100_samples.json --mode fhri --fhri_threshold 0.65
```

**Parameters:**
- `--dataset`: Path to your 100-sample dataset
- `--output`: Where to save results
- `--mode fhri`: Use FHRI scoring (recommended)
- `--fhri_threshold 0.65`: Threshold for "accurate" label

## Step 3: Check Results

After evaluation completes, check the results file:

```bash
# View summary (Windows PowerShell)
Get-Content results/eval_100_samples.json | ConvertFrom-Json | Select-Object -ExpandProperty metrics
```

Or open `results/eval_100_samples.json` in a text editor to see:
- Overall accuracy
- Precision, Recall, F1-score for each label (accurate, hallucination, contradiction)
- Confusion matrix
- Detailed results for each sample

## Step 4: Analyze Specific Labels

### Check Hallucination Detection
Look for samples with `"ground_truth_label": "hallucination"` and see if they were correctly predicted.

### Check Contradiction Detection  
Look for samples with `"ground_truth_label": "contradiction"` and verify NLI scores are present.

### Check US Stock Questions
Filter results for samples mentioning US stocks (AAPL, MSFT, etc.) to verify they're being handled correctly.

## Expected Results

With your current setup (RoBERTa + threshold 0.15):
- **Accurate**: Should have high precision/recall (F1 ≈ 0.85-0.90)
- **Hallucination**: Will depend on entropy detection (may be 0 if no samples have high entropy)
- **Contradiction**: Should detect some (recall ≈ 0.20-0.40 based on previous tests)

## Troubleshooting

### If backend is not running:
```bash
# Start backend
uvicorn src.server:app --reload --port 8000
```

### If evaluation fails:
1. Check backend logs for errors
2. Verify dataset JSON is valid: `python check_dataset.py`
3. Check if samples are timing out (increase timeout in script if needed)

### If NLI scores are missing:
1. Check backend health: `curl http://localhost:8000/health`
2. Verify `nli_loaded: true` in health response
3. Check backend logs for NLI loading errors

## Quick Test Command (All-in-One)

```bash
# 1. Test contradiction detection
python test_contradiction_fix.py

# 2. Run full evaluation
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_100_samples.json --mode fhri --fhri_threshold 0.65

# 3. Check results
python -c "import json; d=json.load(open('results/eval_100_samples.json')); print('Accuracy:', d['metrics']['overall']['accuracy']); print('F1 Scores:', {k: v['f1_score'] for k, v in d['metrics'].items() if k != 'overall'})"
```



























