# src/crypto_data.py
"""
Cryptocurrency data fetcher using Finnhub API.

Features:
- Real-time crypto prices (Bitcoin, Ethereum, etc.)
- Crypto news from major sources
- Support for multiple exchanges (Binance, Coinbase, etc.)
- Price changes and trends

Public API:
- get_crypto_price(symbol: str, api_key: str) -> dict
- get_crypto_news(category: str, api_key: str) -> list
- get_crypto_context(symbol: str, api_key: str) -> str
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import finnhub
import time

logger = logging.getLogger("crypto_data")


# Mapping of common crypto names to Finnhub symbols
CRYPTO_SYMBOLS = {
    # Bitcoin variations
    'BTC': 'BINANCE:BTCUSDT',
    'BITCOIN': 'BINANCE:BTCUSDT',
    'XBT': 'BINANCE:BTCUSDT',

    # Ethereum
    'ETH': 'BINANCE:ETHUSDT',
    'ETHEREUM': 'BINANCE:ETHUSDT',

    # Other major cryptos
    'BNB': 'BINANCE:BNBUSDT',
    'BINANCE': 'BINANCE:BNBUSDT',
    'XRP': 'BINANCE:XRPUSDT',
    'RIPPLE': 'BINANCE:XRPUSDT',
    'ADA': 'BINANCE:ADAUSDT',
    'CARDANO': 'BINANCE:ADAUSDT',
    'DOGE': 'BINANCE:DOGEUSDT',
    'DOGECOIN': 'BINANCE:DOGEUSDT',
    'SOL': 'BINANCE:SOLUSDT',
    'SOLANA': 'BINANCE:SOLUSDT',
    'DOT': 'BINANCE:DOTUSDT',
    'POLKADOT': 'BINANCE:DOTUSDT',
    'MATIC': 'BINANCE:MATICUSDT',
    'POLYGON': 'BINANCE:MATICUSDT',
    'LINK': 'BINANCE:LINKUSDT',
    'CHAINLINK': 'BINANCE:LINKUSDT',
    'AVAX': 'BINANCE:AVAXUSDT',
    'AVALANCHE': 'BINANCE:AVAXUSDT',
    'UNI': 'BINANCE:UNIUSDT',
    'UNISWAP': 'BINANCE:UNIUSDT',
}


class CryptoDataFetcher:
    """Fetch real-time cryptocurrency data from Finnhub."""

    def __init__(self, api_key: str):
        """
        Initialize crypto data fetcher.

        Args:
            api_key: Finnhub API key
        """
        self.client = finnhub.Client(api_key=api_key)
        logger.info("Initialized CryptoDataFetcher")

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize crypto symbol to Finnhub format.

        Args:
            symbol: User input like 'BTC', 'Bitcoin', 'BTCUSDT'

        Returns:
            Finnhub symbol like 'BINANCE:BTCUSDT'
        """
        symbol_upper = symbol.upper().strip()

        # If already in exchange:pair format, return as-is
        if ':' in symbol_upper:
            return symbol_upper

        # Check mapping
        if symbol_upper in CRYPTO_SYMBOLS:
            return CRYPTO_SYMBOLS[symbol_upper]

        # Default to Binance with USDT pair
        return f'BINANCE:{symbol_upper}USDT'

    def get_crypto_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time crypto quote.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'BITCOIN')

        Returns:
            Quote dict with current price, timestamp, etc.
        """
        try:
            normalized = self.normalize_symbol(symbol)
            logger.info(f"Fetching crypto quote for {symbol} ({normalized})")

            quote = self.client.quote(normalized)

            if not isinstance(quote, dict) or quote.get('c', 0) <= 0:
                logger.warning(f"Invalid crypto quote for {normalized}: {quote}")
                return None

            # Add metadata
            quote['symbol'] = normalized
            quote['normalized_name'] = symbol.upper()

            logger.info(f"Crypto quote fetched: {normalized} = ${quote['c']}")
            return quote

        except Exception as e:
            logger.error(f"Failed to fetch crypto quote for {symbol}: {e}")
            return None

    def get_crypto_news(self, category: str = "crypto", min_id: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch cryptocurrency news.

        Args:
            category: News category (default: "crypto")
            min_id: Minimum news ID (for pagination)

        Returns:
            List of news articles
        """
        try:
            logger.info(f"Fetching crypto news (category={category})")
            news = self.client.general_news(category, min_id=min_id)

            if not isinstance(news, list):
                logger.warning(f"Invalid news response: {type(news)}")
                return []

            logger.info(f"Fetched {len(news)} crypto news articles")
            return news

        except Exception as e:
            logger.error(f"Failed to fetch crypto news: {e}")
            return []

    def get_crypto_candles(self, symbol: str, resolution: str = "D",
                          days_back: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get historical crypto price candles.

        Args:
            symbol: Crypto symbol
            resolution: Candle resolution (D=day, 60=hour, etc.)
            days_back: How many days of history

        Returns:
            Candle data with OHLCV
        """
        try:
            normalized = self.normalize_symbol(symbol)
            to_time = int(time.time())
            from_time = to_time - (days_back * 24 * 3600)

            logger.info(f"Fetching candles for {normalized} ({days_back} days)")
            candles = self.client.crypto_candles(
                normalized.split(':')[0],  # exchange
                normalized.split(':')[1],  # pair
                resolution,
                from_time,
                to_time
            )

            if candles.get('s') == 'ok':
                logger.info(f"Fetched {len(candles.get('c', []))} candles")
                return candles
            else:
                logger.warning(f"No candle data for {normalized}")
                return None

        except Exception as e:
            logger.error(f"Failed to fetch candles for {symbol}: {e}")
            return None

    def get_crypto_context(self, symbol: str, include_news: bool = True,
                          max_news: int = 3) -> str:
        """
        Build comprehensive crypto context.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            include_news: Whether to include news
            max_news: Max number of news articles

        Returns:
            Formatted context string
        """
        logger.info(f"Building crypto context for {symbol}")
        context_parts = []

        # 1. Get current price
        quote = self.get_crypto_quote(symbol)
        if not quote:
            return ""

        normalized_name = quote.get('normalized_name', symbol.upper())
        price = quote['c']
        prev_close = quote.get('pc', price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        quote_time = datetime.fromtimestamp(quote['t']).strftime('%Y-%m-%d %H:%M:%S UTC')

        context_parts.append(
            f"{normalized_name} Cryptocurrency Quote (as of {quote_time}):\n"
            f"Current Price: ${price:,.2f}\n"
            f"24h High: ${quote.get('h', 'N/A'):,} | 24h Low: ${quote.get('l', 'N/A'):,}\n"
            f"24h Change: ${change:,.2f} ({change_pct:+.2f}%)\n"
            f"Exchange: {quote['symbol'].split(':')[0]}"
        )

        # 2. Get news if requested
        if include_news:
            news = self.get_crypto_news(category="crypto")
            if news:
                context_parts.append(f"\nLatest Cryptocurrency News:")
                for article in news[:max_news]:
                    news_time = datetime.fromtimestamp(article['datetime']).strftime('%Y-%m-%d %H:%M')
                    context_parts.append(
                        f"- [{news_time}] {article['headline']} "
                        f"(Source: {article.get('source', 'Unknown')})"
                    )

        context = "\n\n".join(context_parts)
        logger.info(f"Crypto context built for {symbol} ({len(context)} chars)")
        return context


def extract_crypto_symbols_from_query(query: str) -> List[str]:
    """
    Extract cryptocurrency symbols from user query.

    Args:
        query: User query text

    Returns:
        List of crypto symbols found
    """
    import re

    query_upper = query.upper()
    found_symbols = []

    # Check for known crypto names/symbols
    for name, symbol in CRYPTO_SYMBOLS.items():
        # Match whole words only
        if re.search(rf'\b{name}\b', query_upper):
            found_symbols.append(name)

    # Also check for common patterns like BTC, ETH (2-5 uppercase chars)
    # But only if crypto keywords are present
    crypto_keywords = ['crypto', 'cryptocurrency', 'coin', 'token', 'blockchain', 'wallet']
    has_crypto_context = any(kw in query.lower() for kw in crypto_keywords)

    if has_crypto_context:
        potential = re.findall(r'\b[A-Z]{2,5}\b', query)
        for p in potential:
            if p in CRYPTO_SYMBOLS and p not in found_symbols:
                found_symbols.append(p)

    logger.debug(f"Extracted crypto symbols: {found_symbols}")
    return list(set(found_symbols))  # Remove duplicates


def get_crypto_context_for_query(query: str, api_key: str) -> str:
    """
    Extract crypto symbols from query and build context.

    Args:
        query: User query
        api_key: Finnhub API key

    Returns:
        Crypto context string
    """
    symbols = extract_crypto_symbols_from_query(query)

    if not symbols:
        logger.info("No crypto symbols found in query")
        return ""

    fetcher = CryptoDataFetcher(api_key)
    contexts = []

    for symbol in symbols:
        try:
            context = fetcher.get_crypto_context(symbol, include_news=True, max_news=3)
            if context:
                contexts.append(context)
        except Exception as e:
            logger.error(f"Failed to get crypto context for {symbol}: {e}")
            continue

    return "\n\n" + "=" * 60 + "\n\n".join(contexts) if contexts else ""


if __name__ == "__main__":
    # Test the module
    import os
    from dotenv import load_dotenv
    load_dotenv()

    API_KEY = os.environ.get("FINNHUB_API_KEY", "d3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag")

    print("Testing CryptoDataFetcher...")
    fetcher = CryptoDataFetcher(API_KEY)

    # Test Bitcoin
    try:
        print("\n" + "=" * 60)
        print("Bitcoin (BTC) Context:")
        print("=" * 60)
        context = fetcher.get_crypto_context("BTC", include_news=True)
        print(context)
    except Exception as e:
        print(f"Error: {e}")

    # Test symbol extraction
    print("\n" + "=" * 60)
    print("Testing symbol extraction:")
    test_queries = [
        "What is Bitcoin price?",
        "How is BTC doing?",
        "Compare BTC and ETH prices",
        "Latest crypto news"
    ]
    for q in test_queries:
        symbols = extract_crypto_symbols_from_query(q)
        print(f"Query: {q}")
        print(f"Symbols: {symbols}")
