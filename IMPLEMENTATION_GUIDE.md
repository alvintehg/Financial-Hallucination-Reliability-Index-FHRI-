# FHRI Tightening Implementation Guide

## Quick Start

This guide provides step-by-step instructions to tighten your FHRI-based hallucination detector for the financial chatbot.

---

## ✅ What's Been Delivered

### **New Modules Created:**

1. **`src/numeric_validators.py`** ✅
   - Extracts numeric claims from text (prices, percentages, EPS, P/E, market cap, etc.)
   - Validates against reference data with configurable tolerances
   - Returns validation results with relative error calculations

2. **`src/entity_validators.py`** ✅
   - Extracts entities (tickers, companies, people, dates)
   - Validates entity grounding in passages and API data
   - Computes grounding penalties for missing entities

3. **`src/nli_answer_evidence.py`** ✅
   - NLI-based contradiction detection between answer and evidence passages
   - Veto mechanism for high-risk scenarios
   - Returns max/avg entailment and contradiction scores

4. **`scripts/calibrate_fhri.py`** ✅
   - Logistic regression calibration script
   - Trains on labeled data with FHRI subscores as features
   - Outputs optimal threshold for hallucination detection

### **Enhanced Files:**

5. **`src/fhri_scoring.py`** ✅ (Partially)
   - **Added:** Imports for validators (lines 30-43)
   - **Enhanced:** `compute_grounding_score` with fact-based validation (lines 253-458)
     - Hard cap (G ≤ 0.2) when numeric claims invalid
     - Entity-based grounding with penalties
     - Fact penalty applied to all scoring paths

### **Documentation:**

6. **`FHRI_TIGHTENING_PLAN.md`** ✅
   - Comprehensive plan with all objectives
   - Detailed code patches for remaining work
   - Testing & validation procedures

7. **`IMPLEMENTATION_GUIDE.md`** ✅ (This file)
   - Quick start guide
   - Step-by-step integration instructions

---

## 🔧 Implementation Steps

### **Phase 1: Fact-Based Grounding** ✅ COMPLETED

**Status:** Already integrated into `src/fhri_scoring.py`

**What it does:**
- For numeric claims: validates against API data within tolerance (5-20% depending on field)
- For non-numeric: checks that entities appear in passages/API
- **Hard cap:** If any numeric claim is invalid → G capped at 0.2
- **Aggressive downweighting:** If entities ungrounded → G penalty

**Test:**
```bash
python -c "from src.numeric_validators import extract_numeric_claims; print(extract_numeric_claims('AAPL price is \$150.50, up 5.2%'))"
```

---

### **Phase 2: Enhanced N/D Score with Hard Checks** 🔧 TODO

**File:** `src/fhri_scoring.py`
**Location:** `compute_numerical_directional_score` method (~line 460)

**Add this code after line 476:**

```python
# HARD EXTERNAL CHECKS: Numeric validation
if multi_source_data and validate_all_numeric_claims:
    # Build reference data
    reference_data = {}
    finnhub_data = multi_source_data.get("finnhub_quote") or {}
    reference_data["price"] = finnhub_data.get("c") or finnhub_data.get("price")
    reference_data["pct_change"] = finnhub_data.get("dp")

    fundamentals = multi_source_data.get("fundamentals", {}).get("data", {}).get("metrics", {})
    reference_data.update(fundamentals)

    # Validate all numeric claims
    numeric_validation = validate_all_numeric_claims(answer, reference_data, require_all_valid=False)

    if numeric_validation["has_numeric_claims"]:
        accuracy_rate = numeric_validation["accuracy_rate"]

        # Hard check: If error > tolerance, set N/D ~0.1-0.2
        if numeric_validation["any_invalid"]:
            score = 0.15
            logger.warning(f"Numeric mismatch in N/D: {numeric_validation['invalid_claims']}/{numeric_validation['validated_claims']}")
            return score

        # Only ≥0.8 when ALL numerics within tolerance
        if accuracy_rate >= 0.9:
            score = 0.88
            logger.info(f"All numeric claims validated")
            return score
```

**What it does:**
- Computes relative error vs API/ground truth
- If error > tolerance → N/D ~0.1-0.2
- Only assigns ≥0.8 when all key numerics within tolerance

---

### **Phase 3: NLI Answer-vs-Evidence Integration** 🔧 TODO

**File:** `src/fhri_scoring.py`
**Location:** Top of file (imports)

**Add import:**
```python
try:
    from nli_answer_evidence import compute_answer_evidence_nli, apply_nli_veto
except ImportError:
    try:
        from src.nli_answer_evidence import compute_answer_evidence_nli, apply_nli_veto
    except ImportError:
        logger.warning("NLI answer-evidence module not available")
        compute_answer_evidence_nli = None
        apply_nli_veto = None
```

**File:** `src/fhri_scoring.py`
**Location:** `compute_fhri` method (~line 800, after computing base FHRI)

