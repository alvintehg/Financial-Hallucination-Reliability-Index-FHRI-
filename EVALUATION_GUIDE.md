# Evaluation Guide for FYP Students

This guide explains how to use the evaluation tools to measure your LLM Financial Chatbot's performance for your Final Year Project report.

## What Has Been Created for You

### 1. Evaluation Scripts ✅

Four Python scripts have been created in the `scripts/` directory:

1. **`evaluate_detection.py`** - Measures precision, recall, F1 for hallucination/contradiction detection
2. **`measure_latency.py`** - Measures response time statistics (mean, p95, p99)
3. **`generate_contradictions.py`** - Generates synthetic contradiction pairs for testing
4. **`generate_plots.py`** - Creates visualizations (confusion matrix, histograms, bar charts)

### 2. Templates ✅

Two templates have been created:

1. **`data/evaluation_template.json`** - Template for creating annotated datasets
2. **`docs/user_study_template.md`** - Complete user study questionnaire with 23 questions

### 3. Documentation ✅

The README.md has been updated with a comprehensive "Evaluation and Testing" section explaining how to use all the tools.

---

## Quick Start: Running Evaluations

### Step 1: Generate Synthetic Test Data (2 minutes)

```bash
# Generate 50 contradiction pairs for NLI testing
python scripts/generate_contradictions.py --output data/contradiction_pairs.json --count 50
```

**Output:** `data/contradiction_pairs.json` with 50 synthetic contradiction pairs

---

### Step 2: Measure Latency (5 minutes)

```bash
# Ensure server is running first
uvicorn src.server:app --port 8000

# In another terminal, run latency measurement
python scripts/measure_latency.py --runs 50 --output results/latency_report.json
```

**What this does:**
- Sends 10 test questions to the backend
- Each question is repeated 50 times
- Measures total time for each request
- Calculates mean, median, p95, p99 latency

**Output:** `results/latency_report.json` with:
- Mean latency (e.g., 1,234ms)
- P95 latency (e.g., 2,100ms)
- Success rate (e.g., 98.5%)
- Detailed measurements for each request

---

### Step 3: Create Annotated Dataset (Manual - 1-2 hours)

**This requires manual work by you:**

```bash
# Copy the template
copy data\evaluation_template.json data\evaluation_dataset.json

# Open data\evaluation_dataset.json in a text editor
# Add 50-100 Q&A pairs with labels
```

**How to annotate:**

1. Use the chatbot to generate answers for various questions
2. For each answer, decide:
   - `"accurate"` - if the answer is correct and grounded in sources
   - `"hallucination"` - if the answer contains fabricated or incorrect information
   - `"contradiction"` - if the answer contradicts a previous response

**Example annotation:**

```json
{
  "id": "sample_010",
  "question": "What was Microsoft's Q3 2024 revenue?",
  "retrieved_passages": [
    "Microsoft Corporation (MSFT) Q3 2024 revenue was $61.9 billion, up 17% YoY..."
  ],
  "llm_answer": "Microsoft reported Q3 2024 revenue of $61.9 billion, a 17% increase year-over-year.",
  "ground_truth_label": "",
  "your_annotation": "accurate",
  "notes": "Answer correctly cites source data"
}
```

**Target:** 50-100 samples (aim for balanced: ~40% accurate, ~40% hallucination, ~20% contradiction)

---

### Step 4: Evaluate Detection Performance (2 minutes)

**After you complete the manual annotation:**

```bash
# Ensure server is running
uvicorn src.server:app --port 8000

# Run evaluation
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/evaluation_report.json
```

**What this does:**
- Reads your annotated dataset
- Sends each question to the chatbot
- Compares system predictions with your annotations
- Calculates precision, recall, F1-score

**Output:** `results/evaluation_report.json` with:
- Precision, Recall, F1 for hallucination detection
- Precision, Recall, F1 for contradiction detection
- Confusion matrix
- Overall accuracy

---

### Step 5: Generate Plots (1 minute)

```bash
# Install plotting libraries (if not already installed)
pip install matplotlib seaborn

# Generate all plots
python scripts/generate_plots.py --evaluation results/evaluation_report.json --latency results/latency_report.json --output results/plots/
```

**What this creates:**
- `confusion_matrix.png` - Heatmap showing prediction accuracy
- `metrics_comparison.png` - Bar chart comparing precision/recall/F1
- `f1_summary.png` - F1-scores for each class
- `latency_histogram.png` - Distribution of response times
- `latency_percentiles.png` - Min, median, mean, p95, p99, max
- `success_rate.png` - Pie chart of successful vs. failed requests

**Use these plots in your FYP report!**

---

## What You Need to Do Manually (Outside VS Code)

### 1. Manual Annotation (1-2 hours)

- Open `data/evaluation_dataset.json`
- Add 50-100 Q&A pairs with labels
- Follow the annotation guidelines in the template

### 2. User Study (2-3 hours)

**Template:** See `docs/user_study_template.md`

**Steps:**

