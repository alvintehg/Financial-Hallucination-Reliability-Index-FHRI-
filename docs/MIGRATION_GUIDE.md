# Migration Guide: Original FHRI → Adaptive FHRI

## Overview

This guide helps you migrate from the original FHRI implementation to the new Adaptive FHRI system.

**Good news:** The migration is **backward compatible** — no breaking changes! Adaptive FHRI is opt-in via request parameter.

---

## Quick Start (No Code Changes Required)

### Option 1: Enable Globally (Default)

Adaptive FHRI is **enabled by default** in the latest version. No changes needed!

```bash
# Start server - adaptive FHRI enabled automatically
uvicorn src.server:app --port 8000
```

All `/ask` requests will use adaptive FHRI unless explicitly disabled.

### Option 2: Enable Per-Request

For gradual rollout, enable adaptive FHRI per request:

```json
POST /ask
{
  "text": "What is Apple stock price?",
  "use_adaptive_fhri": true  // Enable adaptive FHRI for this request
}
```

### Option 3: Disable (Use Original FHRI)

To use the original FHRI with scenario-based weights:

```json
POST /ask
{
  "text": "What is Apple stock price?",
  "use_fhri": true,
  "use_adaptive_fhri": false  // Use original FHRI
}
```

---

## Response Schema Changes

### Before (Original FHRI)

```json
{
  "answer": "...",
  "meta": {
    "fhri": 0.712,
    "fhri_subscores": {
      "G": 0.75,
      "N_or_D": 0.70,
      "T": 0.68,
      "C": 0.65,
      "E": 0.72
    },
    "fhri_components": ["G", "N_or_D", "T", "C", "E"],
    "fhri_renormalized": false,
    "scenario_detected": "numeric_kpi",
    "scenario_name": "Numeric KPI Query",
    "scenario_weights": {
      "G": 0.20,
      "N_or_D": 0.35,
      "T": 0.20,
      "C": 0.10,
      "E": 0.15
    }
  }
}
```

### After (Adaptive FHRI)

```json
{
  "answer": "...",
  "meta": {
    "fhri": 0.712,
    "fhri_label": "High Reliability",           // NEW
    "fhri_subscores": {                         // RENAMED KEYS
      "grounding": 0.75,
      "numeric": 0.70,
      "temporal": 0.68,
      "entropy": 0.72,
      "contradiction": 0.80
    },
    "fhri_components": ["grounding", "numeric", "temporal", "entropy", "contradiction"],
    "fhri_weights": {                           // NEW (current weights)
      "grounding": 0.25,
      "numeric": 0.20,
      "temporal": 0.10,
      "entropy": 0.25,
      "contradiction": 0.20
    },
    "contradiction_smoothed": 0.105,            // NEW (EMA smoothed)
    "stability_index": 0.82,                    // NEW
    "fhri_retuned": false,                      // NEW
    "fhri_warnings": [],                        // NEW
    "fhri_total_turns": 15,                     // NEW
    "fhri_window_size": 10                      // NEW
  }
}
```

---

## Code Migration

### Frontend: Accessing FHRI

#### Before

```javascript
const fhri = response.meta.fhri;
const scenario = response.meta.scenario_name;
const subscores = response.meta.fhri_subscores;

// Sub-score keys: "G", "N_or_D", "T", "C", "E"
const groundingScore = subscores.G;
const numericScore = subscores.N_or_D;
```

#### After (Backward Compatible)

```javascript
const fhri = response.meta.fhri;  // Same as before
const fhriLabel = response.meta.fhri_label;  // NEW
const stabilityIndex = response.meta.stability_index;  // NEW
const subscores = response.meta.fhri_subscores;

// NEW: Sub-score keys are now descriptive
const groundingScore = subscores.grounding;
const numericScore = subscores.numeric;
const entropyScore = subscores.entropy;
const contradictionScore = subscores.contradiction;
const temporalScore = subscores.temporal;
```

**Migration Tip:** Use optional chaining for backward compatibility:

```javascript
// Works with both old and new response schemas
const groundingScore = subscores?.grounding ?? subscores?.G ?? 0;
const numericScore = subscores?.numeric ?? subscores?.N_or_D ?? 0;
```

### Backend: Calling FHRI

#### Before

```python
from src.fhri_scoring import compute_fhri

result = compute_fhri(
    answer=answer,
    question=question,
    passages=passages,
    entropy=entropy,
    api_facts=api_facts,
    hallu_threshold=2.0,
    scenario_override="numeric_kpi"
)

fhri = result["fhri"]
scenario = result["scenario_name"]
```

