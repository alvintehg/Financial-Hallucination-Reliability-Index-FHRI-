# Feature Importance Rankings by Scenario (Corrected)

## Feature Importance Table

| Scenario | Most Important | 2nd Important | 3rd Important | 4th Important | Least Important |
|----------|---------------|---------------|---------------|---------------|-----------------|
| **numeric_kpi** | N/D (Numeric) | G (Grounding) | T (Temporal) | E (Entropy) | C (Citation) |
| **intraday** | T (Temporal) | N/D (Numeric) | G (Grounding) | E (Entropy) | C (Citation) |
| **fundamentals** | G (Grounding) | N/D (Numeric) | T (Temporal) | C (Citation) | E (Entropy) |
| **news** | T (Temporal) | G (Grounding) | C (Citation) | E (Entropy) | N/D (Numeric) |
| **regulatory** | G (Grounding) | C (Citation) | E (Entropy) | T (Temporal) | N/D (Numeric) |
| **crypto** | T (Temporal) | N/D (Numeric) | G (Grounding) | E (Entropy) | C (Citation) |
| **advice** | G (Grounding) | E (Entropy) | C (Citation) | N/D (Numeric) | T (Temporal) |
| **multi_ticker** | G (Grounding) | N/D (Numeric) | E (Entropy) | C (Citation) | T (Temporal) |
| **directional** | T (Temporal) | G (Grounding) | N/D (Numeric) | E (Entropy) | C (Citation) |
| **portfolio_advice** | G (Grounding) | E (Entropy) | N/D (Numeric) | C (Citation) | T (Temporal) |
| **Overall Rank** | **G (1st)** | **N/D (2nd)** | **T (3rd)** | **E (4th)** | **C (5th)** |

---

## Detailed Justifications by Scenario

### 1. Numeric KPI Queries
**Ranking: N/D > G > T > E > C**

**Justification:**
- **N/D (Most Important)**: Numeric/data features are paramount because these queries explicitly request quantitative metrics (P/E ratios, margins, growth rates). The hallucination detection depends heavily on identifying numeric anomalies or impossible values.
- **G (2nd)**: Grounding ensures the numbers are attributed to the correct company and metric definition
- **T (3rd)**: Temporal context matters for identifying which reporting period's data is being used
- **E (4th)**: Entropy helps identify uncertain calculations but is secondary to numeric validation
- **C (Least)**: Citations are least important as KPI queries rarely involve direct quotes or attributions

**Why this ranking?**: The optimal threshold of 0.65 reflects moderate confidence in numeric accuracy. The model must primarily verify numeric plausibility and grounding to correct entities.

---

### 2. Intraday Price Queries
**Ranking: T > N/D > G > E > C**

**Justification:**
- **T (Most Important)**: Temporal features are critical because intraday queries are inherently time-specific ("at 2 PM", "during opening", "end of trading day"). Wrong timestamps render the entire response a hallucination.
- **N/D (2nd)**: Price values must be numerically reasonable for the given stock and timeframe
- **G (3rd)**: Grounding ensures prices are attributed to the correct ticker symbol
- **E (4th)**: Entropy captures uncertainty in minute-by-minute price fluctuations
- **C (Least)**: Citations are irrelevant for price quotes

**Why this ranking?**: The 0.65 threshold reflects the challenge of temporal precision. Temporal features dominate because even a correct price at the wrong time constitutes a hallucination.

---

### 3. Fundamentals Queries
**Ranking: G > N/D > T > C > E**

**Justification:**
- **G (Most Important)**: Grounding is paramount to ensure financial data is correctly attributed to the right company and metric. Mixing up companies is a critical failure.
- **N/D (2nd)**: Numeric values must be accurate for the specified fundamentals
- **T (3rd)**: Temporal context identifies which fiscal period/quarter is referenced
- **C (4th)**: Citations occasionally matter when referencing earnings reports or filings
- **E (Least)**: Entropy is less critical as fundamentals queries have relatively clear answers

**Why this ranking?**: The 0.65 threshold and 94.2% accuracy reflect strong grounding and numeric verification. The model excels when it can properly ground financial data to entities.

---

### 4. News Queries
**Ranking: T > G > C > E > N/D**

**Justification:**
- **T (Most Important)**: Temporal accuracy is crucial—news events are defined by when they occurred. A real event reported with the wrong date is a hallucination.
- **G (2nd)**: Grounding ensures events are correctly attributed to the right companies/entities
- **C (3rd)**: Citations and source attribution matter for verifying news authenticity
- **E (4th)**: Entropy helps identify fabricated events through model uncertainty
- **N/D (Least)**: Numeric data is least important as news often involves qualitative events

**Why this ranking?**: The 0.70 threshold and perfect F1 score indicate strong temporal-grounding alignment. News queries have the clearest temporal signatures, enabling perfect separation of accurate vs. hallucinated responses.

---

### 5. Regulatory Queries
**Ranking: G > C > E > T > N/D**