**Add this code:**

```python
# NLI answer-vs-evidence check
if compute_answer_evidence_nli and passages:
    try:
        from detectors import get_nli_detector
        nli_detector = get_nli_detector()

        nli_answer_evidence_result = compute_answer_evidence_nli(
            answer=answer,
            passages=passages,
            nli_detector=nli_detector,
            timeout=5.0
        )

        logger.info(f"NLI answer-evidence: max_entailment={nli_answer_evidence_result['max_entailment']:.3f}, max_contradiction={nli_answer_evidence_result['max_contradiction']:.3f}")

        # Apply veto for high-risk scenarios
        if apply_nli_veto:
            fhri, vetoed, reason = apply_nli_veto(
                fhri=fhri,
                nli_result=nli_answer_evidence_result,
                scenario=scenario_key,
                veto_threshold=0.7,
                high_risk_scenarios=HIGH_RISK_SCENARIOS
            )

            if vetoed:
                logger.warning(f"FHRI adjusted by NLI veto: {reason}")

    except Exception as e:
        logger.exception(f"NLI answer-evidence check failed: {e}")
```

**What it does:**
- Uses NLI with passages as premise, answer as hypothesis
- Takes max entailment and max contradiction across passages
- For high-risk (numeric_kpi, regulatory): veto or downscale FHRI when contradiction ≥0.7
- Multiplies FHRI by (1 - contradiction) for veto

---

### **Phase 4: Scenario-Specific Caps** 🔧 TODO

**File:** `src/fhri_scoring.py`
**Location:** `compute_fhri` method (~line 805, after NLI check, before boosts)

**Add this code:**

```python
# SCENARIO-SPECIFIC CAPS
if scenario_key in ("numeric_kpi", "regulatory"):
    # Check numeric mismatch
    has_numeric_mismatch = False
    if multi_source_data and validate_all_numeric_claims:
        reference_data = {}
        finnhub_data = multi_source_data.get("finnhub_quote") or {}
        reference_data["price"] = finnhub_data.get("c") or finnhub_data.get("price")
        reference_data["pct_change"] = finnhub_data.get("dp")
        fundamentals = multi_source_data.get("fundamentals", {}).get("data", {}).get("metrics", {})
        reference_data.update(fundamentals)

        numeric_validation = validate_all_numeric_claims(answer, reference_data, require_all_valid=False)
        has_numeric_mismatch = numeric_validation.get("any_invalid", False)

    # Check evidence
    has_evidence = bool(passages or (multi_source_data and multi_source_data.get("sources_used")))

    # Apply cap
    if has_numeric_mismatch or not has_evidence:
        logger.warning(f"Scenario cap for {scenario_key}: numeric_mismatch={has_numeric_mismatch}, has_evidence={has_evidence}")
        fhri = min(fhri, 0.3)
```

**What it does:**
- For numeric_kpi/regulatory: caps FHRI (≤0.3) when numeric_mismatch > threshold or no evidence
- Looser thresholds for low-risk (definition/education)

---

### **Phase 5: Entropy Modulator** 🔧 TODO

**File:** `src/fhri_scoring.py`
**Location:** `compute_fhri` method (~line 785, replace existing entropy handling)

**Replace with:**

```python
# ENTROPY AS MODULATOR
if E_val is not None:
    G_val = subscores.get("G", 0.0)
    N_val = subscores.get("N_or_D", 0.0)
    gn_avg = (G_val + N_val) / 2.0 if (G_val is not None and N_val is not None) else 0.5

    if gn_avg < 0.4 and E_val < 0.4:
        # Low G/N/D + High entropy → push down
        entropy_penalty = 0.85
        fhri = fhri * entropy_penalty
        logger.info(f"Entropy modulator (low G/N/D + high entropy): FHRI *= {entropy_penalty:.2f}")

    elif gn_avg > 0.7 and E_val < 0.6:
        # High G/N/D but moderate entropy → shave slightly
        entropy_penalty = 0.95
        fhri = fhri * entropy_penalty
        logger.info(f"Entropy modulator (high G/N/D + moderate entropy): FHRI *= {entropy_penalty:.2f}")
```

**What it does:**
- If G/N/D low and entropy high → push FHRI down further
- If G/N/D high but entropy high → shave FHRI slightly
- Uses entropy as modulator, not primary signal

---

### **Phase 6: Evaluation Sweep** 🔧 TODO

**File:** `scripts/evaluate_detection.py`
**Location:** After `args = parser.parse_args()` (~line 670)

**See `FHRI_TIGHTENING_PLAN.md` section "Evaluation Sweep Enhancements" for full code.**

**Key additions:**
- `--sweep` flag for threshold sweep
- `--per_scenario` for scenario breakdown
- `--compare_baselines` for baseline comparisons

