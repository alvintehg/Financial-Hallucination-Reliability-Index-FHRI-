# src/commodity_data.py
"""
Commodity data fetcher using Finnhub API.

Features:
- Real-time commodity prices (oil, gold, silver, natural gas, etc.)
- Commodity news from major sources
- Support for futures contracts (WTI, Brent, etc.)

Public API:
- get_commodity_price(symbol: str, api_key: str) -> dict
- get_commodity_news(category: str, api_key: str) -> list
- get_commodity_context(symbol: str, api_key: str) -> str
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
import finnhub
import time

logger = logging.getLogger("commodity_data")


# Mapping of common commodity names to Finnhub symbols
# Finnhub uses Yahoo Finance format for commodities: SYMBOL=F (futures)
COMMODITY_SYMBOLS = {
    # Oil
    'OIL': 'CL=F',  # WTI Crude Oil
    'CRUDE': 'CL=F',
    'CRUDE OIL': 'CL=F',
    'WTI': 'CL=F',
    'WTI CRUDE': 'CL=F',
    'BRENT': 'BZ=F',  # Brent Crude
    'BRENT CRUDE': 'BZ=F',
    'BRENT OIL': 'BZ=F',
    
    # Gold
    'GOLD': 'GC=F',
    'GOLD FUTURES': 'GC=F',
    
    # Silver
    'SILVER': 'SI=F',
    'SILVER FUTURES': 'SI=F',
    
    # Natural Gas
    'NATURAL GAS': 'NG=F',
    'GAS': 'NG=F',
    'NG': 'NG=F',
    
    # Copper
    'COPPER': 'HG=F',
    'COPPER FUTURES': 'HG=F',
    
    # Corn
    'CORN': 'ZC=F',
    'CORN FUTURES': 'ZC=F',
    
    # Wheat
    'WHEAT': 'ZW=F',
    'WHEAT FUTURES': 'ZW=F',
    
    # Soybeans
    'SOYBEANS': 'ZS=F',
    'SOYBEAN': 'ZS=F',
    'SOYBEANS FUTURES': 'ZS=F',
}


class CommodityDataFetcher:
    """Fetch real-time commodity data from Finnhub."""

    def __init__(self, api_key: str):
        """
        Initialize commodity data fetcher.

        Args:
            api_key: Finnhub API key
        """
        self.client = finnhub.Client(api_key=api_key)
        logger.info("Initialized CommodityDataFetcher")

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize commodity symbol to Finnhub format.

        Args:
            symbol: User input like 'OIL', 'Gold', 'WTI'

        Returns:
            Finnhub symbol like 'CL=F' (WTI Crude Oil)
        """
        symbol_upper = symbol.upper().strip()

        # If already in futures format (ends with =F), return as-is
        if symbol_upper.endswith('=F'):
            return symbol_upper

        # Check mapping
        if symbol_upper in COMMODITY_SYMBOLS:
            return COMMODITY_SYMBOLS[symbol_upper]

        # Try to find partial match (e.g., "crude oil" -> "CRUDE OIL")
        for key, value in COMMODITY_SYMBOLS.items():
            if key in symbol_upper or symbol_upper in key:
                return value

        # Default: assume it's already a valid symbol
        return symbol_upper

    def get_commodity_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time commodity quote.

        Args:
            symbol: Commodity symbol (e.g., 'OIL', 'GOLD', 'WTI')

        Returns:
            Quote dict with current price, timestamp, etc.
        """
        normalized = self.normalize_symbol(symbol)
        logger.info(f"Fetching commodity quote for {symbol} ({normalized})")

        # Primary: Finnhub
        quote = None
        try:
            quote = self.client.quote(normalized)
            if isinstance(quote, dict) and quote.get('c', 0) > 0:
                quote['symbol'] = normalized
                quote['normalized_name'] = symbol.upper()
                quote['_source'] = "finnhub"
                logger.info(f"Commodity quote fetched: {normalized} = ${quote['c']}")
                return quote
            else:
                logger.warning(f"Invalid commodity quote for {normalized}: {quote}")
        except Exception as e:
            logger.error(f"Finnhub commodity quote failed for {normalized}: {e}")

        # Fallback: yfinance (works for CL=F, GC=F, etc.)
        fallback = self.fetch_yfinance_commodity_quote(normalized)
        if fallback:
            fallback['normalized_name'] = symbol.upper()
            fallback['_source'] = "yfinance"
            logger.info(f"Commodity quote fetched via yfinance: {normalized} = ${fallback['c']}")
            return fallback

        logger.error(f"All commodity quote providers failed for {normalized}")
        return None

    def fetch_yfinance_commodity_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch commodity quote using yfinance as a fallback.
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            price = None
            prev_close = None
            day_high = None
            day_low = None

            try:
                fast = ticker.fast_info
                price = fast.last_price
                prev_close = fast.previous_close
                day_high = fast.day_high
                day_low = fast.day_low
            except Exception:
                info = ticker.info or {}
                price = info.get("regularMarketPrice") or info.get("currentPrice")
                prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                day_high = info.get("regularMarketDayHigh")
                day_low = info.get("regularMarketDayLow")

            if not price or price <= 0:
                logger.warning(f"yfinance: No price data for {symbol}")
                return None

            if prev_close is None:
                prev_close = price

            pct_change = ((price - prev_close) / prev_close * 100) if prev_close else 0.0

            quote = {
                "symbol": symbol,
                "c": float(price),
                "pc": float(prev_close),
                "h": float(day_high) if day_high else None,
                "l": float(day_low) if day_low else None,
                "t": int(time.time()),
                "price": float(price),
                "pct_change": round(pct_change, 2),
                "source": "yfinance"
            }
            return quote
        except Exception as e:
            logger.error(f"yfinance commodity quote failed for {symbol}: {e}")
            return None

    def get_commodity_news(self, category: str = "general", min_id: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch commodity-related news.

        Args:
            category: News category (default: "general")
            min_id: Minimum news ID (for pagination)

        Returns:
            List of news articles
        """
        try:
            logger.info(f"Fetching commodity news (category={category})")
            news = self.client.general_news(category, min_id=min_id)

            if not isinstance(news, list):
                logger.warning(f"Invalid news response: {type(news)}")
                return []

            # Filter for commodity-related news
            commodity_keywords = ['oil', 'crude', 'gold', 'silver', 'gas', 'commodity', 'futures', 'energy']
            filtered_news = []
            for article in news:
                headline = article.get('headline', '').lower()
                if any(keyword in headline for keyword in commodity_keywords):
                    filtered_news.append(article)

            logger.info(f"Fetched {len(filtered_news)} commodity news articles (from {len(news)} total)")
            return filtered_news[:10]  # Limit to top 10

        except Exception as e:
            logger.error(f"Failed to fetch commodity news: {e}")
            return []

    def get_commodity_context(self, symbol: str, include_news: bool = True,
                             max_news: int = 3) -> Tuple[str, Dict[str, Any]]:
        """
        Build comprehensive commodity context.

        Args:
            symbol: Commodity symbol (e.g., 'OIL', 'GOLD')
            include_news: Whether to include news
            max_news: Max number of news articles

        Returns:
            Tuple of (formatted context string, normalized quote metadata)
        """
        logger.info(f"Building commodity context for {symbol}")
        context_parts = []

        # 1. Get current price
        quote = self.get_commodity_quote(symbol)
        if not quote:
            return "", {}

        normalized_name = quote.get('normalized_name', symbol.upper())
        price = quote['c']
        prev_close = quote.get('pc', price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        quote_time = datetime.fromtimestamp(quote['t']).strftime('%Y-%m-%d %H:%M:%S UTC')

        # Determine commodity type for display
        commodity_type = "Commodity"
        if 'CL=F' in quote['symbol'] or 'BZ=F' in quote['symbol']:
            commodity_type = "Crude Oil"
        elif 'GC=F' in quote['symbol']:
            commodity_type = "Gold"
        elif 'SI=F' in quote['symbol']:
            commodity_type = "Silver"
        elif 'NG=F' in quote['symbol']:
            commodity_type = "Natural Gas"

        context_parts.append(
            f"{normalized_name} {commodity_type} Futures Quote (as of {quote_time}):\n"
            f"Current Price: ${price:,.2f}\n"
            f"Day High: ${quote.get('h', 'N/A'):,} | Day Low: ${quote.get('l', 'N/A'):,}\n"
            f"Previous Close: ${prev_close:,.2f}\n"
            f"Change: ${change:,.2f} ({change_pct:+.2f}%)\n"
            f"Contract: {quote['symbol']}"
        )

        # 2. Get news if requested
        if include_news:
            news = self.get_commodity_news(category="general")
            if news:
                context_parts.append(f"\nLatest Commodity News:")
                for article in news[:max_news]:
                    news_time = datetime.fromtimestamp(article['datetime']).strftime('%Y-%m-%d %H:%M')
                    context_parts.append(
                        f"- [{news_time}] {article['headline']} "
                        f"(Source: {article.get('source', 'Unknown')})"
                    )

        quote_metadata = {
            "symbol": quote['symbol'],
            "normalized_name": normalized_name,
            "price": round(price, 2),
            "pct_change": round(change_pct, 2),
            "ts_utc": datetime.fromtimestamp(quote['t'], timezone.utc).isoformat(),
            "source": "Finnhub Commodities",
            "raw": quote
        }

        context = "\n\n".join(context_parts)
        logger.info(f"Commodity context built for {symbol} ({len(context)} chars)")
        return context, quote_metadata


def extract_commodity_symbols_from_query(query: str) -> List[str]:
    """
    Extract commodity symbols from user query.

    Args:
        query: User query text

    Returns:
        List of commodity symbols found
    """
    import re

    query_upper = query.upper()
    found_symbols = []

    # Check for known commodity names/symbols
    for name, symbol in COMMODITY_SYMBOLS.items():
        # Match whole words only
        if re.search(rf'\b{name}\b', query_upper):
            # Map back to the display name (e.g., 'OIL' not 'CL=F')
            display_name = name.split()[0] if ' ' in name else name
            if display_name not in found_symbols:
                found_symbols.append(display_name)

    # Also check for commodity keywords
    commodity_keywords = ['oil', 'crude', 'gold', 'silver', 'gas', 'natural gas', 
                         'commodity', 'commodities', 'futures', 'energy', 'wti', 'brent']
    has_commodity_context = any(kw in query.lower() for kw in commodity_keywords)

    if has_commodity_context:
        # Look for specific commodity mentions
        for keyword in commodity_keywords:
            if keyword in query.lower():
                # Map keyword to symbol
                if keyword in ['oil', 'crude', 'wti']:
                    if 'OIL' not in found_symbols:
                        found_symbols.append('OIL')
                elif keyword == 'brent':
                    if 'BRENT' not in found_symbols:
                        found_symbols.append('BRENT')
                elif keyword == 'gold':
                    if 'GOLD' not in found_symbols:
                        found_symbols.append('GOLD')
                elif keyword in ['silver']:
                    if 'SILVER' not in found_symbols:
                        found_symbols.append('SILVER')
                elif keyword in ['gas', 'natural gas']:
                    if 'GAS' not in found_symbols:
                        found_symbols.append('GAS')

    logger.debug(f"Extracted commodity symbols: {found_symbols}")
    return list(set(found_symbols))  # Remove duplicates


def get_commodity_context_for_query(query: str, api_key: str) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """
    Extract commodity symbols from query and build context.

    Args:
        query: User query
        api_key: Finnhub API key

    Returns:
        Tuple of (commodity context string, list of normalized quote data entries, symbols detected)
    """
    symbols = extract_commodity_symbols_from_query(query)

    if not symbols:
        logger.info("No commodity symbols found in query")
        return "", [], []

    fetcher = CommodityDataFetcher(api_key)
    contexts = []
    data_entries = []

    for symbol in symbols:
        try:
            context, quote_data = fetcher.get_commodity_context(symbol, include_news=True, max_news=3)
            if context:
                contexts.append(context)
            if quote_data:
                data_entry = {
                    "symbol": quote_data.get("symbol", symbol),
                    "asset_type": "commodity",
                    "primary_data": quote_data,
                    "sources_attempted": ["Finnhub"],
                    "sources_succeeded": ["Finnhub Commodities"],
                    "fetch_time": datetime.now(timezone.utc).isoformat()
                }
                data_entries.append(data_entry)
        except Exception as e:
            logger.error(f"Failed to get commodity context for {symbol}: {e}")
            continue

    context_blob = "\n\n" + "=" * 60 + "\n\n".join(contexts) if contexts else ""
    return context_blob, data_entries, symbols


if __name__ == "__main__":
    # Test the module
    import os
    from dotenv import load_dotenv
    load_dotenv()

    API_KEY = os.environ.get("FINNHUB_API_KEY", "d3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag")

    print("Testing CommodityDataFetcher...")
    fetcher = CommodityDataFetcher(API_KEY)

    # Test Oil
    try:
        print("\n" + "=" * 60)
        print("Oil (WTI Crude) Context:")
        print("=" * 60)
        context, _ = fetcher.get_commodity_context("OIL", include_news=True)
        print(context)
    except Exception as e:
        print(f"Error: {e}")

    # Test symbol extraction
    print("\n" + "=" * 60)
    print("Testing symbol extraction:")
    test_queries = [
        "What are the real-time numbers for oil prices right now?",
        "How is gold doing?",
        "What is the price of crude oil?",
        "Show me WTI and Brent prices"
    ]
    for q in test_queries:
        symbols = extract_commodity_symbols_from_query(q)
        print(f"Query: {q}")
        print(f"Symbols: {symbols}")