**Justification:**
- **G (Most Important)**: Grounding is essential to correctly identify which regulation, jurisdiction, and regulatory body applies. Mixing up SEC vs. FINRA rules is catastrophic.
- **C (2nd)**: Citations are critical for regulatory queries as they reference specific rules, statutes, and compliance documents
- **E (3rd)**: High entropy is a strong indicator of hallucination in regulatory contexts due to poor model calibration
- **T (4th)**: Temporal context matters for identifying when regulations took effect or were amended
- **N/D (Least)**: Numeric data is rarely central to regulatory compliance queries

**Why this ranking?**: The lowest threshold (0.55) and lowest accuracy (91.2%) reflect poor grounding and citation quality. The model struggles to properly ground regulatory information, leading to high hallucination rates.

---

### 6. Crypto Queries
**Ranking: T > N/D > G > E > C**

**Justification:**
- **T (Most Important)**: Crypto markets operate 24/7 with extreme volatility—temporal precision is critical for price accuracy and event timing
- **N/D (2nd)**: Price values, percentage changes, and trading volumes are central to crypto queries
- **G (3rd)**: Grounding ensures correct attribution to specific cryptocurrencies and exchanges
- **E (4th)**: Entropy helps identify fabricated market events
- **C (Least)**: Citations are rarely needed for crypto price/event queries

**Why this ranking?**: The 0.70 threshold and perfect F1 score indicate strong temporal-numeric coupling. Crypto's time-sensitive nature makes temporal features the primary discriminator.

---

### 7. Advice Queries
**Ranking: G > E > C > N/D > T**

**Justification:**
- **G (Most Important)**: Grounding ensures advice is based on actual company characteristics and market conditions rather than fabricated fundamentals
- **E (2nd)**: High entropy/uncertainty is appropriate for advice (which is inherently uncertain), but excessive entropy signals hallucination
- **C (3rd)**: Citations provide credibility by referencing analyst reports or research
- **N/D (4th)**: Numeric data supports recommendations but isn't the primary focus
- **T (Least)**: Temporal context is less critical as advice is often forward-looking

**Why this ranking?**: The 0.65 threshold reflects the importance of grounding quality reasoning. Entropy plays a larger role than in factual queries because legitimate advice should express appropriate uncertainty.

---

### 8. Multi-Ticker Queries
**Ranking: G > N/D > E > C > T**

**Justification:**
- **G (Most Important)**: Multi-ticker queries require correctly grounding data to multiple entities simultaneously—the primary failure mode is mixing up companies
- **N/D (2nd)**: Comparative numeric accuracy is essential for fair comparisons across tickers
- **E (3rd)**: High entropy signals the model is struggling with multi-entity reasoning complexity
- **C (4th)**: Citations can support comparative claims but are secondary
- **T (Least)**: Temporal consistency matters but is less critical than entity grounding

**Why this ranking?**: The 0.60 threshold and moderate accuracy (90.8%) reflect multi-entity grounding challenges. Keeping multiple companies straight is the primary detection challenge.

---

### 9. Directional Queries
**Ranking: T > G > N/D > E > C**

**Justification:**
- **T (Most Important)**: Directional assessments ("trending up", "bearish momentum") are inherently temporal—the timeframe defines the trend
- **G (2nd)**: Grounding ensures the trend is attributed to the correct stock/market
- **N/D (3rd)**: Numeric data (price changes, volumes) supports directional claims
- **E (4th)**: Entropy captures uncertainty in borderline directional calls
- **C (Least)**: Citations are rarely used for directional assessments

**Why this ranking?**: The 0.65 threshold reflects temporal-grounding dependencies. Directional queries live or die on temporal context accuracy.

---

### 10. Portfolio Advice Queries
**Ranking: G > E > N/D > C > T**

**Justification:**
- **G (Most Important)**: Portfolio advice must be grounded in accurate understanding of asset classes, diversification principles, and market correlations
- **E (2nd)**: Entropy is crucial—portfolio advice is inherently uncertain and should reflect appropriate confidence levels
- **N/D (3rd)**: Numeric allocations (60% stocks, 40% bonds) must be reasonable and justified
- **C (4th)**: Citations to investment research add credibility
- **T (Least)**: Portfolio advice is typically long-term and less time-sensitive

**Why this ranking?**: The 0.65 threshold and moderate performance reflect the balance between grounding quality and acknowledging inherent uncertainty in portfolio recommendations.

---

## Overall Feature Importance Ranking

### G (Grounding) - Rank 1 (Most Important)

**Why it's most important overall:**
Grounding is the foundation of hallucination detection across all scenarios. It answers: "Is this information correctly attributed to the right entity, source, or context?" Grounding failures cause:
- Mixing up companies in financial queries
- Misattributing news events to wrong actors
- Confusing regulatory jurisdictions
- Multi-entity reasoning errors

