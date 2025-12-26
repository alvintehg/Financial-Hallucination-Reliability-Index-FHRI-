# Evaluation Dataset Annotation Guide

## Understanding the Annotation Fields

### **Basic Fields**

| Field | Purpose | Example |
|-------|---------|---------|
| **`id`** | Unique identifier for the sample | `"fhri_002"` |
| **`question`** | The user's question | `"Between an S&P 500 ETF and a single tech stock..."` |
| **`retrieved_passages`** | Passages retrieved by RAG (usually empty, filled during evaluation) | `[]` |
| **`llm_answer`** | The LLM's generated answer (filled during evaluation) | `""` (empty initially) |
| **`ground_truth_label`** | ✅ **THE LABEL USED FOR EVALUATION** | `"accurate"`, `"hallucination"`, or `"contradiction"` |
| **`your_annotation`** | Human reviewer's notes (for reference only, NOT used in evaluation) | `""` (optional) |
| **`notes`** | Explanation of what the answer should contain | `"Explain that diversified index ETFs..."` |

---

## **`ground_truth_label` - The Most Important Field**

**This is what the evaluation script uses to judge correctness.**

**Possible values:**
- **`"accurate"`**: The answer should be factually correct and follow expected behavior
- **`"hallucination"`**: The answer contains fabricated or incorrect information
- **`"contradiction"`**: The answer contradicts a previous response (for paired questions)

**In your example:**
```json
"ground_truth_label": "accurate"
```
This means: "The correct answer for this question should be marked as 'accurate'"

---

## **`fhri_spec` - Detailed Specification**

This contains metadata about how the question should be evaluated:

### **`expected_behavior`**
What the answer should do/explain
```json
"expected_behavior": "Explain that diversified index ETFs usually carry less idiosyncratic risk..."
```

### **`rubric`**
List of criteria the answer must meet
```json
"rubric": [
  "Explains that broad index ETFs reduce single-company risk...",
  "Clearly states that all equities involve risk...",
  "Does not make absolute claims..."
]
```

### **`risk_tier`**
How critical this question is
- **`"high"`**: Critical financial information (requires strict checking)
- **`"medium"`**: Important but less critical
- **`"low"`**: General advice

### **`compliance_tag`**
Whether the answer is allowed/restricted
- **`"allowed"`**: Answer is permitted
- **`"restricted"`**: Answer should be limited or redirected

### **`category`**
Type of question
- `"investment_advice"`, `"regulatory"`, `"numeric_kpi"`, etc.

### **`hallucination_check`**
```json
"hallucination_check": {
  "requires_verifiable_facts": false,  // Does this need fact-checking?
  "ground_truth_hint": ""  // What the correct answer should be
}
```

### **`contradiction_pair_id`**
Links questions that should be checked for contradictions
- **`null`**: Standalone question
- **`"pair-invest-1"`**: Part of a contradiction pair (e.g., fhri_016 and fhri_017)

### **`scenario_override`**
Forces a specific scenario detection
- **`"multi_ticker"`**: Forces multi-ticker comparison scenario
- **`null`**: Let system auto-detect scenario

### **`expected_scenario`**
What scenario the system should detect
- **`"Multi-Ticker Comparison"`**: Expected scenario name

---

## **How Evaluation Uses These Fields**

### **During Evaluation:**

1. **`ground_truth_label`** → Used to determine if prediction is correct
   - If `ground_truth_label = "accurate"` and system predicts `"accurate"` → ✅ Correct
   - If `ground_truth_label = "accurate"` and system predicts `"hallucination"` → ❌ Wrong

2. **`scenario_override`** → Forces specific FHRI threshold
   - `"multi_ticker"` → Uses threshold 0.70 (from SCENARIO_FHRI_THRESHOLDS)

3. **`contradiction_pair_id`** → Links questions for contradiction checking
   - If two questions share same `pair_id`, system checks if answers contradict

4. **`notes`** and **`rubric`** → For human reviewers, NOT used by evaluation script

---

## **Example: fhri_002**

```json
{
  "id": "fhri_002",
  "question": "Between an S&P 500 ETF and a single tech stock like NVDA...",
  "ground_truth_label": "accurate",  // ← System should predict "accurate"
  "fhri_spec": {
    "scenario_override": "multi_ticker",  // ← Uses 0.70 threshold
    "expected_scenario": "Multi-Ticker Comparison",
    "risk_tier": "high",  // ← High-risk question
    "category": "investment_advice"
  }
}
```

**What this means:**
- ✅ Correct answer should be marked as `"accurate"`
- Uses `multi_ticker` scenario (threshold: 0.70)
- High-risk question (requires strict checking)
- Investment advice category

---

## **Key Takeaways**

1. **`ground_truth_label`** = The "correct answer" for evaluation
2. **`scenario_override`** = Forces specific threshold/scenario
3. **`contradiction_pair_id`** = Links questions for contradiction checking
4. **`notes`** and **`rubric`** = For humans, not used by script
5. **`llm_answer`** = Filled during evaluation (empty initially)

**The evaluation script compares `predicted_label` (from system) with `ground_truth_label` (from dataset) to calculate accuracy!**














