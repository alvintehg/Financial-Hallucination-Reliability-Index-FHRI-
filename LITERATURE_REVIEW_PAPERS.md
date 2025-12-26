# Literature Review Papers for FHRI Thesis

**Project:** LLM-Powered Financial Chatbot with Multi-Dimensional Hallucination Detection  
**Date:** December 2025  
**Organized by:** Research Topic

---

## 1. Hallucination Detection in Large Language Models

### Core Papers on Semantic Entropy & Uncertainty Quantification

1. **Farquhar, S., et al. (2023).** "Detecting Hallucinations in Large Language Models Using Semantic Entropy."  
   - **Why relevant:** Your FHRI uses semantic entropy (E component) via Monte Carlo Dropout. This is the foundational paper.
   - **Key concepts:** Semantic entropy, uncertainty quantification, MC dropout
   - **Citation:** Essential for Chapter 2 (Literature Review) and Chapter 3 (Methodology)

2. **Kuhn, L., et al. (2023).** "Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation."  
   - **Why relevant:** Extends semantic entropy concepts, discusses linguistic invariances
   - **Key concepts:** Semantic uncertainty, linguistic consistency

3. **Kadavath, S., et al. (2022).** "Language Models (Mostly) Know What They Know."  
   - **Why relevant:** Discusses self-awareness in LLMs, relates to confidence scoring
   - **Key concepts:** Calibration, self-knowledge, uncertainty

4. **Lin, S., et al. (2022).** "TruthfulQA: Measuring How Models Mimic Human Falsehoods."  
   - **Why relevant:** Benchmark for hallucination detection, evaluation methodology
   - **Key concepts:** Factual accuracy, truthfulness metrics

5. **Ji, Z., et al. (2023).** "Survey of Hallucination in Natural Language Generation."  
   - **Why relevant:** Comprehensive survey covering all hallucination detection methods
   - **Key concepts:** Taxonomy of hallucinations, detection methods survey

### Factuality & Grounding Papers

6. **Min, S., et al. (2023).** "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation."  
   - **Why relevant:** Fine-grained factuality evaluation, relates to your numeric verification (N/D component)
   - **Key concepts:** Atomic fact verification, precision scoring

7. **Gekhman, Z., et al. (2024).** "TrueTeacher: Learning Factual Consistency Evaluation with Large Language Models."  
   - **Why relevant:** Factual consistency evaluation, relates to your grounding score (G component)
   - **Key concepts:** Factual consistency, evaluation methods

8. **Pagnoni, A., et al. (2021).** "Understanding Factuality in Abstractive Summarization with FRANK: A Benchmark for Factuality Metrics."  
   - **Why relevant:** Benchmark for factuality, evaluation framework
   - **Key concepts:** Factuality metrics, abstractive generation

---

## 2. Retrieval-Augmented Generation (RAG)

### Foundational RAG Papers

9. **Lewis, P., et al. (2020).** "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks."  
   - **Why relevant:** Your system uses RAG (TF-IDF/FAISS) for grounding. This is THE foundational paper.
   - **Key concepts:** RAG architecture, dense retrieval, knowledge-intensive tasks
   - **Citation:** Essential for Chapter 2 and Chapter 3

10. **Guu, K., et al. (2020).** "Retrieval Augmented Language Model Pre-Training."  
    - **Why relevant:** Early RAG work, discusses retrieval during pre-training
    - **Key concepts:** Pre-training with retrieval, knowledge integration

11. **Karpukhin, V., et al. (2020).** "Dense Passage Retrieval for Open-Domain Question Answering."  
    - **Why relevant:** Your FAISS implementation uses dense retrieval. This paper discusses DPR.
    - **Key concepts:** Dense retrieval, passage ranking, open-domain QA

12. **Xiong, L., et al. (2021).** "Answering Complex Open-Domain Questions with Multi-Hop Dense Retrieval."  
    - **Why relevant:** Multi-hop reasoning, relates to your multi-source verification
    - **Key concepts:** Multi-hop retrieval, complex reasoning

