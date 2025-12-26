# Comparative Evaluation Guide

This guide explains how to run the four comparative evaluation experiments to complete your research contribution analysis.

---

## Overview

You now have **4 evaluation scripts** to run comparative experiments:

1. **Comparative Baselines** (`evaluate_comparative_baselines.py`) - Compare FHRI vs single-method approaches
2. **Ablation Study** (`evaluate_ablation_study.py`) - Measure each component's contribution
3. **Cross-Domain Comparison** (`evaluate_cross_domain.py`) - Compare finance QA vs general QA
4. **Research Contribution Statement** (`RESEARCH_CONTRIBUTION_STATEMENT.md`) - Academic framing document

---

## Prerequisites

1. **Backend Server Running:**
   ```bash
   uvicorn src.server:app --port 8000
   ```

2. **Evaluation Dataset Ready:**
   - Your existing `data/evaluation_dataset.json` (100 samples)
   - For cross-domain: Create `data/general_qa_dataset.json` (see below)

3. **Python Dependencies:**
   - All scripts use existing dependencies from your project
   - No additional packages needed

---

## 1. Comparative Baseline Evaluation

**Purpose:** Compare FHRI-full against single-method baselines (Entropy-only, NLI-only, RAG-only)

**Command:**
```bash
python scripts/evaluate_comparative_baselines.py \
    --dataset data/evaluation_dataset.json \
    --output results/comparative_baselines.json \
    --backend http://localhost:8000
```

**What It Does:**
- Runs each sample through 4 detection methods:
  - `entropy_only`: Only semantic entropy (threshold: 2.0)
  - `nli_only`: Only NLI contradiction (threshold: 0.15 soft, 0.40 hard)
  - `rag_only`: Only grounding/retrieval faithfulness (threshold: 0.6)
  - `fhri_full`: Full FHRI with all components
- Calculates Precision, Recall, F1 for each method
- Generates comparative report

**Output:**
- `results/comparative_baselines.json` - Full results with metrics
- Console report showing:
  - Overall accuracy and macro F1 for each method
  - Per-class F1-score comparison
  - Which method performs best

**Expected Runtime:** ~30-45 minutes (100 samples × 4 methods × ~5 seconds per query)

**How to Use Results:**
- Add to thesis Chapter 4 (Results section)
- Create Table 4.1: "Comparative Baseline Performance"
- Show that FHRI-full outperforms single-method baselines

---

## 2. Ablation Study

**Purpose:** Measure each FHRI component's contribution by removing them one by one

**Command:**
```bash
python scripts/evaluate_ablation_study.py \
    --dataset data/evaluation_dataset.json \
    --output results/ablation_study.json \
    --backend http://localhost:8000
```

**What It Does:**
- Evaluates 6 variants:
  - `fhri_full`: All components
  - `fhri_no_entropy`: Remove entropy component
  - `fhri_no_contradiction`: Remove contradiction component
  - `fhri_no_grounding`: Remove grounding component
  - `fhri_no_numeric`: Remove numeric component
  - `fhri_no_temporal`: Remove temporal component
- Recalculates FHRI score with component removed
- Measures performance drop when each component is removed

**Output:**
- `results/ablation_study.json` - Full results with metrics
- Console report showing:
  - Performance of each variant
  - Δ F1 vs full FHRI (negative = component is important)
  - Component contribution analysis

**Expected Runtime:** ~15-20 minutes (100 samples × 1 query per sample, post-processing)

**How to Use Results:**
- Add to thesis Chapter 4 (Results section)
- Create Table 4.2: "Ablation Study Results"
- Show which components are most critical (largest negative Δ F1)

---

## 3. Cross-Domain Comparison

**Purpose:** Compare FHRI performance on finance QA vs general QA datasets

**Step 1: Create General QA Dataset Template**
```bash
python scripts/evaluate_cross_domain.py --create_template
```

This creates `data/general_qa_dataset.json` with a template structure.

**Step 2: Add General QA Samples**

Edit `data/general_qa_dataset.json` and add 50-100 general knowledge questions:

```json
{
  "samples": [
    {
      "id": "general_001",
      "question": "What is the capital of France?",
      "ground_truth_label": "accurate",
      "your_annotation": "accurate"
    },
    {
      "id": "general_002",
      "question": "Who wrote Romeo and Juliet?",
      "ground_truth_label": "accurate",
      "your_annotation": "accurate"
    },
    {
      "id": "general_003",
      "question": "What is the speed of light?",
      "ground_truth_label": "accurate",
      "your_annotation": "accurate"
    }
    // ... add more samples
  ]
}
```

**Step 3: Run Cross-Domain Evaluation**
```bash
python scripts/evaluate_cross_domain.py \
    --finance_dataset data/evaluation_dataset.json \
    --general_dataset data/general_qa_dataset.json \
    --output results/cross_domain_comparison.json \
    --backend http://localhost:8000
```

