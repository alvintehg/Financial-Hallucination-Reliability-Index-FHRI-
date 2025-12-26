# FHRI Tightening - Quick Reference Card

## 📦 What You Got

### **4 New Python Modules** (Ready to Use)
```
src/numeric_validators.py       # Numeric tolerance validation
src/entity_validators.py         # Entity grounding validation
src/nli_answer_evidence.py       # NLI answer-evidence scoring
scripts/calibrate_fhri.py        # Logistic regression calibration
```

### **Enhanced File**
```
src/fhri_scoring.py  # Fact-based grounding (lines 253-458)
```

### **3 Documentation Files**
```
FHRI_TIGHTENING_PLAN.md     # Complete technical plan + code patches
IMPLEMENTATION_GUIDE.md      # Step-by-step integration guide
SUMMARY.md                   # High-level overview
```

---

## ⚡ Quick Commands

### Test Validators
```bash
# Numeric
python -c "from src.numeric_validators import extract_numeric_claims; print(extract_numeric_claims('AAPL \$150.50, up 5.2%'))"

# Entity
python -c "from src.entity_validators import extract_entities; print(extract_entities('Apple Inc. (AAPL) announced revenue'))"
```

### Run Evaluation
```bash
# Static mode (offline)
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --use_static_answers --mode fhri

# Threshold sweep
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --sweep --sweep_range "0.3,0.5,0.7,0.9"
```

### Train Calibration
```bash
python scripts/calibrate_fhri.py --dataset data/evaluation_dataset.json --output models/fhri_calibration.pkl --metric recall
```

---

## 🎯 What's Already Integrated

✅ **Fact-Based Grounding** in `src/fhri_scoring.py`:
- Numeric claims validated against API (5-20% tolerance)
- Entity grounding checked (tickers, companies)
- **Hard cap:** G ≤ 0.2 when numerics invalid
- **Aggressive downweight** for ungrounded entities

---

## 🔧 What You Need to Add (4-6 hours)

Follow `IMPLEMENTATION_GUIDE.md` for detailed steps:

| Phase | File | What to Add | Lines | Time |
|-------|------|-------------|-------|------|
| **2** | `fhri_scoring.py` | N/D hard checks | ~476 | 30min |
| **3** | `fhri_scoring.py` | NLI integration | ~800 | 1hr |
| **4** | `fhri_scoring.py` | Scenario caps | ~805 | 30min |
| **5** | `fhri_scoring.py` | Entropy modulator | ~785 | 30min |
| **6** | `evaluate_detection.py` | Sweep/baselines | ~670 | 2hr |

**Total:** 4.5 hours coding + 1.5 hours testing = **6 hours**

---

## 📊 Numeric Tolerances

| Field | Tolerance | Example |
|-------|-----------|---------|
| Price | 5% | $150 ± $7.50 |
| % Change | 10% | 5% ± 0.5% |
| EPS | 10% | $1.50 ± $0.15 |
| P/E | 15% | 25 ± 3.75 |
| Revenue | 10% | $90B ± $9B |
| Market Cap | 10% | $2T ± $200B |

---

## 🎨 Key Algorithms

### Grounding Penalty
```python
# If any numeric invalid → G capped at 0.2
if numeric_validation["any_invalid"]:
    return 0.2

# Otherwise, apply penalty
penalty = 0.2 + (0.8 * accuracy_rate)  # 0.2-1.0
score = base_score * penalty
```

### NLI Veto
```python
# For high-risk scenarios (numeric_kpi, regulatory)
if max_contradiction >= 0.7:
    fhri = fhri * (1 - max_contradiction)  # Downscale
```

### Scenario Cap
```python
# For numeric_kpi/regulatory
if has_numeric_mismatch or not has_evidence:
    fhri = min(fhri, 0.3)  # Hard cap
```

---

## 📈 Expected Metrics

| Metric | Before | After |
|--------|--------|-------|
| Hallucination Recall | ~70% | **≥85%** |
| Hallucination Precision | ~60% | **≥75%** |
| Hallucination F1 | ~0.65 | **≥0.80** |

---

## 🚦 Integration Flow

