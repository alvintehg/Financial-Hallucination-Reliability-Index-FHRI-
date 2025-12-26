# Prompt for Gemini: Teacher-Friendly Explanation

**Copy this entire prompt and paste it into Gemini to get a clear explanation for your supervisor.**

---

## Prompt to Send to Gemini:

```
I need help explaining my Final Year Project evaluation results to my supervisor in a clear, educational way. Can you help me create an explanation that makes the methodology and results easy to understand?

Here's my project context:

**Project:** Finance Hallucination Reliability Index (FHRI) Detection System for Financial Chatbot

**Goal:** Detect when a financial chatbot gives wrong information (hallucinations) or contradicts itself (contradictions).

**Evaluation Dataset:**
- 100 manually labeled samples
- 57 "accurate" (correct answers)
- 26 "hallucination" (factually wrong answers)
- 17 "contradiction" (answers that contradict previous responses)

**How I Labeled the Dataset:**
Each sample in my JSON file has:
- `ground_truth_label`: The correct label ("accurate", "hallucination", or "contradiction")
- `fhri_spec`: Metadata including expected behavior, rubric, risk tier
- `contradiction_pair_id`: For contradiction samples, links them to a previous "accurate" answer
- `scenario_override`: Query type (e.g., "numeric_kpi", "advice", "regulatory")

**Detection Methods I Used:**

1. **Entropy Detection (Uncertainty):**
   - Measures how uncertain the AI is about its answer
   - If entropy > 2.0 → likely hallucination

2. **FHRI Score (Reliability Index):**
   - Composite score (0-1) combining 5 sub-scores:
     - G: Grounding (how well answer matches sources)
     - N_or_D: Numeric/Directional consistency
     - T: Temporal validity
     - C: Citation completeness
     - E: Entropy confidence
   - Higher FHRI = more reliable answer

3. **Scenario-Aware Thresholds:**
   - Different FHRI thresholds for different query types:
     - Numeric KPI (stock prices, P/E ratios): 0.80 threshold
     - Advice questions: 0.55 threshold (more lenient)
     - Regulatory questions: 0.75 threshold
   - High-risk numeric questions require FHRI ≥ 0.85 (extra strict)

4. **Contradiction Detection (NLI):**
   - Uses Natural Language Inference to compare current answer vs previous answer
   - Two-tier system: soft threshold (0.15) and hard threshold (0.40)
   - If contradiction score ≥ 0.15 → flag as contradiction

5. **Numeric Price Check (Phase 4):**
   - For price questions, compares answer price vs realtime API price
   - If difference > 10% → flag as hallucination

**Evaluation Process:**
1. Load each sample from dataset
2. Query my chatbot backend with the question
3. Backend returns: answer, entropy, FHRI score, contradiction score
4. Apply thresholds to predict label (contradiction > hallucination > accurate)
5. Compare predicted label vs true label from dataset
6. Calculate metrics: precision, recall, F1-score, accuracy

**My Results (4 Phases):**

**Phase 1 - Baseline:**
- Accuracy: 74%
- Hallucination recall: 3.85% (only 1/26 caught)
- Contradiction recall: 94.12%

**Phase 4 - Latest (with all improvements):**
- Accuracy: 64%
- Hallucination recall: 19.23% (5/26 caught) - 5x improvement!
- Contradiction recall: 100% (perfect!)
- Macro F1: 0.6391 (best overall)

**Trade-off:**
- Accuracy decreased 10 points (74% → 64%)
- But hallucination detection improved 5x (3.85% → 19.23%)
- This is acceptable for finance - safety over convenience

**Current Challenges:**
- Still missing 21 out of 26 hallucinations (80% missed)
- Many hallucinations have very high FHRI scores (0.95-1.0), making them hard to detect
- Need to expand numeric checks beyond just prices

---

**Can you help me create:**
1. A clear, teacher-friendly explanation of my evaluation methodology
2. Why the trade-off (accuracy vs safety) is justified
3. How the scenario-aware thresholds work and why they're important
4. What the results mean in practical terms
5. How to present this in a way that shows both achievements and limitations honestly

Please make it educational and easy to understand, suitable for explaining to a supervisor who may not be deeply familiar with NLP/ML evaluation metrics.
```

---

## Alternative Shorter Prompt (if Gemini has token limits):

```
I need help explaining my FYP evaluation to my supervisor. My project detects hallucinations and contradictions in a financial chatbot.

**Evaluation Setup:**
- 100 labeled samples (57 accurate, 26 hallucination, 17 contradiction)
- Each sample has ground_truth_label in JSON
- Contradiction samples are paired to track previous answers

**Detection Methods:**
1. Entropy (uncertainty) - threshold 2.0
2. FHRI score (reliability 0-1) with scenario-specific thresholds:
   - Numeric KPI: 0.80
   - Advice: 0.55
   - High-risk floor: 0.85
3. NLI contradiction detection (thresholds: 0.15 soft, 0.40 hard)
4. Numeric price comparison (10% tolerance)

**Results:**
- Baseline: 74% accuracy, 3.85% hallucination recall
- Latest: 64% accuracy, 19.23% hallucination recall (5x improvement), 100% contradiction recall

**Trade-off:** 10-point accuracy decrease for 5x better hallucination detection (justified for finance safety).

Can you create a clear, educational explanation that:
1. Explains the evaluation methodology simply
2. Justifies the accuracy/safety trade-off
3. Shows what the results mean practically
4. Is suitable for a supervisor presentation
```

---

## How to Use:

1. **Copy the full prompt** (first one) or the shorter version
2. **Paste into Gemini** (gemini.google.com)
3. **Review the generated explanation** - it should be teacher-friendly
4. **Customize if needed** - add your specific details or adjust the tone
5. **Use in your meeting** - either read it directly or use it as notes

---

## Tips:

- If Gemini's response is too technical, ask: "Can you make this even simpler, as if explaining to someone new to ML evaluation?"
- If you need it shorter, ask: "Can you condense this to 2-3 minutes of speaking time?"
- If you need more detail on a specific part, ask: "Can you elaborate on [specific topic]?"

---

**Good luck with your presentation!**


























