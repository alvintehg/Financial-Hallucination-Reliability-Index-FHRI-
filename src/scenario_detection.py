"""
Scenario Detection Module for Finance Chatbot

Classifies user queries into finance-specific scenarios using regex and keyword matching.
Each scenario has custom FHRI weight profiles to optimize hallucination detection.

Scenarios:
1. Numeric KPI / Ratios - Questions about specific financial metrics
2. Directional Recap - Questions about price/market direction
3. Intraday / Real-time - Questions about current/recent market activity
4. Fundamentals / Long Horizon - Questions about long-term company fundamentals
5. Regulatory / Policy - Questions about regulations, compliance, policy
6. Portfolio Advice / Suitability - Questions about investment recommendations
7. Multi-Ticker Comparison - Questions comparing multiple stocks/assets
8. News Summarization - Questions about recent news or events
9. Default - Fallback for unclassified queries
"""

import re
from typing import Dict, Tuple
from enum import Enum


class Scenario(Enum):
    """Finance query scenario types"""
    NUMERIC_KPI = "numeric_kpi"
    DIRECTIONAL = "directional"
    INTRADAY = "intraday"
    FUNDAMENTALS = "fundamentals"
    REGULATORY = "regulatory"
    ADVICE = "advice"
    MULTI_TICKER = "multi_ticker"
    NEWS = "news"
    CRYPTO = "crypto"
    DEFAULT = "default"


# Scenario-specific FHRI weights (G, N/D, T, C, E)
# Updated to match target scenario-weighted defaults (pre-tuning) table
SCENARIO_WEIGHTS = {
    # Numeric/Real-Time Quote: Prioritizes numeric accuracy and grounding
    Scenario.NUMERIC_KPI: {
        "G": 0.30,      # Grounding
        "N_or_D": 0.40, # Numerical/Directional (highest - numeric accuracy critical)
        "T": 0.20,      # Temporal
        "C": 0.05,      # Citation
        "E": 0.05       # Entropy
    },
    # Directional Recap: Similar to numeric quote
    Scenario.DIRECTIONAL: {
        "G": 0.30,
        "N_or_D": 0.40, # Directional accuracy important
        "T": 0.20,      # Temporal context matters for direction
        "C": 0.05,
        "E": 0.05
    },
    # Intraday / Real-time: Same as numeric quote (real-time data)
    Scenario.INTRADAY: {
        "G": 0.30,
        "N_or_D": 0.40,
        "T": 0.20,      # Temporal accuracy critical for real-time data
        "C": 0.05,
        "E": 0.05
    },
    # Earnings/Fundamentals: Adjusted weights (ChatGPT & Gemini recommendation)
    Scenario.FUNDAMENTALS: {
        "G": 0.30,      # Reduced from 0.35
        "N_or_D": 0.35, # Keep same - numeric accuracy critical
        "T": 0.15,      # Keep same
        "C": 0.10,      # Keep same
        "E": 0.10       # Increased from 0.05 - confidence matters
    },
    # Regulatory / Policy: Citations are critical
    Scenario.REGULATORY: {
        "G": 0.20,
        "N_or_D": 0.05, # Numbers less critical
        "T": 0.20,
        "C": 0.40,      # Citations critical for regulatory claims
        "E": 0.15
    },
    # Comparative/Advisory: Adjusted weights (ChatGPT & Gemini recommendation)
    # Reduce G and C, boost N, T, E for advice scenarios
    Scenario.ADVICE: {
        "G": 0.25,      # Reduced from 0.35 - advice doesn't need perfect grounding
        "N_or_D": 0.30, # Increased from 0.25 - numeric consistency important
        "T": 0.15,      # Increased from 0.10 - temporal context matters
        "C": 0.10,      # Reduced from 0.15 - citations less critical for advice
        "E": 0.20       # Increased from 0.15 - confidence matters more
    },
    # Multi-Ticker Comparison: Adjusted weights (ChatGPT & Gemini recommendation)
    Scenario.MULTI_TICKER: {
        "G": 0.30,      # Reduced from 0.35
        "N_or_D": 0.30, # Increased from 0.25 - comparative numbers critical
        "T": 0.15,      # Increased from 0.10
        "C": 0.15,      # Reduced from 0.20
        "E": 0.10       # Keep same
    },
    # News/Thematic: Highest grounding, low numeric
    Scenario.NEWS: {
        "G": 0.45,      # Grounding in actual news critical
        "N_or_D": 0.10, # Numbers less important for news
        "T": 0.20,      # Temporal accuracy important for news
        "C": 0.15,      # Source citations important
        "E": 0.10
    },
    # Crypto/Blockchain: Balanced weights for crypto-related questions
    Scenario.CRYPTO: {
        "G": 0.35,      # Grounding important for crypto facts
        "N_or_D": 0.15, # Some numeric (prices, market cap)
        "T": 0.20,      # Temporal important (consensus changes, updates)
        "C": 0.20,      # Citations for crypto claims
        "E": 0.10       # Entropy
    },
    # General Definition/Edu: Balanced weights (FIXED from too strict)
    Scenario.DEFAULT: {
        "G": 0.40,      # Grounding important but not overly strict
        "N_or_D": 0.20, # Numeric can be relevant
        "T": 0.15,      # Temporal context matters
        "C": 0.15,      # Citations helpful
        "E": 0.10       # Entropy
    }
}


