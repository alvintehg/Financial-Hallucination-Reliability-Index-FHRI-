# Chapter 2: Literature Review - Structured Outline

**Thesis Topic:** LLM-Powered Financial Chatbot with Multi-Dimensional Hallucination Detection (FHRI)  
**Target Length:** ~6 pages (1,800-2,400 words)  
**Date:** December 2025

---

## Overall Structure

**Chapter 2 should follow this flow:**
1. Introduction to the domain (LLMs in Finance)
2. Core technical components (Hallucination Detection, RAG, NLI)
3. Application context (Robo-Advisors)
4. Supporting methodologies (Temporal, Multi-source, Evaluation)
5. Recent advances (2024-2025)
6. Gap analysis (identify where FHRI fits)

---

## Detailed Section-by-Section Outline

### **2.1 Introduction to Large Language Models in Finance** (~1 page)

**Purpose:** Establish the foundation - why LLMs are being used in finance and what challenges exist.

**Key Points to Cover:**
- Rise of LLMs in financial applications
- Domain-specific challenges (numerical accuracy, temporal sensitivity, regulatory compliance)
- Need for reliability and trustworthiness

**Papers to Cite:**
- **#22** - BloombergGPT (2023) - Domain-specific financial LLM
- **#23** - FinGPT (2023) - Open-source financial LLM
- **#24** - PIXIU (2023) - Financial instruction tuning and benchmarks
- **#25** - FiQA (2022) - Financial QA dataset
- **#26** - FinanceBench (2022) - Financial QA benchmark
- **#27** - FinQA (2018) - Numerical reasoning in finance
- **#50** - FinAgent (2024) - Financial LLM agents

**Writing Strategy:**
- Start with general LLM capabilities
- Transition to finance-specific adaptations
- Highlight numerical reasoning challenges (cite FinQA)
- Mention domain-specific models (BloombergGPT, FinGPT)
- End with the need for reliability metrics

**Example Opening:**
> "Large Language Models (LLMs) have demonstrated remarkable capabilities across diverse domains, with recent advances showing particular promise in financial applications [22, 23]. Domain-specific models such as BloombergGPT [22] and FinGPT [23] have been developed to address the unique challenges of financial data, including numerical reasoning, temporal sensitivity, and regulatory compliance. However, as highlighted by Maia et al. [27], financial applications require precise numerical accuracy, where even minor errors can lead to significant financial consequences."

---

### **2.2 Hallucination Detection Methods in Large Language Models** (~1.5 pages)

**Purpose:** Comprehensive overview of hallucination detection - the core problem your thesis addresses.

**Key Points to Cover:**
- Definition and taxonomy of hallucinations (intrinsic vs extrinsic)
- Semantic entropy and uncertainty quantification (your E component)
- Factuality and grounding methods (your G component)
- Recent advances (2024-2025)

**Papers to Cite:**

**Foundational Methods:**
- **#1** - Farquhar et al. (2023) - Semantic Entropy (FOUNDATIONAL for your E component)
- **#2** - Kuhn et al. (2023) - Semantic Uncertainty
- **#5** - Ji et al. (2023) - Survey of Hallucination in NLG (comprehensive taxonomy)

**Factuality & Grounding:**
- **#6** - Min et al. (2023) - FActScore (atomic fact verification)
- **#7** - Gekhman et al. (2024) - TrueTeacher (factual consistency evaluation)
- **#8** - Pagnoni et al. (2021) - FRANK benchmark

**Recent Advances (2024-2025):**
- **#53** - Zhang et al. (2025) - FAITH (financial tabular hallucinations)
- **#48** - Manakul et al. (2023) - SelfCheckGPT (black-box detection)
- **#47** - Azaria & Mitchell (2023) - Internal state awareness

**Writing Strategy:**
- Start with definition: "Hallucination refers to generated content that is nonsensical or unfaithful to the provided source [5]."
- Categorize: Intrinsic (contradicts source) vs Extrinsic (unverifiable)
- Deep dive into semantic entropy (your E component) - cite Farquhar et al. [1]
- Discuss factuality evaluation methods - cite TrueTeacher [7], FActScore [6]
- Mention domain-specific challenges in finance - cite FAITH [53]
- End with gap: "While these methods address individual aspects of hallucination, no prior work combines multiple detection paradigms into a unified reliability metric for financial applications."

