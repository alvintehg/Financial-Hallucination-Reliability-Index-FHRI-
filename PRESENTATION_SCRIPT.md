# Presentation Script: FHRI Detection System Results

**Duration:** 5-7 minutes  
**Audience:** Supervisor/Teacher  
**Format:** Concise, data-driven presentation

---

## 🎯 Opening (30 seconds)

**"Good [morning/afternoon], [Supervisor Name]. Today I'll present the evaluation results of our Finance Hallucination Reliability Index detection system. We've made significant improvements in detecting hallucinations and contradictions in financial chatbot responses, with some important trade-offs to discuss."**

---

## 📋 Problem Statement (45 seconds)

**"Our system needs to detect three types of problematic answers:**
- **Hallucinations** - factually incorrect information (26 samples in our dataset)
- **Contradictions** - answers that contradict previous responses (17 samples)
- **Accurate** - correct, reliable answers (57 samples)

**The challenge:** Our baseline system had very low hallucination detection recall - only catching 1 out of 26 hallucinations (3.85%). This is dangerous for finance applications where wrong information can lead to poor investment decisions."

---

## 🔧 Methodology (1 minute)

**"We implemented a multi-phase improvement approach:**

**Phase 1 - Baseline:** Original FHRI with scenario-specific thresholds, entropy-only hallucination detection.

**Phase 2 - Strict FHRI:** Very strict thresholds (0.85-0.90) for high-risk numeric questions.

**Phase 3 - Moderate FHRI:** Balanced thresholds (0.70-0.80) with a high-risk floor (0.85).

**Phase 4 - Numeric Check:** Added explicit numeric price comparison against realtime API data (10% tolerance).

**Key innovation:** Scenario-aware thresholds - different rules for different query types like numeric KPIs, regulatory questions, and portfolio advice."

---

## 📊 Key Results (2 minutes)

### **1. Hallucination Detection: 5x Improvement**

**"Our most important achievement:**
- **Baseline:** 3.85% recall (1/26 hallucinations caught)
- **Phase 4:** 19.23% recall (5/26 hallucinations caught)
- **5x improvement** in catching dangerous hallucinations

**However, this came with a trade-off:**
- Overall accuracy decreased from 74% to 64%
- We're now flagging more answers as potentially unreliable, which is acceptable for safety-critical finance applications."

### **2. Contradiction Detection: Perfect Performance**

**"We achieved perfect contradiction detection:**
- **100% recall** - All 17 contradictions correctly identified
- **100% precision** - Zero false positives
- **F1-Score: 1.0**

This is a major success - our system now reliably catches when the chatbot contradicts itself."

### **3. Overall Balance: Best in Phase 4**

**"Phase 4 (Numeric Check) achieves the best overall balance:**
- **Highest Macro F1:** 0.6391 (best overall metric)
- **Recovered Accuracy:** 64% (vs 60% in strict phases)
- **Better Precision:** Fewer false hallucinations (15 vs 20 false positives)

**Per-class performance:**
- Accurate: 67% precision, 74% recall, 0.70 F1
- Hallucination: 25% precision, 19% recall, 0.22 F1
- Contradiction: 100% precision, 100% recall, 1.0 F1"

---

## ⚖️ Trade-off Analysis (1 minute)

**"The key trade-off we made:**

**What we sacrificed:**
- 10 percentage points in overall accuracy (74% → 64%)
- Some accurate answers are now flagged as hallucinations (15 false positives)

**What we gained:**
- 5x improvement in hallucination detection (3.85% → 19.23%)
- Perfect contradiction detection (100%)
- Better safety for users - catching more dangerous errors

**Why this trade-off is justified:**
- In finance, **false negatives (missed hallucinations) are more dangerous than false positives**
- A wrong stock price or P/E ratio can lead to poor investment decisions
- It's better to flag an answer as potentially unreliable than to let wrong information through"

---

## 🔍 Technical Highlights (45 seconds)

**"Key technical innovations:**

