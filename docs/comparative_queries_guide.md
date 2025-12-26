# Quick Reference: Comparative Query Handling

## How It Works

### 1. Automatic Detection

The system automatically detects comparative queries:

```python
from src.scenario_detection import detect_comparative_intent

# Comparative queries
detect_comparative_intent("Compare AAPL vs MSFT")  # → True
detect_comparative_intent("Which is better, TSLA or RIVN?")  # → True
detect_comparative_intent("CRWV vs NBIS performance")  # → True

# Non-comparative queries
detect_comparative_intent("What is AAPL's price?")  # → False
detect_comparative_intent("How did the market perform?")  # → False
```

---

### 2. Contradiction Adjustment

When comparative intent is detected, the system applies intelligent contradiction reduction:

#### Scenario A: Directional Contrast (Strongest Reduction)
```
Query: "Compare AAPL vs MSFT"
Answer: "AAPL is up 5% while MSFT is down 2%"

Raw Contradiction: 0.95
Adjusted Contradiction: 0.29 (70% reduction)
Reason: Opposite directions are normal in comparisons
```

#### Scenario B: Comparative Query (Moderate Reduction)
```
Query: "Compare AAPL vs MSFT P/E ratios"
Answer: "AAPL has P/E of 25, MSFT has P/E of 30"

Raw Contradiction: 0.80
Adjusted Contradiction: 0.40 (50% reduction)
Reason: Comparative intent detected
```

#### Scenario C: Low Query Similarity (Automatic Reduction)
```
Previous Query: "What is AAPL's price?"
Current Query: "Tell me about TSLA fundamentals"

Similarity: 0.35 (< 0.75 threshold)
Contradiction Reduction: 50%
Reason: Different contexts, different focus
```

---

### 3. FHRI Recalibration

The system dynamically adjusts weights for grounded but divergent answers:

#### Example: High Grounding + High Contradiction
```python
result = scorer.compute_adaptive_fhri(
    question="How is Tesla doing?",
    answer="Tesla has strong fundamentals and growth prospects",
    passages=["Tesla reported Q3 earnings with mixed results"],
    contradiction_raw=0.85,  # High contradiction
    grounding_score=0.75     # But well grounded
)

# Automatic adjustments:
# - Contradiction weight: 0.20 → 0.10 (50% reduction)
# - FHRI: Remains high (~0.70) despite contradiction
# - Warning: "Reduced contradiction weight (grounded but divergent)"
```

---

### 4. EMA Smoothing

Contradiction scores are smoothed over the last 3 turns using Exponential Moving Average (α=0.6):

```
Turn 1: Raw = 0.9, Smoothed = 0.9
Turn 2: Raw = 0.8, Smoothed = 0.6*0.8 + 0.4*0.9 = 0.84
Turn 3: Raw = 0.7, Smoothed = 0.6*0.7 + 0.4*0.84 = 0.756

Result: Prevents sudden spikes from causing false alarms
```

---

### 5. Label Smoothing

FHRI labels use smoothed thresholds to prevent tier jumping:

```
FHRI = 0.640  → Label: "High" (not "Moderate")
FHRI = 0.650  → Label: "High"
FHRI = 0.620  → Label: "High" (smoothing prevents drop to "Moderate")

FHRI = 0.380  → Label: "Moderate" (not "Low")
FHRI = 0.370  → Label: "Low" (but close to boundary)
```

---

## API Usage

### Basic Usage

```python
from src.adaptive_fhri import get_default_adaptive_scorer
from src.scenario_detection import detect_comparative_intent

scorer = get_default_adaptive_scorer()

# Detect comparative intent
question = "Compare CRWV vs NBIS"
is_comparative = detect_comparative_intent(question)

# Compute FHRI
result = scorer.compute_adaptive_fhri(
    answer="CRWV is outperforming with 8% gains, while NBIS is down 2%",
    question=question,
    passages=["Market data shows mixed tech sector performance"],
    contradiction_raw=0.92,
    grounding_score=0.75,
    numeric_score=0.85,
    temporal_score=0.80,
    comparative_intent=is_comparative
)

print(result)
```

### Output Format

```json
{
  "fhri": 0.672,
  "fhri_label": "High",
  "fhri_weights": {
    "entropy": 0.167,
    "contradiction": 0.133,
    "grounding": 0.333,
    "numeric": 0.267,
    "temporal": 0.100
  },
  "contradiction_raw": 0.920,
  "contradiction_smoothed": 0.460,
  "comparative_intent": true,
  "query_similarity": 0.85,
  "stability_index": 0.892,
  "warnings": [],
  "contradiction_metadata": {
    "raw": 0.920,
    "smoothed": 0.460,
    "skip_penalty": true,
    "skip_reason": "comparative_intent_detected"
  }
}
```

---

## Integration Points

### In Your RAG Pipeline

