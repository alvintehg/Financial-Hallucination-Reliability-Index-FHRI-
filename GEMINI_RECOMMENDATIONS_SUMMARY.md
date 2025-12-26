# Gemini's Recommendations Summary

## Key Recommendations from Gemini

### 1. **Critical Fix: Upgrade Model (RoBERTa → DeBERTa-v3)**

**Current Model**: RoBERTa (2019) - outdated for NLI tasks
**Recommended Model**: `cross-encoder/nli-deberta-v3-base` (or large if latency allows)

**Why:**
- RoBERTa treats numerical divergence (e.g., "grew 2%" vs "shrank 10%") as "Neutral" rather than "Contradiction"
- DeBERTa uses disentangled attention, better at handling:
  - Negation
  - Antonyms
  - Numerical reasoning
  - Better understanding of "bag-of-words" bias

**Thesis Justification**: Demonstrates awareness of SOTA attention mechanisms (disentangled attention) crucial for financial precision.

---

### 2. **Critical Fix: Contextualize Input**

**Current Approach**: Comparing `prev_answer` vs `current_answer` (strips context)

**Problem Example:**
- User: "Is ETH Proof of Work?" → Bot: "Yes."
- User: "Is ETH Proof of Stake?" → Bot: "Yes."
- NLI Input: "Yes." vs "Yes." → Entailment (No contradiction detected)
- **Reality**: Bot claimed ETH is both PoW and PoS!

**New Input Format:**
```
Premise: Question: [Question Text] Answer: [Previous Answer]
Hypothesis: Question: [Question Text] Answer: [Current Answer]
```

**Why**: Consistency depends on the query context, not just answer text.

---

### 3. **Threshold Strategy Change**

**Current**: 0.35 threshold with RoBERTa
**Recommended**: 0.80-0.90 threshold with DeBERTa

**Reasoning:**
- DeBERTa is much more confident
- True contradictions usually score >0.95 with DeBERTa
- A score of 0.35 in RoBERTa = "unsure"
- DeBERTa will push low scores (like fhri_049's 0.041) closer to 0.99

**Initial Threshold**: Start at 0.50, then tune up to 0.80

**Do NOT**: Lower threshold to 0.25 on RoBERTa (will flood with false positives)

---

### 4. **Understanding False Positives**

**Key Insight**: False positives might be "Self-Corrections" not "Inconsistencies"

**Scenario:**
- Turn 1 (Hallucination): "X is Y."
- Turn 2 (Accurate): "Actually, X is Z."
- NLI Result: Contradiction (Score 0.99) ✅
- Your Label: Accurate ✅

**The Conflict**: NLI is correct - the bot DID contradict itself (it corrected itself)

**Thesis Defense**: Define if system penalizes Self-Correction
- If bot corrects previous error → "Good Contradiction" (safe)
- If bot contradicts without correction → "Inconsistent" (unsafe)

**Strategy**: 
```
If NLI_Score > Threshold AND Current_Answer_Confidence is High 
→ Label as "Self-Correction" (safe), not "Inconsistent" (unsafe)
```

---

### 5. **Specific Issue Explanations**

#### Q: Why is fhri_049's NLI score so low (0.041)?

**Case**: "GDP growth" vs "GDP shrinking by 10%"

**RoBERTa's Problem**: 
- Sees word "GDP" in both
- Sees numerical value in one
- Without "disentangled attention," interprets high lexical overlap as Neutral/Entailment
- Fails to weight "shrank" heavily enough to flip to "Contradiction"

**DeBERTa's Solution**: Specifically fixes this "bag-of-words" bias

#### Q: Why do accurate answers get high NLI scores?

**Diagnosis**: Confusing Factual Accuracy with Conversational Consistency

**Example**: Bot corrects itself (good) but NLI detects contradiction (also correct)

---

### 6. **Implementation Code (Provided by Gemini)**

```python
from sentence_transformers import CrossEncoder

class ContradictionDetector:
    def __init__(self):
        # Switch to DeBERTa-v3
        self.model = CrossEncoder('cross-encoder/nli-deberta-v3-base')
        # Mapping: [contradiction, entailment, neutral]
        self.contradiction_index = 0 

    def predict(self, question, prev_ans, curr_ans):
        # Contextual Prompting: Embed question into comparison
        premise = f"Question: {question} Answer: {prev_ans}"
        hypothesis = f"Question: {question} Answer: {curr_ans}"
        
        scores = self.model.predict([(premise, hypothesis)])
        probs = self._softmax(scores[0])
        contradiction_score = probs[self.contradiction_index]
        
        return contradiction_score

    def _softmax(self, x):
        import numpy as np
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()
```

---

### 7. **Thesis Methodology Justification**

**Architecture Selection**: 
- Transition from RoBERTa to DeBERTa aligns with He et al. (2021) findings
- Disentangled attention improves NLI on adversarial datasets

**Context Injection**: 
- Moving from "Sentence-Pair NLI" to "Dialogue-Context NLI" (Dialogue NLI)
- Acknowledges consistency depends on query, not just answer text

**Optional Hybrid Validation**:
- If NLI > 0.90 AND Semantic Similarity < 0.5 → Flag contradiction
- If Semantic Similarity > 0.95 → Ignore NLI (likely false positive)

---

### 8. **Summary of Next Steps**

1. ✅ **Change Model**: `cross-encoder/nli-deberta-v3-base`
2. ✅ **Change Threshold**: Start at 0.50, tune to 0.80
3. ✅ **Change Input**: Add `Question: [text]` to both inputs
4. ✅ **Re-Evaluate**: Run 10 ground truth samples
   - Expected: fhri_049 (GDP) spikes to high contradiction
   - Expected: fhri_021 (Crypto) clears threshold easily

---

### 9. **Expected Improvements**

**Current Performance**:
- Recall: 30-40% (3-4/10)
- Precision: 66.7-100% (varies)
- F1-Score: 0.46-0.50

**Expected with DeBERTa + Contextual Input**:
- Recall: 70%+ (7/10) ✅
- Precision: 80%+ ✅
- F1-Score: 0.70+ ✅

---

## Files to Modify

1. **`src/nli_infer.py`**: Change model loading to DeBERTa-v3
2. **`src/detectors.py`**: Update `compute_contradiction` to include question context
3. **`src/server.py`**: Pass question text to NLI computation
4. **`scripts/evaluate_detection.py`**: Update threshold from 0.35 to 0.50-0.80

---

## Questions for Implementation

1. Should we implement DeBERTa upgrade first, then test?
2. Should we implement contextual input first, then test?
3. Or implement both together?
4. Do we need to update requirements.txt for new dependencies?



























