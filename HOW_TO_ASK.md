# How to Ask Questions for Real-Time Stock Data

## ✅ CORRECT Ways to Ask

### Format 1: Company Name (✨ NEW - WORKS FOR ANY PUBLIC COMPANY!)
```
What is the price of Apple?
What is Microsoft stock price today?
How is Google doing?
Show me Tesla price
What is Coinbase worth?
What is Palantir trading at?
How is Snowflake stock doing?
Tell me about AMD performance
```

**New Feature:** The system now automatically resolves company names to ticker symbols using Finnhub's API! Works for virtually any publicly traded company.

### Format 2: Direct Ticker Symbol (ALSO WORKS)
```
What is the price of AAPL?
What is COIN stock price today?
How is MSFT doing?
Show me TSLA price
What is PLTR quote?
```

### Format 3: Multiple Tickers
```
Compare AAPL and MSFT performance
What are the prices for COIN and GOOGL?
```

### Format 4: Stock-Related Keywords
Any question with these keywords will trigger better ticker detection and enable company name lookup:
- **stock** - "Palantir stock price"
- **ticker** - "ticker COIN"
- **price** - "price of Snowflake"
- **quote** - "get quote for AMD"
- **share** - "COIN share value"
- **symbol** - "symbol PLTR"
- **trading** - "What is Tesla trading at?"
- **market** - "How is Apple in the market?"

## ❌ WRONG Ways to Ask

### ❌ Lowercase Company Names (Won't Match)
```
❌ What is the price of apple? (lowercase - won't trigger lookup)
❌ How is microsft doing? (misspelled)

✅ What is the price of Apple? (capitalized - will trigger lookup)
✅ How is Microsoft doing?
```

**Important:** Company names must be **properly capitalized** to trigger the API lookup. "Apple" works, "apple" doesn't.

### ❌ Lowercase Tickers (Won't Detect)
```
❌ What is the price of coin?
❌ How is aapl doing?

✅ What is the price of COIN?
✅ How is AAPL doing?
```

### ❌ Missing Stock Context (API Lookup Won't Trigger)
```
❌ "Tell me about Palantir" (no stock keywords)
❌ "What is Snowflake?" (ambiguous)

✅ "What is Palantir stock price?" (has "stock" + "price")
✅ "How is Snowflake trading?" (has "trading")
```

## 📋 Common Stock Tickers

| Company | Ticker | Query with Name | Query with Ticker |
|---------|--------|-----------------|-------------------|
| Coinbase | COIN | "What is Coinbase price?" | "What is COIN price?" |
| Apple | AAPL | "How is Apple doing?" | "How is AAPL doing?" |
| Microsoft | MSFT | "Microsoft stock price today" | "MSFT stock price today" |
| Google/Alphabet | GOOGL | "What is Google trading at?" | "What is GOOGL trading at?" |
| Tesla | TSLA | "Tesla current price" | "TSLA current price" |
| Palantir | PLTR | "Palantir quote" | "PLTR quote" |
| Snowflake | SNOW | "Snowflake stock price" | "SNOW stock price" |
| AMD | AMD | "How is AMD performing?" | "How is AMD performing?" |
| NVIDIA | NVDA | "Nvidia stock" | "NVDA stock" |

**✨ Both columns work now!** You can use either the company name or the ticker symbol.

## 🔍 How the System Detects Tickers (3-Tier Approach)

The system uses a **smart 3-tier detection system**:

### Tier 1: Static Company Mapping (Fast)
- Pre-configured mappings for ~40 major companies
- No API call needed
- Examples: "Apple" → AAPL, "Microsoft" → MSFT, "Coinbase" → COIN

### Tier 2: Uppercase Ticker Symbols (Fast)
- Detects uppercase ticker symbols directly (1-5 characters)
- Examples: COIN, AAPL, MSFT, PLTR
- Filters out common words (THE, AND, WHAT, etc.)

### Tier 3: Finnhub Symbol Lookup API (Fallback)
- **✨ NEW:** Resolves any company name to ticker symbol
- Uses Finnhub's real-time symbol search
- Cached results to avoid repeated API calls
- Examples: "Palantir" → PLTR, "Snowflake" → SNOW

### Detection Examples

```python
"What is the price for COIN today?"
→ Tier 2 Match: ['COIN'] ✅

"What is Apple stock price?"
→ Tier 1 Match: ['AAPL'] ✅ (static mapping)

"How is Palantir doing?"
→ Tier 3 Match: ['PLTR'] ✅ (API lookup)

"What is coinbase price?"
→ No Match: [] ❌ (lowercase, no stock context)

"Tell me about Palantir"
→ No Match: [] ❌ (no stock keywords like "price", "stock")

"What is Palantir stock price?"
→ Tier 3 Match: ['PLTR'] ✅ (API lookup triggered by "stock" + "price")
```

