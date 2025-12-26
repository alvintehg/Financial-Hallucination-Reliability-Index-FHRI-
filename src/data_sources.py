# src/data_sources.py
"""
Multi-source real-time financial data aggregator for FHRI verification.

Supports on-demand fetching from multiple providers with fallback chains:
- Equities/ETFs: Finnhub → Twelve Data → yfinance
- Fundamentals/Ratios: FinancialModelingPrep (FMP)
- Filings: SEC EDGAR (10-K, 10-Q links)
- Crypto: CoinGecko

All calls are per-request with short timeouts (2-3s each).
Includes in-memory cache with 30-60s TTL to avoid rate limits.

Public API:
- fetch_equity_data(symbol: str) -> dict
- fetch_fundamentals(symbol: str) -> dict
- fetch_sec_filings(symbol: str) -> dict
- fetch_crypto_data(symbol: str) -> dict
- fetch_all_sources(symbol: str, asset_type: str) -> dict
"""

import logging
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from collections import OrderedDict
import os

logger = logging.getLogger("data_sources")

# ============================================================================
# In-Memory Cache (TTL: 30-60s)
# ============================================================================

class TTLCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 45):
        """
        Initialize TTL cache.

        Args:
            ttl_seconds: Time-to-live for cached entries (default 45s)
        """
        self.ttl = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.max_size = 1000  # Prevent unbounded growth

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        age = time.time() - timestamp

        if age > self.ttl:
            # Expired, remove from cache
            del self.cache[key]
            logger.debug(f"Cache expired for key: {key} (age: {age:.1f}s)")
            return None

        logger.debug(f"Cache hit for key: {key} (age: {age:.1f}s)")
        return value

    def set(self, key: str, value: Any):
        """Set cache value with current timestamp."""
        # Remove oldest entries if cache is full
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"Cache full, evicted: {oldest_key}")

        self.cache[key] = (value, time.time())
        logger.debug(f"Cache set for key: {key}")

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Cache cleared")


# Global cache instance
_cache = TTLCache(ttl_seconds=45)


# ============================================================================
# Equity/ETF Data Providers (with fallback chain)
# ============================================================================