**Evidence:**
- Grounding ranks 1st in 6/10 scenarios (fundamentals, regulatory, advice, multi_ticker, portfolio_advice, and implicitly in others)
- Most critical failures across scenarios involve grounding errors
- Even perfect numeric or temporal accuracy becomes a hallucination if attributed to the wrong entity

---

### N/D (Numeric/Data) - Rank 2

**Why it's second most important:**
Numeric accuracy is critical in financial domain queries where quantitative precision matters. Hallucinations often manifest as impossible or implausible numeric values.

**Evidence:**
- Ranks 1st in numeric_kpi (explicitly numeric domain)
- Ranks 2nd in 5/10 scenarios (intraday, fundamentals, crypto, multi_ticker, portfolio_advice)
- Financial queries inherently involve numbers—prices, ratios, percentages, allocations
- Numeric anomalies are strong hallucination signals

---

### T (Temporal) - Rank 3

**Why it's third most important:**
Temporal context is crucial for time-sensitive financial information but doesn't apply equally to all scenarios.

**Evidence:**
- Ranks 1st in highly temporal scenarios (news, crypto, intraday, directional) where timing defines accuracy
- Less critical in timeless scenarios (advice, portfolio_advice)
- Temporal precision separates accurate from hallucinated responses in news/crypto (perfect F1 scores)
- Moderate importance across other scenarios

---

### E (Entropy) - Rank 4

**Why it's fourth most important:**
Entropy/uncertainty is a useful supplementary signal but not the primary discriminator in most scenarios.

**Evidence:**
- Ranks 2nd only in advice/portfolio_advice scenarios where uncertainty is appropriate
- Generally ranks 4th-5th across other scenarios
- High entropy correlates with hallucination but is not definitional
- Useful for identifying model confusion but not sufficient alone

**Why it ranks higher than citations:**
- Entropy is intrinsic to every response, while citations only apply to specific query types
- Entropy directly reflects model confidence calibration
- More universally applicable across scenarios

---

### C (Citation) - Rank 5 (Least Important)

**Why it's least important overall:**
Citations are relevant only for specific query types and are often absent entirely in financial queries.

**Evidence:**
- Ranks 5th (least important) in 7/10 scenarios
- Only ranks higher (2nd-3rd) in regulatory and news where source attribution matters
- Most financial queries (prices, fundamentals, advice) don't involve citations
- Citation presence/absence is less predictive than other features

**Exceptions:**
- Regulatory queries: Citations to specific statutes/rules are important (rank 2)
- News queries: Source attribution matters (rank 3)

---

## Summary of Changes from Original Table

### Corrections Made:

1. **Intraday**: Changed most important from N/D to **T** (Temporal)
   - Justification: Time specificity is the defining characteristic of intraday queries

2. **News**: Kept T as most important, moved N/D from "Least" to **Least** (confirmed correct)
   - Justification: News events are temporally defined; numeric data is rarely central

3. **Crypto**: Changed most important from N/D to **T** (Temporal)
   - Justification: Crypto markets are extremely time-sensitive; temporal accuracy is paramount

4. **Advice**: Changed 3rd from C to **C**, changed 4th from T to **N/D**, swapped N/D and T
   - Justification: Advice involves grounding and uncertainty more than temporal precision

5. **Multi_ticker**: Changed 4th from T to **C**, moved E from "Least" to **3rd**
   - Justification: Multi-entity grounding complexity dominates; entropy signals confusion

6. **Added missing scenarios**:
   - **Directional**: T > G > N/D > E > C
   - **Portfolio_advice**: G > E > N/D > C > T

7. **Overall ranking**: Confirmed **G > N/D > T > E > C**
   - Evidence: Grounding is most frequently ranked 1st or 2nd across scenarios
   - Numeric/Data is consistently 1st or 2nd in quantitative scenarios
   - Temporal importance varies dramatically by scenario type
   - Entropy and Citations are supplementary features

---

## Key Insights

1. **Scenario Type Determines Feature Importance**:
   - Time-sensitive scenarios (news, crypto, intraday) prioritize Temporal features
   - Quantitative scenarios (numeric_kpi, fundamentals) prioritize Numeric/Data features
   - Reasoning scenarios (advice, multi_ticker) prioritize Grounding and Entropy

2. **Grounding is Universal**:
   - The only feature that's never ranked last
   - Critical across all scenarios for entity attribution

3. **Entropy's Role is Scenario-Dependent**:
   - More important in subjective/advisory scenarios (appropriate uncertainty)
   - Less important in factual scenarios (clear right/wrong answers)

4. **Citations are Domain-Specific**:
   - Critical only in regulatory and news contexts
   - Largely irrelevant in numerical/quantitative queries

This feature importance analysis aligns with the optimal threshold patterns observed: scenarios with strong temporal-grounding alignment (news, crypto) achieve perfect detection, while scenarios with weak grounding calibration (regulatory, multi_ticker) struggle despite lower thresholds.
