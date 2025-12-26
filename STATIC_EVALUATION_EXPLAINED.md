# Static Evaluation Explained

## What Happens Step-by-Step

### Example: Sample fhri_061

**Dataset Entry (data/evaluation_dataset.json):**
```json
{
  "id": "fhri_061",
  "question": "What is the current stock price of Apple (AAPL)?",
  "llm_answer": "As of today, Apple (AAPL) is trading at $45.20 per share, making it a very affordable investment.",
  "ground_truth_label": "hallucination",
  "retrieved_passages": [],
  "fhri_spec": {
    "scenario_override": "numeric_kpi"
  }
}
```

---

## Step-by-Step Evaluation Process

### **Step 1: Load Sample**

```python
# evaluate_detection.py line 173-188
answer = sample.get("llm_answer", "")  # "As of today, Apple (AAPL) is trading at $45.20..."
question = sample.get("question", "")  # "What is the current stock price..."
passages = sample.get("retrieved_passages", [])  # []
scenario_override = sample.get("fhri_spec", {}).get("scenario_override")  # "numeric_kpi"
```

### **Step 2: Compute FHRI Locally**

```python
# evaluate_detection.py line 180-188
fhri_result = compute_fhri(
    answer=answer,
    question=question,
    passages=passages,  # Empty!
    entropy=None,       # Not computed in static mode
    api_facts=None,     # Not available in static mode
    scenario_override=scenario_override,
    multi_source_data=None  # Not available in static mode
)
```

### **Step 3: FHRI Scoring Components**

Inside `compute_fhri()` in `src/fhri_scoring.py`:

#### **3a. Grounding Score (G)**

```python
# src/fhri_scoring.py compute_grounding_score()

# Extract numeric claims from answer
from src.numeric_validators import extract_numeric_claims
claims = extract_numeric_claims(answer)
# Result: [{"value": 45.20, "unit": "$", "field_type": "price"}]

# Since multi_source_data is None, we can't validate against real price
# Since passages is empty [], there's no evidence

# Check entity grounding
from src.entity_validators import validate_entity_grounding
entity_result = validate_entity_grounding(answer, passages, api_data=None)
# Result: {"grounded_entities": 0, "ungrounded_entities": 1}  # "AAPL" not in passages

# Compute baseline overlap
answer_words = {"as", "of", "today", "apple", "aapl", "trading", "45.20", ...}
passage_words = {}  # Empty because passages is []
overlap = 0.20  # Low score due to no passages

# Apply fact penalty
# No validation possible → moderate penalty
fact_penalty = 0.6

# Final grounding score
G = overlap * fact_penalty = 0.20 * 0.6 = 0.12
```

**Why G is low:** No passages, no API data, can't validate claims.

#### **3b. Numeric/Directional Score (N/D)**

```python
# src/fhri_scoring.py compute_numerical_directional_score()

# Extract numeric claims
claims = extract_numeric_claims(answer)  # ["$45.20"]

# Try to validate against passages
# passages is empty → can't find reference value
# multi_source_data is None → no API price

# Since we can't validate, give a moderate score
N_or_D = 0.50  # Neutral (can't verify)
```

**Why N/D is moderate:** Can't validate without external data.

#### **3c. Temporal Score (T)**

```python
# Check for temporal keywords
has_temporal = "today" in answer.lower()  # True
has_evidence = bool(passages)  # False

# Since answer claims "today" but we have no recent evidence
T = 0.30  # Low score
```

**Why T is low:** Claims current data without recent evidence.

#### **3d. Consistency Score (C)**

```python
# Check internal consistency
# Look for contradictions within the answer itself
# "trading at $45.20" + "very affordable" → consistent
C = 0.75  # No internal contradictions found
```

#### **3e. Entropy Score (E)**

```python
# In static mode, entropy is None (not computed)
E = None
```

### **Step 4: Compute Weighted FHRI**

```python
# For scenario "numeric_kpi", weights are:
weights = {
    "G": 0.20,
    "N_or_D": 0.50,
    "T": 0.20,
    "C": 0.05,
    "E": 0.05
}

# Compute weighted sum (skip E since it's None)
fhri = (G * 0.20) + (N_or_D * 0.50) + (T * 0.20) + (C * 0.05)
fhri = (0.12 * 0.20) + (0.50 * 0.50) + (0.30 * 0.20) + (0.75 * 0.05)
fhri = 0.024 + 0.25 + 0.06 + 0.0375
fhri = 0.3715

# Normalize since E is missing (renormalize over available components)
total_weight = 0.20 + 0.50 + 0.20 + 0.05 = 0.95
fhri = fhri / 0.95 = 0.391
```

### **Step 5: Apply Scenario Threshold**

```python
# For "numeric_kpi" scenario, threshold is 0.75
threshold = 0.75

# Compare
if fhri > threshold:
    predicted_label = "accurate"
else:
    predicted_label = "hallucination"

# 0.391 < 0.75 → predicted_label = "hallucination"
```

### **Step 6: Compare with Ground Truth**

```python
true_label = "hallucination"
predicted_label = "hallucination"

correct = (true_label == predicted_label)  # True ✓
```

**Result:** ✓ Correct prediction!

---

## Why Static Mode is Useful

### **Advantages:**

1. **Reproducible Results**
   - Same answers → same FHRI scores
   - No LLM randomness

2. **Tests FHRI Logic Directly**
   - Isolates scoring algorithm
   - Not affected by LLM generation quality

3. **Fast**
   - No network calls to backend
   - No LLM inference time
   - 100 samples in ~30 seconds