def fetch_finnhub_quote(symbol: str, api_key: str, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """
    Fetch stock quote from Finnhub.

    Args:
        symbol: Stock ticker (e.g., "AAPL")
        api_key: Finnhub API key
        timeout: Request timeout in seconds

    Returns:
        Normalized dict with {symbol, price, pct_change, ts_utc, source_url}
    """
    try:
        import finnhub
        client = finnhub.Client(api_key=api_key)

        quote = client.quote(symbol)

        if not quote or quote.get('c', 0) <= 0:
            logger.warning(f"Finnhub: Invalid quote data for {symbol}")
            return None

        current_price = quote['c']
        prev_close = quote.get('pc', current_price)
        pct_change = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

        result = {
            "symbol": symbol,
            "price": round(current_price, 2),
            "pct_change": round(pct_change, 2),
            "ts_utc": datetime.fromtimestamp(quote['t'], tz=timezone.utc).isoformat(),
            "source_url": f"https://finnhub.io/quote/{symbol}",
            "source": "Finnhub",
            "raw": quote
        }

        logger.info(f"Finnhub: Fetched {symbol} @ ${result['price']} ({result['pct_change']:+.2f}%)")
        return result

    except Exception as e:
        logger.warning(f"Finnhub fetch failed for {symbol}: {e}")
        return None


def fetch_twelvedata_quote(symbol: str, api_key: str, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """
    Fetch stock quote from Twelve Data.

    Args:
        symbol: Stock ticker
        api_key: Twelve Data API key
        timeout: Request timeout in seconds

    Returns:
        Normalized dict
    """
    try:
        url = "https://api.twelvedata.com/quote"
        params = {
            "symbol": symbol,
            "apikey": api_key
        }

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error" or "close" not in data:
            logger.warning(f"TwelveData: Invalid response for {symbol}")
            return None

        current_price = float(data["close"])
        prev_close = float(data.get("previous_close", current_price))
        pct_change = float(data.get("percent_change", 0))

        result = {
            "symbol": symbol,
            "price": round(current_price, 2),
            "pct_change": round(pct_change, 2),
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "source_url": f"https://twelvedata.com/stocks/{symbol}",
            "source": "TwelveData",
            "raw": data
        }

        logger.info(f"TwelveData: Fetched {symbol} @ ${result['price']} ({result['pct_change']:+.2f}%)")
        return result

    except Exception as e:
        logger.warning(f"TwelveData fetch failed for {symbol}: {e}")
        return None


def fetch_yfinance_quote(symbol: str, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Fetch stock quote from yfinance (no API key required).

    Args:
        symbol: Stock ticker
        timeout: Request timeout in seconds

    Returns:
        Normalized dict
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info or "currentPrice" not in info:
            # Try fast_info as fallback
            try:
                current_price = ticker.fast_info.last_price
                prev_close = ticker.fast_info.previous_close
            except:
                logger.warning(f"yfinance: No price data for {symbol}")
                return None
        else:
            current_price = info.get("currentPrice", info.get("regularMarketPrice"))
            prev_close = info.get("previousClose", current_price)

        if not current_price or current_price <= 0:
            return None

        pct_change = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

        result = {
            "symbol": symbol,
            "price": round(float(current_price), 2),
            "pct_change": round(pct_change, 2),
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "source_url": f"https://finance.yahoo.com/quote/{symbol}",
            "source": "yfinance",
            "raw": info
        }

        logger.info(f"yfinance: Fetched {symbol} @ ${result['price']} ({result['pct_change']:+.2f}%)")
        return result

    except Exception as e:
        logger.warning(f"yfinance fetch failed for {symbol}: {e}")
        return None


def fetch_equity_data(symbol: str, api_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Fetch equity data with fallback chain: Finnhub → TwelveData → yfinance.

    Args:
        symbol: Stock ticker
        api_keys: Dict with keys: finnhub_key, twelvedata_key (optional)

    Returns:
        Dict with primary data and all attempted sources
    """
    cache_key = f"equity:{symbol}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    result = {
        "symbol": symbol,
        "asset_type": "equity",
        "primary_data": None,
        "sources_attempted": [],
        "sources_succeeded": [],
        "fetch_time": datetime.now(timezone.utc).isoformat()
    }

    # Try Finnhub (primary)
    finnhub_key = api_keys.get("finnhub_key")
    if finnhub_key:
        result["sources_attempted"].append("Finnhub")
        data = fetch_finnhub_quote(symbol, finnhub_key)
        if data:
            result["primary_data"] = data
            result["sources_succeeded"].append("Finnhub")
            _cache.set(cache_key, result)
            return result

    # Try TwelveData (fallback 1)
    twelvedata_key = api_keys.get("twelvedata_key")
    if twelvedata_key:
        result["sources_attempted"].append("TwelveData")
        data = fetch_twelvedata_quote(symbol, twelvedata_key)
        if data:
            result["primary_data"] = data
            result["sources_succeeded"].append("TwelveData")
            _cache.set(cache_key, result)
            return result

    # Try yfinance (fallback 2)
    result["sources_attempted"].append("yfinance")
    data = fetch_yfinance_quote(symbol)
    if data:
        result["primary_data"] = data
        result["sources_succeeded"].append("yfinance")
        _cache.set(cache_key, result)
        return result

    logger.error(f"All equity providers failed for {symbol}")
    _cache.set(cache_key, result)
    return result


# ============================================================================
# Fundamentals Provider (FinancialModelingPrep)
# ============================================================================

def fetch_fmp_fundamentals(symbol: str, api_key: str, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """
    Fetch company fundamentals and key ratios from FMP.

    Args:
        symbol: Stock ticker
        api_key: FMP API key
        timeout: Request timeout

    Returns:
        Dict with fundamental metrics
    """
    try:
        # Fetch key metrics
        url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}"
        params = {"apikey": api_key, "limit": 1}

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if not data or not isinstance(data, list):
            logger.warning(f"FMP: Invalid fundamentals response for {symbol}")
            return None

        metrics = data[0] if data else {}

        # Fetch ratios
        ratios_url = f"https://financialmodelingprep.com/api/v3/ratios/{symbol}"
        ratios_response = requests.get(ratios_url, params=params, timeout=timeout)
        ratios_response.raise_for_status()
        ratios_data = ratios_response.json()
        ratios = ratios_data[0] if ratios_data and isinstance(ratios_data, list) else {}

        result = {
            "symbol": symbol,
            "source": "FinancialModelingPrep",
            "source_url": f"https://financialmodelingprep.com/financial-summary/{symbol}",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "pe_ratio": ratios.get("priceEarningsRatio"),
                "price_to_book": ratios.get("priceToBookRatio"),
                "debt_to_equity": ratios.get("debtEquityRatio"),
                "roe": ratios.get("returnOnEquity"),
                "roa": ratios.get("returnOnAssets"),
                "market_cap": metrics.get("marketCap"),
                "revenue_per_share": metrics.get("revenuePerShare"),
                "net_income_per_share": metrics.get("netIncomePerShare"),
                "period": metrics.get("period", "TTM")
            },
            "raw": {"metrics": metrics, "ratios": ratios}
        }

        logger.info(f"FMP: Fetched fundamentals for {symbol}")
        return result

    except Exception as e:
        logger.warning(f"FMP fundamentals fetch failed for {symbol}: {e}")
        return None


def _safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float, handling Alpha Vantage's 'None' strings.

    Args:
        value: Value to convert (could be number, string, None, or "None")

    Returns:
        Float value or None if invalid
    """
    if value is None or value == "" or value == "None":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def fetch_alpha_vantage_fundamentals(symbol: str, api_key: str, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Fetch company fundamentals from Alpha Vantage (Overview endpoint).

    Args:
        symbol: Stock ticker
        api_key: Alpha Vantage API key
        timeout: Request timeout

    Returns:
        Dict with fundamental metrics
    """
    try:
        # Alpha Vantage Company Overview endpoint
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": api_key
        }

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if "Error Message" in data or "Note" in data:
            logger.warning(f"Alpha Vantage: API error for {symbol}: {data.get('Error Message') or data.get('Note')}")
            return None

        if not data or "Symbol" not in data:
            logger.warning(f"Alpha Vantage: No data returned for {symbol}")
            return None

        # Extract key metrics using safe conversion
        metrics = {
            "market_cap": _safe_float(data.get("MarketCapitalization")),
            "pe_ratio": _safe_float(data.get("PERatio")),
            "price_to_book": _safe_float(data.get("PriceToBookRatio")),
            "debt_to_equity": _safe_float(data.get("DebtToEquity")),
            "roe": _safe_float(data.get("ReturnOnEquityTTM")),
            "roa": _safe_float(data.get("ReturnOnAssetsTTM")),
            "revenue_ttm": _safe_float(data.get("RevenueTTM")),
            "gross_profit_ttm": _safe_float(data.get("GrossProfitTTM")),
            "eps": _safe_float(data.get("EPS")),
            "dividend_yield": _safe_float(data.get("DividendYield")),
            "profit_margin": _safe_float(data.get("ProfitMargin")),
            "operating_margin_ttm": _safe_float(data.get("OperatingMarginTTM")),
            "period": "TTM"
        }

        # Check if we got at least some valid metrics
        valid_metrics = [v for v in metrics.values() if v is not None and v != "TTM"]
        if not valid_metrics:
            logger.warning(f"Alpha Vantage: No valid metrics returned for {symbol}")
            return None

        result = {
            "symbol": symbol,
            "source": "AlphaVantage",
            "source_url": f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "raw": data
        }

        logger.info(f"Alpha Vantage: Fetched fundamentals for {symbol} ({len(valid_metrics)} valid metrics)")
        return result

    except requests.exceptions.Timeout:
        logger.warning(f"Alpha Vantage fundamentals timeout for {symbol}")
        return None
    except Exception as e:
        logger.warning(f"Alpha Vantage fundamentals fetch failed for {symbol}: {e}")
        return None


def fetch_fundamentals(symbol: str, api_keys: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch fundamental data for a symbol with fallback chain.

    Tries Alpha Vantage first, then FMP as fallback.

    Args:
        symbol: Stock ticker
        api_keys: Dict with keys: alpha_vantage_key, fmp_key

    Returns:
        Dict with fundamental data
    """
    cache_key = f"fundamentals:{symbol}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    result = {
        "symbol": symbol,
        "data_type": "fundamentals",
        "data": None,
        "sources_attempted": [],
        "sources_succeeded": [],
        "fetch_time": datetime.now(timezone.utc).isoformat()
    }

    # Try Alpha Vantage first
    av_key = api_keys.get("alpha_vantage_key")
    if av_key:
        result["sources_attempted"].append("AlphaVantage")
        data = fetch_alpha_vantage_fundamentals(symbol, av_key)
        if data:
            result["data"] = data
            result["sources_succeeded"].append("AlphaVantage")
            _cache.set(cache_key, result)
            return result

    # Fallback to FMP
    fmp_key = api_keys.get("fmp_key")
    if fmp_key:
        result["sources_attempted"].append("FinancialModelingPrep")
        data = fetch_fmp_fundamentals(symbol, fmp_key)
        if data:
            result["data"] = data
            result["sources_succeeded"].append("FinancialModelingPrep")

    _cache.set(cache_key, result)
    return result


# ============================================================================
# SEC EDGAR Filings
# ============================================================================

def fetch_sec_filings(symbol: str, email: str, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """
    Fetch recent SEC filings (10-K, 10-Q) links for a symbol.

    Args:
        symbol: Stock ticker
        email: Contact email (required by SEC)
        timeout: Request timeout

    Returns:
        Dict with filing links
    """
    try:
        # SEC requires User-Agent with email
        headers = {
            "User-Agent": f"LLM-Fin-Chatbot {email}"
        }

        # Search for CIK (Central Index Key)
        cik_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "ticker": symbol,
            "output": "json"
        }

        response = requests.get(cik_url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()

        # SEC doesn't return JSON for this endpoint, use submissions API instead
        # Try submissions API
        submissions_url = f"https://data.sec.gov/submissions/CIK{symbol}.json"

        # Get CIK from ticker lookup (simpler approach)
        # Use SEC company tickers JSON
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        tickers_response = requests.get(tickers_url, headers=headers, timeout=timeout)
        tickers_response.raise_for_status()
        tickers_data = tickers_response.json()

        # Find CIK for symbol
        cik = None
        for entry in tickers_data.values():
            if entry["ticker"].upper() == symbol.upper():
                cik = str(entry["cik_str"]).zfill(10)
                break

        if not cik:
            logger.warning(f"SEC: CIK not found for {symbol}")
            return None

        # Fetch submissions
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        sub_response = requests.get(submissions_url, headers=headers, timeout=timeout)
        sub_response.raise_for_status()
        sub_data = sub_response.json()

        # Extract recent 10-K and 10-Q filings
        filings = sub_data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accession_numbers = filings.get("accessionNumber", [])
        filing_dates = filings.get("filingDate", [])

        recent_filings = []
        for i, form in enumerate(forms):
            if form in ["10-K", "10-Q"] and len(recent_filings) < 5:
                accession = accession_numbers[i].replace("-", "")
                filing_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_numbers[i]}"
                recent_filings.append({
                    "form_type": form,
                    "filing_date": filing_dates[i],
                    "url": filing_url
                })

        result = {
            "symbol": symbol,
            "cik": cik,
            "source": "SEC EDGAR",
            "source_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "filings": recent_filings
        }

        logger.info(f"SEC: Fetched {len(recent_filings)} filings for {symbol}")
        return result

    except Exception as e:
        logger.warning(f"SEC EDGAR fetch failed for {symbol}: {e}")
        return None


def fetch_sec_filings_data(symbol: str, email: str) -> Dict[str, Any]:
    """
    Fetch SEC filing data with caching.

    Args:
        symbol: Stock ticker
        email: Contact email

    Returns:
        Dict with SEC filing links
    """
    cache_key = f"sec:{symbol}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    result = {
        "symbol": symbol,
        "data_type": "sec_filings",
        "data": None,
        "sources_attempted": ["SEC EDGAR"],
        "sources_succeeded": [],
        "fetch_time": datetime.now(timezone.utc).isoformat()
    }

    if email:
        data = fetch_sec_filings(symbol, email)
        if data:
            result["data"] = data
            result["sources_succeeded"].append("SEC EDGAR")

    _cache.set(cache_key, result)
    return result


# ============================================================================
# Crypto Provider (CoinGecko)
# ============================================================================

def fetch_coingecko_crypto(symbol: str, timeout: float = 2.5) -> Optional[Dict[str, Any]]:
    """
    Fetch crypto data from CoinGecko (free API, no key required).

    Args:
        symbol: Crypto symbol (e.g., "BTC", "ETH")
        timeout: Request timeout

    Returns:
        Normalized dict
    """
    try:
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "BNB": "binancecoin",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "LTC": "litecoin"
        }

        coin_id = symbol_map.get(symbol.upper(), symbol.lower())

        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if coin_id not in data:
            logger.warning(f"CoinGecko: No data for {symbol} (coin_id: {coin_id})")
            return None

        coin_data = data[coin_id]

        result = {
            "symbol": symbol.upper(),
            "price": round(coin_data["usd"], 2),
            "pct_change": round(coin_data.get("usd_24h_change", 0), 2),
            "ts_utc": datetime.fromtimestamp(coin_data["last_updated_at"], tz=timezone.utc).isoformat(),
            "source_url": f"https://www.coingecko.com/en/coins/{coin_id}",
            "source": "CoinGecko",
            "raw": coin_data
        }

        logger.info(f"CoinGecko: Fetched {symbol} @ ${result['price']} ({result['pct_change']:+.2f}%)")
        return result

    except Exception as e:
        logger.warning(f"CoinGecko fetch failed for {symbol}: {e}")
        return None


def fetch_crypto_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch cryptocurrency data.

    Args:
        symbol: Crypto symbol (e.g., "BTC")

    Returns:
        Dict with crypto data
    """
    cache_key = f"crypto:{symbol}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    result = {
        "symbol": symbol,
        "asset_type": "crypto",
        "primary_data": None,
        "sources_attempted": ["CoinGecko"],
        "sources_succeeded": [],
        "fetch_time": datetime.now(timezone.utc).isoformat()
    }

    data = fetch_coingecko_crypto(symbol)
    if data:
        result["primary_data"] = data
        result["sources_succeeded"].append("CoinGecko")

    _cache.set(cache_key, result)
    return result


# ============================================================================
# Unified Interface
# ============================================================================

def fetch_all_sources(symbol: str, asset_type: str = "auto",
                     api_keys: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Fetch data from all relevant sources for a symbol.

    Args:
        symbol: Ticker or crypto symbol
        asset_type: "equity", "crypto", or "auto" (detect from symbol)
        api_keys: Dict with API keys (finnhub_key, twelvedata_key, fmp_key, edgar_email)

    Returns:
        Comprehensive dict with all fetched data
    """
    if api_keys is None:
        api_keys = {}

    # Auto-detect asset type
    if asset_type == "auto":
        # Simple heuristic: common crypto symbols
        crypto_symbols = ["BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LTC"]
        asset_type = "crypto" if symbol.upper() in crypto_symbols else "equity"

    result = {
        "symbol": symbol,
        "asset_type": asset_type,
        "equity_data": None,
        "fundamentals": None,
        "sec_filings": None,
        "crypto_data": None,
        "sources_used": [],
        "fetch_time": datetime.now(timezone.utc).isoformat()
    }

    if asset_type == "equity":
        # Fetch equity data
        equity_result = fetch_equity_data(symbol, api_keys)
        if equity_result["primary_data"]:
            result["equity_data"] = equity_result
            result["sources_used"].extend(equity_result["sources_succeeded"])

        # Fetch fundamentals
        fundamentals_result = fetch_fundamentals(symbol, api_keys)
        if fundamentals_result["data"]:
            result["fundamentals"] = fundamentals_result
            result["sources_used"].extend(fundamentals_result["sources_succeeded"])

        # Fetch SEC filings
        edgar_email = api_keys.get("edgar_email")
        if edgar_email:
            sec_result = fetch_sec_filings_data(symbol, edgar_email)
            if sec_result["data"]:
                result["sec_filings"] = sec_result
                result["sources_used"].extend(sec_result["sources_succeeded"])

    elif asset_type == "crypto":
        # Fetch crypto data
        crypto_result = fetch_crypto_data(symbol)
        if crypto_result["primary_data"]:
            result["crypto_data"] = crypto_result
            result["sources_used"].extend(crypto_result["sources_succeeded"])

    return result


# ============================================================================
# Utility Functions
# ============================================================================

def clear_cache():
    """Clear the global cache."""
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "size": len(_cache.cache),
        "max_size": _cache.max_size,
        "ttl_seconds": _cache.ttl
    }


if __name__ == "__main__":
    # Test the module
    import os
    from dotenv import load_dotenv
    load_dotenv()

    # Setup logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    api_keys = {
        "finnhub_key": os.getenv("FINNHUB_API_KEY"),
        "twelvedata_key": os.getenv("TWELVEDATA_API_KEY"),
        "fmp_key": os.getenv("FMP_API_KEY"),
        "edgar_email": os.getenv("EDGAR_CONTACT_EMAIL")
    }

    print("\n" + "="*80)
    print("Testing Multi-Source Data Aggregator")
    print("="*80)

    # Test equity
    print("\n[TEST 1] Fetching equity data for AAPL...")
    result = fetch_all_sources("AAPL", "equity", api_keys)
    print(f"Sources used: {result['sources_used']}")
    if result['equity_data'] and result['equity_data']['primary_data']:
        data = result['equity_data']['primary_data']
        print(f"Price: ${data['price']} ({data['pct_change']:+.2f}%) from {data['source']}")

    # Test crypto
    print("\n[TEST 2] Fetching crypto data for BTC...")
    result = fetch_all_sources("BTC", "crypto", api_keys)
    print(f"Sources used: {result['sources_used']}")
    if result['crypto_data'] and result['crypto_data']['primary_data']:
        data = result['crypto_data']['primary_data']
        print(f"Price: ${data['price']} ({data['pct_change']:+.2f}%) from {data['source']}")

    # Test cache
    print("\n[TEST 3] Testing cache (fetching AAPL again)...")
    result = fetch_all_sources("AAPL", "equity", api_keys)
    print(f"Cache stats: {get_cache_stats()}")

    print("\n" + "="*80)
    print("Tests completed!")
    print("="*80)