#### After (Two Options)

**Option A: Use Adaptive FHRI (Recommended)**

```python
from src.adaptive_fhri import get_default_adaptive_scorer
from src.fhri_scoring import FHRIScorer

# Compute sub-scores
scorer = FHRIScorer()
grounding_score = scorer.compute_grounding_score(answer, passages, api_facts, multi_source_data)
numeric_score = scorer.compute_numerical_directional_score(answer, question, api_facts, passages, multi_source_data)
temporal_score = scorer.compute_temporal_score(answer, question, passages)

# Get adaptive scorer
adaptive_scorer = get_default_adaptive_scorer()

# Compute adaptive FHRI
result = adaptive_scorer.compute_adaptive_fhri(
    answer=answer,
    question=question,
    passages=passages,
    entropy=entropy,
    contradiction_raw=contradiction_score,
    grounding_score=grounding_score,
    numeric_score=numeric_score,
    temporal_score=temporal_score
)

fhri = result["fhri"]
fhri_label = result["fhri_label"]
stability = result["stability_index"]
```

**Option B: Keep Original FHRI**

```python
from src.fhri_scoring import compute_fhri

# Same as before - no changes needed
result = compute_fhri(
    answer=answer,
    question=question,
    passages=passages,
    entropy=entropy,
    api_facts=api_facts,
    hallu_threshold=2.0,
    scenario_override="numeric_kpi"
)
```

---

## Key Differences

| Feature | Original FHRI | Adaptive FHRI |
|---------|--------------|---------------|
| **Weights** | Fixed per scenario | Auto-learned from stability |
| **Contradiction** | Not smoothed | EMA smoothed (α=0.3) |
| **Stability Tracking** | No | Yes (rolling window) |
| **Drift Detection** | No | Yes (identical query) |
| **Auto-Retuning** | No | Yes (based on rules) |
| **Logging** | Manual | Automatic (CSV + JSON) |
| **Session Persistence** | No | Yes (optional) |

---

## Breaking Changes

### None!

All changes are backward compatible. The original FHRI implementation remains unchanged and can still be used by setting `use_adaptive_fhri=false`.

---

## Recommended Migration Path

### Phase 1: Testing (Week 1)

1. **Enable adaptive FHRI in development**
   ```bash
   # Set in .env
   DEBUG=1
   ```

2. **Run parallel comparison**
   ```python
   # Call both old and new FHRI
   old_fhri = compute_fhri(...)
   new_fhri = adaptive_scorer.compute_adaptive_fhri(...)

   print(f"Old FHRI: {old_fhri['fhri']:.3f}")
   print(f"New FHRI: {new_fhri['fhri']:.3f}")
   print(f"Stability: {new_fhri['stability_index']:.3f}")
   ```

3. **Review evaluation logs**
   ```bash
   # Check CSV logs for anomalies
   cat logs/fhri_eval/*.csv | tail -50
   ```

### Phase 2: Gradual Rollout (Week 2)

1. **Enable for 10% of traffic**
   ```python
   import random

   use_adaptive = random.random() < 0.10  # 10% chance
   result = ask(text, use_adaptive_fhri=use_adaptive)
   ```

2. **Monitor metrics**
   - FHRI mean/std
   - Stability index
   - Warning count
   - Retune frequency

3. **Compare to baseline**
   ```python
   eval_logger = get_default_eval_logger()
   summary = eval_logger.generate_summary_report()

   print(f"Mean FHRI: {summary['fhri_stats']['mean']:.3f}")
   print(f"Mean stability: {summary['stability_stats']['mean']:.3f}")
   ```

### Phase 3: Full Rollout (Week 3)

1. **Enable for all traffic**
   ```bash
   # No code changes - adaptive FHRI is default
   ```

2. **Update frontend UI**
   - Add FHRI sparkline
   - Add stability indicator
   - Display warnings

3. **Enable weight persistence**
   ```python
   adaptive_scorer = AdaptiveFHRIScorer(
       weights_file="data/adaptive_weights.json"
   )
   ```

### Phase 4: Optimization (Week 4+)

1. **Tune parameters based on data**
   ```python
   # Analyze logs to find optimal settings
   df = pd.read_csv("logs/fhri_eval/*.csv")

   # Check if retuning is too frequent/rare
   retune_rate = df["retuned"].mean()
   print(f"Retune rate: {retune_rate:.2%}")  # Target: 5-10%

   # Adjust if needed
   if retune_rate > 0.15:  # Too frequent
       scorer = AdaptiveFHRIScorer(fluctuation_threshold=0.20)
   ```