4. **Controlled Testing**
   - Pre-written hallucinated answers
   - Known ground truth
   - Can test specific scenarios

### **When to Use Each Mode:**

| Mode | When to Use | Pros | Cons |
|------|-------------|------|------|
| **Static** | - Testing FHRI logic<br>- Reproducible benchmarks<br>- Quick iteration | Fast, consistent | Requires pre-filled answers |
| **Dynamic** | - End-to-end testing<br>- Live system validation<br>- Real-world simulation | Tests full pipeline | Slow, inconsistent, requires backend |

---

## Command Reference

### Basic Static Evaluation

```bash
# Subset (samples 61-88)
python scripts/evaluate_detection.py \
  --dataset data/evaluation_subset_61_88.json \
  --output results/eval_subset_static.json \
  --mode fhri \
  --use_static_answers

# Full dataset (samples 1-100)
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --output results/eval_full_static.json \
  --mode fhri \
  --use_static_answers
```

### With Custom Threshold

```bash
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --output results/eval_threshold_0.8.json \
  --mode fhri \
  --fhri_threshold 0.80 \
  --use_static_answers
```

### Baseline Comparison

```bash
# Baseline: Entropy-only (no FHRI)
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --output results/eval_baseline.json \
  --mode baseline \
  --use_static_answers

# FHRI mode
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --output results/eval_fhri.json \
  --mode fhri \
  --use_static_answers

# Compare results
python -c "
import json
baseline = json.load(open('results/eval_baseline.json'))
fhri = json.load(open('results/eval_fhri.json'))
print(f'Baseline Accuracy: {baseline[\"metrics\"][\"overall\"][\"accuracy\"]:.2%}')
print(f'FHRI Accuracy: {fhri[\"metrics\"][\"overall\"][\"accuracy\"]:.2%}')
"
```

---

## Expected Output

### Terminal Output (Success):

```
Evaluation mode: FHRI
  (FHRI: full reliability scoring enabled)
============================================================
HALLUCINATION & CONTRADICTION DETECTION EVALUATION
============================================================
Dataset: data/evaluation_subset_61_88.json
Mode: STATIC (using stored answers from dataset)
Hallucination threshold (entropy): 2.0
FHRI threshold (accurate): 0.7
============================================================

Found 28 samples in dataset
============================================================

[1/28] Evaluating sample fhri_061: What is the current stock price...
  [OK] Correct: True=hallucination, Predicted=hallucination

[2/28] Evaluating sample fhri_062: What is the dividend yield...
  [OK] Correct: True=hallucination, Predicted=hallucination

...

============================================================
EVALUATION RESULTS
============================================================

[Overall Performance]
  Accuracy: 89.29%
  Macro F1-Score: 0.4500
  Total Samples: 28
  Correct: 25

[Per-Class Metrics]

Class           Precision    Recall       F1-Score     Support
-----------------------------------------------------------------
hallucination   0.8929       1.0000       0.9434       25
accurate        0.0000       0.0000       0.0000       2
contradiction   0.0000       0.0000       0.0000       1

[OK] Report saved to: results/eval_subset_static.json
[OK] Evaluation complete!
```

### JSON Output (results/eval_subset_static.json):

```json
{
  "evaluation_metadata": {
    "backend_url": "http://localhost:8000",
    "hallucination_threshold": 2.0,
    "fhri_threshold": 0.7,
    "total_samples": 28,
    "evaluation_date": "2025-12-12 00:00:26"
  },
  "metrics": {
    "hallucination": {
      "precision": 0.8929,
      "recall": 1.0,
      "f1_score": 0.9434,
      "true_positives": 25,
      "false_negatives": 0
    },
    "overall": {
      "accuracy": 0.8929,
      "total_samples": 28
    }
  },
  "detailed_results": [
    {
      "sample_id": "fhri_061",
      "question": "What is the current stock price of Apple (AAPL)?",
      "true_label": "hallucination",
      "predicted_label": "hallucination",
      "fhri": 0.391,
      "fhri_subscores": {
        "G": 0.12,
        "N_or_D": 0.50,
        "T": 0.30,
        "C": 0.75
      },
      "correct": true
    }
  ]
}
```

---

## Troubleshooting

### Issue: "No samples available for calibration"

**Solution:** Make sure dataset has `llm_answer` fields filled:

```bash
python -c "
import json
data = json.load(open('data/evaluation_dataset.json'))
samples_with_answers = sum(1 for s in data['samples'] if s.get('llm_answer'))
print(f'{samples_with_answers} out of {len(data[\"samples\"])} have answers')
"
```

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution:** Run from project root:

```bash
cd "c:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
python scripts/evaluate_detection.py --use_static_answers ...
```

### Issue: Evaluation hangs or is slow

**Check:** Make sure you're using `--use_static_answers` flag! Without it, it will try to query the backend (dynamic mode).

---

## Next Steps

1. **Run static evaluation on full dataset:**
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --use_static_answers --mode fhri --output results/eval_full.json
   ```

2. **Analyze results:**
   ```bash
   python -c "
   import json
   with open('results/eval_full.json') as f:
       data = json.load(f)
   print(f'Accuracy: {data[\"metrics\"][\"overall\"][\"accuracy\"]:.2%}')
   print(f'Hallucination Recall: {data[\"metrics\"][\"hallucination\"][\"recall\"]:.2%}')
   "
   ```

3. **Compare with baseline:**
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --use_static_answers --mode baseline --output results/eval_baseline.json
   ```
