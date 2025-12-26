# src/realtime_data.py
"""
Real-time financial data fetcher with validation and freshness checks.

Features:
- Fetch live data from Finnhub API (stock quotes, company news, fundamentals)
- Validate data freshness (reject stale data)
- Cross-validation support (compare across multiple sources)
- Error handling and fallback mechanisms
- Rate limiting awareness

Public API:
- get_realtime_context(ticker: str, api_key: str) -> str
- validate_quote_freshness(quote: dict, max_age_seconds: int) -> bool
- fetch_stock_quote(ticker: str, api_key: str) -> dict
- fetch_company_news(ticker: str, api_key: str, days_back: int) -> list
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import finnhub

logger = logging.getLogger("realtime_data")

# Global cache for symbol lookups to avoid repeated API calls
_SYMBOL_CACHE: Dict[str, Optional[str]] = {}


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class FinnhubDataFetcher:
    """
    Real-time financial data fetcher with validation.

    Handles:
    - Live stock quotes with timestamp validation
    - Company news with date filtering
    - Fundamental data
    - Data freshness checks
    """

    def __init__(self, api_key: str, max_quote_age_seconds: int = 900):
        """
        Initialize Finnhub data fetcher.

        Args:
            api_key: Finnhub API key
            max_quote_age_seconds: Maximum age for quote data (default 15 minutes)
        """
        self.client = finnhub.Client(api_key=api_key)
        self.max_quote_age = max_quote_age_seconds
        logger.info(f"Initialized FinnhubDataFetcher (max_quote_age={max_quote_age_seconds}s)")

    def validate_quote_freshness(self, quote: Dict[str, Any]) -> bool:
        """
        Validate that quote data is fresh enough to use.

        Args:
            quote: Quote dict with 't' (timestamp) field

        Returns:
            True if fresh, False otherwise

        Raises:
            DataValidationError: If quote is too old or missing timestamp
        """
        if 't' not in quote:
            raise DataValidationError("Quote missing timestamp field 't'")

        quote_time = quote['t']
        current_time = time.time()
        age_seconds = current_time - quote_time

        if age_seconds < 0:
            raise DataValidationError(f"Quote timestamp is in the future (clock skew?)")

        if age_seconds > self.max_quote_age:
            age_minutes = age_seconds / 60
            raise DataValidationError(
                f"Quote data too old: {age_minutes:.1f} minutes "
                f"(max: {self.max_quote_age/60:.1f} minutes)"
            )

        logger.debug(f"Quote freshness validated (age: {age_seconds:.1f}s)")
        return True

    def fetch_stock_quote(self, ticker: str, validate_freshness: bool = True,
                          allow_stale_if_closed: bool = True) -> Dict[str, Any]:
        """
        Fetch real-time stock quote.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            validate_freshness: Whether to validate data freshness
            allow_stale_if_closed: If True, allow stale quotes outside market hours with warning

        Returns:
            Quote dict with fields: c (current price), h (high), l (low), o (open), pc (prev close), t (timestamp)

        Raises:
            DataValidationError: If data validation fails
            RuntimeError: If API call fails
        """
        try:
            logger.info(f"Fetching quote for {ticker}")
            quote = self.client.quote(ticker)

            # Validate response structure
            if not isinstance(quote, dict):
                raise RuntimeError(f"Invalid quote response type: {type(quote)}")

            required_fields = ['c', 't']
            missing_fields = [f for f in required_fields if f not in quote]
            if missing_fields:
                raise RuntimeError(f"Quote missing required fields: {missing_fields}")

            # Check if we got valid data (current price should be > 0)
            if quote.get('c', 0) <= 0:
                raise RuntimeError(f"Invalid quote data for {ticker}: current price is {quote.get('c')}")

            # Validate freshness if requested
            if validate_freshness:
                try:
                    self.validate_quote_freshness(quote)
                    logger.info(f"Quote fetched successfully for {ticker}: ${quote['c']}")
                except DataValidationError as e:
                    if allow_stale_if_closed:
                        # Market might be closed, allow stale data but add warning flag
                        quote['_stale_warning'] = str(e)
                        logger.warning(f"Using stale quote for {ticker} (market may be closed): {e}")
                    else:
                        raise

            return quote

        except DataValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch quote for {ticker}: {e}")
            raise RuntimeError(f"Finnhub API error for {ticker}: {e}")

    def fetch_company_news(self, ticker: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent company news.

        Args:
            ticker: Stock ticker symbol
            days_back: Number of days back to fetch news

        Returns:
            List of news articles with fields: headline, summary, source, datetime, url
        """
        try:
            logger.info(f"Fetching news for {ticker} ({days_back} days back)")

            # Calculate date range
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            news = self.client.company_news(ticker, _from=from_date, to=to_date)

            if not isinstance(news, list):
                logger.warning(f"Invalid news response type: {type(news)}")
                return []

            logger.info(f"Fetched {len(news)} news articles for {ticker}")
            return news

        except Exception as e:
            logger.error(f"Failed to fetch news for {ticker}: {e}")
            return []  # Return empty list on error rather than raising

    def fetch_company_profile(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company profile/fundamentals.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company profile dict with fields like: name, country, currency, marketCapitalization, etc.
        """
        try:
            logger.info(f"Fetching company profile for {ticker}")
            profile = self.client.company_profile2(symbol=ticker)

            if not isinstance(profile, dict):
                logger.warning(f"Invalid profile response type: {type(profile)}")
                return None

            logger.info(f"Profile fetched for {ticker}: {profile.get('name', 'Unknown')}")
            return profile

        except Exception as e:
            logger.error(f"Failed to fetch profile for {ticker}: {e}")
            return None

    def get_realtime_context(self, ticker: str, include_news: bool = True,
                            include_profile: bool = False, max_news: int = 3,
                            allow_stale: bool = True) -> str:
        """
        Build comprehensive real-time context for a stock ticker.

        Args:
            ticker: Stock ticker symbol
            include_news: Whether to include recent news
            include_profile: Whether to include company profile
            max_news: Maximum number of news articles to include
            allow_stale: Allow stale quotes when market is closed

        Returns:
            Formatted context string ready for LLM grounding

        Raises:
            DataValidationError: If quote data validation fails and allow_stale=False
            RuntimeError: If quote fetching fails
        """
        logger.info(f"Building real-time context for {ticker}")
        context_parts = []

        # 1. Fetch and validate stock quote (REQUIRED)
        quote = self.fetch_stock_quote(ticker, validate_freshness=True, allow_stale_if_closed=allow_stale)

        quote_time = datetime.fromtimestamp(quote['t']).strftime('%Y-%m-%d %H:%M:%S UTC')

        # Check if quote is stale
        stale_warning = quote.get('_stale_warning', '')
        freshness_note = " [Last Close - Market Closed]" if stale_warning else " [Live]"

        context_parts.append(
            f"{ticker} Stock Quote{freshness_note} (as of {quote_time}):\n"
            f"Price: ${quote['c']:.2f}\n"
            f"Day High: ${quote.get('h', 'N/A')}, Day Low: ${quote.get('l', 'N/A')}\n"
            f"Previous Close: ${quote.get('pc', 'N/A')}\n"
            f"Change: ${quote['c'] - quote.get('pc', quote['c']):.2f} "
            f"({((quote['c'] - quote.get('pc', quote['c'])) / quote.get('pc', quote['c']) * 100):.2f}%)"
        )

        # 2. Fetch company news (OPTIONAL)
        if include_news:
            news = self.fetch_company_news(ticker, days_back=7)
            if news:
                context_parts.append(f"\nRecent News for {ticker}:")
                for article in news[:max_news]:
                    news_date = datetime.fromtimestamp(article['datetime']).strftime('%Y-%m-%d')
                    context_parts.append(
                        f"- [{news_date}] {article['headline']} (Source: {article.get('source', 'Unknown')})"
                    )

        # 3. Fetch company profile (OPTIONAL)
        if include_profile:
            profile = self.fetch_company_profile(ticker)
            if profile:
                context_parts.append(
                    f"\nCompany Profile:\n"
                    f"Name: {profile.get('name', 'N/A')}\n"
                    f"Industry: {profile.get('finnhubIndustry', 'N/A')}\n"
                    f"Market Cap: ${profile.get('marketCapitalization', 0):.2f}B\n"
                    f"Country: {profile.get('country', 'N/A')}"
                )

        context = "\n\n".join(context_parts)
        logger.info(f"Real-time context built for {ticker} ({len(context)} chars)")
        return context


# Company name to ticker mapping
COMPANY_TO_TICKER = {
    'APPLE': 'AAPL',
    'MICROSOFT': 'MSFT',
    'GOOGLE': 'GOOGL',
    'ALPHABET': 'GOOGL',
    'AMAZON': 'AMZN',
    'TESLA': 'TSLA',
    'META': 'META',
    'FACEBOOK': 'META',
    'NVIDIA': 'NVDA',
    'NETFLIX': 'NFLX',
    'COINBASE': 'COIN',
    'TWITTER': 'X',
    'INTEL': 'INTC',
    'AMD': 'AMD',
    'PAYPAL': 'PYPL',
    'UBER': 'UBER',
    'LYFT': 'LYFT',
    'AIRBNB': 'ABNB',
    'SNAPCHAT': 'SNAP',
    'SPOTIFY': 'SPOT',
    'ZOOM': 'ZM',
    'SLACK': 'WORK',
    'SALESFORCE': 'CRM',
    'ORACLE': 'ORCL',
    'IBM': 'IBM',
    'CISCO': 'CSCO',
    'WALMART': 'WMT',
    'TARGET': 'TGT',
    'COSTCO': 'COST',
    'STARBUCKS': 'SBUX',
    'MCDONALDS': 'MCD',
    'DISNEY': 'DIS',
    'NIKE': 'NKE',
    'VISA': 'V',
    'MASTERCARD': 'MA',
    'JPMORGAN': 'JPM',
    'BANK OF AMERICA': 'BAC',
    'WELLS FARGO': 'WFC',
    'GOLDMAN SACHS': 'GS',
    'MORGAN STANLEY': 'MS',
    'MICROSTRATEGY': 'MSTR',
}


def resolve_company_name_to_ticker(company_name: str, api_key: str, use_cache: bool = True) -> Optional[str]:
    """
    Resolve a company name to its ticker symbol using Finnhub's symbol lookup API.

    Args:
        company_name: Company name to search for (e.g., "Palantir", "Advanced Micro Devices")
        api_key: Finnhub API key
        use_cache: Whether to use cached results (default True)

    Returns:
        Ticker symbol if found (e.g., "PLTR"), None otherwise
    """
    # Normalize the company name for caching
    cache_key = company_name.upper().strip()

    # Check cache first
    if use_cache and cache_key in _SYMBOL_CACHE:
        cached_result = _SYMBOL_CACHE[cache_key]
        logger.debug(f"Symbol lookup cache hit: '{company_name}' -> {cached_result}")
        return cached_result

    try:
        # Use Finnhub symbol lookup API
        client = finnhub.Client(api_key=api_key)
        results = client.symbol_lookup(company_name)

        if not results or 'result' not in results or not results['result']:
            logger.debug(f"No symbol found for company name: '{company_name}'")
            _SYMBOL_CACHE[cache_key] = None
            return None

        # Get the first (most relevant) result
        # Finnhub returns results sorted by relevance
        best_match = results['result'][0]
        ticker = best_match.get('symbol', '').split('.')[0]  # Remove exchange suffix (e.g., "AAPL.US" -> "AAPL")

        if ticker:
            logger.info(f"Resolved company name '{company_name}' -> {ticker} (via Finnhub API)")
            _SYMBOL_CACHE[cache_key] = ticker
            return ticker

    except Exception as e:
        logger.warning(f"Symbol lookup API failed for '{company_name}': {e}")
        _SYMBOL_CACHE[cache_key] = None

    return None


def extract_tickers_from_query(query: str, api_key: Optional[str] = None) -> List[str]:
    """
    Extract potential stock ticker symbols from user query.

    Enhanced heuristic with API fallback:
    1. Check static company name mapping (fast, no API call)
    2. Match uppercase ticker symbols (1-5 chars)
    3. Use Finnhub symbol lookup API for unrecognized company names (if api_key provided)

    Args:
        query: User query text
        api_key: Optional Finnhub API key for symbol lookup

    Returns:
        List of potential ticker symbols
    """
    import re

    query_upper = query.upper()
    tickers = []

    blocked_tokens = {
        "COVID", "COVID19", "COVID-19", "CORONAVIRUS", "PANDEMIC",
        "REIT", "REITS", "ETF", "ETFS", "INDEX", "MARKET", "ECONOMY"
    }

    # Step 1: Check for company names in the static mapping
    for company_name, ticker in COMPANY_TO_TICKER.items():
        # Match whole words only (avoid "APPLE" matching in "PINEAPPLE")
        if re.search(rf'\b{company_name}\b', query_upper):
            if ticker not in tickers and ticker not in blocked_tokens:
                tickers.append(ticker)
                logger.debug(f"Mapped company name '{company_name}' -> {ticker}")

    # Step 2: Match uppercase ticker symbols (1-5 chars)
    potential_tickers = re.findall(r'\b[A-Z]{1,5}\b', query)

    # Filter out common English words that might be false positives
    common_words = {'AND', 'OR', 'NOT', 'THE', 'FOR', 'ARE', 'WAS', 'BUT', 'HAS', 'HAD', 'CAN', 'ITS', 'A', 'I', 'IS', 'AT', 'TO', 'IN', 'IT', 'OF', 'AS', 'ON', 'BY', 'AN', 'BE', 'IF', 'SO', 'UP', 'MY', 'ME', 'DO', 'GO', 'NO', 'WHAT', 'WHATS', 'HOW', 'WHY', 'WHEN', 'WHERE', 'WHICH', 'WHO', 'TELL', 'SHOW', 'GIVE', 'COMPARE', 'EXPLAIN'}

    # Known stock context keywords that indicate a ticker follows
    stock_keywords = ['ticker', 'stock', 'price', 'share', 'quote', 'symbol', 'trading', 'market', 'nasdaq', 'nyse']
    has_stock_context = any(keyword in query.lower() for keyword in stock_keywords)

    # If query has stock context, be more lenient with ticker extraction
    for t in potential_tickers:
        if t not in common_words and t not in tickers and t not in blocked_tokens:
            if has_stock_context or len(t) >= 2:  # Require at least 2 chars unless stock context
                tickers.append(t)

    # Step 3: Use API symbol lookup for capitalized words (potential company names)
    # Only if we have stock context and an API key, and no tickers found yet
    if api_key and has_stock_context and not tickers:
        # Extract capitalized words that might be company names
        # Match words like "Palantir", "MicroStrategy", "Advanced"
        potential_company_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)

        # Common question words to exclude
        question_words = {'What', 'How', 'Why', 'When', 'Where', 'Which', 'Who', 'Tell', 'Show', 'Give', 'Compare', 'Explain'}

        for company_name in potential_company_names:
            # Skip if it's too short or a question word
            if len(company_name) < 4 or company_name in question_words:
                continue

            ticker = resolve_company_name_to_ticker(company_name, api_key)
            if ticker and ticker not in tickers:
                tickers.append(ticker)
                logger.info(f"API resolved '{company_name}' -> {ticker}")

    logger.debug(f"Extracted tickers from query: {tickers} (stock_context={has_stock_context})")
    return tickers


# Convenience function for easy integration
def get_realtime_context_for_query(query: str, api_key: str,
                                   max_quote_age_seconds: int = 900) -> str:
    """
    Extract tickers from query and build real-time context.

    Args:
        query: User query (e.g., "What's AAPL stock price?")
        api_key: Finnhub API key
        max_quote_age_seconds: Maximum acceptable quote age

    Returns:
        Real-time context string, or empty string if no tickers found
    """
    tickers = extract_tickers_from_query(query, api_key=api_key)

    if not tickers:
        logger.info("No tickers found in query")
        return ""

    fetcher = FinnhubDataFetcher(api_key, max_quote_age_seconds)
    contexts = []

    for ticker in tickers:
        try:
            context = fetcher.get_realtime_context(ticker, include_news=True, include_profile=False)
            contexts.append(context)
        except Exception as e:
            logger.error(f"Failed to get context for {ticker}: {e}")
            # Continue with other tickers
            continue

    return "\n\n" + "=" * 60 + "\n\n".join(contexts) if contexts else ""


if __name__ == "__main__":
    # Test the module
    import os
    from dotenv import load_dotenv
    load_dotenv()

    API_KEY = os.environ.get("FINNHUB_API_KEY", "d3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag")

    print("Testing FinnhubDataFetcher...")
    fetcher = FinnhubDataFetcher(API_KEY)

    # Test with AAPL
    try:
        context = fetcher.get_realtime_context("AAPL", include_news=True, include_profile=True)
        print("\n" + "=" * 60)
        print("Real-time Context for AAPL:")
        print("=" * 60)
        print(context)
    except Exception as e:
        print(f"Error: {e}")

    # Test ticker extraction
    print("\n" + "=" * 60)
    print("Testing ticker extraction:")
    test_query = "What's the current price of AAPL and MSFT?"
    tickers = extract_tickers_from_query(test_query)
    print(f"Query: {test_query}")
    print(f"Extracted tickers: {tickers}")