1. **Scenario-Aware Thresholds:** Different FHRI thresholds for different query types
   - Numeric KPI: 0.80 threshold, 0.85 high-risk floor
   - Regulatory: 0.75 threshold
   - Fundamentals: 0.70 threshold

2. **High-Risk Floor:** Critical numeric questions require FHRI ≥ 0.85

3. **Numeric Price Comparison:** Explicit comparison of answer prices vs realtime API data (10% tolerance)

4. **Two-Tier Contradiction Detection:** Soft threshold (0.15) and hard threshold (0.40) for different confidence levels"

---

## 🚀 Future Work (30 seconds)

**"Next steps to further improve:**

1. **Expand Numeric Checks:** Currently only checks prices; will add P/E ratios, market cap, dividend yield, revenue
2. **Rule-Based Verification:** Add explicit rules for binary facts (market holidays, Dow membership, legal facts)
3. **Threshold Optimization:** Fine-tune on larger dataset
4. **Address High-FHRI Hallucinations:** Some hallucinations still have FHRI > 0.95, need additional detection methods"

---

## ✅ Conclusion (30 seconds)

**"In summary:**
- ✅ **5x improvement** in hallucination detection (3.85% → 19.23%)
- ✅ **Perfect contradiction detection** (100% recall/precision)
- ✅ **Best overall balance** achieved in Phase 4 (Macro F1: 0.6391)
- ⚠️ **Trade-off:** 10-point accuracy decrease (acceptable for safety-critical domain)

**The system is now significantly safer for finance applications, catching more dangerous hallucinations while maintaining reasonable overall performance. Thank you. Are there any questions?"**

---

## 📝 Quick Reference Card (for your notes)

### Key Numbers to Remember:
- **Baseline Accuracy:** 74%
- **Phase 4 Accuracy:** 64%
- **Hallucination Recall:** 3.85% → 19.23% (5x improvement)
- **Contradiction Recall:** 94.12% → 100% (perfect)
- **Macro F1:** 0.6194 → 0.6391 (best in Phase 4)

### Main Points:
1. ✅ 5x hallucination improvement
2. ✅ Perfect contradiction detection
3. ✅ Best balance in Phase 4
4. ⚠️ Trade-off: accuracy for safety (justified)

### If Asked About Trade-off:
**"We prioritized safety over convenience. In finance, catching wrong information is more critical than having perfect accuracy. A 10-point accuracy decrease is acceptable when it means catching 5x more dangerous hallucinations."**

---

## 🎤 Delivery Tips

1. **Start strong:** Lead with the 5x improvement achievement
2. **Use visuals:** Show the comparison table if possible
3. **Emphasize safety:** Frame trade-off as "safety vs convenience"
4. **Be confident:** The results show clear improvement, even with trade-offs
5. **Prepare for questions:** Be ready to explain why 64% accuracy is acceptable

---

## ❓ Anticipated Questions & Answers

### Q: "Why did accuracy decrease?"
**A:** "We made the system more conservative to catch more hallucinations. This means some borderline answers are now flagged as potentially unreliable. In finance, this is safer than letting wrong information through. We're prioritizing false negatives (missed hallucinations) over false positives."

### Q: "Why is hallucination recall still only 19%?"
**A:** "Some hallucinations have very high FHRI scores (0.95-1.0) because they're well-written and appear well-grounded. We're working on explicit numeric checks and rule-based verification to catch these. This is ongoing work."

### Q: "Is 64% accuracy acceptable?"
**A:** "Yes, for safety-critical finance applications. The 10-point decrease is justified by the 5x improvement in catching dangerous hallucinations. We're catching 5x more wrong information, which is more valuable than perfect accuracy."

### Q: "What's next?"
**A:** "We'll expand numeric checks to more metrics (P/E, market cap, revenue), add rule-based fact verification, and fine-tune thresholds on a larger dataset. The goal is to improve hallucination recall further while maintaining or improving accuracy."

---

**Total Presentation Time: ~5-7 minutes**  
**Recommended Format:** Slides with 1-2 key metrics per slide, use this script as your speaking notes.


