```
User Query
    ↓
LLM Answer
    ↓
┌─────────────────────────────────────┐
│ FHRI Scoring (src/fhri_scoring.py) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Grounding (G) - FACT-BASED ✅       │
│  • Numeric validation               │
│  • Entity grounding                 │
│  • Hard cap if invalid (G ≤ 0.2)    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Numeric/Directional (N/D) 🔧        │
│  • Hard external checks (TODO)      │
│  • Only ≥0.8 if all valid           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ NLI Answer-Evidence 🔧              │
│  • Max contradiction (TODO)         │
│  • Veto if ≥0.7                     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Scenario Caps 🔧                    │
│  • numeric_kpi: ≤0.3 (TODO)         │
│  • regulatory: ≤0.3 (TODO)          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Entropy Modulator 🔧                │
│  • Low G/N/D + high E → ×0.85       │
│  • High G/N/D + high E → ×0.95      │
└─────────────────────────────────────┘
    ↓
FHRI Score (0-1)
    ↓
Threshold Check → Flag if Hallucination
```

---

## 📁 File Map

```
llm-fin-chatbot/
│
├── src/
│   ├── fhri_scoring.py              ← Main scoring logic (ENHANCED ✅)
│   ├── numeric_validators.py        ← NEW ✅
│   ├── entity_validators.py         ← NEW ✅
│   ├── nli_answer_evidence.py       ← NEW ✅
│   └── detectors.py                 ← NLI wrapper (existing)
│
├── scripts/
│   ├── evaluate_detection.py        ← TO ENHANCE 🔧
│   └── calibrate_fhri.py            ← NEW ✅
│
├── data/
│   └── evaluation_dataset.json      ← Labeled data (100 samples)
│
└── docs/
    ├── FHRI_TIGHTENING_PLAN.md      ← Technical plan ✅
    ├── IMPLEMENTATION_GUIDE.md      ← Step-by-step ✅
    ├── SUMMARY.md                   ← Overview ✅
    └── QUICK_REFERENCE.md           ← This file ✅
```

---

## 🎯 Decision Tree

**Should I cap G at 0.2?**
```
Has numeric claims?
  Yes → Any invalid? (error > tolerance)
    Yes → G = 0.2 ❌
    No → Apply fact penalty (0.2-1.0) ✅
  No → Check entity grounding
    All grounded → No penalty ✅
    Some ungrounded → Penalty (0.3-1.0) ⚠️
```

**Should I veto with NLI?**
```
High-risk scenario? (numeric_kpi, regulatory)
  Yes → Max contradiction ≥ 0.7?
    Yes → FHRI *= (1 - contradiction) ❌
    No → Soft penalty if ≥ 0.5 ⚠️
  No → Soft penalty if ≥ 0.5 ⚠️
```

**Should I cap FHRI at 0.3?**
```
Scenario = numeric_kpi OR regulatory?
  Yes → Has numeric mismatch OR no evidence?
    Yes → FHRI = min(FHRI, 0.3) ❌
    No → No cap ✅
  No → No cap ✅
```

---

## 🧪 Test Checklist

```bash
# 1. Unit tests
python -c "from src.numeric_validators import extract_numeric_claims; assert len(extract_numeric_claims('AAPL \$150')) > 0"
python -c "from src.entity_validators import extract_entities; assert len(extract_entities('AAPL')['tickers']) > 0"

# 2. Integration test
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --use_static_answers --mode fhri

# 3. Threshold sweep
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --sweep --sweep_range "0.5,0.7,0.9"

# 4. Calibration
python scripts/calibrate_fhri.py --dataset data/evaluation_dataset.json --metric recall

# 5. Check results
cat results/fhri_tightened.json | grep '"hallucination_recall"'
```

---

## 🔗 Next Steps

1. **Read:** `IMPLEMENTATION_GUIDE.md` (30 min)
2. **Implement:** Phase 2-6 (4-6 hours)
3. **Test:** Run evaluation sweep (30 min)
4. **Calibrate:** Train model (15 min)
5. **Deploy:** A/B test (1 week monitoring)

---

## 💡 Pro Tips

- **Start with Phase 2** (N/D hard checks) - easiest integration
- **Test incrementally** - run eval after each phase
- **Use static mode** for fast iteration (`--use_static_answers`)
- **Monitor logs** - validators log detailed debug info
- **Adjust tolerances** if needed - edit `NUMERIC_TOLERANCES` dict

---

## 🆘 Common Issues

**"Validators not available"**
→ Check imports in `src/fhri_scoring.py` (lines 30-43)

**"NLI detector not available"**
→ Run: `python -c "from src.detectors import get_nli_detector; print(get_nli_detector().is_available())"`

**"No samples for calibration"**
→ Run eval first: `python scripts/evaluate_detection.py --use_static_answers`

---

**Questions? → See `IMPLEMENTATION_GUIDE.md` or `FHRI_TIGHTENING_PLAN.md`**