**Example Paragraph:**
> "Semantic entropy, introduced by Farquhar et al. [1], quantifies uncertainty at the level of meaning rather than specific word sequences, making it particularly suitable for detecting hallucinations in generative tasks. This method employs Monte Carlo Dropout to generate multiple stochastic forward passes, calculating entropy across semantic variations of the output. Kuhn et al. [2] extended this concept by incorporating linguistic invariances, demonstrating improved uncertainty estimation. However, semantic entropy alone may miss factual inconsistencies that require external verification, highlighting the need for complementary detection methods."

---

### **2.3 Retrieval-Augmented Generation for Financial Applications** (~0.75 pages)

**Purpose:** Explain RAG as a grounding mechanism (your G component).

**Key Points to Cover:**
- RAG architecture and principles
- Dense retrieval methods (FAISS)
- Financial domain-specific RAG adaptations

**Papers to Cite:**
- **#9** - Lewis et al. (2020) - RAG foundational paper (ESSENTIAL)
- **#11** - Karpukhin et al. (2020) - Dense Passage Retrieval (your FAISS implementation)
- **#15** - Saad-Falcon et al. (2023) - Falcon: RAG for Financial QA (domain-specific)
- **#12** - Xiong et al. (2021) - Multi-hop dense retrieval (relates to multi-source)

**Writing Strategy:**
- Start with RAG definition: "Retrieval-Augmented Generation combines parametric memory (LLM) with non-parametric memory (retrieval) [9]."
- Explain dense retrieval: "Dense Passage Retrieval uses learned embeddings for semantic similarity [11]."
- Domain adaptation: "Financial RAG requires handling numerical data and temporal contexts [15]."
- Connect to your system: "Our system employs hybrid retrieval combining TF-IDF and FAISS for financial knowledge grounding."

**Example Paragraph:**
> "Retrieval-Augmented Generation (RAG), introduced by Lewis et al. [9], addresses the knowledge limitation of LLMs by combining parametric memory with external knowledge retrieval. The architecture retrieves relevant passages from a knowledge base and conditions the LLM generation on these retrieved contexts, thereby grounding outputs in verifiable sources. Karpukhin et al. [11] demonstrated that dense passage retrieval using learned embeddings significantly outperforms sparse retrieval methods. In financial applications, Saad-Falcon et al. [15] developed Falcon, a RAG framework specifically tailored for financial question answering, highlighting the importance of domain-specific retrieval strategies for handling numerical data and temporal contexts."

---

### **2.4 Natural Language Inference and Contradiction Detection** (~0.5 pages)

**Purpose:** Explain NLI for contradiction detection (your C component).

**Key Points to Cover:**
- NLI foundations and datasets
- Dialogue-specific NLI (for conversation consistency)
- Contradiction detection in financial contexts

**Papers to Cite:**
- **#19** - Welleck et al. (2019) - Dialogue Natural Language Inference (ESSENTIAL for your C component)
- **#16** - Bowman et al. (2015) - SNLI dataset (foundational)
- **#17** - Williams et al. (2018) - MultiNLI (broader coverage)
- **#21** - Laurer et al. (2024) - NLI with limited data

**Writing Strategy:**
- Define NLI: "Natural Language Inference determines if a hypothesis is entailed, contradicted, or neutral given a premise [16]."
- Dialogue NLI: "Welleck et al. [19] extended NLI to dialogue systems, enabling contradiction detection across conversation turns."
- Financial application: "In financial chatbots, NLI can detect when current answers contradict previous responses, ensuring conversation consistency."

**Example Paragraph:**
> "Natural Language Inference (NLI) has been widely used for detecting contradictions in generated text. While foundational datasets like SNLI [16] and MultiNLI [17] focus on sentence-level inference, Welleck et al. [19] introduced Dialogue Natural Language Inference, specifically designed for detecting inconsistencies in conversational contexts. This approach enables systems to identify when a current response contradicts information provided in previous conversation turns, a critical capability for maintaining consistency in multi-turn financial advisory dialogues."