1. **Create Google Form:**
   - Go to [Google Forms](https://forms.google.com)
   - Copy questions from `docs/user_study_template.md`
   - Set up Likert scales as "Multiple choice grid"

2. **Recruit Participants:**
   - Find 5-10 people (students, friends, family)
   - Target: Anyone with basic financial knowledge
   - No expert knowledge required

3. **Conduct Study:**
   - Have each participant use the chatbot for 10 minutes
   - Give them 5 task scenarios (see template)
   - Have them complete the questionnaire (5 minutes)
   - Record observations (confusion, surprises, issues)

4. **Analyze Results:**
   - Calculate mean trust score (Q1-Q7 average)
   - Calculate mean satisfaction score (Q8-Q12 average)
   - Count % who noticed hallucination detection
   - Analyze qualitative feedback (Q18-Q23)

**Expected Results:**

| Metric | Example Value |
|--------|---------------|
| Mean Trust Score | 3.8 / 5.0 |
| Mean Satisfaction Score | 4.1 / 5.0 |
| % Noticed Detection | 75% |
| Would Recommend | 80% |

### 3. Write FYP Report Sections

Use the evaluation results to write:

**Evaluation Section:**
- Describe your evaluation methodology
- Explain the annotated dataset (size, distribution)
- Explain the user study protocol
- Justify sample sizes

**Results Section:**
- Present metrics in tables
- Include plots (confusion matrix, latency histogram)
- Report user study findings
- Show statistical significance (if applicable)

**Discussion Section:**
- Interpret the results
- Explain why metrics are high/low
- Discuss limitations
- Compare with baseline (vanilla ChatGPT)
- Suggest improvements

---

## Expected Timeline

| Task | Time Required | When to Do It |
|------|--------------|---------------|
| Generate synthetic data | 2 min | Now ✅ |
| Measure latency | 5 min | Now ✅ |
| Manual annotation | 1-2 hours | This week |
| Run detection evaluation | 2 min | After annotation |
| Generate plots | 1 min | After evaluation |
| Create Google Form | 15 min | This week |
| Conduct user study | 2-3 hours | Next week |
| Analyze user study data | 1 hour | After study |
| Write report sections | 3-5 hours | Final week |

**Total estimated time:** ~8-12 hours (excluding report writing)

---

## Checklist for FYP Completion

### Scripts (All Done ✅)
- [x] Evaluation script created
- [x] Latency measurement script created
- [x] Contradiction generator created
- [x] Plotting script created

### Evaluation Tasks (You Need to Do)
- [ ] Generate synthetic contradiction pairs
- [ ] Measure latency (run script)
- [ ] Manually annotate 50-100 Q&A pairs
- [ ] Run detection evaluation
- [ ] Generate plots

### User Study Tasks (You Need to Do)
- [ ] Create Google Form from template
- [ ] Recruit 5-10 participants
- [ ] Conduct study sessions
- [ ] Collect questionnaire responses
- [ ] Analyze trust and satisfaction scores
- [ ] Extract qualitative themes

### Report Writing (You Need to Do)
- [ ] Write Evaluation methodology section
- [ ] Create Results tables with actual metrics
- [ ] Insert plots into report
- [ ] Write Discussion section
- [ ] Create presentation slides

---

## Troubleshooting

### "Backend offline" error
**Solution:** Start the server with `uvicorn src.server:app --port 8000`

### "Dataset not found" error
**Solution:** Create `data/evaluation_dataset.json` by copying the template

### "matplotlib not installed" error
**Solution:** Run `pip install matplotlib seaborn`

### Low F1-scores (< 0.5)
**Possible causes:**
- HALLU_THRESHOLD too strict (try increasing from 2.0 to 2.5)
- Poor quality annotations (review your labels)
- System genuinely struggling (discuss in limitations)

### High latency (> 5000ms)
**Possible causes:**
- Slow internet connection
- OpenRouter rate limits
- Heavy load on DeepSeek servers
- Try: Use `--provider demo` to measure baseline

---

## Example Results Section for Report

```markdown
## 5. Results

### 5.1 Hallucination Detection Performance

Table 5.1 shows the detection performance metrics.

| Metric | Precision | Recall | F1-Score |
|--------|-----------|--------|----------|
| Hallucination | 0.85 | 0.82 | 0.83 |
| Accurate | 0.88 | 0.90 | 0.89 |
| Contradiction | 0.78 | 0.75 | 0.76 |
| **Macro Average** | **0.84** | **0.82** | **0.83** |

The system achieved an overall accuracy of 84.3% across 87 test samples.
Figure 5.1 shows the confusion matrix.

### 5.2 Latency Analysis

Response latency was measured over 500 requests. Table 5.2 summarizes the results.

| Metric | Value |
|--------|-------|
| Mean Latency | 1,234ms |
| Median (p50) | 1,150ms |
| P95 Latency | 2,100ms |
| P99 Latency | 2,850ms |
| Success Rate | 98.5% |

The mean response time of 1.2 seconds is acceptable for a research prototype.
Figure 5.2 shows the latency distribution.

### 5.3 User Study Results

8 participants completed the user study (5 students, 3 early professionals).

**Trust and Reliability (n=8):**
- Mean trust score: 3.8 / 5.0 (SD = 0.6)
- Mean satisfaction score: 4.1 / 5.0 (SD = 0.5)
- 75% of participants noticed the hallucination detection feature
- 87.5% would use the chatbot for investment research

**Qualitative Findings:**
- Most liked: "Transparency about confidence", "Honest about limitations"
- Most disliked: "Sometimes too cautious", "Occasional false alarms"
- Improvement suggestions: "Explain why answers are flagged", "Add more financial data"
```

---

## Need Help?

1. **Evaluation scripts not working?** Check that the server is running first
2. **Not sure how to annotate?** See examples in `data/evaluation_template.json`
3. **User study questions unclear?** Read the full template in `docs/user_study_template.md`
4. **Report writing?** Follow the example structure above

**Good luck with your FYP!** 🎓📊