```python
# Step 1: Detect scenario (includes comparative detection)
from src.scenario_detection import detect_scenario, detect_comparative_intent

scenario_id, scenario_name, weights = detect_scenario(user_query)
is_comparative = detect_comparative_intent(user_query)

# Step 2: Generate answer with LLM
answer = llm.generate(user_query, context=retrieved_passages)

# Step 3: Compute NLI contradiction with comparative awareness
from src.nli_infer import load_model, contradiction_score_comparative

tokenizer, model = load_model()
contradiction_raw, probs, metadata = contradiction_score_comparative(
    premise=previous_answer,
    hypothesis=answer,
    tokenizer=tokenizer,
    model=model,
    query=user_query,
    comparative_intent=is_comparative
)

# Step 4: Compute FHRI
from src.adaptive_fhri import get_default_adaptive_scorer

scorer = get_default_adaptive_scorer()
fhri_result = scorer.compute_adaptive_fhri(
    answer=answer,
    question=user_query,
    passages=retrieved_passages,
    contradiction_raw=contradiction_raw,
    grounding_score=grounding,  # From your grounding computation
    numeric_score=numeric,      # From your numeric verification
    temporal_score=temporal,    # From your temporal analysis
    comparative_intent=is_comparative
)

# Step 5: Use FHRI for decision making
if fhri_result['fhri'] < 0.4:
    # Low reliability - add disclaimer or request clarification
    response = f"{answer}\n\n⚠️ Low confidence ({fhri_result['fhri_label']})"
else:
    response = answer
```

---

## Best Practices

### 1. Always Detect Comparative Intent
```python
# ✅ Good
is_comparative = detect_comparative_intent(query)
result = scorer.compute_adaptive_fhri(..., comparative_intent=is_comparative)

# ❌ Bad
result = scorer.compute_adaptive_fhri(...)  # Misses comparative detection
```

### 2. Pass Query Context to NLI
```python
# ✅ Good - Query context enables comparative detection
contradiction, probs, meta = contradiction_score_comparative(
    premise=prev_answer,
    hypothesis=current_answer,
    query=user_query,
    tokenizer=tokenizer,
    model=model
)

# ❌ Bad - No query context, misses comparative signals
contradiction, probs = contradiction_score(premise, hypothesis, tokenizer, model)
```

### 3. Monitor Warnings
```python
result = scorer.compute_adaptive_fhri(...)

if result['warnings']:
    for warning in result['warnings']:
        logger.info(f"FHRI Warning: {warning}")
```

### 4. Use Both Raw and Smoothed Scores
```python
# For debugging/logging
print(f"Raw: {result['contradiction_raw']}")
print(f"Smoothed: {result['contradiction_smoothed']}")

# For decision making, use smoothed
if result['contradiction_smoothed'] > 0.8:
    # High contradiction even after smoothing
    pass
```

---

## Troubleshooting

### Issue: High contradiction despite comparative query

**Check**:
1. Is `comparative_intent=True` being passed?
2. Check `contradiction_metadata` for adjustment details
3. Verify directional contrast detection working

**Debug**:
```python
result = scorer.compute_adaptive_fhri(..., comparative_intent=True)
print(result['contradiction_metadata'])
# Expected: 'skip_penalty': True, 'skip_reason': 'comparative_intent_detected'
```

---

### Issue: FHRI jumping between tiers

**Cause**: Borderline FHRI values near tier boundaries

**Solution**: Label smoothing is already applied. If still occurring:
1. Check `stability_index` - should be > 0.7
2. Review `warnings` for drift detection
3. Consider increasing smoothing range (currently ±0.025)

---

### Issue: Semantic similarity not working

**Check**:
1. Is `sentence-transformers` installed?
   ```bash
   pip install sentence-transformers
   ```
2. Check logs for loading errors
3. If model fails to load, system will gracefully degrade

**Verify**:
```python
from src.adaptive_fhri import compute_semantic_similarity

sim = compute_semantic_similarity("text1", "text2")
if sim is None:
    print("Model not available - check installation")
```

---

## Performance Tips

### 1. Reuse Scorer Instance
```python
# ✅ Good - Reuse scorer across requests
scorer = get_default_adaptive_scorer()
for query in queries:
    result = scorer.compute_adaptive_fhri(...)

# ❌ Bad - Creates new instance each time
for query in queries:
    scorer = AdaptiveFHRIScorer()
    result = scorer.compute_adaptive_fhri(...)
```

### 2. Lazy Loading
All models (NLI, sentence-transformers) are lazy-loaded on first use. First query may be slower.

### 3. GPU Acceleration
```python
# NLI model automatically uses GPU if available
import torch
print(f"Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
```

---

## Testing

Run comprehensive test suite:

```bash
cd "c:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
python scripts/test_comparative_fhri.py
```

Expected output:
- ✓ All comparative queries detected
- ✓ Directional contrasts identified
- ✓ Contradiction reduction applied
- ✓ Label smoothing working
- ✓ FHRI in expected ranges

---

## Support

For issues or questions:
1. Check logs for detailed debugging info
2. Review `COMPARATIVE_FHRI_UPDATE.md` for implementation details
3. Run test suite to verify functionality
4. Check model availability (NLI, sentence-transformers)