---

### **2.5 Robo-Advisors and AI-Powered Financial Advisory Systems** (~0.75 pages)

**Purpose:** Establish the application context - your system is a robo-advisor.

**Key Points to Cover:**
- Robo-advisor foundations and evolution
- Trust and explainability in financial AI
- LLM-based robo-advisors

**Papers to Cite:**
- **#28** - Jung et al. (2018) - Robo-Advisors: Investing through Machines (FOUNDATIONAL)
- **#31** - Dietvorst et al. (2015) - Algorithm Aversion (trust in AI)
- **#32** - Bussone et al. (2015) - Role of Explanations in Trustworthy AI
- **#51** - Li et al. (2024) - INVESTORBENCH (LLM-based financial agents benchmark)

**Writing Strategy:**
- Define robo-advisors: "Robo-advisors are automated investment platforms that provide algorithm-based portfolio management [28]."
- Trust challenges: "Users exhibit algorithm aversion when AI systems make errors [31], highlighting the need for transparency."
- Explainability: "Bussone et al. [32] demonstrated that explanations improve user trust in AI systems."
- LLM evolution: "Recent work has explored LLM-based agents for financial decision-making [51]."

**Example Paragraph:**
> "Robo-advisors have emerged as automated investment platforms that provide algorithm-based portfolio management and financial advice [28]. However, user trust remains a critical challenge, with Dietvorst et al. [31] demonstrating that users exhibit algorithm aversion when AI systems make errors. Bussone et al. [32] found that providing explanations significantly improves user trust, suggesting that transparency is essential for financial AI adoption. Recent advances have explored LLM-based agents for financial decision-making, with Li et al. [51] introducing INVESTORBENCH, a benchmark for evaluating LLM-based financial agents across diverse decision-making tasks."

---

### **2.6 Temporal Consistency and Multi-Source Verification** (~0.5 pages)

**Purpose:** Explain temporal (T) and multi-source aspects of your system.

**Key Points to Cover:**
- Temporal reasoning in LLMs
- Multi-source data fusion
- Real-time data integration

**Papers to Cite:**
- **#41** - Dhingra et al. (2017) - Tracking World State (temporal tracking)
- **#42** - Jia et al. (2021) - Temporal Reasoning in NLU
- **#52** - Jiang et al. (2025) - Explainable Temporal Reasoning (RECENT, relevant to your T component)
- **#34** - Li et al. (2023) - Multi-Source Information Fusion for Financial Decision Making

**Writing Strategy:**
- Temporal reasoning: "Financial data is inherently time-sensitive, requiring models to track temporal relationships [41, 42]."
- Recent advances: "Jiang et al. [52] proposed explainable temporal reasoning frameworks using graph structures."
- Multi-source: "Financial decision-making often requires integrating information from multiple sources [34]."

**Example Paragraph:**
> "Temporal consistency is critical in financial applications, where information validity depends on time context. Dhingra et al. [41] introduced methods for tracking world state across temporal sequences, while Jia et al. [42] explored temporal reasoning capabilities in natural language understanding. Recent work by Jiang et al. [52] proposed explainable temporal reasoning frameworks that leverage graph structures to enhance LLM understanding of temporal relationships. Additionally, financial decision-making often requires integrating information from multiple sources, with Li et al. [34] demonstrating the effectiveness of multi-source information fusion for financial applications."

---

### **2.7 Evaluation Methodologies and Benchmarks** (~0.5 pages)

**Purpose:** Discuss evaluation approaches relevant to your work.

**Key Points to Cover:**
- Hallucination evaluation benchmarks
- Financial decision-making benchmarks
- Composite scoring methods

**Papers to Cite:**
- **#51** - Li et al. (2024) - INVESTORBENCH (financial decision-making benchmark)
- **#53** - Zhang et al. (2025) - FAITH (financial tabular hallucination benchmark)
- **#37** - Rajpurkar et al. (2016) - SQuAD (QA evaluation methodology)
- **#39** - Lin (2004) - ROUGE (composite metric example)

