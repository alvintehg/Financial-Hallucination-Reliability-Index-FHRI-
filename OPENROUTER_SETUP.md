# OpenRouter Setup Complete! ✅

Your scripts are now configured to work with **OpenRouter API keys** (DeepSeek via OpenRouter).

## What Changed

The following scripts now **automatically detect** OpenRouter keys and use the correct API endpoint:

1. ✅ **[scripts/evaluate_detection.py](scripts/evaluate_detection.py)** - Main evaluation script
2. ✅ **[scripts/evaluate_detection_checkpoint.py](scripts/evaluate_detection_checkpoint.py)** - Checkpoint version
3. ✅ **[scripts/test_deepseek_api.py](scripts/test_deepseek_api.py)** - API test script

## How It Works

The scripts detect if your key starts with `sk-or-` and automatically:
- Use OpenRouter endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Set correct model name: `deepseek/deepseek-chat`
- Add OpenRouter headers

**No configuration needed - it just works!**

---

## Your API Key Status

✅ **API Key Set:** `sk-or-v1-4...d6e0a`
✅ **Type:** OpenRouter (DeepSeek)
✅ **Status:** Working correctly
✅ **Test Result:** Successfully completed API call

---

## Commands to Run SelfCheckGPT Evaluation

### **Test Your Setup (Run This First)**

```bash
python scripts/test_deepseek_api.py
```

**Expected output:**
```
[OK] DEEPSEEK_API_KEY found: sk-or-v1-4...d6e0a
  Detected: OpenRouter API key
[SUCCESS] API call successful!
[OK] DeepSeek API is working correctly!
```

---

### **Day 1: Process First 5000 Samples**

```bash
python scripts/evaluate_detection_checkpoint.py --dataset data/fhri_evaluation_dataset_full.json --output results/eval_10k_selfcheck_static.json --mode selfcheck --use_static_answers --selfcheck_k 3 --start_index 0 --end_index 5000 --checkpoint_interval 100
```

**Expected time:** 7-14 hours (run overnight)
**Checkpoint file:** `results/eval_10k_selfcheck_static.json.checkpoint`

---

### **Day 2: Process Next 5000 Samples**

```bash
python scripts/evaluate_detection_checkpoint.py --dataset data/fhri_evaluation_dataset_full.json --output results/eval_10k_selfcheck_static.json --mode selfcheck --use_static_answers --selfcheck_k 3 --start_index 5000 --end_index 10000 --checkpoint_interval 100 --resume
```

**Expected time:** 7-14 hours (run overnight)
**Final report:** `results/eval_10k_selfcheck_static.json`

---

## Cost Estimate (OpenRouter)

OpenRouter adds a small markup over DeepSeek's base pricing.

**DeepSeek via OpenRouter pricing:**
- Input: ~$0.20-0.30 per million tokens
- Output: ~$0.40-0.60 per million tokens

**For 10,000 samples:**
- Total API calls: 30,000 (3 calls per sample with k=3)
- Estimated tokens: 10-20 million
- **Estimated cost: $3-7 USD** (slightly more than direct DeepSeek)

**For 5,000 samples:**
- Total API calls: 15,000
- **Estimated cost: $1.5-3.5 USD per chunk**

**Note:** OpenRouter pricing may vary. Check https://openrouter.ai/models for exact rates.

---

## Monitoring Your Run

While running, you'll see output like:

```
[1/5000] Evaluating sample numeric_kpi_0893: What's Google's dividend yield?...
  [OK] Correct: True=hallucination, Predicted=hallucination

[100/5000] Evaluating sample ...
[CHECKPOINT] Saved at sample 100/5000
  Progress: 100 samples processed
  Speed: 0.18 samples/sec
  ETA: 7:33:20
  Checkpoint: results/eval_10k_selfcheck_static.json.checkpoint
```

---

## Key Features

✅ **Auto-detection** - Automatically detects OpenRouter vs Direct DeepSeek keys
✅ **Checkpoint support** - Saves progress every 100 samples
✅ **Resume capability** - Continue from where you left off
✅ **No backend required** - Uses `--use_static_answers` (offline mode)
✅ **Progress tracking** - Shows speed, ETA, and completion

---

## Differences: OpenRouter vs Direct DeepSeek

| Feature | OpenRouter | Direct DeepSeek |
|---------|-----------|-----------------|
| **API Endpoint** | `openrouter.ai/api/v1/...` | `api.deepseek.com/v1/...` |
| **Model Name** | `deepseek/deepseek-chat` | `deepseek-chat` |
| **Cost** | Slightly higher (markup) | Lower (direct) |
| **Setup** | Easier (single key for many models) | More restrictive |
| **Rate Limits** | OpenRouter's limits | DeepSeek's limits |
| **Reliability** | Extra routing layer | Direct connection |

Your current setup uses **OpenRouter**, which works great for this evaluation!

---

## Troubleshooting

### **"Selfcheck call failed" errors**

If you see occasional failures:
- **Normal:** API timeouts happen, script continues
- **Many failures:** Check OpenRouter status or rate limits

### **Rate limiting**

OpenRouter may have rate limits. If hit:
- Script will show timeout errors
- Reduce `--selfcheck_k` from 3 to 2
- Or increase timeout in the script

### **Want to switch to Direct DeepSeek?**

1. Get API key from https://platform.deepseek.com/
2. Set it: `setx DEEPSEEK_API_KEY "sk-..."`
3. Script will auto-detect and use direct endpoint

---

## Quick Reference

**Test API:**
```bash
python scripts/test_deepseek_api.py
```

**Run Day 1 (0-5000):**
```bash
python scripts/evaluate_detection_checkpoint.py --dataset data/fhri_evaluation_dataset_full.json --output results/eval_10k_selfcheck_static.json --mode selfcheck --use_static_answers --selfcheck_k 3 --start_index 0 --end_index 5000 --checkpoint_interval 100
```

**Run Day 2 (5000-10000):**
```bash
python scripts/evaluate_detection_checkpoint.py --dataset data/fhri_evaluation_dataset_full.json --output results/eval_10k_selfcheck_static.json --mode selfcheck --use_static_answers --selfcheck_k 3 --start_index 5000 --end_index 10000 --checkpoint_interval 100 --resume
```

---

**You're all set! 🚀**

Your OpenRouter key is working and the scripts are ready to run.