**Usage:**
```bash
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --sweep \
  --sweep_range "0.3,0.4,0.5,0.6,0.7,0.8,0.9" \
  --per_scenario \
  --compare_baselines
```

---

## 🧪 Testing

### 1. Unit Tests

```bash
# Test numeric validators
python -c "
from src.numeric_validators import extract_numeric_claims, validate_numeric_claim
claims = extract_numeric_claims('AAPL price \$150.50, up 5.2%, EPS \$1.46')
print(f'Found {len(claims)} claims:', claims)
"

# Test entity validators
python -c "
from src.entity_validators import extract_entities
entities = extract_entities('Apple Inc. (AAPL) announced Q3 revenue of \$90B')
print('Entities:', entities)
"
```

### 2. Integration Test

```bash
# Run evaluation with static answers
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --mode fhri \
  --use_static_answers \
  --output results/fhri_tightened.json
```

### 3. Threshold Sweep

```bash
# Find optimal threshold
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --sweep \
  --sweep_range "0.3,0.5,0.7,0.9" \
  --per_scenario
```

### 4. Calibration

```bash
# Train calibration model
python scripts/calibrate_fhri.py \
  --dataset data/evaluation_dataset.json \
  --output models/fhri_calibration.pkl \
  --metric recall
```

---

## 📊 Expected Results

| Metric | Before | After |
|--------|--------|-------|
| **Hallucination Recall** | ~70% | **≥85%** |
| **Hallucination Precision** | ~60% | **≥75%** |
| **Numeric False Positives** | High | **Low** |
| **Grounding Quality** | Similarity-based | **Fact-based** |

---

## 🔍 Numeric Tolerances Reference

| Field Type | Tolerance | Example |
|-----------|-----------|---------|
| Price | 5% | $150 ± $7.50 |
| % Change | 10% | 5% ± 0.5% |
| Returns | 15% | 10% ± 1.5% |
| EPS | 10% | $1.50 ± $0.15 |
| Revenue | 10% | $90B ± $9B |
| Market Cap | 10% | $2T ± $200B |
| P/E Ratio | 15% | 25 ± 3.75 |
| Dividend Yield | 20% | 2% ± 0.4% |
| **Default** | 10% | — |

---

## 🚀 Deployment Checklist

- [ ] Phase 1: Fact-based grounding ✅ (Already integrated)
- [ ] Phase 2: Enhanced N/D score (Add code to `compute_numerical_directional_score`)
- [ ] Phase 3: NLI answer-evidence (Add NLI integration to `compute_fhri`)
- [ ] Phase 4: Scenario caps (Add caps before boosts in `compute_fhri`)
- [ ] Phase 5: Entropy modulator (Replace entropy handling in `compute_fhri`)
- [ ] Phase 6: Evaluation sweep (Enhance `evaluate_detection.py`)
- [ ] Run full evaluation sweep
- [ ] Train calibration model
- [ ] A/B test in production
- [ ] Monitor hallucination recall/precision

---

## 📝 Next Steps

1. **Review completed code:**
   - `src/numeric_validators.py` ✅
   - `src/entity_validators.py` ✅
   - `src/nli_answer_evidence.py` ✅
   - `scripts/calibrate_fhri.py` ✅
   - Enhanced `src/fhri_scoring.py` (grounding) ✅

2. **Implement remaining TODOs:**
   - Follow Phase 2-6 instructions above
   - Test each phase incrementally

3. **Run evaluation:**
   - Baseline: `python scripts/evaluate_detection.py --mode baseline`
   - FHRI: `python scripts/evaluate_detection.py --mode fhri`
   - Sweep: `python scripts/evaluate_detection.py --sweep`

4. **Calibrate:**
   - `python scripts/calibrate_fhri.py --metric recall`

5. **Deploy:**
   - Update `src/server.py` to use calibrated model
   - A/B test with 10% traffic
   - Monitor metrics for 1 week

---

## 🆘 Troubleshooting

### Issue: "Validators not available"
**Solution:** Check imports in `src/fhri_scoring.py`. Ensure `numeric_validators.py` and `entity_validators.py` are in `src/` directory.

### Issue: "NLI detector not available"
**Solution:**
```bash
python -c "from src.detectors import get_nli_detector; nli = get_nli_detector(); print(nli.is_available())"
```

### Issue: Calibration fails with "No samples"
**Solution:** Dataset needs FHRI subscores computed first. Run:
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --use_static_answers --mode fhri
```

---

## 📖 Additional Resources

- **Full implementation plan:** See `FHRI_TIGHTENING_PLAN.md`
- **Codebase files:**
  - `src/fhri_scoring.py` - Main FHRI logic
  - `src/detectors.py` - NLI/entropy detectors
  - `src/server.py` - API server with FHRI integration
  - `scripts/evaluate_detection.py` - Evaluation script

---

**Questions?** Refer to `FHRI_TIGHTENING_PLAN.md` for detailed code patches and rationale.
