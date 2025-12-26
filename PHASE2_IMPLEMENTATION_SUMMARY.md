# Phase 2 Implementation Summary

## ✅ All Phase 2 Features Completed

### 1. Question Similarity Gating ✅
- **File**: `src/nli_utils.py`, `src/server.py`
- **Status**: Implemented
- **Details**:
  - Only runs NLI if questions are semantically similar (threshold: 0.7) OR have entity overlap
  - Uses sentence-transformers for semantic similarity
  - Checks entity overlap (tickers, financial terms, time references)
  - Prevents false positives from unrelated questions

**Key Functions**:
- `should_run_nli_contradiction_check()`: Determines if NLI should run based on question similarity
- `check_entity_overlap()`: Checks if questions reference same entities
- `compute_semantic_similarity()`: Computes cosine similarity between questions

### 2. Numeric Contradiction Heuristic ✅
- **File**: `src/nli_utils.py`, `src/server.py`
- **Status**: Implemented
- **Details**:
  - Detects numeric contradictions by parsing percentages and directionality
  - Overrides low NLI scores (< 0.5) if numeric contradiction detected
  - Boosts score to at least 0.6 when numeric contradiction found
  - Handles growth vs shrink, percentage differences

**Key Functions**:
- `detect_numeric_contradiction()`: Parses numeric claims and detects contradictions
- Checks for sign differences (growth vs shrink)
- Checks for magnitude differences (>50% difference)

### 3. Answer Similarity Check ✅
- **File**: `src/nli_utils.py`, `src/server.py`
- **Status**: Implemented
- **Details**:
  - Suppresses high NLI scores (>0.8) if answer similarity is very high (>0.9)
  - Prevents false positives when answers are semantically similar
  - Reduces score to 30% of original when suppressed

**Key Functions**:
- `check_answer_similarity_contradiction()`: Checks if high NLI should be suppressed
- Uses semantic similarity to detect false positives

### 4. Question Context Formatting ✅
- **File**: `src/nli_infer.py` (already implemented in Phase 1)
- **Status**: Already completed
- **Details**:
  - Question is included in premise/hypothesis format
  - Format: `"Question: {question} Answer: {answer}"`
  - Applied in both directions for bidirectional NLI

---

## Files Modified

1. **`src/nli_utils.py`** (NEW):
   - Question similarity gating
   - Numeric contradiction detection
   - Answer similarity checking
   - Entity overlap detection

2. **`src/server.py`**:
   - Added `prev_question` to `AskRequest` model
   - Integrated Phase 2 features into NLI computation
   - Added numeric contradiction override
   - Added answer similarity suppression

3. **`scripts/evaluate_detection.py`**:
   - Added `prev_question` parameter tracking
   - Updated `pair_data` to store (sample_id, question, answer, true_label)
   - Passes `prev_question` to backend for similarity gating

---

## Integration Flow

```
1. Evaluation script tracks previous question + answer for contradiction pairs
   ↓
2. Passes prev_question to backend via AskRequest
   ↓
3. Server checks question similarity (Phase 2.1)
   - If similarity < 0.7 AND no entity overlap → Skip NLI
   - Otherwise → Run NLI
   ↓
4. Run bidirectional NLI with question context (Phase 1)
   ↓
5. Apply numeric contradiction heuristic (Phase 2.2)
   - If numeric contradiction detected AND NLI < 0.5 → Boost to 0.6
   ↓
6. Apply answer similarity check (Phase 2.3)
   - If NLI > 0.8 AND answer similarity > 0.9 → Suppress (reduce to 30%)
   ↓
7. Return final contradiction score
```

---

## Expected Improvements

### Before Phase 2:
- False positives from unrelated questions
- Missed numeric contradictions (e.g., "grew 2%" vs "shrank 10%")
- False positives from semantically similar answers

### After Phase 2:
- **Reduced false positives**: Question similarity gating filters unrelated questions
- **Better numeric detection**: Heuristic catches contradictions NLI might miss
- **Fewer false positives**: Answer similarity suppresses high scores for similar answers
- **Expected recall**: 60-70% (up from 50-60%)
- **Expected precision**: 80-85% (up from 75%)

---

## Testing

To test Phase 2 features:

```bash
# 1. Restart backend
uvicorn src.server:app --reload --port 8000

# 2. Run evaluation
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_phase2.json

# 3. Check results for:
#    - Question similarity metadata
#    - Numeric contradiction detections
#    - Answer similarity suppressions
```

---

## Configuration

### Thresholds (configurable in `src/nli_utils.py`):
- **Question similarity threshold**: 0.7 (default)
- **Answer similarity threshold**: 0.9 (default)
- **NLI threshold for answer check**: 0.8 (default)
- **Numeric boost threshold**: 0.5 (NLI score below this gets boosted if numeric contradiction detected)

---

## Notes

1. **Question Similarity**: Currently only works if `prev_question` is provided. In production, this would come from conversation history.

2. **Numeric Heuristic**: Simple pattern matching. Could be enhanced with more sophisticated NLP.

3. **Answer Similarity**: Uses sentence-transformers model (same as question similarity). First run will download model.

4. **Backward Compatibility**: All Phase 2 features are optional and gracefully degrade if `nli_utils` is not available.



























