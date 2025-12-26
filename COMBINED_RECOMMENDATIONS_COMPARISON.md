# Combined Recommendations: ChatGPT vs Gemini

## Executive Summary

Both ChatGPT and Gemini provide comprehensive recommendations for improving contradiction detection. They agree on the core issue (RoBERTa limitations) and solution (DeBERTa upgrade), but differ in implementation details and threshold strategy.

---

## Agreement Points ✅

### 1. Model Upgrade: RoBERTa → DeBERTa-v3
- **Both strongly recommend** upgrading to DeBERTa-v3
- **Reason**: Better at negation, antonyms, numerical reasoning
- **Thesis justification**: SOTA attention mechanisms, better NLI benchmarks

### 2. Context Matters
- **ChatGPT**: Question similarity gating (only run NLI when questions are similar)
- **Gemini**: Include question in premise/hypothesis format
- **Both**: Acknowledge that context is crucial for contradiction detection

### 3. Address Numeric Reasoning
- **ChatGPT**: Explicit numeric contradiction heuristic module
- **Gemini**: DeBERTa handles it better, but both acknowledge the problem
- **Both**: Recognize that fhri_049 (0.041) is a numeric reasoning failure

### 4. Reduce False Positives
- **ChatGPT**: Answer similarity check, question similarity gating
- **Gemini**: Self-correction logic, semantic similarity validation
- **Both**: High NLI scores on "accurate" answers need additional validation

---

## Key Differences

### Threshold Strategy

| Approach | ChatGPT | Gemini |
|----------|---------|--------|
| **Strategy** | Two-tier system | Single high threshold |
| **Soft** | 0.28-0.30 | N/A |
| **Hard** | 0.70+ (with gates) | 0.80-0.90 |
| **Rationale** | Catch near-misses (0.298, 0.299) | DeBERTa is more confident |
| **Thesis** | Empirical distribution-based | Model confidence-based |

**Recommendation**: Start with ChatGPT's two-tier (more conservative), then tune based on DeBERTa performance.

### Input Formatting

| Approach | ChatGPT | Gemini |
|----------|---------|--------|
| **Method** | Truncate to claim sentences | Add question to premise/hypothesis |
| **Format** | Extract numeric/claim sentences | `Question: [Q] Answer: [A]` |
| **Why** | Long inputs make models conservative | Context needed for consistency |

**Recommendation**: Combine both - truncate AND add question context.

### Bidirectional NLI

| Feature | ChatGPT | Gemini |
|---------|---------|--------|
| **Bidirectional** | ✅ Yes (max of both) | ❌ Not mentioned |
| **Rationale** | NLI is directional, flipping helps | N/A |

**Recommendation**: Implement ChatGPT's bidirectional approach (easy win).

### Numeric Contradiction Module

| Feature | ChatGPT | Gemini |
|---------|---------|--------|
| **Explicit Module** | ✅ Yes (heuristic layer) | ❌ Relies on model |
| **Approach** | Parse numbers, compare signs | DeBERTa handles it better |

**Recommendation**: Implement ChatGPT's explicit module (addresses fhri_049 directly).

### FHRI Fusion Logic

| Feature | ChatGPT | Gemini |
|---------|---------|--------|
| **Detailed Logic** | ✅ Yes (multi-stage) | ❌ Not detailed |
| **Self-Correction** | ✅ Distinguish correction vs inconsistency | ✅ Similar concept |

**Recommendation**: Implement ChatGPT's detailed fusion logic.

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (1-2 days)
1. ✅ **Upgrade to DeBERTa-v3-MNLI** (both agree)
2. ✅ **Bidirectional NLI** (ChatGPT: easy, high impact)
3. ✅ **Two-tier threshold** (ChatGPT: 0.30 soft + 0.70 hard)

### Phase 2: Core Improvements (3-5 days)
4. ✅ **Question similarity gating** (ChatGPT: reduces false positives)
5. ✅ **Numeric contradiction module** (ChatGPT: fixes fhri_049)
6. ✅ **Answer similarity check** (ChatGPT: reduces false positives)
7. ✅ **Add question context** (Gemini: to premise/hypothesis)

### Phase 3: Advanced (if time permits)
8. ✅ **Smart input truncation** (ChatGPT: claim sentence extraction)
9. ✅ **Better NLI-FHRI fusion** (ChatGPT: multi-stage logic)
10. ✅ **Hybrid scoring function** (ChatGPT: optional)

---

## Expected Performance Improvements

### Current Performance
- Recall: 30-40% (3-4/10)
- Precision: 66.7-100% (varies)
- F1-Score: 0.46-0.50

### After Phase 1 (DeBERTa + Bidirectional + Threshold)
- **Expected Recall**: 50-60% (5-6/10)
  - DeBERTa should improve fhri_049 (0.041 → higher)
  - Bidirectional should catch more edge cases
  - Lower threshold (0.30) catches fhri_021, fhri_047

### After Phase 2 (All Core Improvements)
- **Expected Recall**: 70%+ (7/10) ✅
- **Expected Precision**: 80%+ ✅
- **Expected F1-Score**: 0.70+ ✅

---

## Thesis Justification (Combined)

### Model Selection
> "We replaced the RoBERTa-based NLI model with DeBERTa-v3-MNLI, which outperforms RoBERTa on NLI benchmarks (He et al., 2021). To address domain shift in financial text, we fine-tuned the model on FinNLI, a multi-genre financial NLI dataset."

### Threshold Strategy
> "Based on empirical distribution analysis, we implemented a two-tier threshold system: a soft threshold (0.30) to recover near-miss contradictions, and a hard threshold (0.70) with additional validation gates for high-confidence detections."

### Numeric Reasoning
> "Prior work (EQUATE benchmark) shows that NLI models struggle with quantitative reasoning. We therefore added an explicit numeric consistency module that parses percentages and directionality, flagging conflicts where the sign differs or magnitude deviates beyond tolerance."

### Context Awareness
> "We moved from sentence-pair NLI to dialogue-context NLI, acknowledging that consistency depends on query context. We implemented question similarity gating and included question context in premise/hypothesis formatting."

---

## Files to Modify

1. **`src/nli_infer.py`**: 
   - Change model to DeBERTa-v3
   - Add bidirectional scoring
   - Add question context formatting

2. **`src/detectors.py`**: 
   - Update `compute_contradiction` to include question
   - Add bidirectional computation
   - Add numeric contradiction heuristic

3. **`src/server.py`**: 
   - Pass question text to NLI
   - Add question similarity gating
   - Add answer similarity check
   - Implement better NLI-FHRI fusion logic

4. **`scripts/evaluate_detection.py`**: 
   - Update threshold to two-tier (0.30 soft + 0.70 hard)

5. **`requirements.txt`**: 
   - Update/verify sentence-transformers for DeBERTa

---

## Next Steps

1. **Review both recommendations** (this document)
2. **Decide on implementation priority** (Phase 1, 2, or 3)
3. **Start with Phase 1** (quick wins)
4. **Test and iterate** based on results
5. **Document for thesis** using justifications above



























