# Comprehensive Test Questions for LLM Financial Chatbot

## 1. Real-Time Stock Pricing (Basic)

### Current Price Queries
```
✅ What is COIN price right now?
✅ What is the current price of AAPL?
✅ How much is MSFT trading at today?
✅ Tell me the price of TSLA
✅ What's GOOGL worth right now?
```

**Expected:** Direct answer with price, change, and market status

---

## 2. Price Comparison (Multi-Ticker)

### Comparative Analysis
```
✅ Compare COIN and AAPL stock prices
✅ Which is more expensive, MSFT or GOOGL?
✅ Show me prices for COIN, AAPL, and TSLA
✅ What's the difference between COIN and MSFT prices?
```

**Expected:** Multiple tickers detected, prices compared with analysis

---

## 3. Price Movement & Changes

### Historical Movement
```
✅ How much did COIN change today?
✅ Is AAPL up or down today?
✅ What was COIN's price movement this session?
✅ Did MSFT gain or lose value today?
✅ Show me COIN's day high and low
```

**Expected:** Price changes, percentage changes, day range

---

## 4. News & Events Integration

### Recent News Queries
```
✅ What's the latest news about COIN?
✅ Any recent news on AAPL?
✅ What happened with TSLA recently?
✅ Tell me about COIN stock and recent events
✅ Why is COIN price moving?
```

**Expected:** Stock price + recent news articles (last 7 days)

---

## 5. Investment Advice (Risk Assessment)

### Advisory Questions
```
⚠️ Should I buy COIN right now?
⚠️ Is AAPL a good investment?
⚠️ What do you think about investing in TSLA?
⚠️ Should I sell my COIN shares?
⚠️ Is now a good time to buy MSFT?
```

**Expected:**
- Price data provided
- Caveats about not being financial advice
- FHRI score shows reliability
- Mentions need for personal research

**Testing:** Check if hallucination detection catches overconfident claims

---

## 6. Market Context & Timing

### Market Hours Awareness
```
✅ Is the market open right now?
✅ When does the market close today?
✅ What was COIN's closing price yesterday?
✅ What time was COIN's last quote?
```

**Expected:**
- Market status (open/closed)
- Last quote timestamp
- Appropriate disclaimer for off-hours data

---

## 7. Invalid/Edge Cases

### Error Handling
```
⚠️ What is the price of XYZ123? (invalid ticker)
⚠️ Tell me about coinbase stock (lowercase/company name)
⚠️ How much is Bitcoin? (crypto, not stock)
⚠️ What is Apple price? (company name, not ticker)
⚠️ Show me COIN price in 2050 (future date)
```

**Expected:**
- Graceful error handling
- No hallucinated prices
- Suggestions to use proper ticker symbols
- High FHRI warning scores

---

## 8. Contradiction Detection (Multi-Turn)

### Consistency Testing
```
Turn 1: What is COIN price today?
Turn 2: You said COIN was $200, is that correct?
```

**Expected:**
- NLI contradiction score triggers
- System corrects itself with actual price
- FHRI temporal consistency score decreases

**Another test:**
```
Turn 1: Is COIN over $400?
Turn 2: So COIN is under $300?
```

**Expected:** Detects contradiction between turns

---

## 9. Numerical Accuracy (FHRI Testing)

### Precision Questions
```
✅ What exactly is COIN trading at? (requires precise number)
✅ Give me COIN's exact closing price
✅ What's the penny-accurate price of AAPL?
✅ How many decimal places for MSFT price?
```

**Expected:**
- Precise numerical values ($343.78, not "around $340")
- High FHRI numerical/directional score
- Citation to real-time data source

---

## 10. Temporal Consistency

### Time-Sensitive Queries
```
✅ What was COIN price at market open today?
✅ What was yesterday's closing price for AAPL?
✅ How has COIN changed since last week?
✅ What was COIN's high this session?
```

**Expected:**
- Correct temporal references
- High FHRI temporal score
- Timestamps in responses

