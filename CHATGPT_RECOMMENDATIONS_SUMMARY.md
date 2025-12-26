# ChatGPT's Recommendations Summary

## Key Recommendations from ChatGPT

### 1. **Two-Tier Threshold Strategy** (Different from Gemini)

**ChatGPT's Approach:**
- **Hard contradiction**: score >= 0.70 (with additional checks)
- **Soft contradiction flag**: 0.28 <= score < 0.70 (gated by extra checks)
- **Base threshold**: 0.28-0.30 (to catch fhri_021: 0.298, fhri_047: 0.299)

**Rationale:**
- Lowering to 0.30 gains 2 contradictions (0.298, 0.299) → recall 40% → 60%
- Lowering to 0.25 gains 1 more (0.276) → recall 60% → 70%
- But false positives grow quickly below 0.25
- Two-tier balances recall with conservative deployment

**Thesis Justification:**
> "Based on the empirical distribution of contradiction scores in our dataset, we lowered the NLI decision threshold from 0.35 to 0.30 to recover near-miss contradictions (0.298, 0.299), while introducing a stricter 0.70 threshold for 'hard' contradictions."

---

### 2. **Bidirectional NLI Scoring** (New Approach)

**Current**: Only compute `nli(prev_answer, current_answer)`

**Recommended**: Compute both directions and take max
```python
s1 = nli(prev_answer, current_answer)      # P = prev, H = current
s2 = nli(current_answer, prev_answer)      # P = current, H = prev
contradiction_score = max(s1, s2)
```

**Why**: NLI is directional; flipping often rescues borderline mismatches

---

### 3. **Numeric Contradiction Heuristic Layer** (Critical for fhri_049)

**Problem**: NLI models struggle with quantitative reasoning (EQUATE benchmark shows failures)

**Solution**: Add explicit numeric consistency module
- Extract numeric claims (percentages, "grew", "shrank")
- Compare sign (growth vs shrink) and magnitude
- Flag conflicts where sign differs or magnitude deviates

**Example**:
- Previous: "grow +2%"
- Current: "shrink 10%" or "fall 3%"
- → Flag as numeric contradiction even if NLI score is low (0.041)

**Thesis Justification**:
> "Prior work shows that NLI models struggle on quantitative reasoning tasks. We therefore add an explicit numeric consistency module that parses percentages and directionality (grow/shrink), and flags conflicts where the sign differs or the magnitude deviates beyond a pre-defined tolerance."

---

### 4. **Question Similarity Gating** (False Positive Reduction)

**Strategy**: Only run NLI when questions are about the same thing

**Implementation**:
- Compute embeddings for `prev_question` and `current_question`
- Only run NLI if cosine similarity ≥ 0.7
- Also require entity overlap (same ticker, macro variable, time frame)

**If gate fails** → Skip NLI (or label as non-contradiction regardless of score)

---

### 5. **Answer Similarity Check** (False Positive Reduction)

**Rule**: If two answers are very similar paraphrases, they shouldn't be a contradiction

**Implementation**:
```python
if NLI_score >= 0.8 and answer_similarity >= 0.9:
    treat as entailment / consistent, not a contradiction
```

**Why**: High lexical overlap but subtle meaning differences can fool NLI

---

### 6. **Two-Stage Decision Logic**

**Stage 1 – Strong candidates (high NLI)**:
```
If NLI_score >= 0.70 AND:
    question_similarity ≥ 0.7, and
    entity overlap present,
→ label as "strong contradiction"
```

**Stage 2 – Moderate candidates (0.28–0.70)**:
```
If 0.28 ≤ score < 0.70:
    If question similarity low → ignore
    If numeric/keyword heuristic contradiction present → label as "soft contradiction warning"
```

---

### 7. **Better NLI-FHRI Fusion Logic**

**Current Logic** (Problem):
```python
if contradiction_score > 0.35:
    predicted_label = "contradiction"
elif fhri > threshold:
    predicted_label = "accurate"
else:
    predicted_label = "hallucination"
```

**Issues**:
- NLI overrides FHRI: even very reliable answers (high FHRI) are called "contradiction"
- Doesn't distinguish "fixing a hallucination" vs "making a hallucination"

**Better Fusion Logic**:
```python
# 1. Gating
if question_similarity < 0.7 or not same_entity:
    # no contradiction check
    if h >= H_THR:
        label = "accurate"
    else:
        label = "hallucination"
else:
    # 2. Contradiction hard flag
    if c >= 0.70 and h <= H_THR:
        label = "contradiction"
    # 3. Soft contradiction / potential correction
    elif c >= 0.70 and h > H_THR:
        # current answer is more reliable, but contradicts previous
        label = "correction_of_previous_answer"
    # 4. No strong contradiction: fall back to FHRI
    else:
        if h >= H_THR:
            label = "accurate"
        else:
            label = "hallucination"
```

**Key Idea**: Contradiction is only trusted when both NLI score is high AND FHRI indicates new answer is less reliable than old one.

---

### 8. **Model Selection: RoBERTa → DeBERTa-v3** (Same as Gemini)

**Recommendation**: Swap to `DeBERTa-v3-large-MNLI` (or base for speed)

**Why**:
- DeBERTa v3 outperforms BERT/RoBERTa on NLI benchmarks (SuperGLUE, MultiNLI)
- More calibrated probabilities
- Better general NLI performance

**Optional**: Fine-tune on FinNLI (financial NLI dataset) for domain adaptation

