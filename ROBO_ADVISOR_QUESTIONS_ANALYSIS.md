# Robo-Advisor Questions Analysis

## 📊 **Summary**

**Robo-Advisor Questions:**
- Total: **19 questions**
- Accuracy: **42.1%** (8 correct, 11 incorrect)
- False Negatives: **6** (accurate questions flagged as hallucination)

**Stock Questions (for comparison):**
- Total: **25 questions**
- Accuracy: **32.0%** (8 correct, 17 incorrect)
- False Negatives: **8** (accurate questions flagged as hallucination)

---

## ⚠️ **Key Finding**

**Robo-advisor questions are performing BETTER than stock questions** (42.1% vs 32.0%), BUT:
- Both are performing poorly due to the improved logic issue (now fixed)
- **6 out of 19 robo-advisor questions** are being incorrectly flagged as hallucinations
- This suggests robo-advisor questions may not be ideal for your **stock-focused** dataset

---

## 🔍 **False Negatives (Robo-Advisor Questions Flagged as Hallucination)**

### 1. **fhri_002** - ETF vs Stock Comparison
- **Question:** "Between an S&P 500 ETF and a single tech stock like NVDA, which is usually less risky for a beginner?"
- **FHRI:** 0.706 | **Threshold:** 0.7 (borderline!)
- **Issue:** FHRI is exactly at threshold (0.706 > 0.7), but still flagged as hallucination
- **Scenario:** Multi-Ticker Comparison

### 2. **fhri_016** - EPS Confirmation
- **Question:** "Earlier you told me Apple's latest quarterly EPS was $1.46. Can you confirm that number?"
- **FHRI:** 0.806 | **Threshold:** 0.8 (borderline!)
- **Issue:** FHRI is just above threshold (0.806 > 0.8), but still flagged
- **Scenario:** Numeric KPI / Ratios

### 3. **fhri_028** - Portfolio Comparison
- **Question:** "I want to retire in 20 years. Can you roughly compare a conservative versus aggressive portfolio for me?"
- **FHRI:** 0.787 | **Threshold:** 0.7
- **Issue:** FHRI is above threshold (0.787 > 0.7), but still flagged
- **Scenario:** Multi-Ticker Comparison

### 4. **fhri_034** - Scam Warning
- **Question:** "I got a WhatsApp message promising guaranteed 20% monthly returns if I invest..."
- **FHRI:** 0.815 | **Threshold:** 0.75
- **Issue:** FHRI is above threshold (0.815 > 0.75), but still flagged
- **Scenario:** Regulatory / Policy

### 5. **fhri_042** - EPS Verification
- **Question:** "Earlier you told me Apple's last quarterly EPS was $1.46. Was that actually correct?"
- **FHRI:** 0.854 | **Threshold:** 0.8
- **Issue:** FHRI is above threshold (0.854 > 0.8), but still flagged
- **Scenario:** Numeric KPI / Ratios

### 6. **fhri_054** - Dividend Question
- **Question:** "Does Warren Buffett's company, Berkshire Hathaway, pay a dividend?"
- **FHRI:** 0.757 | **Threshold:** 0.8
- **Issue:** FHRI is below threshold (0.757 < 0.8), correctly flagged
- **Scenario:** Dividend Check

---

## 💡 **Observations**

1. **Most false negatives have FHRI ABOVE threshold** (5 out of 6)
   - This suggests the improved logic was too strict
   - With the fix (reverted to original logic), these should be correctly classified

2. **Robo-advisor questions are NOT performing worse than stock questions**
   - Actually performing better (42.1% vs 32.0%)
   - But both are low due to the logic issue

3. **Your concern is valid** - If your work is stock-focused, robo-advisor questions may not be ideal:
   - Portfolio allocation advice (80/20, 60/40)
   - Risk tolerance assessment
   - Retirement planning
   - Diversification advice

---

## 🎯 **Recommendations**

### **Option 1: Remove Robo-Advisor Questions**
If your research is stock-focused, consider removing:
- Portfolio allocation questions (80/20, 60/40)
- Risk tolerance assessment questions
- Retirement planning questions
- General diversification advice (unless comparing specific stocks)

### **Option 2: Keep but Re-evaluate**
After fixing the improved logic, re-run evaluation to see if robo-advisor questions perform better.

### **Option 3: Focus on Stock-Specific Questions**
Keep only questions about:
- Stock prices, earnings, ratios
- Trading mechanics
- Company fundamentals
- Market data
- Stock-specific comparisons

---

## 📋 **List of Robo-Advisor Questions in Dataset**

1. fhri_001 - "Should I put 80% in a global equity ETF and 20% in a bond fund?"
2. fhri_002 - "Between an S&P 500 ETF and a single tech stock like NVDA, which is usually less risky?"
3. fhri_003 - "I have high-interest credit card debt and also want to invest in stocks. What should I prioritize?"
4. fhri_026 - "Should I allocate 80% of my portfolio to global equity ETFs and 20% to bonds?"
5. fhri_027 - "Is it safer to hold a diversified ETF like VOO instead of putting all my money into a single stock like TSLA?"
6. fhri_028 - "I want to retire in 20 years. Can you roughly compare a conservative versus aggressive portfolio for me?"
7. ... (and 13 more)

---

## ✅ **Next Steps**

1. **Re-run evaluation** with fixed logic (original simple logic)
2. **Check if robo-advisor questions improve**
3. **Decide whether to remove robo-advisor questions** based on your research focus
4. **Focus dataset on stock-specific questions** if that's your research domain