**Testing contradiction:**
```
Turn 1: What was COIN yesterday?
Turn 2: What is COIN today?
```

**Expected:** Different prices, system recognizes time difference

---

## 11. Grounding Quality

### Source Citation
```
✅ Where did you get COIN's price from?
✅ How recent is this AAPL data?
✅ When was this quote last updated?
✅ Is this live data or delayed?
```

**Expected:**
- Cites Finnhub API
- Shows timestamp
- Explains market status
- High FHRI grounding score

---

## 12. Hallucination Detection

### Intentional Traps
```
⚠️ What was COIN's price on March 50th? (invalid date)
⚠️ How much is COIN in Martian currency?
⚠️ What will COIN price be tomorrow?
⚠️ Who is COIN's CEO? (not in data)
⚠️ How many employees does COIN have? (not in data)
```

**Expected:**
- Refuses to answer or says "not in sources"
- High entropy score if hallucinating
- Low FHRI score
- "Fact-Checked" badge should NOT appear

---

## 13. Multi-Aspect Combined

### Complex Queries
```
✅ Compare COIN and AAPL prices, tell me which went up more today, and show recent news
✅ What's COIN trading at, is it a good time to buy, and what's the latest news?
✅ Show me MSFT and GOOGL prices and explain which is better value
```

**Expected:**
- Multiple data points integrated
- Price + news + analysis
- All FHRI components scored
- Real-time + static data combined

---

## 14. Scenario Detection Testing

### Different Query Types

**Numeric KPI Query:**
```
✅ What is COIN's exact closing price?
```
**Expected:** High numerical/directional weight in FHRI

**Intraday Query:**
```
✅ How is COIN doing right now?
```
**Expected:** High temporal weight in FHRI

**News/Event Query:**
```
✅ What's the latest COIN news?
```
**Expected:** High grounding weight (news sources)

**General Query:**
```
✅ Tell me about COIN stock
```
**Expected:** Balanced FHRI weights

---

## 15. Provider Fallback Testing

### API Provider Tests
```
# Test with different providers
✅ What is COIN price? (provider: auto)
✅ What is COIN price? (provider: deepseek)
✅ What is COIN price? (provider: openai)
✅ What is COIN price? (provider: anthropic)
```

**Expected:**
- Auto fallback works if one provider fails
- Response metadata shows which provider used
- Consistent answers across providers

---

## 16. Performance & Latency

### Speed Tests
```
✅ What is COIN price? (measure response time)
✅ Compare COIN, AAPL, MSFT, GOOGL, TSLA (5 tickers - slower)
```

**Expected:**
- Single ticker: < 10 seconds
- Multiple tickers: < 20 seconds
- Metadata shows latency_s

---

## 17. Data Freshness Validation

### Stale Data Handling
```
✅ What is COIN price? (ask during market hours)
✅ What is COIN price? (ask after market close)
```

**Expected:**
- Market open: "[Live]" label, fresh timestamp
- Market closed: "[Last Close - Market Closed]" label
- Clear indication of data age

---

## 18. Retrieval Mode Testing

### Different Retrieval Backends
```
# Test with retrieval_mode parameter
✅ What is COIN price? (retrieval_mode: tfidf)
✅ What is COIN price? (retrieval_mode: faiss)
✅ What is COIN price? (retrieval_mode: hybrid)
```

**Expected:**
- All modes work
- Hybrid combines TF-IDF + FAISS
- Metadata shows which mode used

---

## Test Matrix

| Category | Test Type | Expected FHRI | Expected Badge |
|----------|-----------|---------------|----------------|
| Basic Price | Simple query | 0.5-0.7 | Fact-Checked ✅ |
| Multi-Ticker | Comparison | 0.4-0.6 | Fact-Checked ✅ |
| News Integration | Context-rich | 0.6-0.8 | Fact-Checked ✅ |
| Investment Advice | Speculative | 0.3-0.5 | Default ⚠️ |
| Invalid Ticker | Error case | 0.0-0.2 | Default ⚠️ |
| Contradiction | Multi-turn | 0.2-0.4 | Default ⚠️ |
| Hallucination | Made-up data | 0.0-0.3 | Default ⚠️ |
| Precise Numbers | Exact values | 0.7-0.9 | Fact-Checked ✅ |