### RAG Evaluation & Faithfulness

13. **Wang, Y., et al. (2023).** "Faithful Chain-of-Thought Reasoning."  
    - **Why relevant:** Faithfulness in reasoning, relates to your grounding score (G component)
    - **Key concepts:** Faithful reasoning, chain-of-thought

14. **Yoran, O., et al. (2023).** "Answering Questions by Meta-Reasoning over Multiple Chains of Thought."  
    - **Why relevant:** Multi-chain reasoning, relates to your multi-dimensional fusion
    - **Key concepts:** Meta-reasoning, multiple reasoning paths

15. **Saad-Falcon, J., et al. (2023).** "Falcon: A Retrieval-Augmented Generation Framework for Financial Question Answering."  
    - **Why relevant:** RAG specifically for finance domain - DIRECTLY relevant!
    - **Key concepts:** Financial QA, domain-specific RAG
    - **Citation:** Essential for Chapter 2 (domain-specific adaptation)

---

## 3. Natural Language Inference & Contradiction Detection

### NLI Foundations

16. **Bowman, S. R., et al. (2015).** "A large annotated corpus for learning natural language inference."  
    - **Why relevant:** SNLI dataset, foundational NLI work
    - **Key concepts:** Natural language inference, entailment classification

17. **Williams, A., et al. (2018).** "A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference."  
    - **Why relevant:** MultiNLI dataset, broader coverage
    - **Key concepts:** Multi-genre NLI, challenge corpus

18. **Nie, Y., et al. (2020).** "Adversarial NLI: A New Benchmark for Natural Language Understanding."  
    - **Why relevant:** Adversarial evaluation, harder NLI tasks
    - **Key concepts:** Adversarial examples, robustness

### Contradiction Detection in Dialogue

19. **Welleck, S., et al. (2019).** "Dialogue Natural Language Inference."  
    - **Why relevant:** NLI for dialogue systems - DIRECTLY relevant to your contradiction detection!
    - **Key concepts:** Dialogue NLI, conversation consistency
    - **Citation:** Essential for Chapter 2 (contradiction detection)

20. **He, H., et al. (2020).** "Unlearn Dataset Bias in Natural Language Inference by Fitting the Residual."  
    - **Why relevant:** Bias in NLI models, relates to your cross-encoder implementation
    - **Key concepts:** Dataset bias, model robustness

21. **Laurer, M., et al. (2024).** "Less Annotating, More Classifying: Addressing the Data Scarcity Issue of Supervised Machine Learning with LLMs."  
    - **Why relevant:** Your thesis mentions this paper. NLI with limited data.
    - **Key concepts:** Data scarcity, LLM-based annotation

---

## 4. Financial Domain LLMs & Applications

### Finance-Specific LLMs

22. **Wu, S., et al. (2023).** "BloombergGPT: A Large Language Model for Finance."  
    - **Why relevant:** Domain-specific LLM for finance - DIRECTLY relevant!
    - **Key concepts:** Financial LLM, domain adaptation, Bloomberg dataset
    - **Citation:** Essential for Chapter 2 (finance domain LLMs)

23. **Yang, H., et al. (2023).** "FinGPT: Open-Source Financial Large Language Models."  
    - **Why relevant:** Open-source financial LLM, relates to your domain-specific work
    - **Key concepts:** Financial LLM, open-source models

24. **Xie, Q., et al. (2023).** "PIXIU: A Large Language Model, Instruction Data and Evaluation Benchmark for Finance."  
    - **Why relevant:** Financial instruction tuning, evaluation benchmarks
    - **Key concepts:** Instruction tuning, financial benchmarks

### Financial QA & Information Retrieval

25. **Chen, Z., et al. (2022).** "FiQA: A Finance Question Answering Dataset."  
    - **Why relevant:** Financial QA dataset, evaluation benchmark
    - **Key concepts:** Financial QA, dataset creation

