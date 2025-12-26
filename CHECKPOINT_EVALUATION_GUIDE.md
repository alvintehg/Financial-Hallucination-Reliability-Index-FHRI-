# Checkpoint Evaluation Guide

This guide explains how to run SelfCheckGPT evaluation on the 10k dataset in chunks with checkpoint support.

## Features

✅ **Checkpoint saving** - Saves progress every N samples (default: 100)
✅ **Resume capability** - Continue from where you left off if interrupted
✅ **Chunked processing** - Process dataset in parts (e.g., first 5000, then next 5000)
✅ **Progress tracking** - Shows speed, ETA, and completion status
✅ **No backend required** - Works in static mode using stored answers

---

## Quick Start: SelfCheckGPT Evaluation in Two Days

### **Day 1: Process First 5000 Samples**

```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_10k_selfcheck_static.json \
  --mode selfcheck \
  --use_static_answers \
  --selfcheck_k 3 \
  --start_index 0 \
  --end_index 5000 \
  --checkpoint_interval 100
```

**Expected time:** 7-14 hours
**Checkpoint file:** `results/eval_10k_selfcheck_static.json.checkpoint`

---

### **Day 2: Process Next 5000 Samples**

```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_10k_selfcheck_static.json \
  --mode selfcheck \
  --use_static_answers \
  --selfcheck_k 3 \
  --start_index 5000 \
  --end_index 10000 \
  --checkpoint_interval 100 \
  --resume
```

**Expected time:** 7-14 hours
**Final report:** `results/eval_10k_selfcheck_static.json`

---

## Important Notes

### **DeepSeek API Key Required**

The script automatically reads from environment variable `DEEPSEEK_API_KEY`.

**Check if set:**
```powershell
# PowerShell
echo $env:DEEPSEEK_API_KEY

# Command Prompt
echo %DEEPSEEK_API_KEY%
```

**If not set:**
```powershell
# PowerShell (temporary, current session only)
$env:DEEPSEEK_API_KEY = "sk-your-key-here"

# Windows (permanent)
setx DEEPSEEK_API_KEY "sk-your-key-here"
```

**After setting permanently, restart your terminal.**

---

### **Checkpoint Behavior**

1. **Auto-save:** Checkpoint saved every 100 samples (configurable with `--checkpoint_interval`)
2. **Resume:** Use `--resume` flag to continue from last checkpoint
3. **Atomic saves:** Uses temporary file + rename to prevent corruption
4. **Progress info:** Shows speed (samples/sec) and estimated time remaining

**Checkpoint file location:**
By default: `{output_path}.checkpoint`
Example: `results/eval_10k_selfcheck_static.json.checkpoint`

**Checkpoint contains:**
- Current index position
- All processed results so far
- Evaluation settings (mode, thresholds, etc.)
- Timestamp of last save

---

### **If Interrupted**

If the script crashes or you need to stop it:

1. **Don't delete the checkpoint file** - it contains your progress
2. **Resume with `--resume` flag:**
   ```bash
   python scripts/evaluate_detection_checkpoint.py \
     --dataset data/fhri_evaluation_dataset_full.json \
     --output results/eval_10k_selfcheck_static.json \
     --mode selfcheck \
     --use_static_answers \
     --selfcheck_k 3 \
     --start_index 0 \
     --end_index 5000 \
     --checkpoint_interval 100 \
     --resume
   ```

The script will:
- Load results from checkpoint
- Continue from the last saved index
- Preserve all previous results

---

## Advanced Usage

### **Change Checkpoint Frequency**

Save more frequently (every 50 samples):
```bash
--checkpoint_interval 50
```

Save less frequently (every 500 samples):
```bash
--checkpoint_interval 500
```

**Trade-off:**
- More frequent = safer if crash, but slower (more disk I/O)
- Less frequent = faster, but lose more progress if crash

---

### **Custom Checkpoint Path**

Specify a different checkpoint file:
```bash
--checkpoint results/my_custom_checkpoint.json
```

---

### **Process Specific Range**

Process samples 2000-3000 only:
```bash
--start_index 2000 \
--end_index 3000
```

---

### **Test on Small Sample First**

Test on first 100 samples (takes ~5-15 minutes):
```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_100_selfcheck_test.json \
  --mode selfcheck \
  --use_static_answers \
  --selfcheck_k 3 \
  --start_index 0 \
  --end_index 100 \
  --checkpoint_interval 10
```

---

## Baseline and FHRI Modes

The checkpoint script also works with other modes:

### **Entropy Baseline (Fast - no checkpoints needed)**
```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_10k_baseline_static.json \
  --mode baseline \
  --use_static_answers \
  --threshold 2.0 \
  --start_index 0 \
  --end_index 10000
```

**Time:** ~30-45 minutes for 10k samples

---

### **FHRI Mode (Fast - but you already have results)**
```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_10k_fhri_static.json \
  --mode fhri \
  --use_static_answers \
  --fhri_threshold 0.70 \
  --start_index 0 \
  --end_index 10000
```

**Time:** ~35-50 minutes for 10k samples

---

## Monitoring Progress

While the script is running, you'll see:

```
[1/5000] Evaluating sample numeric_kpi_0893: What's Google's dividend yield?...
  [OK] Correct: True=hallucination, Predicted=hallucination

[2/5000] Evaluating sample directional_0124: Is Tesla stock going up?...
  [X] Incorrect: True=accurate, Predicted=hallucination

...

[100/5000] Evaluating sample ...
[CHECKPOINT] Saved at sample 100/5000
  Progress: 100 samples processed
  Speed: 0.18 samples/sec
  ETA: 7:33:20
  Checkpoint: results/eval_10k_selfcheck_static.json.checkpoint
```

**Key metrics:**
- **Speed:** Samples processed per second
- **ETA:** Estimated time remaining
- **Progress:** How many samples completed

---

## Cost Estimation (SelfCheckGPT)

**DeepSeek API pricing:**
- Input: ~$0.14 per million tokens
- Output: ~$0.28 per million tokens

**For 10,000 samples:**
- Total API calls: 30,000 (3 per sample)
- Estimated tokens: 10-20 million
- **Estimated cost: $2-5 USD**

**For 5,000 samples:**
- Total API calls: 15,000
- **Estimated cost: $1-2.5 USD**

---

## Troubleshooting

### **"DEEPSEEK_API_KEY not set" warning**

Set the environment variable:
```powershell
$env:DEEPSEEK_API_KEY = "sk-your-key-here"
```

---

### **"Selfcheck call failed" errors**

Common causes:
1. **Rate limit hit** - DeepSeek limits requests per minute
2. **Network timeout** - API took too long to respond
3. **Invalid API key** - Check your key is correct

The script will continue and mark failed calls with empty answers.

---

### **Script is too slow**

For SelfCheckGPT, this is expected (3 API calls per sample).

**Speed improvements:**
- Reduce `--selfcheck_k` from 3 to 2 (faster but less accurate)
- Use smaller sample range for testing
- Run on a faster network connection

---

### **Checkpoint file corrupted**

If checkpoint is corrupted:
1. Delete the checkpoint file
2. Note the last index you saw in terminal output
3. Run with `--start_index <last_index>` (without `--resume`)

---

## Example: Complete Two-Day Workflow

### **Setup (Do Once)**
```powershell
# Set API key (if not already set)
setx DEEPSEEK_API_KEY "sk-your-actual-key-here"

# Restart terminal to load the new environment variable
```

### **Day 1 Evening (Start before bed)**
```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_10k_selfcheck_static.json \
  --mode selfcheck \
  --use_static_answers \
  --selfcheck_k 3 \
  --start_index 0 \
  --end_index 5000 \
  --checkpoint_interval 100
```

**Let it run overnight (~7-14 hours)**

### **Day 2 Evening (Continue)**
```bash
python scripts/evaluate_detection_checkpoint.py \
  --dataset data/fhri_evaluation_dataset_full.json \
  --output results/eval_10k_selfcheck_static.json \
  --mode selfcheck \
  --use_static_answers \
  --selfcheck_k 3 \
  --start_index 5000 \
  --end_index 10000 \
  --checkpoint_interval 100 \
  --resume
```

**Let it run overnight again**

### **Day 3 Morning (Check Results)**
```bash
# Check if completed
ls results/eval_10k_selfcheck_static.json

# View summary
python -c "import json; data=json.load(open('results/eval_10k_selfcheck_static.json')); print(f\"Accuracy: {data['metrics']['overall']['accuracy']:.2%}\"); print(f\"Macro F1: {data['metrics']['overall']['macro_f1']:.4f}\")"
```

---

## Cleanup After Completion

Once evaluation is complete and you've verified the results:

```bash
# Delete checkpoint file (optional)
rm results/eval_10k_selfcheck_static.json.checkpoint
```

Keep the final report: `results/eval_10k_selfcheck_static.json`

---

## Summary of Files

| File | Purpose |
|------|---------|
| `scripts/evaluate_detection_checkpoint.py` | Main checkpoint-enabled evaluation script |
| `results/eval_10k_selfcheck_static.json` | Final evaluation report |
| `results/eval_10k_selfcheck_static.json.checkpoint` | Temporary checkpoint file (auto-created) |
| `data/fhri_evaluation_dataset_full.json` | Input dataset (10,000 samples) |

---

## Quick Reference: Command Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--dataset` | Path to dataset JSON | `data/evaluation_dataset.json` |
| `--output` | Path to save final report | `results/evaluation_checkpoint.json` |
| `--checkpoint` | Custom checkpoint path | `{output}.checkpoint` |
| `--checkpoint_interval` | Save every N samples | `100` |
| `--start_index` | Start from this sample | `0` |
| `--end_index` | End at this sample | End of dataset |
| `--resume` | Resume from checkpoint | `False` (flag) |
| `--mode` | `baseline`, `fhri`, or `selfcheck` | `fhri` |
| `--use_static_answers` | Use stored answers (offline) | `False` (flag) |
| `--selfcheck_k` | Self-consistency samples | `3` |
| `--fhri_threshold` | FHRI accuracy threshold | `0.70` |
| `--threshold` | Entropy threshold (baseline) | `2.0` |

---

**Good luck with your evaluation! 🚀**