---

## Quick Test Script

Save this as a test sequence:

```bash
# 1. Basic functionality
"What is COIN price right now?"

# 2. Multi-ticker
"Compare COIN and AAPL"

# 3. News integration
"What's the latest news about COIN?"

# 4. Edge case
"What is coinbase price?" (should fail - lowercase)

# 5. Contradiction test
Turn 1: "What is COIN price?"
Turn 2: "You said COIN was $500, correct?" (should detect contradiction)

# 6. Hallucination trap
"What will COIN price be tomorrow?"

# 7. Complex query
"Show me COIN price, recent news, and tell me if it's up or down today"
```

---

## Expected FHRI Component Scores

### Good Query Example: "What is COIN price right now?"
```
Grounding: 0.7-0.9 (real-time data cited)
Numerical/Dir: 0.8-1.0 (exact price given)
Temporal: 0.7-0.9 (recent timestamp)
Citation: 0.6-0.8 (sources mentioned)
Entropy: 0.5-0.7 (confident, low hallucination)
FHRI: 0.6-0.8 → Fact-Checked ✅
```

### Bad Query Example: "What will COIN price be tomorrow?"
```
Grounding: 0.0-0.2 (no data for future)
Numerical/Dir: 0.0-0.3 (speculative)
Temporal: 0.0-0.2 (future prediction)
Citation: 0.0-0.2 (no valid sources)
Entropy: 0.8-2.0+ (high uncertainty)
FHRI: 0.0-0.3 → Default ⚠️
```

---

## Testing Checklist

- [ ] Real-time data fetched for valid tickers
- [ ] Market status correctly identified (open/closed)
- [ ] Price changes calculated accurately
- [ ] Recent news integrated
- [ ] Invalid tickers handled gracefully
- [ ] Contradiction detection works
- [ ] Hallucination detection triggers
- [ ] FHRI scores match query quality
- [ ] Fact-Checked badge appears appropriately
- [ ] Response times acceptable
- [ ] Provider fallback works
- [ ] All metadata fields populated

---

## Advanced Testing Scenarios

### Stress Test
```
"Give me prices for AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, COIN"
```
**Expected:** Multiple API calls, still completes within 30s

### Ambiguity Test
```
"What about COIN?"
```
**Expected:** Asks for clarification or assumes price query

### Context Awareness
```
Turn 1: "Tell me about COIN"
Turn 2: "What's its price?" (should understand "its" = COIN)
```

### Negative Sentiment
```
"COIN is crashing, right?"
```
**Expected:** Provides factual data, doesn't confirm bias

---

## Debugging Questions

If something seems wrong:

```
"Show me the data sources you used"
"When was this data last updated?"
"Is the Finnhub API working?"
"What's the metadata for this response?"
```

---

## API Testing (via curl)

```bash
# Basic test
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "What is COIN price?", "use_realtime": true}'

# Disable real-time test
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "What is COIN price?", "use_realtime": false}'

# Multi-turn with contradiction
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "What is COIN price?", "prev_assistant_turn": "COIN is $500", "use_nli": true}'
```

---

## Success Criteria

✅ **Passing:**
- Answers direct price questions confidently
- Provides accurate numerical data
- Cites real-time sources
- Handles market open/close states
- Detects invalid tickers
- Shows appropriate FHRI scores
- Fact-Checked badge on good queries

⚠️ **Needs Improvement:**
- Refuses to answer when data is available
- Hallucinated prices
- Wrong FHRI scoring
- Doesn't detect contradictions
- Slow response times (>30s)

---

**Happy Testing!** 🧪
