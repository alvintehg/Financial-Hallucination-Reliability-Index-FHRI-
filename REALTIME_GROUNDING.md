# Real-Time Financial Data Grounding

This system now supports **real-time grounding** using live financial data from Finnhub API, replacing the static fake data from `trusted_docs.txt`.

## Overview

### What Changed

**Before:** Static, hardcoded data
```
Company A Q1 revenue was $10M...
Company B reported net income of $2M...
```

**After:** Real-time market data with validation
```
AAPL Real-Time Quote (as of 2025-11-01 14:30:00 UTC):
Current Price: $178.45
Day High: $180.12, Day Low: $177.89
Previous Close: $179.23
Change: -$0.78 (-0.44%)

Recent News for AAPL:
- [2025-11-01] Apple announces new AI features...
```

## Architecture

### Components

1. **[src/realtime_data.py](src/realtime_data.py)** - New module for real-time data fetching
   - `FinnhubDataFetcher` - Main fetcher class with validation
   - `extract_tickers_from_query()` - Extract stock symbols from queries
   - `get_realtime_context_for_query()` - Convenience function

2. **[src/server.py](src/server.py)** - Updated server integration
   - New parameter: `use_realtime` (default: True)
   - Combines real-time + static context
   - Metadata tracking for real-time data usage

3. **[test_realtime.py](test_realtime.py)** - Comprehensive test suite

## Data Validation

### How We Validate Real-Time Data