# Scenario detection patterns (order matters - first match wins)
SCENARIO_PATTERNS = [
    # Multi-Ticker Comparison (check FIRST - before directional)
    (
        Scenario.MULTI_TICKER,
        [
            r'\b(compare|comparison|versus|vs\.?|between)\b',
            r'\b(better|worse|outperform|underperform|relative to)\b',
            r'\b(which|what.*between|difference between)\b',
            # Multiple tickers in query
            r'\b[A-Z]{1,5}\s+(and|vs\.?|versus|or)\s+[A-Z]{1,5}\b',
        ],
        ["stocks", "companies", "sector", "peers", "competitors"]
    ),

    # Numeric KPI / Ratios
    (
        Scenario.NUMERIC_KPI,
        [
            r'\b(P/E|PE|price[ -]to[ -]earnings|price earnings)\b',
            r'\b(EPS|earnings per share)\b',
            r'\b(ROE|ROA|return on equity|return on assets)\b',
            r'\b(debt[ -]to[ -]equity|D/E|debt ratio)\b',
            r'\b(profit margin|operating margin|net margin)\b',
            r'\b(revenue|revenue growth|earnings|earnings growth|CAGR|sales)\b',
            r'\b(dividend yield|payout ratio)\b',
            r'\b(market cap|market capitalization)\b',
            r'\b(book value|price[ -]to[ -]book|P/B)\b',
            r'\b(current ratio|quick ratio|liquidity)\b',
            r'\b(EBITDA|free cash flow|FCF)\b',
            r'\b(beta|volatility|standard deviation)\b',
        ],
        ["ratio", "metric", "KPI", "indicator", "what is the", "calculate", "measure"]
    ),

    # Directional Recap
    (
        Scenario.DIRECTIONAL,
        [
            r'\b(up|down|rise|fall|gain|loss|increase|decrease|climb|drop|rally|decline)\b',
            r'\b(bullish|bearish|uptrend|downtrend)\b',
            r'\b(outperform|underperform|beat|miss)\b',
            r'\b(higher|lower|above|below)\b',
        ],
        ["direction", "trend", "moving", "going", "perform", "did"]
    ),

    # Intraday / Real-time
    (
        Scenario.INTRADAY,
        [
            r'\b(today|now|current|currently|right now|at the moment)\b',
            r'\b(intraday|real[ -]time|live|latest)\b',
            r'\b(this morning|this afternoon|so far today)\b',
            r'\b(opening|close|closing|after hours|pre[ -]market)\b',
            r'\b(session|trading day)\b',
        ],
        ["price", "quote", "trading", "volume", "movement"]
    ),

    # Regulatory / Policy
    (
        Scenario.REGULATORY,
        [
            r'\b(regulation|regulatory|SEC|FINRA|compliance|rule|law)\b',
            r'\b(policy|guideline|requirement|mandate|restriction)\b',
            r'\b(disclosure|filing|10-K|10-Q|8-K|proxy)\b',
            r'\b(Basel|Dodd[ -]Frank|MiFID|GDPR|SOX|Sarbanes)\b',
            r'\b(audit|oversight|supervision|enforcement)\b',
            r'\b(legal|statutory|regulatory framework)\b',
        ],
        ["require", "must", "allowed", "permitted", "compliant", "violation"]
    ),

    # Portfolio Advice / Suitability
    (
        Scenario.ADVICE,
        [
            r'\b(should I|recommend|suggestion|advice|portfolio)\b',
            r'\b(buy|sell|hold|invest|allocation|position)\b',
            r'\b(suitable|appropriate|right for me|good for)\b',
            r'\b(diversify|rebalance|hedge|strategy)\b',
            r'\b(risk tolerance|investment goal|time horizon)\b',
            r'\b(what.*do|how.*invest)\b',
        ],
        ["invest", "money", "retirement", "savings", "wealth", "financial plan"]
    ),

    # News Summarization
    (
        Scenario.NEWS,
        [
            r'\b(news|headline|announcement|report|press release)\b',
            r'\b(recently|latest|recent|just|new|breaking)\b',
            r'\b(happened|occurred|announced|reported|released)\b',
            r'\b(event|development|update|story)\b',
            r'\b(yesterday|last week|past.*days|this week)\b',
        ],
        ["summary", "summarize", "what happened", "tell me about", "update on"]
    ),

    # Crypto/Blockchain (check before DEFAULT)
    (
        Scenario.CRYPTO,
        [
            r'\b(bitcoin|BTC|ethereum|ETH|crypto|cryptocurrency|blockchain)\b',
            r'\b(proof[ -]of[ -]stake|proof[ -]of[ -]work|PoS|PoW|consensus)\b',
            r'\b(blockchain explorer|explorer|transaction|wallet|exchange)\b',
            r'\b(altcoin|token|defi|nft|stablecoin)\b',
            r'\b(mining|validator|staking|gas fee|network)\b',
            r'\b(merge|fork|upgrade|hard fork|soft fork)\b',
        ],
        ["crypto", "blockchain", "digital currency", "decentralized", "ledger"]
    ),

    # Fundamentals / Long Horizon
    (
        Scenario.FUNDAMENTALS,
        [
            r'\b(fundamental|intrinsic value|valuation)\b',
            r'\b(long[ -]term|long run|over time|historically|future)\b',
            r'\b(business model|competitive advantage|moat)\b',
            r'\b(growth prospects|outlook|forecast|projection)\b',
            r'\b(management|CEO|leadership|board)\b',
            r'\b(industry|sector|market share|competition)\b',
            r'\b(balance sheet|income statement|cash flow)\b',
        ],
        ["company", "firm", "corporation", "business", "operations", "performance"]
    ),
]