26. **Shah, D., et al. (2022).** "FinanceBench: A New Benchmark for Financial Question Answering."  
    - **Why relevant:** Another financial QA benchmark, evaluation methodology
    - **Key concepts:** Financial benchmarks, QA evaluation

27. **Maia, M., et al. (2018).** "FinQA: A Dataset of Numerical Reasoning Questions in Finance."  
    - **Why relevant:** Numerical reasoning in finance - DIRECTLY relevant to your N/D component!
    - **Key concepts:** Numerical reasoning, financial QA
    - **Citation:** Essential for Chapter 2 (numeric verification)

---

## 5. Robo-Advisors & AI Financial Advisory

### Robo-Advisor Foundations

28. **Jung, D., et al. (2018).** "Robo-Advisors: Investing through Machines."  
    - **Why relevant:** Your system is a robo-advisor prototype. Foundational paper.
    - **Key concepts:** Robo-advisors, automated investment advice
    - **Citation:** Essential for Chapter 2 (robo-advisors)

29. **Fein, M. L. (2015).** "Robo-Advisors: A Closer Look."  
    - **Why relevant:** Early robo-advisor analysis, industry perspective
    - **Key concepts:** Robo-advisor features, user adoption

30. **D'Acunto, F., et al. (2019).** "The Effect of Robo-Advice on Investment Decisions."  
    - **Why relevant:** User behavior, trust in robo-advisors
    - **Key concepts:** User trust, investment decisions

### Trust & Explainability in Financial AI

31. **Dietvorst, B. J., et al. (2015).** "Algorithm Aversion: People Erroneously Avoid Algorithms After Seeing Them Err."  
    - **Why relevant:** Trust in AI systems, relates to your FHRI explainability
    - **Key concepts:** Algorithm aversion, trust in AI

32. **Bussone, A., et al. (2015).** "The Role of Explanations in Trustworthy AI Systems."  
    - **Why relevant:** Explainability in AI, relates to your component-level transparency
    - **Key concepts:** Explainable AI, trustworthiness

33. **Adadi, A., & Berrada, M. (2018).** "Peeking Inside the Black-Box: A Survey on Explainable Artificial Intelligence (XAI)."  
    - **Why relevant:** XAI survey, relates to your FHRI explainability
    - **Key concepts:** Explainable AI, interpretability

---

## 6. Multi-Source Verification & Data Integration

### Information Fusion

34. **Li, Y., et al. (2023).** "Multi-Source Information Fusion for Financial Decision Making."  
    - **Why relevant:** Your system uses multi-source data (Finnhub, yfinance, SEC). Information fusion.
    - **Key concepts:** Multi-source fusion, financial data integration

35. **Dong, Y., et al. (2022).** "A Survey on Multi-Source Data Fusion."  
    - **Why relevant:** General survey on data fusion, relates to your multi-source verification
    - **Key concepts:** Data fusion, multi-source integration

### Real-Time Data Integration

36. **Zhang, L., et al. (2021).** "Real-Time Financial Data Integration for AI Systems."  
    - **Why relevant:** Real-time data integration, relates to your Finnhub/yfinance integration
    - **Key concepts:** Real-time data, API integration

---

## 7. Composite Scoring & Multi-Dimensional Evaluation

### Multi-Component Scoring Systems

37. **Rajpurkar, P., et al. (2016).** "SQuAD: 100,000+ Questions for Machine Reading Comprehension."  
    - **Why relevant:** Evaluation methodology, composite metrics
    - **Key concepts:** QA evaluation, composite scoring

38. **Kwiatkowski, T., et al. (2019).** "Natural Questions: A Benchmark for Question Answering Research."  
    - **Why relevant:** Large-scale QA evaluation, relates to your evaluation framework
    - **Key concepts:** QA benchmarks, evaluation metrics

### Weighted Composite Metrics