**Writing Strategy:**
- Benchmarks: "Recent benchmarks have been developed for evaluating financial LLM systems [51, 53]."
- Composite metrics: "Composite scoring methods combine multiple evaluation dimensions [39]."
- Gap: "However, no existing benchmark evaluates multi-dimensional reliability across grounding, entropy, contradiction, numeric, and temporal dimensions simultaneously."

**Example Paragraph:**
> "Evaluation of financial LLM systems has been addressed through various benchmarks. Li et al. [51] introduced INVESTORBENCH, a comprehensive benchmark for evaluating LLM-based agents in financial decision-making tasks, while Zhang et al. [53] developed FAITH, a framework for assessing intrinsic tabular hallucinations in finance. Composite evaluation metrics, such as ROUGE [39], demonstrate how multiple dimensions can be combined into unified scores. However, existing benchmarks focus on individual aspects of reliability, leaving a gap for multi-dimensional reliability assessment that simultaneously evaluates grounding, uncertainty, contradiction, numeric accuracy, and temporal consistency."

---

### **2.8 Recent Advances and Regulatory Considerations** (~0.5 pages)

**Purpose:** Cover 2024-2025 advances and regulatory context.

**Key Points to Cover:**
- Recent hallucination detection methods (2024-2025)
- Regulatory compliance frameworks
- Multi-modal financial data

**Papers to Cite:**
- **#7** - Gekhman et al. (2024) - TrueTeacher
- **#53** - Zhang et al. (2025) - FAITH
- **#54** - Fazlija et al. (2025) - Reasoning with financial regulatory texts
- **#52** - Jiang et al. (2025) - Explainable Temporal Reasoning

**Writing Strategy:**
- Recent methods: "2024-2025 has seen significant advances in hallucination detection [7, 53]."
- Regulatory: "Fazlija et al. [54] explored LLM applications for regulatory compliance, demonstrating the need for reliable systems."
- Multi-modal: "Financial applications increasingly require handling multi-modal data [53]."

**Example Paragraph:**
> "Recent advances in 2024-2025 have significantly advanced hallucination detection capabilities. Gekhman et al. [7] introduced TrueTeacher, a method for learning factual consistency evaluation using LLMs, while Zhang et al. [53] developed FAITH, a framework specifically for assessing tabular hallucinations in financial documents. Regulatory considerations have also gained attention, with Fazlija et al. [54] exploring LLM applications for interpreting financial regulatory texts such as Basel III, highlighting the critical need for reliable and accurate systems in compliance contexts."

---

### **2.9 Gap Analysis and Research Contribution** (~0.5 pages)

**Purpose:** Synthesize all literature to identify the gap that FHRI addresses.

**Key Points to Cover:**
- Individual methods exist but are not unified
- No composite reliability metric for financial LLMs
- Need for explainable, multi-dimensional assessment
- Your contribution: FHRI as first unified framework

**Writing Strategy:**
- Synthesize: "While individual detection methods exist for semantic entropy [1], RAG grounding [9], NLI contradiction [19], numeric verification [27], and temporal consistency [41, 42], no prior work combines these into a unified reliability metric."
- Gap: "Existing benchmarks evaluate individual aspects [51, 53] but lack a comprehensive multi-dimensional assessment framework."
- Contribution: "This research introduces FHRI, the first composite reliability index that fuses five detection paradigms into an explainable confidence score for financial LLM applications."

**Example Paragraph:**
> "While comprehensive research exists on individual hallucination detection methods—semantic entropy for uncertainty quantification [1], RAG for knowledge grounding [9], NLI for contradiction detection [19], numeric verification for financial data [27], and temporal reasoning for time-sensitive contexts [41, 42]—no prior work has integrated these diverse paradigms into a unified reliability assessment framework. Existing benchmarks such as INVESTORBENCH [51] and FAITH [53] evaluate specific aspects of financial LLM performance but lack a comprehensive multi-dimensional reliability metric. This research addresses this gap by introducing the Financial Hallucination Reliability Index (FHRI), a novel composite scoring system that fuses five complementary detection methods into a single explainable confidence metric, specifically tailored for financial advisory applications."