**What It Does:**
- Evaluates finance dataset (your existing 100 samples)
- Evaluates general QA dataset (your new samples)
- Compares performance metrics across domains
- Analyzes domain adaptation (does FHRI work better in finance?)

**Output:**
- `results/cross_domain_comparison.json` - Full results
- Console report showing:
  - Performance by domain (accuracy, macro F1, avg FHRI)
  - Per-class F1 comparison
  - Domain adaptation conclusion

**Expected Runtime:** ~20-30 minutes (depends on general QA dataset size)

**How to Use Results:**
- Add to thesis Chapter 4 (Results section)
- Create Table 4.3: "Cross-Domain Performance Comparison"
- Show that FHRI performs better in finance domain (domain adaptation success)

---

## 4. Research Contribution Statement

**File:** `RESEARCH_CONTRIBUTION_STATEMENT.md`

**What It Contains:**
- Formal academic framing of your contributions
- Methodological contribution (FHRI framework)
- Empirical contribution (comparative evaluation)
- Comparison with prior work
- Metrics summary
- Thesis integration guide

**How to Use:**
1. **Read the document** - Understand how your work is framed
2. **Update with actual results** - Replace "(to be measured)" with your evaluation results
3. **Copy sections to thesis:**
   - Chapter 1: Contribution statement (Section 1.3)
   - Chapter 4: Results tables (use actual metrics)
   - Chapter 5: Discussion points

---

## Running All Experiments

**Recommended Order:**

1. **First:** Run comparative baselines (establishes FHRI vs baselines)
2. **Second:** Run ablation study (shows component contributions)
3. **Third:** Create general QA dataset and run cross-domain comparison
4. **Fourth:** Update research contribution statement with actual results

**Full Command Sequence:**
```bash
# 1. Comparative Baselines
python scripts/evaluate_comparative_baselines.py \
    --dataset data/evaluation_dataset.json \
    --output results/comparative_baselines.json

# 2. Ablation Study
python scripts/evaluate_ablation_study.py \
    --dataset data/evaluation_dataset.json \
    --output results/ablation_study.json

# 3. Create General QA Template
python scripts/evaluate_cross_domain.py --create_template

# 4. (Manually edit data/general_qa_dataset.json to add samples)

# 5. Cross-Domain Comparison
python scripts/evaluate_cross_domain.py \
    --finance_dataset data/evaluation_dataset.json \
    --general_dataset data/general_qa_dataset.json \
    --output results/cross_domain_comparison.json
```

**Total Runtime:** ~1.5-2 hours (depending on dataset sizes and server performance)

---

## Interpreting Results

### Comparative Baselines

**What to Look For:**
- FHRI-full should have **higher macro F1** than single methods
- FHRI-full should have **better balance** (not sacrificing precision for recall)
- **Key Finding:** "FHRI fusion outperforms single-method baselines by X% in macro F1"

### Ablation Study

**What to Look For:**
- Components with **large negative Δ F1** are most important
- Components with **small or positive Δ F1** may be less critical
- **Key Finding:** "Numeric and grounding components show highest impact (Δ F1 = -0.XX)"

### Cross-Domain Comparison

**What to Look For:**
- Finance domain should have **higher macro F1** than general domain
- **Key Finding:** "FHRI performs X% better in finance domain, demonstrating successful domain adaptation"

---

## Troubleshooting

### Backend Connection Failed
- **Solution:** Make sure `uvicorn src.server:app --port 8000` is running
- Check `http://localhost:8000/health` in browser

### Timeout Errors
- **Solution:** Increase timeout in script (default: 90s) or check server logs
- Some queries may take longer (especially with entropy calculation)

### Empty Results
- **Solution:** Check that dataset has valid `ground_truth_label` fields
- Ensure samples have format: `{"id": "...", "question": "...", "ground_truth_label": "accurate|hallucination|contradiction"}`

### Component Scores Missing
- **Solution:** Check that backend is returning FHRI subscores in `meta.fhri_subscores`
- Verify `use_fhri=True` in query payload

---

## Next Steps

1. **Run all experiments** (1-2 hours)
2. **Update RESEARCH_CONTRIBUTION_STATEMENT.md** with actual metrics
3. **Create thesis tables** from JSON results:
   - Table 4.1: Comparative baselines
   - Table 4.2: Ablation study
   - Table 4.3: Cross-domain comparison
4. **Write Chapter 4 (Results)** using the tables
5. **Write Chapter 5 (Discussion)** using the contribution statement

---

## Files Created

- ✅ `scripts/evaluate_comparative_baselines.py` - Baseline comparison script
- ✅ `scripts/evaluate_ablation_study.py` - Ablation study script
- ✅ `scripts/evaluate_cross_domain.py` - Cross-domain comparison script
- ✅ `RESEARCH_CONTRIBUTION_STATEMENT.md` - Academic contribution document
- ✅ `COMPARATIVE_EVALUATION_GUIDE.md` - This guide

---

**Good luck with your evaluation!** 🚀




















