# Step-by-Step Evaluation Guide

## ✅ Confirmation: All scripts use the SAME dataset
- **Dataset:** `data/evaluation_dataset.json` (100 samples: 57 accurate, 26 hallucination, 17 contradiction)
- **Same dataset used for:** All 3 evaluation scripts

---

## Step 1: Start Backend Server

**Open Terminal 1 (keep it running):**
```bash
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
uvicorn src.server:app --port 8000
```

**Wait for:** Server to start (you'll see "Uvicorn running on http://127.0.0.1:8000")

**✅ Check:** Open browser to `http://localhost:8000/health` - should return JSON

---

## Step 2: Run Comparative Baseline Evaluation

**Open Terminal 2 (new terminal):**
```bash
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
python scripts/evaluate_comparative_baselines.py --dataset data/evaluation_dataset.json --output results/comparative_baselines.json
```

**What it does:**
- Tests 4 methods on your 100 samples:
  - Entropy-only
  - NLI-only  
  - RAG-only
  - FHRI-full
- **Runtime:** ~30-45 minutes (100 samples × 4 methods)

**Output:**
- Console: Progress and final comparison table
- File: `results/comparative_baselines.json`

**What you'll get:**
- Table showing which method performs best
- Precision/Recall/F1 for each method
- Proof that FHRI-full outperforms single methods

---

## Step 3: Run Ablation Study

**In Terminal 2 (after Step 2 completes):**
```bash
python scripts/evaluate_ablation_study.py --dataset data/evaluation_dataset.json --output results/ablation_study.json
```

**What it does:**
- Tests FHRI with components removed one by one:
  - FHRI-full (baseline)
  - FHRI - Entropy
  - FHRI - Contradiction
  - FHRI - Grounding
  - FHRI - Numeric
  - FHRI - Temporal
- **Runtime:** ~15-20 minutes (100 samples × 1 query per sample)

**Output:**
- Console: Component contribution analysis
- File: `results/ablation_study.json`

**What you'll get:**
- Which components are most important (largest performance drop when removed)
- Δ F1 scores showing component impact

---

## Step 4: Cross-Domain Comparison (Optional)

**This requires a general QA dataset. Two options:**

### Option A: Skip This (Recommended for now)
- You can skip this if you don't have time to create a general QA dataset
- Your thesis can still show comparative baselines and ablation study

### Option B: Create General QA Dataset

**Step 4a: Create Template**
```bash
python scripts/evaluate_cross_domain.py --create_template
```

**Step 4b: Edit `data/general_qa_dataset.json`**
- Add 50-100 general knowledge questions (not finance-related)
- Examples:
  - "What is the capital of France?"
  - "Who wrote Romeo and Juliet?"
  - "What is the speed of light?"
- Format: Same as your finance dataset

**Step 4c: Run Cross-Domain Evaluation**
```bash
python scripts/evaluate_cross_domain.py --finance_dataset data/evaluation_dataset.json --general_dataset data/general_qa_dataset.json --output results/cross_domain_comparison.json
```

**Runtime:** ~20-30 minutes

---

## Step 5: View Results

**All results saved in `results/` folder:**

1. **`results/comparative_baselines.json`**
   - Open in text editor or JSON viewer
   - Contains: Metrics for each method (entropy_only, nli_only, rag_only, fhri_full)

2. **`results/ablation_study.json`**
   - Contains: Metrics for each variant (fhri_full, fhri_no_entropy, etc.)

3. **`results/cross_domain_comparison.json`** (if you ran Step 4)
   - Contains: Finance vs General domain comparison

---

## Step 6: Update Research Contribution Statement

**Edit:** `RESEARCH_CONTRIBUTION_STATEMENT.md`

**Replace these placeholders with actual results:**
- `(to be measured)` → Your actual metrics
- Update tables with real numbers from JSON files

**Example:**
```markdown
| Method | Macro F1 |
|--------|----------|
| Entropy-Only | 0.5234 |  ← From comparative_baselines.json
| FHRI-Full | 0.6391 |     ← Your existing result
```

---

## Quick Reference: All Commands in Order

```bash
# Terminal 1: Start server (keep running)
uvicorn src.server:app --port 8000

# Terminal 2: Run evaluations
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"

# 1. Comparative Baselines (~30-45 min)
python scripts/evaluate_comparative_baselines.py --dataset data/evaluation_dataset.json --output results/comparative_baselines.json

# 2. Ablation Study (~15-20 min)
python scripts/evaluate_ablation_study.py --dataset data/evaluation_dataset.json --output results/ablation_study.json

# 3. Cross-Domain (optional, ~20-30 min if you create general QA dataset)
python scripts/evaluate_cross_domain.py --create_template
# (Edit data/general_qa_dataset.json)
python scripts/evaluate_cross_domain.py --finance_dataset data/evaluation_dataset.json --general_dataset data/general_qa_dataset.json --output results/cross_domain_comparison.json
```

---

## Expected Total Runtime

- **Minimum (Steps 1-3):** ~45-65 minutes
- **Full (Steps 1-4):** ~65-95 minutes

---

## Troubleshooting

### "Backend connection failed"
- Make sure Terminal 1 has server running
- Check `http://localhost:8000/health` in browser

### "Timeout errors"
- Some queries take longer, this is normal
- Scripts have retry logic built-in

### "Empty results"
- Check that `data/evaluation_dataset.json` exists
- Verify it has 100 samples

---

## What Results You'll Get

### 1. Comparative Baselines
**Proves:** FHRI-full outperforms single-method baselines
- Use for: Thesis Table 4.1

### 2. Ablation Study  
**Proves:** Each component contributes to performance
- Use for: Thesis Table 4.2

### 3. Cross-Domain (if run)
**Proves:** FHRI works better in finance domain
- Use for: Thesis Table 4.3

---

## Next Steps After Running

1. **Read JSON files** to get exact metrics
2. **Update RESEARCH_CONTRIBUTION_STATEMENT.md** with real numbers
3. **Create thesis tables** from the metrics
4. **Write Chapter 4 (Results)** using the tables

---

**Ready to start? Begin with Step 1!** 🚀




