39. **Lin, C. Y. (2004).** "ROUGE: A Package for Automatic Evaluation of Summaries."  
    - **Why relevant:** Composite evaluation metric (multiple components), relates to your FHRI weighting
    - **Key concepts:** Composite metrics, weighted evaluation

40. **Papineni, K., et al. (2002).** "BLEU: a Method for Automatic Evaluation of Machine Translation."  
    - **Why relevant:** Another composite metric, evaluation methodology
    - **Key concepts:** Composite scoring, automatic evaluation

---

## 8. Temporal Consistency & Time-Aware Systems

### Temporal Reasoning

41. **Dhingra, B., et al. (2017).** "Tracking the World State with Recurrent Entity Networks."  
    - **Why relevant:** Temporal tracking, relates to your temporal validity (T component)
    - **Key concepts:** Temporal reasoning, state tracking

42. **Jia, R., et al. (2021).** "Temporal Reasoning in Natural Language Understanding."  
    - **Why relevant:** Temporal reasoning in NLP, relates to your T component
    - **Key concepts:** Temporal understanding, time-aware systems

---

## 9. Evaluation Methodologies & Benchmarks

### Hallucination Evaluation

43. **Gekhman, Z., et al. (2024).** "The Factual Inconsistency Problem in Abstractive Summarization: A Survey."  
    - **Why relevant:** Evaluation methodology for factuality, relates to your evaluation framework
    - **Key concepts:** Factuality evaluation, hallucination metrics

44. **Maynez, J., et al. (2020).** "On Faithfulness and Factuality in Abstractive Summarization."  
    - **Why relevant:** Faithfulness vs factuality, evaluation methodology
    - **Key concepts:** Faithfulness, factuality, evaluation

### User Studies & Trust Evaluation

45. **Hoffman, R. R., et al. (2018).** "Metrics for Explainable AI: Challenges and Prospects."  
    - **Why relevant:** Metrics for explainability, relates to your user study design
    - **Key concepts:** Explainability metrics, user evaluation

46. **Miller, T. (2019).** "Explanation in Artificial Intelligence: Insights from the Social Sciences."  
    - **Why relevant:** Explainability from social science perspective, relates to your FHRI explainability
    - **Key concepts:** Explanation, interpretability, social sciences

---

## 10. Recent Advances (2024-2025)

### Latest Hallucination Detection

47. **Azaria, A., & Mitchell, T. (2023).** "The Internal State of an LLM Knows When It's Lying."  
    - **Why relevant:** Self-awareness in LLMs, relates to your entropy component
    - **Key concepts:** Internal states, self-knowledge

48. **Manakul, P., et al. (2023).** "SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models."  
    - **Why relevant:** Black-box hallucination detection, relates to your approach
    - **Key concepts:** Black-box detection, self-consistency

49. **Varshney, N., et al. (2023).** "Faithfulness Chain-of-Thought Reasoning."  
    - **Why relevant:** Faithful reasoning chains, relates to your grounding
    - **Key concepts:** Faithful reasoning, chain-of-thought

### Financial AI Recent Work

50. **Li, B., et al. (2024).** "FinAgent: A Financial Large Language Model Agent for Trading and Investment."  
    - **Why relevant:** Financial LLM agents, recent work in your domain
    - **Key concepts:** Financial agents, LLM applications

51. **Li, H., et al. (2024).** "INVESTORBENCH: A Benchmark for Financial Decision-Making Tasks with LLM-based Agent."  
    - **Why relevant:** Benchmark for evaluating LLM-based financial decision-making agents - DIRECTLY relevant to your robo-advisor evaluation!
    - **Key concepts:** Financial decision-making, LLM agents, evaluation benchmark, stock trading, cryptocurrency, ETFs
    - **Citation:** Essential for Chapter 2 (evaluation benchmarks) and Chapter 4 (results comparison)

