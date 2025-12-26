# Brief Meeting Script: FHRI Results (2-3 minutes)

---

## 🎯 Opening (15 seconds)

**"Hi [Supervisor Name], I wanted to quickly update you on our FHRI detection system evaluation results."**

---

## 🔬 Evaluation Methodology (45 seconds)

**"How we evaluated:**

**1. Dataset:**
- 100 manually labeled samples (57 accurate, 26 hallucination, 17 contradiction)
- Each sample has `ground_truth_label` in JSON file
- Contradiction samples are paired using `contradiction_pair_id` to track previous answers

**2. Detection Process:**
- For each sample, query backend and get: FHRI score, entropy, contradiction score
- Apply thresholds to predict label:
  - **Contradiction:** NLI score ≥ 0.15 (two-tier: soft 0.15, hard 0.40)
  - **Hallucination:** Entropy > 2.0 OR FHRI < scenario threshold OR high-risk floor breach (< 0.85)
  - **Accurate:** FHRI > scenario threshold (varies: 0.55 for advice, 0.80 for numeric KPI)

**3. Scenario-Aware Thresholds:**
- Different FHRI thresholds per query type (numeric KPI: 0.80, advice: 0.55, etc.)
- High-risk floor (0.85) for critical numeric questions
- Phase 4 added numeric price comparison (10% tolerance vs realtime API)

**4. Metrics:**
- Compare predicted vs true labels
- Calculate precision, recall, F1 per class
- Overall accuracy and macro F1"

---

## 📊 Key Results (1 minute)

**"We tested four configurations on 100 samples. Here are the highlights:**

**1. Hallucination Detection - Major Improvement:**
- Baseline: Only caught 1 out of 26 hallucinations (3.85%)
- Latest (Phase 4): Caught 5 out of 26 (19.23%)
- **5x improvement** in catching dangerous errors

**2. Contradiction Detection - Perfect:**
- Achieved 100% recall and precision
- All 17 contradictions correctly identified

**3. Overall Balance:**
- Best configuration: Phase 4 (Numeric Check)
- Accuracy: 64% (down from 74% baseline)
- Macro F1: 0.6391 (best overall metric)"

---

## ⚖️ Trade-off (30 seconds)

**"The trade-off:**
- Accuracy decreased 10 points (74% → 64%)
- But we're catching 5x more hallucinations
- **This is acceptable for finance** - safety over convenience
- Wrong stock prices are more dangerous than flagging borderline answers"

---

## ⚠️ Current Problems (30 seconds)

**"Main challenges we're facing:**

**1. Hallucination Recall Still Low:**
- Only catching 19-23% of hallucinations (21 out of 26 still missed)
- Many hallucinations have very high FHRI scores (0.95-1.0)
- They appear well-grounded and confident, making them hard to detect

**2. Limited Numeric Check Coverage:**
- Currently only checks stock prices vs realtime API
- Need to expand to P/E ratios, market cap, dividend yield, revenue
- This would catch more numeric hallucinations

**3. False Positives:**
- Some accurate answers flagged as hallucinations (15 false positives)
- Need better balance between safety and precision"

---

## ✅ Conclusion (15 seconds)

**"Summary:**
- ✅ 5x better at catching hallucinations
- ✅ Perfect contradiction detection
- ✅ Best balance achieved in Phase 4

**Next steps:** Expand numeric checks to more metrics (P/E, market cap, revenue). Any questions?"**

---

## 📝 Quick Notes (for your reference)

**Key Numbers:**
- Accuracy: 74% → 64%
- Hallucination: 3.85% → 19.23% recall (5x)
- Contradiction: 94% → 100% recall (perfect)
- Best: Phase 4 (Macro F1: 0.6391)

**One-liner:** *"We improved hallucination detection 5x and achieved perfect contradiction detection, with a 10-point accuracy trade-off that's justified for safety-critical finance applications."*

---

**Total Time: ~4-5 minutes**

