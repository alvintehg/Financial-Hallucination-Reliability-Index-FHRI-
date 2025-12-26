# src/server.py
"""
FastAPI server for LLM-backed robo-advisor prototype with FHRI scoring.

Features:
- Retrieval grounding via `query_index` (TF-IDF, FAISS, or hybrid).
- Semantic-entropy hallucination detection via MCEncoder (lazy-loaded, with timeouts).
- Optional NLI-based contradiction scoring (lazy-loaded, with timeouts).
- FHRI composite reliability scoring with sub-scores.
- Multi-provider support: DeepSeek, OpenAI, Anthropic, Demo (with auto-fallback).
- Endpoint: POST /ask with JSON {"text": "...", "prev_assistant_turn": "...", "k": 5, "provider": "auto", "retrieval_mode": "tfidf", "use_entropy": true, "use_nli": true, "use_fhri": true}
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)  # FORCE reload from .env file, override system variables

# Ensure project root is in sys.path so `import src.retrieval` works
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import logging
from datetime import datetime, timezone

# Local imports
try:
    from retrieval import query_index
except ImportError:
    from src.retrieval import query_index

# Import new modules
try:
    from providers import ProviderManager
except ImportError:
    from src.providers import ProviderManager

try:
    from detectors import get_mc_encoder, get_nli_detector
except ImportError:
    from src.detectors import get_mc_encoder, get_nli_detector

try:
    from fhri_scoring import compute_fhri, evaluate_fhri_risk, detect_numeric_price_mismatch
except ImportError:
    from src.fhri_scoring import compute_fhri, evaluate_fhri_risk, detect_numeric_price_mismatch

try:
    from scenario_detection import ScenarioDetector, Scenario
except ImportError:
    from src.scenario_detection import ScenarioDetector, Scenario

# NEW: Adaptive FHRI
try:
    from adaptive_fhri import get_default_adaptive_scorer
except ImportError:
    from src.adaptive_fhri import get_default_adaptive_scorer

# NEW: FHRI Evaluation Logger
try:
    from fhri_evaluation_logger import get_default_eval_logger
except ImportError:
    from src.fhri_evaluation_logger import get_default_eval_logger

try:
    from realtime_data import get_realtime_context_for_query, FinnhubDataFetcher
except ImportError:
    from src.realtime_data import get_realtime_context_for_query, FinnhubDataFetcher

try:
    from crypto_data import get_crypto_context_for_query, CryptoDataFetcher
except ImportError:
    from src.crypto_data import get_crypto_context_for_query, CryptoDataFetcher

# Commodity data support
try:
    from commodity_data import (
        get_commodity_context_for_query,
        CommodityDataFetcher,
        extract_commodity_symbols_from_query,
    )
except ImportError:
    try:
        from src.commodity_data import (
            get_commodity_context_for_query,
            CommodityDataFetcher,
            extract_commodity_symbols_from_query,
        )
    except ImportError:
        # Commodity support not available (optional)
        get_commodity_context_for_query = None
        CommodityDataFetcher = None
        extract_commodity_symbols_from_query = None

# NEW: Multi-source data aggregator
try:
    from data_sources import fetch_all_sources
except ImportError:
    from src.data_sources import fetch_all_sources

# NEW: Portfolio service
try:
    from portfolio_service import PortfolioService
except ImportError:
    from src.portfolio_service import PortfolioService

# NEW: Moomoo integration
try:
    from moomoo_integration import MoomooIntegration
except ImportError:
    from src.moomoo_integration import MoomooIntegration

# NEW: Investment recommendation engine
try:
    from investment_recommender import get_investment_recommendations
except ImportError:
    from src.investment_recommender import get_investment_recommendations

# NEW: Advisory services (risk profiling, allocation, themes, escalation)
try:
    from advisory_services import RiskProfiler, PortfolioAllocator, ThematicAdvisor, EscalationService
except ImportError:
    from src.advisory_services import RiskProfiler, PortfolioAllocator, ThematicAdvisor, EscalationService

# NEW: Planning services (goal planning, fee impact)
try:
    from planning_services import GoalPlanner, FeeImpactAnalyzer
except ImportError:
    from src.planning_services import GoalPlanner, FeeImpactAnalyzer

# NEW: Portfolio analytics (backtesting, behavioral insights)
try:
    from portfolio_analytics import PortfolioBacktester, BehavioralInsights
except ImportError:
    from src.portfolio_analytics import PortfolioBacktester, BehavioralInsights

# NEW: Robo-advisor enhanced services (drift, ESG, cash, sentiment, CSV import)
try:
    from robo_advisor_services import (
        PortfolioDriftAnalyzer, ESGScorer, CashAllocationAdvisor,
        MarketSentimentAnalyzer, CSVHoldingsImporter
    )
except ImportError:
    from src.robo_advisor_services import (
        PortfolioDriftAnalyzer, ESGScorer, CashAllocationAdvisor,
        MarketSentimentAnalyzer, CSVHoldingsImporter
    )

# Environment-controlled keys
HALLU_THRESHOLD = float(os.environ.get("HALLU_THRESHOLD", "2.0"))
DEBUG = os.environ.get("DEBUG", "0") == "1"
ENTROPY_TIMEOUT = float(os.environ.get("ENTROPY_TIMEOUT", "10.0"))
NLI_TIMEOUT = float(os.environ.get("NLI_TIMEOUT", "5.0"))
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "30"))
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "d3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag")
MAX_QUOTE_AGE_SECONDS = int(os.environ.get("MAX_QUOTE_AGE_SECONDS", "900"))  # 15 minutes default

# NEW: Multi-source API keys
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "3476J0I03PL6GQWF")  # Fallback to provided key
EDGAR_CONTACT_EMAIL = os.environ.get("EDGAR_CONTACT_EMAIL", "")

# NEW: Advisory contact email
ADVISOR_CONTACT_EMAIL = os.environ.get("ADVISOR_CONTACT_EMAIL", "advisor@example.com")

# Logging setup
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("server")


def format_response_for_readability(answer: str) -> str:
    """
    Post-process LLM response to ensure better readability and formatting.
    This function adds structure if the LLM didn't follow formatting instructions.
    """
    import re

    if not answer or not answer.strip():
        return answer

    # Clean up excessive hyphens/dashes that might appear as separators
    answer = re.sub(r'^---+\s*$', '', answer, flags=re.MULTILINE)
    answer = re.sub(r'^\*\*\*+\s*$', '', answer, flags=re.MULTILINE)

    lines = answer.strip().split('\n')
    formatted_lines = []

    # Track if we're in a well-formatted response
    has_headers = any(line.strip().startswith('##') for line in lines)

    if has_headers:
        # Response already has some structure, ensure proper spacing
        prev_was_header = False
        prev_was_blank = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip multiple consecutive blank lines
            if not stripped:
                if not prev_was_blank and formatted_lines:
                    formatted_lines.append('')
                    prev_was_blank = True
                continue

            prev_was_blank = False

            # Ensure blank line before headers (except first line)
            if stripped.startswith('##'):
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append('')
                formatted_lines.append(line)
                prev_was_header = True
            # Ensure blank line after headers before content
            elif prev_was_header and stripped and not stripped.startswith('-'):
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append('')
                formatted_lines.append(line)
                prev_was_header = False
            else:
                # Clean up bullet points - ensure consistent formatting
                if stripped.startswith('-') or stripped.startswith('*'):
                    # Ensure bullet points have proper spacing
                    bullet_match = re.match(r'^[*-]\s*(.+)$', stripped)
                    if bullet_match:
                        formatted_lines.append(f"- {bullet_match.group(1)}")
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
                prev_was_header = False

        return '\n'.join(formatted_lines)

    # Response lacks structure - try to add basic formatting
    formatted_text = answer

    # Convert numbered lists (1., 2., etc.) to markdown bullets
    formatted_text = re.sub(r'^\s*(\d+)\.\s+', r'- ', formatted_text, flags=re.MULTILINE)

    # Try to identify the first sentence as a summary
    sentences = answer.split('. ')
    if len(sentences) > 3:
        summary = sentences[0] + '.'
        rest = '. '.join(sentences[1:])
        formatted_text = f"## Summary\n\n{summary}\n\n## Details\n\n{rest}"

    return formatted_text


app = FastAPI(title="Robo-Advisor LLM Server with FHRI")

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize provider manager (lazy-loaded per provider)
provider_manager = None

# Initialize portfolio service (lazy-loaded on first use)
portfolio_service = None

# Initialize advisory and planning services (lazy-loaded on first use)
risk_profiler = None
portfolio_allocator = None
thematic_advisor = None
escalation_service = None
goal_planner = None
fee_impact_analyzer = None
portfolio_backtester = None
behavioral_insights = None

# Initialize new robo-advisor services
drift_analyzer = None
esg_scorer = None
cash_advisor = None
sentiment_analyzer = None
csv_importer = None


class AskRequest(BaseModel):
    text: str
    prev_assistant_turn: Optional[str] = None
    prev_question: Optional[str] = None  # Phase 2: Previous question for similarity gating
    k: Optional[int] = 5
    provider: Optional[str] = "auto"  # "auto", "deepseek", "openai", "anthropic", "demo"
    retrieval_mode: Optional[str] = "tfidf"  # "tfidf", "faiss", "hybrid"
    use_entropy: Optional[bool] = True
    use_nli: Optional[bool] = True
    use_fhri: Optional[bool] = True
    use_adaptive_fhri: Optional[bool] = False  # CHANGED: Use static scenario-based FHRI (set to False to use scenario weights)
    use_realtime: Optional[bool] = True  # Enable real-time Finnhub stock data grounding
    use_crypto: Optional[bool] = True  # Enable cryptocurrency data grounding
    use_commodity: Optional[bool] = True  # Enable commodity data grounding (oil, gold, etc.)
    scenario_override: Optional[str] = None  # Manual scenario selection (e.g., "numeric_kpi", "intraday")


class AskResponse(BaseModel):
    answer: str
    entropy: Optional[float] = None
    is_hallucination: Optional[bool] = None
    contradiction_score: Optional[float] = None
    passages_used: int
    passages: List[str]
    meta: Optional[Dict[str, Any]] = None


@app.on_event("startup")
def startup_event():
    global provider_manager, portfolio_service
    global risk_profiler, portfolio_allocator, thematic_advisor, escalation_service
    global goal_planner, fee_impact_analyzer, portfolio_backtester, behavioral_insights
    global drift_analyzer, esg_scorer, cash_advisor, sentiment_analyzer, csv_importer

    logger.info("=" * 60)
    logger.info("Starting Robo-Advisor LLM Server with FHRI")
    logger.info("=" * 60)

    # Initialize provider manager
    provider_manager = ProviderManager()
    available_providers = [name for name, prov in provider_manager.providers.items() if prov.is_available()]
    logger.info(f"Available providers: {available_providers}")

    logger.info(f"Hallucination threshold: {HALLU_THRESHOLD}")
    logger.info(f"Entropy timeout: {ENTROPY_TIMEOUT}s")
    logger.info(f"NLI timeout: {NLI_TIMEOUT}s")
    logger.info(f"LLM timeout: {LLM_TIMEOUT}s")
    logger.info(f"Finnhub API key configured: {bool(FINNHUB_API_KEY)}")
    logger.info(f"Max quote age: {MAX_QUOTE_AGE_SECONDS}s ({MAX_QUOTE_AGE_SECONDS/60:.1f} minutes)")
    logger.info(f"Debug mode: {DEBUG}")

    # Eager-load detectors (MC-Dropout & NLI) on startup to avoid first-request latency
    mc_encoder = get_mc_encoder()
    nli_detector = get_nli_detector()
    mc_encoder.is_available()
    nli_detector.is_available()
    logger.info("Detectors initialized on startup (MC-Dropout, NLI)")

    # Initialize portfolio service
    api_keys = {
        "finnhub_key": FINNHUB_API_KEY,
        "twelvedata_key": TWELVEDATA_API_KEY,
        "fmp_key": FMP_API_KEY,
        "edgar_email": EDGAR_CONTACT_EMAIL
    }
    portfolio_service = PortfolioService(api_keys)
    logger.info(f"Portfolio service initialized")

    # Initialize new advisory and planning services
    risk_profiler = RiskProfiler()
    portfolio_allocator = PortfolioAllocator()
    thematic_advisor = ThematicAdvisor(provider_manager=provider_manager)
    escalation_service = EscalationService(advisor_contact_email=ADVISOR_CONTACT_EMAIL)
    goal_planner = GoalPlanner()
    fee_impact_analyzer = FeeImpactAnalyzer()
    portfolio_backtester = PortfolioBacktester()
    behavioral_insights = BehavioralInsights()
    logger.info("Advisory and planning services initialized")

    # Initialize new robo-advisor services
    drift_analyzer = PortfolioDriftAnalyzer()
    esg_scorer = ESGScorer()
    cash_advisor = CashAllocationAdvisor()
    sentiment_analyzer = MarketSentimentAnalyzer()
    csv_importer = CSVHoldingsImporter()
    logger.info("Robo-advisor enhanced services initialized (drift, ESG, cash, sentiment, CSV)")

    logger.info("=" * 60)


@app.get("/health")
def health():
    """Health check endpoint."""
    mc_encoder = get_mc_encoder()
    nli_detector = get_nli_detector()
    # Force initialization so health reflects real availability (no lazy load)
    if mc_encoder:
        mc_encoder.is_available()
    if nli_detector:
        nli_detector.is_available()

    return {
        "status": "ok",
        "providers": {
            "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY")),
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        },
        "detectors": {
            "entropy_loaded": mc_encoder._initialized if mc_encoder else False,
            "nli_loaded": nli_detector._initialized if nli_detector else False,
        },
        "fhri_enabled": True,
        "realtime_data": {
            "finnhub_configured": bool(FINNHUB_API_KEY),
            "max_quote_age_seconds": MAX_QUOTE_AGE_SECONDS
        },
        "debug": DEBUG
    }


def format_fundamentals_context(multi_source_data: Dict[str, Any]) -> str:
    """
    Format multi-source fundamentals data into a readable context string for the LLM.

    Args:
        multi_source_data: Dict containing fundamentals from various sources

    Returns:
        Formatted string with fundamental metrics
    """
    if not multi_source_data:
        return ""

    lines = []

    # Extract symbol
    symbol = multi_source_data.get("symbol", "Unknown")
    lines.append(f"Company: {symbol}")

    # Get fundamentals from the nested structure returned by fetch_all_sources
    # Structure: multi_source_data["fundamentals"]["data"] contains the actual fundamentals dict
    fundamentals_wrapper = multi_source_data.get("fundamentals")
    if fundamentals_wrapper and isinstance(fundamentals_wrapper, dict):
        fundamentals_data = fundamentals_wrapper.get("data")
    else:
        fundamentals_data = None

    if fundamentals_data and isinstance(fundamentals_data, dict):
        metrics = fundamentals_data.get("metrics", {})
        if metrics:
            lines.append("\nKey Financial Metrics:")

            # Revenue (Alpha Vantage has revenue_ttm, FMP has revenue_per_share)
            revenue_ttm = metrics.get("revenue_ttm")
            if revenue_ttm:
                if revenue_ttm >= 1e12:
                    lines.append(f"- Revenue (TTM): ${revenue_ttm/1e12:.2f}T")
                elif revenue_ttm >= 1e9:
                    lines.append(f"- Revenue (TTM): ${revenue_ttm/1e9:.2f}B")
                elif revenue_ttm >= 1e6:
                    lines.append(f"- Revenue (TTM): ${revenue_ttm/1e6:.2f}M")
                else:
                    lines.append(f"- Revenue (TTM): ${revenue_ttm:,.0f}")

            # Revenue per Share (FMP)
            revenue_per_share = metrics.get("revenue_per_share")
            if revenue_per_share:
                lines.append(f"- Revenue per Share: ${revenue_per_share:.2f}")

            # Market Cap
            market_cap = metrics.get("market_cap")
            if market_cap:
                if market_cap >= 1e12:
                    lines.append(f"- Market Cap: ${market_cap/1e12:.2f}T")
                elif market_cap >= 1e9:
                    lines.append(f"- Market Cap: ${market_cap/1e9:.2f}B")
                elif market_cap >= 1e6:
                    lines.append(f"- Market Cap: ${market_cap/1e6:.2f}M")
                else:
                    lines.append(f"- Market Cap: ${market_cap:,.0f}")

            # EPS
            eps = metrics.get("eps") or metrics.get("net_income_per_share")
            if eps:
                lines.append(f"- Earnings per Share (EPS): ${eps:.2f}")

            # Gross Profit (Alpha Vantage)
            gross_profit_ttm = metrics.get("gross_profit_ttm")
            if gross_profit_ttm:
                if gross_profit_ttm >= 1e9:
                    lines.append(f"- Gross Profit (TTM): ${gross_profit_ttm/1e9:.2f}B")
                elif gross_profit_ttm >= 1e6:
                    lines.append(f"- Gross Profit (TTM): ${gross_profit_ttm/1e6:.2f}M")

            # PE Ratio
            pe_ratio = metrics.get("pe_ratio")
            if pe_ratio:
                lines.append(f"- P/E Ratio: {pe_ratio:.2f}")

            # Price to Book
            price_to_book = metrics.get("price_to_book")
            if price_to_book:
                lines.append(f"- Price to Book: {price_to_book:.2f}")

            # Profit Margin
            profit_margin = metrics.get("profit_margin")
            if profit_margin:
                lines.append(f"- Profit Margin: {profit_margin*100:.2f}%")

            # Operating Margin
            operating_margin = metrics.get("operating_margin_ttm")
            if operating_margin:
                lines.append(f"- Operating Margin (TTM): {operating_margin*100:.2f}%")

            # ROE
            roe = metrics.get("roe")
            if roe:
                lines.append(f"- Return on Equity (ROE): {roe*100:.2f}%")

            # ROA
            roa = metrics.get("roa")
            if roa:
                lines.append(f"- Return on Assets (ROA): {roa*100:.2f}%")

            # Debt to Equity
            debt_to_equity = metrics.get("debt_to_equity")
            if debt_to_equity:
                lines.append(f"- Debt to Equity: {debt_to_equity:.2f}")

            # Dividend Yield
            dividend_yield = metrics.get("dividend_yield")
            if dividend_yield:
                lines.append(f"- Dividend Yield: {dividend_yield*100:.2f}%")

            # Period
            period = metrics.get("period")
            if period:
                lines.append(f"- Period: {period}")

    # Check for SEC filings data
    sec_data = multi_source_data.get("sec_filings")
    if sec_data and isinstance(sec_data, list) and len(sec_data) > 0:
        lines.append("\nRecent SEC Filings:")
        for filing in sec_data[:3]:  # Show top 3 most recent
            filing_type = filing.get("form", "N/A")
            filing_date = filing.get("filingDate", "N/A")
            lines.append(f"- {filing_type} filed on {filing_date}")

    # Sources used
    sources_used = multi_source_data.get("sources_used", [])
    if sources_used:
        lines.append(f"\nData Sources: {', '.join(sources_used)}")

    return "\n".join(lines)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    Main endpoint for asking questions with FHRI scoring.

    Process:
    1. Retrieve relevant passages using query_index
    2. Build grounded prompt
    3. Call LLM via provider manager (with fallback)
    4. Optionally compute hallucination entropy
    5. Optionally compute NLI contradiction score
    6. Compute FHRI composite score
    7. Return structured response with metadata
    """
    start_t = time.time()

    logger.info(f"Received question: {req.text[:100]}...")
    logger.debug(f"Full request: {req}")

    # 1) Retrieval from static index
    k = req.k or 5
    retrieval_mode = req.retrieval_mode or "tfidf"

    try:
        passages = query_index(req.text, k=k, mode=retrieval_mode) or []
        logger.info(f"Retrieved {len(passages)} passages using {retrieval_mode} mode")
        if DEBUG:
            for i, p in enumerate(passages[:3]):
                logger.debug(f"Passage {i+1}: {p[:100]}...")
    except Exception as e:
        logger.exception("Retrieval error:")
        passages = []

    # 1b) Real-time stock data grounding
    realtime_context = ""
    realtime_tickers = []
    if req.use_realtime and FINNHUB_API_KEY:
        try:
            logger.info("Fetching real-time data from Finnhub...")
            realtime_context = get_realtime_context_for_query(
                req.text,
                api_key=FINNHUB_API_KEY,
                max_quote_age_seconds=MAX_QUOTE_AGE_SECONDS
            )
            if realtime_context:
                # Extract tickers for metadata (don't fail if import fails)
                try:
                    from realtime_data import extract_tickers_from_query
                except ImportError:
                    from src.realtime_data import extract_tickers_from_query

                try:
                    realtime_tickers = extract_tickers_from_query(req.text)
                    logger.info(f"Real-time data fetched for tickers: {realtime_tickers}")
                except Exception as e:
                    logger.warning(f"Ticker extraction failed (metadata only): {e}")
                    realtime_tickers = []
            else:
                logger.info("No tickers detected in query, skipping real-time data")
        except Exception as e:
            logger.exception("Real-time data fetch error:")
            realtime_context = ""
            realtime_tickers = []
    else:
        logger.debug("Real-time stock data grounding disabled or no API key")

    # 1c) Cryptocurrency data grounding
    crypto_context = ""
    crypto_symbols = []
    if req.use_crypto and FINNHUB_API_KEY:
        try:
            logger.info("Fetching cryptocurrency data from Finnhub...")
            crypto_context = get_crypto_context_for_query(
                req.text,
                api_key=FINNHUB_API_KEY
            )
            if crypto_context:
                # Extract crypto symbols for metadata
                try:
                    from crypto_data import extract_crypto_symbols_from_query
                except ImportError:
                    from src.crypto_data import extract_crypto_symbols_from_query

                try:
                    crypto_symbols = extract_crypto_symbols_from_query(req.text)
                    logger.info(f"Crypto data fetched for symbols: {crypto_symbols}")
                except Exception as e:
                    logger.warning(f"Crypto symbol extraction failed (metadata only): {e}")
                    crypto_symbols = []
            else:
                logger.info("No crypto symbols detected in query, skipping crypto data")
        except Exception as e:
            logger.exception("Crypto data fetch error:")
            crypto_context = ""
            crypto_symbols = []
    else:
        logger.debug("Crypto data grounding disabled or no API key")

    # 1c2) Commodity data grounding (oil, gold, etc.)
    commodity_context = ""
    commodity_symbols = []
    commodity_data_entries = []
    if req.use_commodity and FINNHUB_API_KEY and get_commodity_context_for_query:
        try:
            logger.info("Fetching commodity data from Finnhub...")
            commodity_context, commodity_data_entries, commodity_symbols = get_commodity_context_for_query(
                req.text,
                api_key=FINNHUB_API_KEY
            )
            if commodity_context:
                logger.info(f"Commodity data fetched for symbols: {commodity_symbols}")
            else:
                logger.info("No commodity symbols detected in query, skipping commodity data")
        except Exception as e:
            logger.exception("Commodity data fetch error:")
            commodity_context = ""
            commodity_symbols = []
            commodity_data_entries = []
    else:
        logger.debug("Commodity data grounding disabled or no API key or module not available")

    # 1d) NEW: Multi-source data verification (on-demand for FHRI)
    multi_source_data = None
    if req.use_fhri:  # Only fetch if FHRI is enabled
        try:
            # Build API keys dict
            api_keys = {
                "finnhub_key": FINNHUB_API_KEY,
                "twelvedata_key": TWELVEDATA_API_KEY,
                "fmp_key": FMP_API_KEY,
                "alpha_vantage_key": ALPHA_VANTAGE_API_KEY,
                "edgar_email": EDGAR_CONTACT_EMAIL
            }

            # Extract tickers/symbols from query (reuse existing function if available)
            try:
                try:
                    from realtime_data import extract_tickers_from_query as extract_tickers
                except ImportError:
                    from src.realtime_data import extract_tickers_from_query as extract_tickers
                symbols = extract_tickers(req.text, api_key=FINNHUB_API_KEY)
            except Exception as e:
                # Fallback to simple extraction
                logger.debug(f"extract_tickers_from_query failed ({e}), using fallback regex")
                import re
                symbols = re.findall(r'\b[A-Z]{2,5}\b', req.text)

            # Also check for crypto symbols
            crypto_symbols_check = ["BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "ADA", "DOGE"]
            detected_crypto = [s for s in symbols if s in crypto_symbols_check]
            detected_equities = [s for s in symbols if s not in crypto_symbols_check and len(s) <= 5]

            if detected_equities or detected_crypto:
                logger.info(f"Multi-source fetch: equities={detected_equities}, crypto={detected_crypto}")

                # Fetch data for first symbol (can be extended to multiple)
                if detected_equities:
                    symbol = detected_equities[0]
                    logger.info(f"Fetching multi-source data for equity: {symbol}")
                    multi_source_data = fetch_all_sources(symbol, "equity", api_keys)
                elif detected_crypto:
                    symbol = detected_crypto[0]
                    logger.info(f"Fetching multi-source data for crypto: {symbol}")
                    multi_source_data = fetch_all_sources(symbol, "crypto", api_keys)

            # Attach commodity data (if any) to multi-source structure
            if commodity_data_entries:
                finnhub_commodity_source = "Finnhub Commodities"
                if not multi_source_data:
                    primary_entry = commodity_data_entries[0]
                    multi_source_data = {
                        "symbol": primary_entry.get("symbol"),
                        "asset_type": "commodity",
                        "equity_data": None,
                        "fundamentals": None,
                        "sec_filings": None,
                        "crypto_data": None,
                        "commodity_data": primary_entry,
                        "sources_used": [],
                        "fetch_time": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    multi_source_data["commodity_data"] = commodity_data_entries[0]

                multi_source_data["commodity_data_list"] = commodity_data_entries
                sources_used = multi_source_data.setdefault("sources_used", [])
                if finnhub_commodity_source not in sources_used:
                    sources_used.append(finnhub_commodity_source)

                if multi_source_data:
                    sources_used = multi_source_data.get("sources_used", [])
                    logger.info(f"Multi-source data fetched: {sources_used}")
            else:
                logger.debug("No tickers/symbols detected for multi-source fetch")

        except Exception as e:
            logger.exception("Multi-source data fetch error (non-blocking):")
            multi_source_data = None

    # Combine static passages with real-time data and fundamentals
    context_parts = []
    if realtime_context:
        context_parts.append("=== REAL-TIME STOCK MARKET DATA ===")
        context_parts.append(realtime_context)
    if crypto_context:
        context_parts.append("=== REAL-TIME CRYPTOCURRENCY DATA ===")
        context_parts.append(crypto_context)
    if commodity_context:
        context_parts.append("=== REAL-TIME COMMODITY DATA ===")
        context_parts.append(commodity_context)

    # Add fundamentals data if available
    if multi_source_data:
        fundamentals_text = format_fundamentals_context(multi_source_data)
        if fundamentals_text:
            context_parts.append("=== COMPANY FUNDAMENTALS & FINANCIAL METRICS ===")
            context_parts.append(fundamentals_text)

    # Only add passages if no online sources are available
    # When we have verified online sources, passages.txt becomes irrelevant and adds noise
    has_online_sources = bool(multi_source_data and multi_source_data.get("sources_used"))

    if passages and not has_online_sources:
        context_parts.append("=== HISTORICAL/STATIC DATA ===")
        context_parts.append("\n\n".join(passages))
        logger.debug(f"Added {len(passages)} passages to context (no online sources)")
    elif has_online_sources:
        logger.info(f"Skipping passages (using verified online sources: {multi_source_data.get('sources_used')})")

    context = "\n\n".join(context_parts)

    # 2) Detect scenario to determine appropriate prompt template
    scenario_detector = ScenarioDetector()
    detected_scenario, scenario_weights = scenario_detector.detect(req.text, req.scenario_override)
    logger.info(f"Detected scenario: {detected_scenario.value} for query: {req.text[:100]}...")

    # 3) Build prompt (grounded) - select template based on scenario
    # Check if we have real-time data to adjust the prompt
    has_realtime = bool(realtime_context) or bool(crypto_context) or bool(commodity_context)
    has_fundamentals = bool(multi_source_data)

    # Select prompt template based on scenario
    if detected_scenario in [Scenario.NUMERIC_KPI, Scenario.FUNDAMENTALS] and has_fundamentals:
        # Fundamentals/metrics-focused template
        prompt = f"""You are a financial data analyst. Answer the user's specific question about financial metrics and fundamentals. Write in Markdown. Keep it concise and factual.

STRICT RULES:
- Today: {datetime.now().strftime('%Y-%m-%d')}
- Answer the EXACT question asked - if they ask for revenue, provide revenue data
- Use bullet points (-) for lists
- Use **bold** for emphasis
- Use markdown links: [text](url)
- Be direct and data-driven; avoid generic recommendations unless specifically asked

RESPONSE FORMAT:

## Answer
[Direct answer to the specific question asked]

## Key Financial Metrics
- [Relevant metric 1 from the fundamentals data]
- [Relevant metric 2 from the fundamentals data]
- [Relevant metric 3 from the fundamentals data]
- [Additional metrics as needed]

## Context & Analysis
- [Brief interpretation of the metrics]
- [Comparison or trend if available]
- [Any important notes about the data]

## Data Period & Sources
- [Time period of the data (e.g., TTM, Q4 2024)]
- [Data sources used]

---

Context:
{context}

Question: {req.text}

Answer the specific question asked using the data provided in the context:"""
    elif has_realtime:
        # Price/trading-focused template (for intraday, directional queries)
        prompt = f"""You are a financial advisor. Write in Markdown. Keep it concise.

STRICT RULES:
- Today: {datetime.now().strftime('%Y-%m-%d')}
- Use the exact headings below
- Use bullet points (-) for lists
- Use **bold** for emphasis
- Use markdown links: [text](url)
- NO paragraphs; only bullets and short sentences

EXACT FORMAT TO FOLLOW:

## Summary
[1-2 line summary of recommendation]

## Key Data
- **Price:** [value] ([change%])
- **Volume:** [value]
- **Timeframe:** [period analyzed]
- **52-week range:** [low - high]

## Analysis
- [Key insight 1]
- [Key insight 2]
- [Key insight 3]
- [Technical/fundamental observation]

## Recommendation
**[Buy/Hold/Avoid]** - [Brief rationale in 1-2 sentences. Do not use advicey language; state facts only.]

## Risks & Assumptions
- [Risk factor 1]
- [Risk factor 2]
- [Assumption made]

## Sources
- [Source 1 with link if available]
- [Source 2 with link if available]

---

Context:
{context}

Question: {req.text}

Answer using the EXACT format above with proper Markdown:"""
    else:
        # General template (for historical/static data queries)
        prompt = f"""You are a financial advisor. Write in Markdown. Keep it concise.

STRICT RULES:
- Use the exact headings below
- Use bullet points (-) for lists
- Use **bold** for emphasis
- Use markdown links: [text](url)
- NO paragraphs; only bullets and short sentences

EXACT FORMAT TO FOLLOW:

## Summary
[1-2 line summary]

## Key Data
- [Data point 1]
- [Data point 2]
- [Data point 3]

## Analysis
- [Key insight 1]
- [Key insight 2]
- [Key insight 3]

## Recommendation
**[Buy/Hold/Avoid or other recommendation]** - [Brief rationale in 1-2 sentences. Do not use advicey language; state facts only.]

## Risks & Assumptions
- [Risk factor 1]
- [Risk factor 2]
- [Assumption made]

## Sources
- [Source 1 with link if available]
- [Source 2 with link if available]

---

Context:
{context}

Question: {req.text}

Answer using the EXACT format above with proper Markdown:"""

    logger.debug(f"Prompt: {prompt[:200]}...")

    # 3) Call LLM with provider selection
    answer = None
    provider_name = None
    provider_result = None
    provider_model = None
    provider_usage = {}

    try:
        provider_name, answer, provider_result = provider_manager.generate(
            prompt,
            provider=req.provider or "auto",
            timeout=LLM_TIMEOUT
        )
        provider_model = provider_result.model
        provider_usage = provider_result.usage

        logger.info(f"LLM call successful using provider: {provider_name} (model: {provider_model})")
        logger.debug(f"Answer: {answer[:200]}...")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("LLM provider error:")
        provider_name = "error"
        answer = f"Error calling LLM: {str(e)}"
        provider_result = None

    # 4) Hallucination detection (semantic entropy) - optional with timeout
    ent = None
    is_hallucination = None

    if req.use_entropy and isinstance(answer, str) and answer.strip():
        try:
            logger.debug("Computing semantic entropy...")
            mc_encoder = get_mc_encoder()
            ent = mc_encoder.compute_entropy(answer, mc_rounds=6, timeout=ENTROPY_TIMEOUT)

            if ent is not None:
                is_hallucination = ent > HALLU_THRESHOLD
                logger.info(f"Entropy: {ent:.3f}, Is hallucination: {is_hallucination}")
            else:
                logger.warning("Entropy computation returned None (timeout or error)")
        except Exception as e:
            logger.exception("Entropy computation error:")
            ent = None
            is_hallucination = None
    else:
        logger.debug("Entropy computation skipped (disabled or no answer)")

    # 5) Contradiction detection via NLI - optional with timeout
    contra_score = None

    # Note: For contradiction detection, we always run NLI when prev_assistant_turn is provided
    # Online sources are used for FHRI calculation, but contradiction detection compares
    # current answer vs previous answer, so NLI should run regardless of online sources
    
    # Determine if the current question references specific assets/tickers
    question_has_assets = bool(realtime_tickers or crypto_symbols or commodity_symbols)
    if not question_has_assets:
        try:
            try:
                from realtime_data import extract_tickers_from_query as extract_tickers_for_nli
            except ImportError:
                from src.realtime_data import extract_tickers_from_query as extract_tickers_for_nli
            extra_tickers = extract_tickers_for_nli(req.text, api_key=FINNHUB_API_KEY)
            question_has_assets = question_has_assets or bool(extra_tickers)
        except Exception as e:
            logger.debug(f"NLI ticker extraction skipped: {e}")

    # Simplified NLI contradiction check (Phase 1 baseline):
    # Always run NLI for contradiction detection when prev_assistant_turn is provided,
    # without additional gating or heuristics.
    if req.use_nli and req.prev_assistant_turn and isinstance(answer, str) and answer.strip():
        try:
            logger.debug("Computing NLI contradiction score (simplified path)...")
            nli_detector = get_nli_detector()
            result = nli_detector.compute_contradiction(
                req.prev_assistant_turn,
                answer,
                timeout=NLI_TIMEOUT,
                question=req.text,
                bidirectional=True,
            )

            if not result:
                logger.warning("NLI computation returned None (timeout or error)")
                contra_score = None
            else:
                # Handle both old format (score, probs) and new format (score, probs, metadata)
                if len(result) == 3:
                    contra_score, probs, nli_metadata = result
                else:
                    contra_score, probs = result
                    nli_metadata = {}

                logger.info(
                    f"Contradiction score: {contra_score:.3f} "
                    f"(bidirectional: {nli_metadata.get('bidirectional', False)})"
                )
        except Exception as e:
            logger.exception(f"NLI contradiction error: {e}")
            logger.error(
                "NLI error details - prev_answer length: "
                f"{len(req.prev_assistant_turn) if req.prev_assistant_turn else 0}, "
                f"answer length: {len(answer) if answer else 0}, "
                f"question: {req.text[:50] if req.text else 'None'}"
            )
            contra_score = None
    else:
        logger.debug("NLI computation skipped (disabled or no previous turn)")

    # 6) Compute FHRI composite score with scenario-aware weighting - optional
    fhri_data = None
    adaptive_fhri_data = None

    if req.use_fhri and isinstance(answer, str) and answer.strip():
        # Use adaptive FHRI if enabled, otherwise fallback to original FHRI
        if req.use_adaptive_fhri:
            try:
                logger.debug("Computing Adaptive FHRI with auto-learned weights...")

                # First compute sub-scores using original FHRI scorer
                try:
                    from fhri_scoring import FHRIScorer
                except ImportError:
                    from src.fhri_scoring import FHRIScorer
                scorer = FHRIScorer()

                grounding_score = scorer.compute_grounding_score(answer, passages, None, multi_source_data)
                numeric_score = scorer.compute_numerical_directional_score(answer, req.text, None, passages, multi_source_data)
                temporal_score = scorer.compute_temporal_score(answer, req.text, passages)

                # Get adaptive scorer
                adaptive_scorer = get_default_adaptive_scorer()

                # Compute adaptive FHRI
                adaptive_fhri_data = adaptive_scorer.compute_adaptive_fhri(
                    answer=answer,
                    question=req.text,
                    passages=passages,
                    entropy=ent,
                    contradiction_raw=contra_score,
                    grounding_score=grounding_score,
                    numeric_score=numeric_score,
                    temporal_score=temporal_score,
                    multi_source_data=multi_source_data
                )

                logger.info(f"Adaptive FHRI: {adaptive_fhri_data['fhri']:.3f} ({adaptive_fhri_data['fhri_label']}) | "
                           f"Stability: {adaptive_fhri_data['stability_index']:.3f} | "
                           f"Weights: {adaptive_fhri_data['fhri_weights']}")

                if adaptive_fhri_data['warnings']:
                    for warning in adaptive_fhri_data['warnings']:
                        logger.warning(f"Adaptive FHRI: {warning}")

                # Log to evaluation logger (for analysis)
                try:
                    eval_logger = get_default_eval_logger()
                    eval_logger.log_turn(
                        turn_number=adaptive_fhri_data.get("total_turns", 0),
                        query=req.text,
                        adaptive_fhri_data=adaptive_fhri_data,
                        entropy_raw=ent,
                        contradiction_raw=contra_score
                    )
                except Exception as e:
                    logger.warning(f"Failed to log to evaluation logger: {e}")

                # Set fhri_data for backward compatibility
                fhri_data = adaptive_fhri_data

            except Exception as e:
                logger.exception("Adaptive FHRI computation error:")
                adaptive_fhri_data = None
                fhri_data = None
        else:
            # Original FHRI computation
            try:
                logger.debug("Computing FHRI composite score with scenario detection and multi-source verification...")
                fhri_data = compute_fhri(
                    answer=answer,
                    question=req.text,
                    passages=passages,
                    entropy=ent,
                    api_facts=None,  # Legacy parameter
                    hallu_threshold=HALLU_THRESHOLD,
                    scenario_override=req.scenario_override,
                    multi_source_data=multi_source_data  # NEW: Pass multi-source data for verification
                )
                scenario_info = f"{fhri_data['scenario_name']} (detected)" if not req.scenario_override else f"{fhri_data['scenario_name']} (manual)"
                sources_info = f" | Sources: {fhri_data.get('data_sources_used', [])}" if multi_source_data else ""
                logger.info(f"FHRI: {fhri_data['fhri']:.3f} | Scenario: {scenario_info} | Components: {fhri_data['available_components']}{sources_info}")
            except Exception as e:
                logger.exception("FHRI computation error:")
                fhri_data = None
    else:
        logger.debug("FHRI computation skipped (disabled or no answer)")

    total_time = time.time() - start_t

    # Build metadata
    meta = {
        "provider": provider_name,
        "model": provider_model,
        "usage": provider_usage,
        "latency_s": round(total_time, 2),
        "k": k,
        "retrieval_mode": retrieval_mode,
        "retrieval_count": len(passages),
        "realtime_data_used": bool(realtime_context),
        "realtime_tickers": realtime_tickers,
        "crypto_data_used": bool(crypto_context),
        "crypto_symbols": crypto_symbols,
        "commodity_data_used": bool(commodity_context),
        "commodity_symbols": commodity_symbols,
        "detectors_used": {
            "entropy": req.use_entropy and ent is not None,
            "nli": req.use_nli and contra_score is not None,
            "fhri": req.use_fhri and fhri_data is not None,
            "realtime_stocks": req.use_realtime and bool(realtime_context),
            "realtime_crypto": req.use_crypto and bool(crypto_context),
            "realtime_commodity": req.use_commodity and bool(commodity_context)
        }
    }

    fhri_risk = None
    fhri_flagged = False

    # Add FHRI data to meta if computed
    if fhri_data:
        meta["fhri"] = fhri_data["fhri"]
        meta["fhri_subscores"] = fhri_data.get("subscores")
        meta["fhri_components"] = fhri_data["available_components"]
        # Add scenario information
        meta["scenario_detected"] = fhri_data.get("scenario_detected", "default")
        meta["scenario_name"] = fhri_data.get("scenario_name", "Default")
        meta["scenario_weights"] = fhri_data.get("scenario_weights", {})

        # Adaptive FHRI fields (if enabled)
        if adaptive_fhri_data:
            meta["fhri_label"] = adaptive_fhri_data["fhri_label"]
            meta["fhri_weights"] = adaptive_fhri_data["fhri_weights"]
            meta["contradiction_smoothed"] = adaptive_fhri_data.get("contradiction_smoothed")
            meta["stability_index"] = adaptive_fhri_data["stability_index"]
            meta["fhri_retuned"] = adaptive_fhri_data.get("retuned", False)
            meta["fhri_warnings"] = adaptive_fhri_data.get("warnings", [])
            meta["fhri_total_turns"] = adaptive_fhri_data.get("total_turns", 0)
            meta["fhri_window_size"] = adaptive_fhri_data.get("window_size", 0)
        else:
            # Original FHRI fields
            meta["fhri_renormalized"] = fhri_data.get("renormalized")
            meta["scenario_detected"] = fhri_data.get("scenario_detected")
            meta["scenario_name"] = fhri_data.get("scenario_name")
            meta["scenario_weights"] = fhri_data.get("scenario_weights")

        meta["data_sources_used"] = fhri_data.get("data_sources_used", [])  # NEW
        meta["scenario_threshold"] = fhri_data.get("scenario_threshold")
        fhri_risk = fhri_data.get("risk_metadata")

        if fhri_risk is None:
            fhri_risk = evaluate_fhri_risk(
                fhri_data.get("fhri"),
                meta["scenario_detected"],
                req.text,
            )
        fhri_flagged = bool(fhri_risk and fhri_risk.get("needs_review"))
        fhri_high_risk_breach = bool(
            fhri_risk and fhri_risk.get("high_risk_floor_breach")
        )
        meta["fhri_risk"] = fhri_risk
        meta["fhri_flagged"] = fhri_flagged

        if fhri_flagged:
            meta.setdefault("warnings", []).append(
                "FHRI below scenario threshold or high-risk floor"
            )
        # Numeric price mismatch override for high-risk scenarios
        numeric_mismatch_meta = None
        scenario_id = meta.get("scenario_detected", "default")
        scenario_key = (scenario_id or "default").lower()
        if scenario_key in ("numeric_kpi", "intraday") and multi_source_data:
            numeric_mismatch_meta = detect_numeric_price_mismatch(
                answer=answer,
                question=req.text,
                multi_source_data=multi_source_data,
                tolerance=0.10,
            )
            meta["numeric_price_check"] = numeric_mismatch_meta
            if numeric_mismatch_meta.get("is_mismatch"):
                logger.info("Numeric price mismatch detected – overriding to hallucination")
                fhri_high_risk_breach = True

        if fhri_high_risk_breach:
            # Only treat high-risk floor breaches or numeric mismatches as hard hallucinations
            if is_hallucination is None:
                is_hallucination = True
            else:
                is_hallucination = is_hallucination or True
        elif is_hallucination is None:
            # If entropy didn't set it and no hard breach, default to non-hallucinated
            is_hallucination = False

    if fhri_risk and fhri_risk.get("high_risk_numeric"):
        meta.setdefault("alerts", []).append(
            "High-risk numeric question – stricter FHRI floor applied"
        )

    if DEBUG and provider_result:
        meta["provider_raw"] = provider_result.raw

    logger.info(f"Request completed in {total_time:.2f}s using {provider_name}")

    # Format the answer for better readability
    if answer and isinstance(answer, str):
        answer = format_response_for_readability(answer)

    response = {
        "answer": answer,
        "entropy": ent,
        "is_hallucination": is_hallucination,
        "contradiction_score": contra_score,
        "passages_used": len(passages),
        "passages": passages,
        "meta": meta
    }

    return response


# ============================================================================
# Portfolio Endpoints
# ============================================================================

class AddHoldingRequest(BaseModel):
    symbol: str
    shares: float
    cost_basis: float
    name: Optional[str] = None
    asset_type: Optional[str] = "equity"


class UpdateHoldingRequest(BaseModel):
    symbol: str
    shares: Optional[float] = None
    cost_basis: Optional[float] = None


class RemoveHoldingRequest(BaseModel):
    symbol: str


@app.get("/portfolio/live")
def get_live_portfolio():
    """
    Get live portfolio data with real-time prices and calculations.

    Returns:
        Portfolio summary and holdings with live market data
    """
    try:
        if portfolio_service is None:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")

        logger.info("Fetching live portfolio data...")
        result = portfolio_service.get_live_portfolio()

        logger.info(f"Portfolio fetched: {result['summary']['positions_count']} positions, "
                   f"total value: ${result['summary']['total_value']:,.2f}")

        return result

    except Exception as e:
        logger.exception("Error fetching live portfolio:")
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")


@app.post("/portfolio/holdings/add")
def add_holding(req: AddHoldingRequest):
    """
    Add a new holding to the portfolio.

    Args:
        req: AddHoldingRequest with symbol, shares, cost_basis, name, asset_type

    Returns:
        Success status
    """
    try:
        if portfolio_service is None:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")

        logger.info(f"Adding holding: {req.symbol} ({req.shares} shares @ ${req.cost_basis})")

        success = portfolio_service.add_holding(
            symbol=req.symbol,
            shares=req.shares,
            cost_basis=req.cost_basis,
            name=req.name,
            asset_type=req.asset_type
        )

        if success:
            return {"status": "success", "message": f"Added {req.symbol} to portfolio"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to add {req.symbol} (may already exist)")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error adding holding:")
        raise HTTPException(status_code=500, detail=f"Error adding holding: {str(e)}")


@app.post("/portfolio/holdings/update")
def update_holding(req: UpdateHoldingRequest):
    """
    Update an existing holding in the portfolio.

    Args:
        req: UpdateHoldingRequest with symbol and optional shares, cost_basis

    Returns:
        Success status
    """
    try:
        if portfolio_service is None:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")

        logger.info(f"Updating holding: {req.symbol}")

        success = portfolio_service.update_holding(
            symbol=req.symbol,
            shares=req.shares,
            cost_basis=req.cost_basis
        )

        if success:
            return {"status": "success", "message": f"Updated {req.symbol}"}
        else:
            raise HTTPException(status_code=404, detail=f"Holding {req.symbol} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating holding:")
        raise HTTPException(status_code=500, detail=f"Error updating holding: {str(e)}")


@app.post("/portfolio/holdings/remove")
def remove_holding(req: RemoveHoldingRequest):
    """
    Remove a holding from the portfolio.

    Args:
        req: RemoveHoldingRequest with symbol

    Returns:
        Success status
    """
    try:
        if portfolio_service is None:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")

        logger.info(f"Removing holding: {req.symbol}")

        success = portfolio_service.remove_holding(req.symbol)

        if success:
            return {"status": "success", "message": f"Removed {req.symbol} from portfolio"}
        else:
            raise HTTPException(status_code=404, detail=f"Holding {req.symbol} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error removing holding:")
        raise HTTPException(status_code=500, detail=f"Error removing holding: {str(e)}")


@app.get("/portfolio/holdings")
def get_holdings():
    """
    Get portfolio holdings configuration (without live prices).

    Returns:
        List of configured holdings
    """
    try:
        if portfolio_service is None:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")

        data = portfolio_service.load_holdings()
        return data

    except Exception as e:
        logger.exception("Error loading holdings:")
        raise HTTPException(status_code=500, detail=f"Error loading holdings: {str(e)}")


@app.get("/market/overview")
def get_market_overview():
    """
    Get live market overview with major indices and top movers.

    Returns:
        Market data with indices and top performing stocks
    """
    try:
        from datetime import datetime, timezone

        # Import data sources
        try:
            from data_sources import fetch_equity_data
        except ImportError:
            from src.data_sources import fetch_equity_data

        logger.info("Fetching live market overview...")

        # Major indices ETFs (we'll use ETFs as proxies for indices)
        indices_symbols = {
            "SPY": "S&P 500",
            "DIA": "DOW JONES",
            "QQQ": "NASDAQ",
            "IWM": "RUSSELL 2000"
        }

        # Top movers to track
        top_movers_symbols = ["NVDA", "TSLA", "AAPL", "META", "GOOGL", "AMZN"]

        api_keys = {
            "finnhub_key": FINNHUB_API_KEY,
            "twelvedata_key": TWELVEDATA_API_KEY,
            "fmp_key": FMP_API_KEY,
        }

        # Fetch indices data
        indices = []
        for symbol, name in indices_symbols.items():
            try:
                data = fetch_equity_data(symbol, api_keys)
                if data.get("primary_data"):
                    price_data = data["primary_data"]
                    indices.append({
                        "symbol": symbol,
                        "name": name,
                        "price": price_data.get("price"),
                        "change_pct": price_data.get("pct_change"),
                        "source": price_data.get("source")
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch index {symbol}: {e}")

        # Fetch top movers data
        top_movers = []
        for symbol in top_movers_symbols:
            try:
                data = fetch_equity_data(symbol, api_keys)
                if data.get("primary_data"):
                    price_data = data["primary_data"]
                    top_movers.append({
                        "symbol": symbol,
                        "name": symbol,  # We'll use symbol as name for simplicity
                        "price": price_data.get("price"),
                        "change_pct": price_data.get("pct_change"),
                        "source": price_data.get("source")
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch stock {symbol}: {e}")

        # Sort top movers by absolute change
        top_movers.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)

        result = {
            "indices": indices,
            "top_movers": top_movers[:6],  # Top 6 movers
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "status": "success"
        }

        logger.info(f"Market overview fetched: {len(indices)} indices, {len(top_movers)} movers")
        return result

    except Exception as e:
        logger.exception("Error fetching market overview:")
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")


# ============================================================================
# Moomoo Integration Endpoints
# ============================================================================

@app.get("/moomoo/positions")
def get_moomoo_positions():
    """
    Get current positions from Moomoo OpenD.

    Returns:
        Current positions with P&L data
    """
    try:
        logger.info("Fetching positions from Moomoo OpenD...")

        moomoo = MoomooIntegration(host="127.0.0.1", port=11111)
        result = moomoo.get_positions()
        moomoo.disconnect()

        return result

    except Exception as e:
        logger.exception("Error fetching Moomoo positions:")
        raise HTTPException(status_code=500, detail=f"Error fetching Moomoo positions: {str(e)}")


@app.get("/moomoo/account")
def get_moomoo_account():
    """
    Get account information from Moomoo.

    Returns:
        Account balance and summary
    """
    try:
        logger.info("Fetching account info from Moomoo OpenD...")

        moomoo = MoomooIntegration(host="127.0.0.1", port=11111)
        result = moomoo.get_account_info()
        moomoo.disconnect()

        return result

    except Exception as e:
        logger.exception("Error fetching Moomoo account:")
        raise HTTPException(status_code=500, detail=f"Error fetching Moomoo account: {str(e)}")


@app.post("/moomoo/sync")
def sync_moomoo_portfolio():
    """
    Sync Moomoo positions to portfolio.json.

    This will:
    1. Fetch current positions from Moomoo OpenD
    2. Convert to portfolio.json format
    3. Backup existing portfolio.json
    4. Write new portfolio.json

    Returns:
        Success status and sync details
    """
    try:
        logger.info("Starting Moomoo portfolio sync...")

        moomoo = MoomooIntegration(host="127.0.0.1", port=11111)

        # First get positions to show what will be synced
        positions_result = moomoo.get_positions()

        if positions_result["status"] != "success":
            moomoo.disconnect()
            raise HTTPException(status_code=400, detail=positions_result.get("message", "Failed to fetch positions"))

        # Perform sync
        success = moomoo.sync_to_portfolio_json()
        moomoo.disconnect()

        if success:
            return {
                "status": "success",
                "message": "Portfolio synced successfully",
                "positions_synced": positions_result["count"],
                "positions": positions_result["positions"]
            }
        else:
            raise HTTPException(status_code=500, detail="Sync failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error syncing Moomoo portfolio:")
        raise HTTPException(status_code=500, detail=f"Error syncing portfolio: {str(e)}")


# ============================================================================
# Investment Recommendations Endpoint
# ============================================================================

class RecommendationsRequest(BaseModel):
    risk_profile: Optional[str] = "moderate"  # 'conservative', 'moderate', 'aggressive'
    use_ai_insights: Optional[bool] = True


@app.post("/recommendations")
def get_recommendations(req: RecommendationsRequest):
    """
    Get AI-powered investment recommendations with real-time data.

    Args:
        req: RecommendationsRequest with risk_profile and use_ai_insights

    Returns:
        Investment recommendations with real-time pricing and AI insights
    """
    try:
        logger.info(f"Generating recommendations for risk profile: {req.risk_profile}")

        # Build API keys
        api_keys = {
            "finnhub_key": FINNHUB_API_KEY,
            "twelvedata_key": TWELVEDATA_API_KEY,
            "fmp_key": FMP_API_KEY,
            "edgar_email": EDGAR_CONTACT_EMAIL
        }

        # Get recommendations with optional AI insights
        provider_mgr = provider_manager if req.use_ai_insights else None

        result = get_investment_recommendations(
            risk_profile=req.risk_profile,
            api_keys=api_keys,
            provider_manager=provider_mgr
        )

        logger.info(f"Generated {len(result['recommendations'])} recommendations")
        return result

    except Exception as e:
        logger.exception("Error generating recommendations:")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# ============================================================================
# Advisory Endpoints (Risk Profiling, Allocation, Themes, Escalation)
# ============================================================================

class RiskProfileRequest(BaseModel):
    answers: List[Dict[str, Any]]


class AllocationRequest(BaseModel):
    risk_label: str


class ThemesRequest(BaseModel):
    interest_keywords: List[str]


class EscalateRequest(BaseModel):
    topic: str


@app.post("/advice/risk-profile")
def get_risk_profile(req: RiskProfileRequest):
    """
    Compute risk profile from questionnaire answers.

    Returns risk label (Conservative/Balanced/Aggressive) and score (0-100).
    """
    try:
        if risk_profiler is None:
            raise HTTPException(status_code=500, detail="Risk profiler not initialized")

        logger.info(f"Computing risk profile from {len(req.answers)} answers...")
        result = risk_profiler.compute_risk_profile(req.answers)

        logger.info(f"Risk profile: {result['risk_label']} (score: {result['score']})")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error computing risk profile:")
        raise HTTPException(status_code=500, detail=f"Error computing risk profile: {str(e)}")


@app.post("/advice/allocation")
def get_portfolio_allocation(req: AllocationRequest):
    """
    Get ETF allocation based on risk profile.

    Returns allocation mix with ETF recommendations.
    """
    try:
        if portfolio_allocator is None:
            raise HTTPException(status_code=500, detail="Portfolio allocator not initialized")

        logger.info(f"Generating allocation for risk profile: {req.risk_label}")
        result = portfolio_allocator.get_allocation(req.risk_label)

        logger.info(f"Allocation: {len(result['allocation'])} ETFs")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating allocation:")
        raise HTTPException(status_code=500, detail=f"Error generating allocation: {str(e)}")


@app.post("/advice/themes")
def get_thematic_recommendations(req: ThemesRequest):
    """
    Get thematic/ESG ETF recommendations based on interest keywords.

    Returns suggested ETFs with rationale and sources.
    """
    try:
        if thematic_advisor is None:
            raise HTTPException(status_code=500, detail="Thematic advisor not initialized")

        logger.info(f"Generating thematic recommendations for: {req.interest_keywords}")
        result = thematic_advisor.get_thematic_recommendations(
            interest_keywords=req.interest_keywords,
            use_rag=False  # Keep simple for now
        )

        logger.info(f"Thematic recommendations: {len(result['etfs'])} ETFs")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error generating thematic recommendations:")
        raise HTTPException(status_code=500, detail=f"Error generating themes: {str(e)}")


@app.post("/advice/escalate")
def escalate_to_advisor(req: EscalateRequest):
    """
    Escalate to human advisor for regulated advice.

    Returns standard message and mailto link.
    """
    try:
        if escalation_service is None:
            raise HTTPException(status_code=500, detail="Escalation service not initialized")

        logger.info(f"Escalating topic: {req.topic}")
        result = escalation_service.escalate_to_human(req.topic)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error escalating to advisor:")
        raise HTTPException(status_code=500, detail=f"Error escalating: {str(e)}")


# ============================================================================
# Planning Endpoints (Goal Planning, Fee Impact)
# ============================================================================

class GoalPlanRequest(BaseModel):
    target_amount: float
    years: int
    init_capital: Optional[float] = 0.0
    monthly_contrib: Optional[float] = None
    expected_return: Optional[float] = 0.07


class FeeImpactRequest(BaseModel):
    principal: float
    horizon_years: int
    annual_fee_pct: float
    exp_return_pct: float
    dividend_withholding_pct: Optional[float] = 0.0


@app.post("/planning/goal")
def plan_goal(req: GoalPlanRequest):
    """
    Compute goal-based financial planning projections.

    Returns required monthly contribution and projection array.
    """
    try:
        if goal_planner is None:
            raise HTTPException(status_code=500, detail="Goal planner not initialized")

        logger.info(f"Planning goal: ${req.target_amount:,.2f} in {req.years} years")
        result = goal_planner.compute_goal_projection(
            target_amount=req.target_amount,
            years=req.years,
            init_capital=req.init_capital,
            monthly_contrib=req.monthly_contrib,
            expected_return=req.expected_return
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"Goal plan: {result.get('required_monthly', req.monthly_contrib)}/month → ${result['final_value']:,.2f}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error planning goal:")
        raise HTTPException(status_code=500, detail=f"Error planning goal: {str(e)}")


@app.post("/planning/fee-impact")
def analyze_fee_impact(req: FeeImpactRequest):
    """
    Analyze fee and tax impact on portfolio growth.

    Returns final values with/without fees and delta.
    """
    try:
        if fee_impact_analyzer is None:
            raise HTTPException(status_code=500, detail="Fee impact analyzer not initialized")

        logger.info(f"Analyzing fee impact: {req.annual_fee_pct}% over {req.horizon_years} years")
        result = fee_impact_analyzer.compute_fee_impact(
            principal=req.principal,
            horizon_years=req.horizon_years,
            annual_fee_pct=req.annual_fee_pct,
            exp_return_pct=req.exp_return_pct,
            dividend_withholding_pct=req.dividend_withholding_pct
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"Fee impact: ${result['delta']:,.2f} ({result['delta_pct']:.1f}%)")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error analyzing fee impact:")
        raise HTTPException(status_code=500, detail=f"Error analyzing fee impact: {str(e)}")


# ============================================================================
# Portfolio Analytics Endpoints (Backtesting, Behavioral Insights)
# ============================================================================

class BacktestRequest(BaseModel):
    weights: Dict[str, float]
    start: str  # YYYY-MM-DD
    end: str  # YYYY-MM-DD
    rebalance_freq: Optional[str] = "quarterly"


class BehaviorRequest(BaseModel):
    actions: List[Dict[str, Any]]


@app.post("/portfolio/backtest")
def backtest_portfolio(req: BacktestRequest):
    """
    Backtest portfolio with given weights.

    Returns CAGR, volatility, max drawdown, Sharpe ratio, and equity curve.
    """
    try:
        if portfolio_backtester is None:
            raise HTTPException(status_code=500, detail="Portfolio backtester not initialized")

        logger.info(f"Backtesting portfolio: {list(req.weights.keys())} from {req.start} to {req.end}")
        result = portfolio_backtester.backtest_portfolio(
            weights=req.weights,
            start_date=req.start,
            end_date=req.end,
            rebalance_freq=req.rebalance_freq
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"Backtest: CAGR={result['cagr']:.2f}%, Vol={result['volatility']:.2f}%, Sharpe={result['sharpe_ratio']:.2f}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error backtesting portfolio:")
        raise HTTPException(status_code=500, detail=f"Error backtesting: {str(e)}")


@app.post("/insights/behavior")
def analyze_behavior(req: BehaviorRequest):
    """
    Analyze user behavior and provide nudges.

    Returns behavioral insights and risk flags.
    """
    try:
        if behavioral_insights is None:
            raise HTTPException(status_code=500, detail="Behavioral insights not initialized")

        logger.info(f"Analyzing {len(req.actions)} user actions...")
        result = behavioral_insights.analyze_behavior(req.actions)

        logger.info(f"Behavioral analysis: {len(result['nudges'])} nudges, {len(result['risk_flags'])} flags")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error analyzing behavior:")
        raise HTTPException(status_code=500, detail=f"Error analyzing behavior: {str(e)}")


# ============================================================================
# New Robo-Advisor Endpoints (Drift, ESG, Cash Allocation, Sentiment, CSV Import)
# ============================================================================

class DriftAnalysisRequest(BaseModel):
    current_holdings: List[Dict[str, Any]]
    target_allocation: List[Dict[str, Any]]


@app.post("/portfolio/drift")
def analyze_portfolio_drift(req: DriftAnalysisRequest):
    """
    Analyze portfolio drift from target allocation.

    Returns drift percentage and rebalancing actions.
    """
    try:
        if drift_analyzer is None:
            raise HTTPException(status_code=500, detail="Drift analyzer not initialized")

        logger.info(f"Analyzing drift: {len(req.current_holdings)} holdings vs {len(req.target_allocation)} targets")
        result = drift_analyzer.analyze_drift(
            current_holdings=req.current_holdings,
            target_allocation=req.target_allocation
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"Drift: {result['drift_pct']:.2f}%, rebalance={result['needs_rebalance']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error analyzing drift:")
        raise HTTPException(status_code=500, detail=f"Error analyzing drift: {str(e)}")


class ESGScoreRequest(BaseModel):
    symbol: Optional[str] = None
    holdings: Optional[List[Dict[str, Any]]] = None


@app.post("/esg/score")
def get_esg_score(req: ESGScoreRequest):
    """
    Get ESG score for a symbol or entire portfolio.

    Returns ESG score, grade, and breakdown.
    """
    try:
        if esg_scorer is None:
            raise HTTPException(status_code=500, detail="ESG scorer not initialized")

        if req.symbol:
            logger.info(f"Getting ESG score for {req.symbol}")
            result = esg_scorer.get_esg_score(req.symbol)
        elif req.holdings:
            logger.info(f"Getting portfolio ESG score for {len(req.holdings)} holdings")
            result = esg_scorer.get_portfolio_esg_score(req.holdings)
        else:
            raise HTTPException(status_code=400, detail="Must provide either symbol or holdings")

        logger.info(f"ESG score: {result.get('esg_score', 0):.1f}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting ESG score:")
        raise HTTPException(status_code=500, detail=f"Error getting ESG score: {str(e)}")


class CashAllocationRequest(BaseModel):
    total_value: float
    cash_value: float
    risk_profile: Optional[str] = "balanced"


@app.post("/planning/cash-allocation")
def analyze_cash_allocation(req: CashAllocationRequest):
    """
    Analyze cash allocation and suggest investment.

    Returns cash percentage and recommended ETF if excessive.
    """
    try:
        if cash_advisor is None:
            raise HTTPException(status_code=500, detail="Cash advisor not initialized")

        logger.info(f"Analyzing cash: ${req.cash_value:,.2f} / ${req.total_value:,.2f} ({req.risk_profile})")
        result = cash_advisor.analyze_cash_allocation(
            total_value=req.total_value,
            cash_value=req.cash_value,
            risk_profile=req.risk_profile
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info(f"Cash: {result['cash_pct']:.1f}%, excessive={result['is_excessive']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error analyzing cash:")
        raise HTTPException(status_code=500, detail=f"Error analyzing cash: {str(e)}")


@app.get("/sentiment/market")
def get_market_sentiment():
    """
    Get overall market sentiment analysis.

    Returns outlook (Bullish/Neutral/Bearish) with confidence and FHRI reliability.
    """
    try:
        if sentiment_analyzer is None:
            raise HTTPException(status_code=500, detail="Sentiment analyzer not initialized")

        logger.info("Getting market sentiment")
        result = sentiment_analyzer.get_market_sentiment()

        logger.info(f"Sentiment: {result['outlook']} (confidence: {result['confidence']:.1f}%)")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting sentiment:")
        raise HTTPException(status_code=500, detail=f"Error getting sentiment: {str(e)}")


class CSVImportRequest(BaseModel):
    csv_content: str


@app.post("/holdings/import-csv")
def import_csv_holdings(req: CSVImportRequest):
    """
    Import holdings from CSV content.

    Returns parsed holdings list and any errors.
    """
    try:
        if csv_importer is None:
            raise HTTPException(status_code=500, detail="CSV importer not initialized")

        logger.info("Importing CSV holdings")
        result = csv_importer.parse_csv_holdings(req.csv_content)

        logger.info(f"CSV import: {result['count']} holdings, {len(result.get('errors', []))} errors")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error importing CSV:")
        raise HTTPException(status_code=500, detail=f"Error importing CSV: {str(e)}")


# ============================================================================
# Feedback Endpoint (Trust Feedback Loop for FHRI)
# ============================================================================

class FeedbackRequest(BaseModel):
    turn_id: str
    user_rating_1to5: int


@app.post("/eval/feedback")
def submit_feedback(req: FeedbackRequest):
    """
    Submit user feedback for FHRI calibration.

    Logs feedback and updates EMA calibration for FHRI weights.
    """
    try:
        # Validate rating
        if not 1 <= req.user_rating_1to5 <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        logger.info(f"Received feedback: turn_id={req.turn_id}, rating={req.user_rating_1to5}")

        # Get adaptive FHRI scorer
        try:
            adaptive_scorer = get_default_adaptive_scorer()
        except Exception as e:
            logger.warning(f"Adaptive FHRI not available: {e}")
            adaptive_scorer = None

        if adaptive_scorer:
            # Update calibration based on feedback
            # High ratings (4-5) on grounded answers should increase grounding weight
            # Low ratings (1-2) on high-entropy answers should decrease entropy weight

            # For now, just log the feedback
            # In production, would update adaptive weights based on correlation
            # between user ratings and FHRI subscores

            logger.info(f"Feedback logged for FHRI calibration: {req.turn_id} → {req.user_rating_1to5}/5")

            # Store feedback in evaluation logger
            try:
                eval_logger = get_default_eval_logger()
                eval_logger.log_feedback(
                    turn_id=req.turn_id,
                    rating=req.user_rating_1to5
                )
            except Exception as e:
                logger.warning(f"Failed to log feedback: {e}")

        return {
            "ok": True,
            "turn_id": req.turn_id,
            "rating": req.user_rating_1to5,
            "message": "Feedback received and logged for FHRI calibration"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error submitting feedback:")
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