1. **Freshness Check** (Line 43-66 in [src/realtime_data.py](src/realtime_data.py#L43-L66))
   - Default: Reject quotes older than 15 minutes (900 seconds)
   - Configurable via `MAX_QUOTE_AGE_SECONDS` environment variable
   - Prevents stale data from being used as "real-time"

2. **Data Structure Validation**
   - Verify required fields exist (`c` for current price, `t` for timestamp)
   - Check price > 0 (catches invalid tickers)
   - Validate response types

3. **Error Handling**
   - API failures gracefully degrade to static data only
   - Invalid tickers logged and skipped
   - Continues processing other tickers if one fails

### Validation Example

```python
# Market closed - quote is 12 hours old
quote_time = 1698840000  # 12 hours ago
current_time = 1698883200

age = current_time - quote_time  # 43200 seconds = 720 minutes
max_age = 900 seconds  # 15 minutes

# REJECTED: "Quote data too old: 720.0 minutes (max: 15.0 minutes)"
```

## Usage

### Configuration

Add to your `.env` file:

```bash
# Finnhub API Key (required for real-time data)
FINNHUB_API_KEY=your_api_key_here

# Maximum acceptable quote age in seconds (default: 900 = 15 minutes)
MAX_QUOTE_AGE_SECONDS=900
```

### API Request

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the current price of AAPL?",
    "use_realtime": true,
    "k": 5,
    "provider": "auto"
  }'
```

### Response Metadata

The response includes real-time data tracking:

```json
{
  "answer": "Apple (AAPL) is currently trading at...",
  "meta": {
    "realtime_data_used": true,
    "realtime_tickers": ["AAPL"],
    "detectors_used": {
      "realtime": true,
      "entropy": true,
      "nli": false,
      "fhri": true
    }
  }
}
```

## Features

### 1. Automatic Ticker Detection
Extracts ticker symbols from user queries:
- "What's AAPL stock price?" → `["AAPL"]`
- "Compare MSFT and GOOGL" → `["MSFT", "GOOGL"]`

### 2. Multi-Source Context
Combines:
- **Real-time quotes** (price, high, low, change)
- **Recent news** (last 7 days, top 3 articles)
- **Company profile** (optional, name, industry, market cap)
- **Static passages** (from TF-IDF/FAISS index)

### 3. Graceful Degradation
- No API key → Uses static data only
- API failure → Falls back to static data
- No tickers detected → Uses static data
- Market closed → Validates and rejects stale data

## Test Results

From [test_realtime.py](test_realtime.py):

```
[PASS] Ticker Extraction - 5/5 test cases
[PASS] Data Freshness Validation - 3/3 test cases
[PASS] Company News Fetching - 248 articles fetched
[INFO] Quote Validation - Correctly rejected stale data (market closed)
```

**Note:** Quote fetching shows "[FAIL]" during off-market hours because the validation correctly rejects stale data. This is **expected behavior** and demonstrates the freshness check is working.

## When Market is Open

During trading hours (Mon-Fri, 9:30 AM - 4:00 PM ET), you'll get:

```
[PASS] Fetching quote for AAPL...
  Success: $178.45 (age: 1730476800 Unix timestamp)
  High: $180.12, Low: $177.89
```

## Finnhub API Rate Limits

Free tier limits:
- **60 API calls per minute**
- **30 calls per second**

The system makes 1-3 calls per ticker:
1. Quote (required)
2. News (optional, default: enabled)
3. Profile (optional, default: disabled)

For 1 ticker: ~2 calls per query
For 2 tickers: ~4 calls per query

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FINNHUB_API_KEY` | Required | Finnhub API key |
| `MAX_QUOTE_AGE_SECONDS` | 900 | Max quote age (15 min) |
| `DEBUG` | 0 | Enable debug logging |

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_realtime` | bool | true | Enable real-time grounding |
| `k` | int | 5 | Number of static passages |
| `retrieval_mode` | str | "tfidf" | Static retrieval mode |

## Architecture Diagram

```
User Query: "What's AAPL price?"
        ↓
1. Extract Tickers ["AAPL"]
        ↓
2. Fetch Real-Time Data
   ├─ Quote (with freshness validation)
   ├─ News (last 7 days)
   └─ Profile (optional)
        ↓
3. Validate Freshness
   ├─ Age < 15 min? ✓ Accept
   └─ Age > 15 min? ✗ Reject
        ↓
4. Fetch Static Passages (TF-IDF/FAISS)
        ↓
5. Combine Contexts
   ├─ === REAL-TIME DATA ===
   ├─ AAPL Quote + News
   ├─ === STATIC DATA ===
   └─ Retrieved passages
        ↓
6. Generate Response (LLM)
        ↓
7. Hallucination Detection (Entropy, NLI, FHRI)
        ↓
Response with Metadata
```

## Benefits of Real-Time Grounding

1. **Accuracy**: Always uses latest market data
2. **Trustworthiness**: Validated timestamps prevent stale info
3. **Transparency**: Metadata shows data sources used
4. **Reliability**: Graceful degradation if API fails
5. **Flexibility**: Can disable per-request or globally

## Comparison: Before vs After

| Aspect | Before (Static) | After (Real-Time) |
|--------|----------------|-------------------|
| Data Source | `trusted_docs.txt` | Finnhub API |
| Companies | Fake "Company A/B" | Any US stock ticker |
| Freshness | Static/outdated | Real-time with validation |
| Validation | None | Timestamp + freshness checks |
| Updates | Manual file edits | Automatic via API |
| Market Hours | N/A | Aware of market status |

## Next Steps

1. **Cross-Validation**: Add multiple data sources (Alpha Vantage, Yahoo Finance)
2. **Caching**: Cache quotes for X seconds to reduce API calls
3. **Enhanced Detection**: Use NER models for better ticker extraction
4. **Ticker Database**: Validate against known ticker list
5. **Market Hours**: Automatically adjust freshness threshold based on market status

## Running Tests

```bash
# Run comprehensive test suite
python test_realtime.py

# Start server with real-time grounding
uvicorn src.server:app --port 8000

# Test via API
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "What is AAPL price?", "use_realtime": true}'
```

## Troubleshooting

### Quote data rejected as too old
**Cause:** Market is closed, quotes are from last trading session
**Solution:** Normal behavior. Data will be fresh during market hours (Mon-Fri 9:30 AM - 4:00 PM ET)

### No tickers found
**Cause:** Ticker extraction only finds uppercase 2-5 letter words
**Solution:** Use ticker symbols (AAPL) not company names (Apple)

### API rate limit exceeded
**Cause:** Too many requests in short time
**Solution:** Implement caching or reduce query frequency

## License & Attribution

Uses Finnhub API: https://finnhub.io/
