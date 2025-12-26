# FHRI Scoring Problem Description

## Context
I'm building a financial chatbot with a **Finance Hallucination Reliability Index (FHRI)** system that scores answer reliability on a scale of 0-1. The FHRI is a weighted composite of 5 sub-scores:
- **G (Grounding)**: Alignment with retrieved passages and verified data (0-1)
- **N_or_D (Numerical/Directional)**: Consistency of numeric claims (0-1)
- **T (Temporal)**: Date/period alignment (0-1)
- **C (Citation)**: Presence and credibility of sources (0-1)
- **E (Entropy)**: Inverse-normalized model uncertainty (0-1)

**Formula**: `FHRI = w_G*G + w_N*N_or_D + w_T*T + w_C*C + w_E*E` (weights sum to 1.0)

## Current Problem

### Evaluation Results
- **Total samples**: 51 (41 accurate, 10 contradiction)
- **FHRI threshold**: 0.65 (for marking answers as "accurate")
- **Overall accuracy**: 19.61% (very low)
- **Accurate recall**: 14.6% (only 6/41 accurate samples detected)

### Key Issue: FHRI Scores Too Low

**For accurate samples:**
- Average FHRI: **0.525** (below 0.65 threshold)
- Only **6/41 (14.6%)** have FHRI > 0.65
- **35/41 (85.4%)** accurate samples are incorrectly marked as "hallucination"

**FHRI Distribution:**
- 0.0-0.5: ~54% of samples
- 0.5-0.65: ~18% of samples
- 0.65-0.85: ~14% of samples
- 0.85-1.0: ~14% of samples

### Sub-score Analysis (for accurate samples)

Example accurate sample that's being missed:
- **Question**: "I'm 24 with a 30-year investment horizon. Should I put 80% in a global equity ETF and 20% in a bond fund?"
- **True Label**: accurate (correct answer)
- **FHRI**: 0.591 (below 0.65 threshold)
- **Subscores**:
  - G (Grounding): 0.492
  - N_or_D (Numeric): 0.700
  - T (Temporal): 0.750
  - C (Citation): 0.350
  - E (Entropy): 0.580
- **Scenario**: Portfolio Advice (weights: G:0.35, N:0.25, T:0.10, C:0.15, E:0.15)
- **Calculated FHRI**: 0.35×0.492 + 0.25×0.700 + 0.10×0.750 + 0.15×0.350 + 0.15×0.580 = 0.591

### Scenario-Specific Weights (Currently Used)

Different question types use different weight profiles:

1. **Numeric KPI**: G:0.30, N:0.40, T:0.20, C:0.05, E:0.05
2. **Portfolio Advice**: G:0.35, N:0.25, T:0.10, C:0.15, E:0.15
3. **Regulatory**: G:0.20, N:0.05, T:0.20, C:0.40, E:0.15
4. **Multi-Ticker**: G:0.35, N:0.25, T:0.10, C:0.20, E:0.10
5. **Crypto/Blockchain**: G:0.35, N:0.15, T:0.20, C:0.20, E:0.10
6. **Default**: G:0.40, N:0.20, T:0.15, C:0.15, E:0.10

### Performance by Scenario

| Scenario | Accuracy | Avg FHRI (accurate samples) | Issue |
|----------|----------|----------------------------|-------|
| Numeric KPI | 50.0% | 0.734 | Working well |
| Regulatory | 40.0% | 0.553 | Some samples below threshold |
| Default | 33.3% | 0.287 | Very low FHRI |
| Portfolio Advice | 25.0% | 0.536 | Below threshold |
| Crypto/Blockchain | 0.0% | ~0.30 | Very low FHRI |
| Multi-Ticker | 0.0% | 0.479 | Below threshold |
| Fundamentals | 0.0% | 0.478 | Below threshold |

## Questions for ChatGPT/Gemini

1. **Why are FHRI scores so low for accurate answers?**
   - Average 0.525 when threshold is 0.65
   - Subscores seem reasonable (G:0.49, N:0.70, T:0.75, C:0.35, E:0.58)
   - But weighted combination results in low overall FHRI

2. **Are the scenario weights appropriate?**
   - Should I adjust weights for specific scenarios?
   - Are some weights too low (e.g., Citation: 0.15 for advice)?
   - Should I boost certain components?

3. **Should I modify the FHRI calculation?**
   - Add a baseline/offset?
   - Use non-linear combination (e.g., geometric mean)?
   - Apply normalization/scaling to subscores?
   - Add quality boost for certain score combinations?

4. **What threshold should I use?**
   - Current: 0.65 (only catches 14.6% of accurate samples)
   - Lower threshold (0.55-0.60) would catch more but may increase false positives
   - How to balance precision vs recall?

5. **How to improve sub-score calculation?**
   - Grounding (G) seems low (0.49) - how to improve?
   - Citation (C) is 0.35 - should this be higher for advice questions?
   - Are the sub-score algorithms too strict?

6. **Should I use different thresholds per scenario?**
   - Numeric KPI works well at 0.65
   - But Default/Crypto scenarios need much lower threshold
   - Is scenario-specific thresholding a good approach?

## Current System Behavior

- **Precision is good** (75% for accurate, 57% for contradiction)
- **Recall is very poor** (14.6% for accurate, 40% for contradiction)
- **Main issue**: FHRI scoring algorithm produces scores that are too conservative
- **Impact**: 85% of accurate answers are incorrectly flagged as unreliable

## What I Need Help With

1. **Diagnosis**: Why is FHRI so low despite reasonable subscores?
2. **Solutions**: What modifications to FHRI calculation would help?
3. **Threshold Strategy**: Should I use adaptive/scenario-specific thresholds?
4. **Sub-score Improvement**: How to boost G, C, or other components?
5. **Alternative Approaches**: Are there better ways to combine subscores?




