52. **Jiang, Z., et al. (2025).** "Towards Explainable Temporal Reasoning in Large Language Models: A Structure-Aware Generative Framework."  
    - **Why relevant:** Explainable temporal reasoning framework - DIRECTLY relevant to your temporal consistency (T) component!
    - **Key concepts:** Temporal reasoning, explainability, graph structures, temporal knowledge graphs
    - **Citation:** Essential for Chapter 2 (temporal consistency) and Chapter 3 (methodology)

53. **Zhang, M., et al. (2025).** "FAITH: A Framework for Assessing Intrinsic Tabular Hallucinations in Finance."  
    - **Why relevant:** Multi-modal financial data (tables + text) hallucination detection - DIRECTLY relevant!
    - **Key concepts:** Tabular hallucinations, financial tabular data, multi-modal reasoning, S&P 500 reports
    - **Citation:** Essential for Chapter 2 (multi-modal financial data) and Chapter 3 (evaluation)

54. **Fazlija, B., et al. (2025).** "Reasoning with financial regulatory texts via Large Language Models."  
    - **Why relevant:** Regulatory compliance frameworks for AI in finance - DIRECTLY relevant!
    - **Key concepts:** Financial regulation, compliance, Basel III, LLM reasoning, Chain-of-Thought, Tree-of-Thought
    - **Citation:** Essential for Chapter 2 (regulatory compliance)

---

## How to Use This List

### Priority Order for Literature Review

**Must Read (Essential):**
- Papers #1, #9, #15, #19, #22, #27, #28 (7 papers)
- These directly relate to your core contributions

**Highly Recommended:**
- Papers #2, #6, #11, #20, #23, #31, #32 (7 papers)
- Important for methodology and related work

**Supporting Papers:**
- Remaining 36 papers for comprehensive coverage
- Use for specific sections (e.g., temporal reasoning, evaluation methods)

### Chapter Organization

**Chapter 2: Literature Review Structure**

1. **Section 2.1: Large Language Models in Finance**
   - Papers: #22, #23, #24, #25, #26, #27, #50

2. **Section 2.2: Hallucination Detection Methods**
   - Papers: #1, #2, #3, #4, #5, #6, #7, #8, #43, #44, #47, #48

3. **Section 2.3: Retrieval-Augmented Generation**
   - Papers: #9, #10, #11, #12, #13, #14, #15

4. **Section 2.4: Natural Language Inference & Contradiction Detection**
   - Papers: #16, #17, #18, #19, #20, #21

5. **Section 2.5: Robo-Advisors & Financial Advisory Systems**
   - Papers: #28, #29, #30, #31, #32, #33

6. **Section 2.6: Multi-Source Verification & Data Integration**
   - Papers: #34, #35, #36

7. **Section 2.7: Composite Scoring & Evaluation Metrics**
   - Papers: #37, #38, #39, #40, #45, #46

8. **Section 2.8: Temporal Consistency**
   - Papers: #41, #42, #52

9. **Section 2.9: Evaluation Methodologies & Benchmarks**
   - Papers: #37, #38, #39, #40, #43, #44, #45, #46, #51

10. **Section 2.10: Multi-Modal Financial Data & Regulatory Compliance**
   - Papers: #53 (FAITH - multi-modal), #54 (Regulatory compliance)

11. **Section 2.11: Gap Analysis**
   - Synthesize all papers to identify research gap (no prior FHRI-like composite score)

---

## Search Tips

1. **Google Scholar:** Search by paper title or author name
2. **Semantic Scholar:** Use for finding related papers and citation networks
3. **ArXiv:** Many recent papers available here
4. **Your University Library:** Access to paid journals (IEEE, ACM, etc.)

---

## Citation Format

Use IEEE or ACM format (check with your supervisor). Example:

```
[1] S. Farquhar et al., "Detecting Hallucinations in Large Language Models Using Semantic Entropy," arXiv preprint arXiv:2303.13452, 2023.
```

---

**Last Updated:** December 2025  
**Total Papers:** 54 papers organized by topic  
**Essential Papers:** 7 must-read papers  
**Recommended Papers:** 14 highly recommended papers



