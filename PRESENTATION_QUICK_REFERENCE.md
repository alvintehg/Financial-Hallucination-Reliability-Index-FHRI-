# Quick Reference: Evaluation Results for Supervisor Presentation

## 📊 Performance Summary Table

| Configuration | Accuracy | Macro F1 | Hallucination Recall | Contradiction Recall | Best For |
|--------------|----------|----------|---------------------|---------------------|----------|
| **Baseline** | **74%** | 0.6194 | 3.85% (1/26) | 94.12% (16/17) | High accuracy, low safety |
| **Strict FHRI** | 60% | 0.6201 | 23.08% (6/26) | 94.12% (16/17) | Maximum safety |
| **Moderate FHRI** | 60% | 0.6266 | 23.08% (6/26) | **100%** (17/17) | Balanced |
| **Numeric Check** ⭐ | **64%** | **0.6391** | 19.23% (5/26) | **100%** (17/17) | **RECOMMENDED** |

⭐ **Recommended Configuration**

---

## 🎯 Key Achievements

### ✅ Contradiction Detection: PERFECT
- **100% recall** (17/17 contradictions caught)
- **100% precision** (zero false positives)
- **F1-Score: 1.0**

### ✅ Hallucination Detection: 5x Improvement
- **Baseline:** 3.85% recall (1/26) → **Phase 4:** 19.23% recall (5/26)
- **5x improvement** in catching hallucinations
- Trade-off: Accuracy 74% → 64% (acceptable for safety-critical domain)

### ✅ Overall Balance: Best in Phase 4
- **Highest Macro F1:** 0.6391
- **Recovered Accuracy:** 64% (vs 60% in strict phases)
- **Better Precision:** Fewer false hallucinations

---

## 📈 Evolution Timeline

```
Phase 1 (Baseline)
├─ Accuracy: 74% ✅
├─ Hallucination Recall: 3.85% ❌
└─ Contradiction Recall: 94.12%

    ↓ (Stricter thresholds)

Phase 2 (Strict FHRI)
├─ Accuracy: 60% ⚠️
├─ Hallucination Recall: 23.08% ✅ (6x improvement!)
└─ Contradiction Recall: 94.12%

    ↓ (Moderate thresholds + perfect contradiction)

Phase 3 (Moderate FHRI)
├─ Accuracy: 60% ⚠️
├─ Hallucination Recall: 23.08% ✅
└─ Contradiction Recall: 100% ✅✅✅

    ↓ (Add numeric price check)

Phase 4 (Numeric Check) ⭐ RECOMMENDED
├─ Accuracy: 64% ✅ (recovered!)
├─ Hallucination Recall: 19.23% ✅
├─ Contradiction Recall: 100% ✅✅✅
└─ Macro F1: 0.6391 ✅ (best overall)
```

---

## 🔍 Per-Class Performance (Phase 4 - Best)

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| **Hallucination** | 0.25 | 0.19 | 0.22 | 26 |
| **Accurate** | **0.67** | **0.74** | **0.70** | 57 |
| **Contradiction** | **1.00** | **1.00** | **1.00** | 17 |

---

## 💡 Key Insights for Discussion

### 1. **Trade-off Analysis**
- **Sacrificed:** 10 percentage points in overall accuracy (74% → 64%)
- **Gained:** 5x improvement in hallucination detection (3.85% → 19.23%)
- **Verdict:** ✅ **Acceptable trade-off** for finance domain (safety > convenience)

### 2. **Contradiction Detection Success**
- Achieved **perfect detection** (100% recall, 100% precision)
- This is a major win - all contradictions correctly identified

### 3. **Hallucination Detection Challenge**
- Still only catching ~20% of hallucinations
- Remaining 80% have very high FHRI scores (0.95-1.0)
- **Solution:** Need explicit numeric/rule checks (Phase 4 started this)

### 4. **Scenario-Aware Thresholds**
- Different thresholds for different query types:
  - Numeric KPI: 0.80 threshold, 0.85 high-risk floor
  - Regulatory: 0.75 threshold
  - Fundamentals: 0.70 threshold
- This allows **fine-tuned detection** per query type

---

## 🚀 Next Steps (Future Work)

1. **Expand Numeric Checks:**
   - Currently: Only price comparison (10% tolerance)
   - Future: Add P/E ratio, market cap, dividend yield, revenue checks

2. **Rule-Based Fact Verification:**
   - Market holidays (e.g., "open on Christmas?" → No)
   - Dow membership (e.g., "Is Google in Dow?" → No)
   - Legal facts (e.g., "Are buybacks illegal?" → No)

3. **Threshold Optimization:**
   - Fine-tune scenario thresholds on larger dataset
   - A/B test different tolerance levels for numeric checks

---

## 📝 Talking Points for Supervisor

### Opening Statement:
"We've successfully improved hallucination detection recall from 3.85% to 19-23% (5-6x improvement) while achieving perfect contradiction detection (100% recall/precision). The trade-off is a 10-point decrease in overall accuracy (74% → 64%), which is acceptable for safety-critical finance applications."

### Key Achievements:
1. **Perfect Contradiction Detection** - All 17 contradictions correctly identified
2. **5x Hallucination Improvement** - From 1/26 to 5-6/26 hallucinations caught
3. **Best Overall Balance** - Phase 4 achieves highest macro F1 (0.6391) and recovered accuracy

### Technical Innovation:
- Scenario-aware FHRI thresholds (different rules for different query types)
- High-risk floor for critical numeric questions
- Numeric price comparison against realtime API data
- Two-tier contradiction detection (soft/hard thresholds)

### Future Work:
- Expand numeric checks to more metrics (P/E, market cap, revenue)
- Add rule-based fact verification for binary questions
- Fine-tune thresholds on larger dataset

---

**Quick Stats:**
- **Dataset:** 100 samples (57 accurate, 26 hallucination, 17 contradiction)
- **Evaluation Period:** December 2, 2025
- **Best Configuration:** Phase 4 (Numeric Check)
- **Key Metric:** Macro F1 = 0.6391 (highest)


























