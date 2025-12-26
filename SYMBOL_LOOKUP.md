# Company Name to Ticker Symbol Lookup

## Overview

The system now supports **automatic company name resolution** using Finnhub's Symbol Lookup API. You can ask about virtually any publicly traded company using its name, and the system will automatically find the ticker symbol.

## How It Works

The system uses a **3-tier approach** to detect ticker symbols:

### Tier 1: Static Company Mapping (Fastest)
- Pre-configured mappings for ~40 major companies
- No API call required
- Examples: "Apple" → AAPL, "Microsoft" → MSFT, "Microstrategy" → MSTR

### Tier 2: Uppercase Ticker Symbols (Fast)
- Detects uppercase ticker symbols directly
- Examples: "AAPL", "MSFT", "PLTR"

### Tier 3: Finnhub Symbol Lookup API (Fallback)
- Resolves company names not in static mapping
- Uses real-time symbol search
- Cached results to avoid repeated API calls
- Examples: "Palantir" → PLTR, "Snowflake" → SNOW

## Supported Query Formats

All of these will work:

```
✅ "What is the price for Palantir?"
✅ "How is Snowflake doing?"
✅ "Tell me about AMD stock"
✅ "What is PLTR price?"
✅ "Compare Apple and Microsoft"
✅ "What is Microstrategy trading at?"
✅ "How is Advanced Micro Devices performing?"
```

## Examples

### Example 1: Using Company Name
**Query:** "What is the price for Palantir?"

**What happens:**
1. System checks static mapping → Not found
2. System checks for uppercase tickers → Not found
3. System calls Finnhub API: `client.symbol_lookup('Palantir')`
4. API returns: `{'symbol': 'PLTR', 'description': 'Palantir Technologies Inc', ...}`
5. System fetches real-time data for PLTR
6. Result cached for future queries

### Example 2: Using Ticker Symbol
**Query:** "What is PLTR price?"

**What happens:**
1. System checks static mapping → Not found
2. System detects uppercase ticker "PLTR" → Found!
3. System fetches real-time data for PLTR
4. No API lookup needed

### Example 3: Using Common Company Name
**Query:** "What is Apple price?"

**What happens:**
1. System checks static mapping → Found: APPLE → AAPL
2. System fetches real-time data for AAPL
3. No API lookup needed

## Caching

The symbol lookup results are **cached in memory** to avoid repeated API calls:

```python
# First query - calls API
"What is Palantir price?" → API lookup → PLTR

# Subsequent queries - uses cache
"What is Palantir doing?" → Cache hit → PLTR (no API call)
"How is Palantir stock?" → Cache hit → PLTR (no API call)
```

Cache persists for the lifetime of the server process.

## Limitations

1. **Only works for publicly traded companies**
   - Private companies like Databricks won't be found
   - API will return no results for private companies

2. **Requires stock context keywords**
   - Query must contain words like: "price", "stock", "share", "quote", "trading", "market"
   - This prevents false positives (e.g., "What is Palantir?" without stock context)

3. **API rate limits**
   - Symbol lookup counts against your Finnhub API rate limit
   - Caching helps minimize API calls

4. **Best match is used**
   - If a company name matches multiple tickers, the first (most relevant) result is used
   - Example: "Google" might return GOOGL instead of GOOG

## Technical Details

### Symbol Lookup Function

```python
def resolve_company_name_to_ticker(company_name: str, api_key: str, use_cache: bool = True) -> Optional[str]:
    """
    Resolve a company name to its ticker symbol using Finnhub's symbol lookup API.

    Returns:
        Ticker symbol if found (e.g., "PLTR"), None otherwise
    """
```

### Enhanced Ticker Extraction

```python
def extract_tickers_from_query(query: str, api_key: Optional[str] = None) -> List[str]:
    """
    Extract potential stock ticker symbols from user query.

    Enhanced heuristic with API fallback:
    1. Check static company name mapping (fast, no API call)
    2. Match uppercase ticker symbols (1-5 chars)
    3. Use Finnhub symbol lookup API for unrecognized company names (if api_key provided)
    """
```

### False Positive Filtering

The system filters out common question words to avoid false positives:
- "What", "How", "Why", "When", "Where", "Which", "Who"
- "Tell", "Show", "Give", "Compare", "Explain"

Example:
- "What is Palantir price?" → Detects "Palantir" (not "What")
- "Tell me about Snowflake" → Detects "Snowflake" (not "Tell")

## Testing

Run the test suite to verify symbol lookup:

```bash
cd "c:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"

# Test ticker extraction
python -c "
from src.realtime_data import extract_tickers_from_query
api_key = 'd3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag'

queries = [
    'What is the price for Palantir?',
    'How is Snowflake doing?',
    'What is AMD price?'
]

for query in queries:
    tickers = extract_tickers_from_query(query, api_key=api_key)
    print(f'{query} -> {tickers}')
"

# Test full context fetch
python -c "
from src.realtime_data import get_realtime_context_for_query
api_key = 'd3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag'

context = get_realtime_context_for_query('What is Palantir price?', api_key=api_key)
print(context[:500])
"
```

## Environment Variables

No new environment variables required. Uses existing `FINNHUB_API_KEY`:

```bash
FINNHUB_API_KEY=your_api_key_here
```

## Integration

The symbol lookup is **automatically integrated** into the existing data fetching pipeline:

1. User asks: "What is Palantir price?"
2. Server calls: `get_realtime_context_for_query(query, api_key)`
3. Function calls: `extract_tickers_from_query(query, api_key)`
4. Symbol lookup runs if needed
5. Real-time data fetched for resolved ticker
6. Context returned to LLM

**No code changes needed** - just upgrade and restart the server!

## Performance

- **Static mapping**: ~1ms (no API call)
- **Uppercase ticker**: ~1ms (no API call)
- **Symbol lookup API**: ~100-300ms (first query)
- **Cached lookup**: ~1ms (subsequent queries)

## FAQ

**Q: Do I need to add every company to the static mapping?**
A: No! The API lookup automatically handles any publicly traded company.

**Q: What if the company name is ambiguous?**
A: Finnhub returns the most relevant result. You can always use the exact ticker symbol for precision.

**Q: Does this work for cryptocurrencies?**
A: No, this is for stocks only. Crypto uses a separate module (`crypto_data.py`).

**Q: Can I disable the API lookup?**
A: Yes, just don't pass the `api_key` parameter to `extract_tickers_from_query()`.

**Q: How do I clear the cache?**
A: Restart the server. The cache is in-memory only.

## Changelog

### 2025-11-02
- Added Finnhub symbol lookup API integration
- Implemented in-memory caching for lookups
- Enhanced ticker extraction with 3-tier approach
- Added false positive filtering for question words
- Updated documentation

---

For more information, see:
- [HOW_TO_ASK.md](HOW_TO_ASK.md) - User guide for asking questions
- [REALTIME_GROUNDING.md](REALTIME_GROUNDING.md) - Real-time data system overview
- [TEST_QUESTIONS.md](TEST_QUESTIONS.md) - Comprehensive testing guide