**Important:** For API lookup to work, your query must contain stock-related keywords like "stock", "price", "quote", "trading", etc.

## ⏰ Market Hours & Data Freshness

### During Market Hours (Mon-Fri 9:30 AM - 4:00 PM ET)
You'll get **live quotes** marked as `[Live]`:
```
COIN Stock Quote [Live] (as of 2025-11-01 14:30:00 UTC):
Price: $343.78
```

### Outside Market Hours
You'll get **last closing price** marked as `[Last Close - Market Closed]`:
```
COIN Stock Quote [Last Close - Market Closed] (as of 2025-11-01 04:00:00 UTC):
Price: $343.78
```

**Note:** The system validates data freshness:
- During market hours: Rejects quotes older than 15 minutes
- Outside market hours: Provides last close price with disclaimer

## 🎯 Example Queries That Work Well

### Single Ticker Queries
```
"What is the current price of AAPL?"
"How is COIN performing today?"
"MSFT stock quote"
"Tell me about TSLA stock"
"Get me the price for GOOGL"
```

### Multiple Ticker Queries
```
"Compare AAPL and MSFT"
"What are the prices for COIN, AAPL, and TSLA?"
"How do GOOGL and META compare?"
```

### With Context
```
"Is COIN a good buy right now?"
"Should I invest in AAPL stock?"
"What's happening with TSLA today?"
"Analysis of MSFT performance"
```

## 🔧 Troubleshooting

### Problem: "Sources do not contain information"

**Possible Causes:**
1. Ticker not in uppercase → Use `COIN` not `coin`
2. Company name not capitalized → Use `Palantir` not `palantir`
3. Missing stock context → Add keywords like "stock", "price", "quote", "trading"
4. Company not publicly traded → Only works for public companies

**Solutions:**
```
Instead of: "What is coinbase price?"
Try this:   "What is COIN stock price?" (uppercase ticker)
       OR:  "What is Coinbase stock price?" (capitalized company name)

Instead of: "Tell me about Palantir"
Try this:   "What is Palantir stock price?" (add stock keywords)

Instead of: "What is palantir doing?"
Try this:   "What is Palantir stock doing?" (capitalize + stock keyword)
```

### Problem: Response shows old data

**Cause:** Market is closed (outside trading hours)

**Expected Behavior:** System shows `[Last Close - Market Closed]` label

**Solution:** This is normal! You're getting the most recent closing price.

### Problem: No real-time data at all

**Check:**
1. Is `use_realtime` parameter set to `true`? (default is true)
2. Is Finnhub API key configured in `.env`?
3. Check server logs for errors

## 📊 What Data You Get

For each ticker, you receive:

### 1. Stock Quote
- Current/Last price
- Day high and low
- Previous close
- Price change ($ and %)
- Timestamp
- Market status (Live or Closed)

### 2. Recent News (Last 7 Days)
- Top 3 recent articles
- Headlines and sources
- Publication dates

### 3. FHRI Reliability Score
- Grounding score
- Numerical accuracy
- Temporal consistency
- Citation quality

## 🚀 Quick Reference Card

```
✅ DO:
- Use UPPERCASE ticker symbols
- Include stock-related keywords
- Be specific with ticker symbols

❌ DON'T:
- Use company names instead of tickers
- Use lowercase letters
- Mix up similar company tickers

EXAMPLES:
Good: "What is COIN price?"
Good: "How is AAPL stock doing?"
Good: "Compare MSFT and GOOGL"

Bad:  "What is coinbase price?"
Bad:  "How is apple doing?"
Bad:  "Compare Microsoft and Google"
```

## 📝 Finding Ticker Symbols

If you don't know a ticker symbol:

1. **Google**: Search "company name ticker symbol"
2. **Yahoo Finance**: https://finance.yahoo.com
3. **Finnhub**: https://finnhub.io/
4. **Common Pattern**: Usually 1-5 uppercase letters

## 💡 Pro Tips

1. **✨ Company names now work!** - "Palantir stock price" is just as good as "PLTR stock price"
2. **Capitalize company names** - "Palantir" works, "palantir" doesn't
3. **Add stock keywords** - Words like "stock", "price", "quote" help detection and enable API lookup
4. **Keep it simple** - "COIN price" or "Coinbase price" both work great
5. **Multiple tickers** - You can ask about multiple stocks in one question
6. **Check market hours** - Live data only available during trading hours
7. **Use ticker for speed** - Ticker symbols (PLTR) are faster than company names (no API call)

## 🎓 Learning Resources

- [Stock Market Basics](https://www.investopedia.com/terms/s/stock.asp)
- [How to Read Stock Quotes](https://www.investopedia.com/investing/how-read-stock-quotes/)
- [List of NASDAQ Tickers](https://www.nasdaq.com/market-activity/stocks/screener)