**Thesis Justification**:
> "We replaced the RoBERTa-based NLI model with DeBERTa-v3-MNLI, which is known to outperform RoBERTa on NLI benchmarks. To address domain shift in financial text, we further fine-tuned the model on FinNLI, a recently introduced multi-genre financial NLI dataset."

---

### 9. **Smart Input Truncation**

**Problem**: Long, verbose answers make models conservative

**Solution**: Extract only claim sentences
- Identify sentences containing: numbers, "is/was/will be", key domain terms
- Concatenate just those, not full paragraphs

**Example**:
- Instead of 5 paragraphs about crypto history
- Use: "Ethereum no longer uses Proof-of-Work; since 2022 it is secured by Proof-of-Stake."

---

### 10. **Hybrid Scoring Function** (Optional)

**Composite Score**:
```
S = α·NLI_contradiction_prob 
  + β·(1 - answer_similarity) 
  + γ·numeric_contradiction_flag 
  + δ·entity_overlap
```

**Then**: Label as contradiction if S > S_thresh

**With more data**: Train logistic regression or small MLP to learn weights (α, β, γ, δ)

---

### 11. **NLI Ensemble** (Optional Extension)

**Models**:
- RoBERTa-MNLI
- DeBERTa-v3-MNLI
- (Optionally) Financial-fine-tuned NLI model

**Combine via**:
- Simple average, or
- Max (pessimistic – higher recall, lower precision), or
- Weighted average (DeBERTa gets higher weight)

---

### 12. **Concrete "Do This Next" List**

**Minimal time implementation**:

1. ✅ Swap NLI model → DeBERTa-v3-MNLI (drop-in)
2. ✅ Bidirectional, truncated NLI:
   - Extract claim sentences
   - Compute NLI both directions; use max
3. ✅ Lower base threshold to ~0.28–0.30, introduce:
   - Hard contradiction: c >= 0.70 + high question similarity + entity overlap
   - Soft contradiction warning: 0.28 <= c < 0.70 + numeric/keyword conflict
4. ✅ Add gates:
   - Question similarity ≥ 0.7 and same entity before you believe any contradiction
   - If answer similarity ≥ 0.9, treat high NLI as artifact and suppress contradiction
5. ✅ Numeric contradiction module:
   - Parse numbers and growth/shrink words
   - Override low NLI (like fhri_049 = 0.041) when numeric conflict is obvious

**Expected**: Move from (40% R, 66.7% P, F1=0.5) to (≥70% recall, ≥80% precision)

---

### 13. **Papers/Benchmarks to Cite**

**DeBERTa v3 & NLI SOTA**:
- Microsoft blog on DeBERTa surpassing human performance on SuperGLUE
- Comparisons showing DeBERTa outperforming BERT/RoBERTa on NLU tasks

**Financial NLI domain shift**:
- FinNLI: Benchmark dataset for financial NLI
- Shows performance drop of general NLI models and benefit of domain-specific training

**Numeric reasoning weaknesses**:
- EQUATE: "Evaluating Quantitative Understanding Aptitude in Textual Entailment"
- Shows NLI models struggle badly with numeric reasoning

**NLI robustness & dataset artifacts**:
- Studies comparing BERT/RoBERTa/DeBERTa and highlighting vulnerability to superficial cues

---

## Key Differences: ChatGPT vs Gemini

| Aspect | ChatGPT | Gemini |
|--------|---------|--------|
| **Threshold** | Two-tier: 0.28-0.30 (soft) + 0.70 (hard) | Single: 0.80-0.90 (start at 0.50) |
| **Context** | Question similarity gating | Question in premise/hypothesis |
| **Bidirectional** | ✅ Yes (max of both directions) | ❌ Not mentioned |
| **Numeric Module** | ✅ Explicit heuristic layer | ❌ Not mentioned |
| **Answer Similarity** | ✅ Check to reduce FPs | ✅ Mentioned in hybrid validation |
| **FHRI Fusion** | ✅ Detailed fusion logic | ❌ Not detailed |
| **Input Format** | Truncate to claim sentences | Add question to premise/hypothesis |
| **Self-Correction** | ✅ Distinguish correction vs inconsistency | ✅ Similar concept |

---

## Common Recommendations (Both Agree)

1. ✅ **Upgrade to DeBERTa-v3** (both strongly recommend)
2. ✅ **Add question context** (ChatGPT: similarity gating, Gemini: in premise/hypothesis)
3. ✅ **Address numeric reasoning** (ChatGPT: explicit module, Gemini: better model handles it)
4. ✅ **Reduce false positives** (ChatGPT: similarity checks, Gemini: self-correction logic)
5. ✅ **Domain adaptation** (both mention FinNLI fine-tuning)

---

## Implementation Priority (Combined Recommendations)

### Phase 1: High-Impact, Low-Effort
1. Swap to DeBERTa-v3-MNLI
2. Add bidirectional NLI (max of both directions)
3. Lower threshold to 0.30 (or two-tier: 0.30 soft + 0.70 hard)

### Phase 2: Medium-Effort, High-Impact
4. Add question similarity gating
5. Add numeric contradiction heuristic module
6. Implement answer similarity check

### Phase 3: Advanced (If Time Permits)
7. Add question context to premise/hypothesis (Gemini's approach)
8. Implement better NLI-FHRI fusion logic
9. Smart input truncation (claim sentence extraction)
10. Hybrid scoring function



