class ScenarioDetector:
    """
    Detects finance query scenarios using regex patterns and keyword matching.

    Methods:
        detect(query: str) -> Tuple[Scenario, Dict[str, float]]
            Returns detected scenario and corresponding FHRI weights
    """

    def __init__(self):
        """Initialize scenario detector with default patterns"""
        self.patterns = SCENARIO_PATTERNS
        self.weights = SCENARIO_WEIGHTS

    def detect(self, query: str, manual_override: str = None) -> Tuple[Scenario, Dict[str, float]]:
        """
        Detect scenario from user query

        Args:
            query: User's question text
            manual_override: Optional manual scenario selection (e.g., "numeric_kpi", "directional")

        Returns:
            Tuple of (Scenario enum, weights dict)

        Example:
            >>> detector = ScenarioDetector()
            >>> scenario, weights = detector.detect("What is Apple's P/E ratio?")
            >>> print(scenario)  # Scenario.NUMERIC_KPI
            >>> print(weights["N_or_D"])  # 0.35
        """
        # Handle manual override
        if manual_override:
            try:
                scenario = Scenario(manual_override.lower())
                return scenario, self.weights[scenario]
            except (ValueError, KeyError):
                pass  # Fall through to auto-detection

        # Auto-detect scenario
        query_lower = query.lower()

        for scenario, regex_patterns, keywords in self.patterns:
            # Check regex patterns
            regex_match = any(re.search(pattern, query, re.IGNORECASE)
                            for pattern in regex_patterns)

            # Check keywords
            keyword_match = any(keyword.lower() in query_lower
                               for keyword in keywords)

            # Match if either regex or keywords match (lenient matching)
            if regex_match or keyword_match:
                return scenario, self.weights[scenario]

        # Default fallback
        return Scenario.DEFAULT, self.weights[Scenario.DEFAULT]

    def get_scenario_name(self, scenario: Scenario) -> str:
        """Get human-readable scenario name"""
        names = {
            Scenario.NUMERIC_KPI: "Numeric KPI / Ratios",
            Scenario.DIRECTIONAL: "Directional Recap",
            Scenario.INTRADAY: "Intraday / Real-time",
            Scenario.FUNDAMENTALS: "Fundamentals / Long Horizon",
            Scenario.REGULATORY: "Regulatory / Policy",
            Scenario.ADVICE: "Portfolio Advice / Suitability",
            Scenario.MULTI_TICKER: "Multi-Ticker Comparison",
            Scenario.NEWS: "News Summarization",
            Scenario.CRYPTO: "Crypto / Blockchain",
            Scenario.DEFAULT: "Default"
        }
        return names.get(scenario, "Unknown")

    def get_all_scenarios(self) -> Dict[str, str]:
        """Get all scenario IDs and display names for UI"""
        return {
            scenario.value: self.get_scenario_name(scenario)
            for scenario in Scenario
        }