---

## Paper Citation Mapping by Section

### Section 2.1: LLMs in Finance
**Primary Citations:** [22], [23], [27]  
**Supporting Citations:** [24], [25], [26], [50]

### Section 2.2: Hallucination Detection
**Primary Citations:** [1], [5], [7]  
**Supporting Citations:** [2], [6], [8], [47], [48], [53]

### Section 2.3: RAG
**Primary Citations:** [9], [11], [15]  
**Supporting Citations:** [10], [12], [13], [14]

### Section 2.4: NLI & Contradiction
**Primary Citations:** [19]  
**Supporting Citations:** [16], [17], [18], [20], [21]

### Section 2.5: Robo-Advisors
**Primary Citations:** [28], [31], [32]  
**Supporting Citations:** [29], [30], [33], [51]

### Section 2.6: Temporal & Multi-Source
**Primary Citations:** [41], [42], [52], [34]  
**Supporting Citations:** [35], [36]

### Section 2.7: Evaluation
**Primary Citations:** [51], [53]  
**Supporting Citations:** [37], [39], [43], [44]

### Section 2.8: Recent Advances
**Primary Citations:** [7], [53], [54], [52]  
**Supporting Citations:** Recent 2024-2025 papers

### Section 2.9: Gap Analysis
**Synthesis Citations:** [1], [9], [19], [27], [41], [42], [51], [53]

---

## Writing Guidelines

### Tone & Style
- **Formal academic tone** (third person)
- **Precise technical language** (e.g., "semantic entropy" not "uncertainty score")
- **Hedging where appropriate** ("suggests", "indicates", "appears to")
- **No first person** ("This research" not "I/We")

### Citation Frequency
- **2-4 citations per paragraph** (average)
- **Heavy citation in Section 2.2** (hallucination detection - many methods)
- **Moderate citation in other sections** (2-3 per paragraph)

### Flow & Transitions
- **Start broad, narrow down** (general LLMs → finance → your specific problem)
- **Use transition sentences** ("However, existing methods...", "To address this gap...")
- **Connect sections** (each section should logically lead to the next)

### Key Phrases to Use
- "Recent advances have demonstrated..."
- "However, existing methods focus on..."
- "To address this limitation..."
- "While [method X] addresses [aspect Y], it fails to..."
- "This research gap motivates..."

---

## Target Word Count Distribution

| Section | Target Words | Target Pages |
|---------|-------------|--------------|
| 2.1 Introduction to LLMs in Finance | 300-400 | ~1.0 |
| 2.2 Hallucination Detection Methods | 450-600 | ~1.5 |
| 2.3 RAG for Financial Applications | 250-300 | ~0.75 |
| 2.4 NLI & Contradiction Detection | 200-250 | ~0.5 |
| 2.5 Robo-Advisors | 250-300 | ~0.75 |
| 2.6 Temporal & Multi-Source | 200-250 | ~0.5 |
| 2.7 Evaluation Methodologies | 200-250 | ~0.5 |
| 2.8 Recent Advances | 200-250 | ~0.5 |
| 2.9 Gap Analysis | 200-250 | ~0.5 |
| **TOTAL** | **2,250-2,850** | **~6 pages** |

---

## Quality Checklist

Before finalizing Chapter 2, ensure:

- [ ] All 7 essential papers are cited (#1, #9, #15, #19, #22, #27, #28)
- [ ] At least 2-3 recent papers (2024-2025) are included
- [ ] Each section has clear topic sentences
- [ ] Transitions between sections are smooth
- [ ] Gap analysis clearly identifies where FHRI fits
- [ ] No first-person language
- [ ] All technical terms are properly defined
- [ ] Citations follow consistent format (IEEE/ACM)
- [ ] Total length is approximately 6 pages (1,800-2,400 words)

---

**Last Updated:** December 2025  
**Status:** Ready for literature review generation