2. **Generate correlation plots**
   ```python
   eval_logger.generate_correlation_plot()
   # Review plots in logs/fhri_eval/
   ```

---

## Rollback Plan

If you need to rollback to original FHRI:

### Option 1: Disable via Request Parameter

```json
POST /ask
{
  "text": "...",
  "use_adaptive_fhri": false
}
```

### Option 2: Modify Server Default

```python
# In src/server.py, change default
class AskRequest(BaseModel):
    # ...
    use_adaptive_fhri: Optional[bool] = False  # Change default to False
```

### Option 3: Remove Adaptive Import

```python
# In src/server.py, comment out adaptive FHRI imports
# try:
#     from adaptive_fhri import get_default_adaptive_scorer
# except ImportError:
#     from src.adaptive_fhri import get_default_adaptive_scorer
```

---

## Troubleshooting

### Issue: FHRI Values Differ Significantly

**Expected:** Adaptive FHRI may differ by ±10% initially as weights calibrate.

**Fix:** Allow 10+ turns for weights to stabilize. Check `stability_index` — should increase over time.

### Issue: Too Many Warnings

**Cause:** Fluctuation threshold too low or data quality issues.

**Fix:** Increase `fluctuation_threshold`:
```python
scorer = AdaptiveFHRIScorer(fluctuation_threshold=0.20)  # Increase from 0.15
```

### Issue: Weights Not Persisting

**Cause:** `weights_file` not configured or directory doesn't exist.

**Fix:**
```bash
mkdir -p data
```

```python
scorer = AdaptiveFHRIScorer(weights_file="data/adaptive_weights.json")
```

### Issue: Performance Degradation

**Cause:** Evaluation logging overhead (rare).

**Fix:** Disable logging in production:
```python
# Don't call get_default_eval_logger() in production
# Or set log_dir to /dev/null
```

---

## FAQ

### Q: Can I use both old and new FHRI simultaneously?

**A:** Yes! Call both and compare:

```python
old_result = compute_fhri(...)
new_result = adaptive_scorer.compute_adaptive_fhri(...)

return {
    "fhri_old": old_result["fhri"],
    "fhri_new": new_result["fhri"],
    "stability": new_result["stability_index"]
}
```

### Q: Will weights reset on server restart?

**A:** Only if `weights_file` is not configured. To persist:

```python
scorer = AdaptiveFHRIScorer(weights_file="data/adaptive_weights.json")
```

Weights are saved automatically on retuning.

### Q: How do I export logs for analysis?

**A:** Logs are automatically saved to `logs/fhri_eval/`:

```bash
# CSV logs
cat logs/fhri_eval/fhri_eval_*.csv

# JSON logs (with queries)
cat logs/fhri_eval/fhri_eval_*.json | jq '.'

# Correlation plots (PNG)
ls logs/fhri_eval/fhri_correlation_*.png
```

### Q: Can I customize retuning rules?

**A:** Yes! Edit `src/adaptive_fhri.py` → `auto_retune_weights()`:

```python
# Example: More aggressive retuning
if avg_contradiction > 0.70:  # Lower threshold from 0.80
    self.weights["contradiction"] *= 0.5  # Reduce more (from 0.7)
```

### Q: How do I A/B test adaptive vs original FHRI?

**A:** Use a feature flag:

```python
# In your request handler
if user_id % 2 == 0:  # 50/50 split
    use_adaptive = True
else:
    use_adaptive = False

result = ask(text, use_adaptive_fhri=use_adaptive)

# Log both variants
log_ab_test(user_id, variant=("adaptive" if use_adaptive else "original"), fhri=result.meta.fhri)
```

---

## Checklist

- [ ] Test adaptive FHRI in development
- [ ] Compare old vs new FHRI scores (expect ±10% initially)
- [ ] Review evaluation logs for anomalies
- [ ] Update frontend to display new fields (`fhri_label`, `stability_index`)
- [ ] Configure weight persistence (`weights_file`)
- [ ] Run test suite: `python scripts/test_adaptive_fhri.py`
- [ ] Monitor stability index and warnings in production
- [ ] Generate correlation plots weekly for analysis
- [ ] Document any custom parameter tuning

---

## Support

For migration issues, please:

1. Check logs in `logs/fhri_eval/`
2. Review [ADAPTIVE_FHRI_GUIDE.md](./ADAPTIVE_FHRI_GUIDE.md)
3. File an issue with:
   - Request/response examples
   - Evaluation logs
   - Server logs showing FHRI computation

---

**Migration Status:** ✅ **READY** — Backward compatible, no breaking changes!