# Singleton instance for easy import
_detector = None

def get_scenario_detector() -> ScenarioDetector:
    """Get singleton ScenarioDetector instance"""
    global _detector
    if _detector is None:
        _detector = ScenarioDetector()
    return _detector


def detect_comparative_intent(query: str) -> bool:
    """
    Detect if query has comparative intent (e.g., "compare AAPL vs MSFT").

    Args:
        query: User's question text

    Returns:
        True if comparative intent detected, False otherwise

    Example:
        >>> detect_comparative_intent("Compare AAPL vs MSFT")
        True
        >>> detect_comparative_intent("What is AAPL's price?")
        False
    """
    comparative_patterns = [
        r'\b(compare|comparison|versus|vs\.?|v\.s\.?)\b',
        r'\b(relative to|compared to|against)\b',
        r'\b(better than|worse than|outperform|underperform)\b',
        r'\b(which is better|which is worse|which.*more|which.*less)\b',
        r'\b(difference between|contrast)\b',
        r'\b[A-Z]{1,5}\s+(vs\.?|versus|or|and)\s+[A-Z]{1,5}\b',  # Ticker vs Ticker
    ]

    query_lower = query.lower()

    # Check regex patterns
    for pattern in comparative_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True

    # Check for multiple tickers in query (suggests comparison)
    ticker_pattern = r'\b[A-Z]{2,5}\b'
    tickers = re.findall(ticker_pattern, query)
    # Filter out common words that might match ticker pattern
    common_words = {'USA', 'SEC', 'CEO', 'CFO', 'IPO', 'ETF', 'GDP', 'CPI', 'API', 'FAQ', 'PDF'}
    tickers = [t for t in tickers if t not in common_words]

    # If 2+ tickers and query contains comparison keywords
    if len(tickers) >= 2:
        comparison_keywords = ['compare', 'vs', 'versus', 'between', 'difference', 'which', 'better', 'worse', 'performance']
        if any(keyword in query_lower for keyword in comparison_keywords):
            return True

    return False


def detect_scenario(query: str, manual_override: str = None) -> Tuple[str, str, Dict[str, float]]:
    """
    Convenience function to detect scenario and return metadata

    Args:
        query: User's question text
        manual_override: Optional manual scenario selection

    Returns:
        Tuple of (scenario_id, scenario_name, weights)

    Example:
        >>> scenario_id, name, weights = detect_scenario("What's AAPL's P/E?")
        >>> print(f"{name}: {weights}")
        # "Numeric KPI / Ratios: {'G': 0.25, 'N_or_D': 0.35, ...}"
    """
    detector = get_scenario_detector()
    scenario, weights = detector.detect(query, manual_override)
    return scenario.value, detector.get_scenario_name(scenario), weights


if __name__ == "__main__":
    # Test scenario detection
    detector = ScenarioDetector()

    test_queries = [
        "What is Apple's P/E ratio?",
        "Did the stock go up or down today?",
        "What's the current price of TSLA?",
        "Compare AAPL and MSFT performance",
        "What are the SEC requirements for disclosure?",
        "Should I buy Tesla stock?",
        "What happened with GameStop recently?",
        "What is Amazon's long-term growth outlook?",
        "Tell me about the company",
    ]

    print("Scenario Detection Test\n" + "="*60)
    for query in test_queries:
        scenario, weights = detector.detect(query)
        name = detector.get_scenario_name(scenario)
        print(f"\nQuery: {query}")
        print(f"Scenario: {name}")
        print(f"Weights: G={weights['G']:.2f} N/D={weights['N_or_D']:.2f} "
              f"T={weights['T']:.2f} C={weights['C']:.2f} E={weights['E']:.2f}")
