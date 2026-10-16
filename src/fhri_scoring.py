# src/fhri_scoring.py
"""
Finance Hallucination Reliability Index (FHRI) composite scoring.

FHRI is a weighted composite score in [0, 1] that combines:
- G: Grounding Score (alignment with retrieved passages and API facts)
- N/D: Numerical/Directional Consistency (numeric claims vs verified data)
- T: Temporal Validity (date/period alignment)
- C: Citation Completeness (presence and credibility of sources)
- E: Entropy Confidence (inverse-normalized uncertainty from MC-Dropout)

Default weights (sum to 1.0): G=0.25, N/D=0.25, T=0.20, C=0.15, E=0.15

SCENARIO-AWARE WEIGHTING:
FHRI now supports dynamic weighting based on detected query scenarios.
Weights are automatically adjusted based on query type (e.g., numeric KPI,
intraday trading, regulatory, etc.) to optimize hallucination detection.

If any sub-score is unavailable, FHRI renormalizes over available components.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import math

logger = logging.getLogger("fhri")

# Import validators
try:
    from numeric_validators import validate_all_numeric_claims, compute_numeric_grounding_penalty
    from entity_validators import validate_entity_grounding, compute_entity_grounding_penalty
except ImportError:
    try:
        from src.numeric_validators import validate_all_numeric_claims, compute_numeric_grounding_penalty
        from src.entity_validators import validate_entity_grounding, compute_entity_grounding_penalty
    except ImportError:
        logger.warning("Validators not available, using fallback grounding")
        validate_all_numeric_claims = None
        compute_numeric_grounding_penalty = None
        validate_entity_grounding = None
        compute_entity_grounding_penalty = None

# ---------------------------------------------------------------------------
# Scenario-level configuration
# ---------------------------------------------------------------------------

# Optimal FHRI thresholds by scenario (based on threshold sweep evaluation results)
SCENARIO_FHRI_THRESHOLDS = {
    # Thresholds optimized based on 10K sample evaluations (maximizing Macro F1)
    "numeric_kpi": 0.70,        # Optimal: 0.70 (Macro F1: 0.8242, Hall Recall: 80%)
    "intraday": 0.65,           # Optimal: 0.65 (Macro F1: 0.8242, Hall Recall: 80%)
    "directional": 0.65,        # Optimal: 0.65 (Macro F1: 0.8242, Hall Recall: 80%)
    "regulatory": 0.55,         # Optimal: 0.55 (Macro F1: 0.8242, Hall Recall: 80%)
    "fundamentals": 0.70,       # Optimal: 0.70 (Macro F1: 0.8468, Hall Recall: 90%) - BEST
    "multi_ticker": 0.55,       # Optimal: 0.55 (Macro F1: 0.8242, Hall Recall: 80%)
    "news": 0.60,               # Optimal: 0.60 (Macro F1: 1.0, Hall Recall: 100%)
    "crypto": 0.60,             # Optimal: 0.60 (Macro F1: 1.0, Hall Recall: 100%)
    "advice": 0.60,             # Optimal: 0.60 (Macro F1: 1.0, Hall Recall: 100%)
    "portfolio_advice": 0.50,   # Optimal: 0.50 (Macro F1: 0.9555, Hall Recall: 100%)
    "default": 0.70,            # Global optimal: 0.70 (Macro F1: 0.8683, Hall Recall: 100%)
}

HIGH_RISK_SCENARIOS = set()  # High-risk scenario handling disabled
HIGH_RISK_FHRI_FLOOR = None  # No high-risk floor when disabled

HIGH_RISK_NUMERIC_PATTERNS = [
    r"\bcurrent (price|quote)\b",
    r"\blast (close|closing price)\b",
    r"\b(as of|today|right now)\b",
    r"\bdividend yield\b",
    r"\bP\/?E\b",
    r"\bmarket cap(italization)?\b",
    r"\brevenue (last year|ttm|trailing)\b",
    r"\bEPS\b",
    r"\b(%|percent)\b\s*(growth|change)",
]

SCENARIO_WEIGHT_OVERRIDES = {
    "numeric_kpi": {
        "G": 0.20,
        "N_or_D": 0.50,
        "T": 0.20,
        "C": 0.05,
        "E": 0.05,
    },
    "intraday": {
        "G": 0.20,
        "N_or_D": 0.50,
        "T": 0.20,
        "C": 0.05,
        "E": 0.05,
    },
    "directional": {
        "G": 0.25,
        "N_or_D": 0.45,
        "T": 0.20,
        "C": 0.05,
        "E": 0.05,
    },
    "fundamentals": {
        "G": 0.25,
        "N_or_D": 0.40,
        "T": 0.15,
        "C": 0.10,
        "E": 0.10,
    },
}


def get_scenario_threshold(scenario_id: Optional[str]) -> float:
    """Return the recommended FHRI threshold for a scenario."""
    if not scenario_id:
        return SCENARIO_FHRI_THRESHOLDS["default"]
    scenario_key = scenario_id.lower()
    return SCENARIO_FHRI_THRESHOLDS.get(scenario_key, SCENARIO_FHRI_THRESHOLDS["default"])


def is_high_risk_numeric_question(question: Optional[str]) -> bool:
    """Detect if the question demands strict numeric accuracy."""
    if not question:
        return False
    for pattern in HIGH_RISK_NUMERIC_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return True
    return False


def evaluate_fhri_risk(
    fhri_value: Optional[float],
    scenario_id: Optional[str],
    question: Optional[str],
    override_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Determine whether an answer should be flagged as low-reliability
    based on FHRI, scenario, and question intent.
    """
    scenario_key = (scenario_id or "default").lower()
    threshold = override_threshold if override_threshold is not None else get_scenario_threshold(scenario_key)
    # High-risk handling disabled
    high_risk_numeric = False
    below_threshold = fhri_value is None or fhri_value < threshold
    high_risk_floor_breach = False

    return {
        "threshold": threshold,
        "high_risk_numeric": high_risk_numeric,
        "below_threshold": below_threshold,
        "high_risk_floor_breach": high_risk_floor_breach,
        "needs_review": below_threshold or high_risk_floor_breach,
    }


def detect_numeric_price_mismatch(
    answer: Optional[str],
    question: Optional[str],
    multi_source_data: Optional[Dict[str, Any]],
    tolerance: float = 0.10,
) -> Dict[str, Any]:
    """
    Heuristic numeric consistency check for current price-style questions.

    - Uses Finnhub quote (multi_source_data['finnhub_quote']['c'] or 'price')
      as the reference price.
    - Extracts the first \"$123.45\" style price from the answer.
    - If both are present and relative error > tolerance → mismatch.

    Returns a dict:
        {
            "enabled": bool,
            "has_reference": bool,
            "has_answer_price": bool,
            "relative_error": Optional[float],
            "is_mismatch": bool,
        }
    """
    metadata: Dict[str, Any] = {
        "enabled": False,
        "has_reference": False,
        "has_answer_price": False,
        "relative_error": None,
        "is_mismatch": False,
    }

    if not answer or not multi_source_data:
        return metadata

    finnhub_data = multi_source_data.get("finnhub_quote") or {}
    ref_price = finnhub_data.get("c") or finnhub_data.get("price")
    if not ref_price or not isinstance(ref_price, (int, float)):
        return metadata

    metadata["enabled"] = True
    metadata["has_reference"] = True

    # Find first dollar-amount in the answer
    match = re.search(r"\$([0-9]+(?:\.[0-9]+)?)", answer)
    if not match:
        return metadata

    try:
        ans_price = float(match.group(1))
    except ValueError:
        return metadata

    metadata["has_answer_price"] = True

    if ref_price <= 0:
        return metadata

    rel_err = abs(ans_price - ref_price) / ref_price
    metadata["relative_error"] = rel_err
    metadata["is_mismatch"] = rel_err > tolerance

    logger.debug(
        f"Numeric price check: answer=${ans_price:.2f}, ref=${ref_price:.2f}, "
        f"rel_err={rel_err:.3f}, mismatch={metadata['is_mismatch']}"
    )
    return metadata


class FHRIScorer:
    """Computes FHRI and its sub-scores."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize FHRI scorer with custom weights.

        Args:
            weights: Dict with keys G, N_or_D, T, C, E. If None, uses defaults.
        """
        self.default_weights = {
            "G": 0.25,      # Grounding
            "N_or_D": 0.25, # Numerical/Directional
            "T": 0.20,      # Temporal
            "C": 0.15,      # Citation
            "E": 0.15       # Entropy
        }
        self.weights = weights if weights else self.default_weights.copy()
        self._validate_weights()

    def _validate_weights(self):
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            logger.warning(f"Weights sum to {total}, normalizing to 1.0")
            for key in self.weights:
                self.weights[key] /= total

    def compute_grounding_score(self, answer: str, passages: List[str],
                                  api_facts: Optional[Dict[str, Any]] = None,
                                  multi_source_data: Optional[Dict[str, Any]] = None) -> float:
        """
        Compute FACT-BASED grounding score with numeric and entity validation.

        Enhanced behavior:
        1. For numeric claims: require matches in passages/API within tolerance
        2. For non-numeric: require entities + relations to appear in evidence
        3. Missing/mismatched numerics → cap G ~0.2
        4. Missing entities → downweight G aggressively

        Args:
            answer: LLM-generated answer
            passages: Retrieved passages from static index
            api_facts: Legacy API facts dict (optional)
            multi_source_data: NEW - Data from multiple providers (Finnhub, SEC, FMP, etc.)

        Returns: score in [0, 1]
        """
        if not answer or not answer.strip():
            return 0.0

        answer_lower = answer.lower()

        # Extract meaningful words (skip common stopwords)
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "is", "was", "are", "were"}
        answer_words = set(re.findall(r'\b\w+\b', answer_lower)) - stopwords

        if not answer_words:
            return 0.70  # Generous baseline for valid content

        # ============================================================
        # FACT-BASED GROUNDING: Numeric + Entity Validation
        # ============================================================
        base_score = 0.0
        numeric_penalty = 1.0
        entity_penalty = 1.0

        # 1. NUMERIC VALIDATION
        if validate_all_numeric_claims and multi_source_data:
            # Build reference data from multi_source_data
            reference_data = {}

            # Extract Finnhub quote data
            finnhub_data = multi_source_data.get("finnhub_quote") or {}
            reference_data["price"] = finnhub_data.get("c") or finnhub_data.get("price")
            reference_data["pct_change"] = finnhub_data.get("dp")

            # Extract fundamentals
            fundamentals = multi_source_data.get("fundamentals", {}).get("data", {}).get("metrics", {})
            reference_data.update(fundamentals)

            # Validate numeric claims
            numeric_validation = validate_all_numeric_claims(answer, reference_data, require_all_valid=False)

            if numeric_validation["has_numeric_claims"]:
                numeric_penalty = compute_numeric_grounding_penalty(numeric_validation)
                logger.debug(f"Numeric validation: {numeric_validation['valid_claims']}/{numeric_validation['validated_claims']} valid, penalty={numeric_penalty:.2f}")

                # HARD CAP: If any numeric claim is invalid, cap G ~0.2
                if numeric_validation["any_invalid"]:
                    logger.warning(f"Invalid numeric claims detected, capping grounding score to 0.2")
                    return 0.2

        # 2. ENTITY VALIDATION
        if validate_entity_grounding:
            entity_validation = validate_entity_grounding(answer, passages, multi_source_data)
            entity_penalty = compute_entity_grounding_penalty(entity_validation)
            logger.debug(f"Entity validation: {entity_validation['grounded_entities']}/{entity_validation['grounded_entities'] + entity_validation['ungrounded_entities']} grounded, penalty={entity_penalty:.2f}")

            # If entities are mentioned but not grounded, downweight
            if entity_validation["ungrounded_entities"] > 0:
                logger.debug(f"Ungrounded entities: {entity_validation['ungrounded_tickers']}, {entity_validation['ungrounded_companies']}")

        # Combine penalties
        fact_penalty = numeric_penalty * entity_penalty

        # ============================================================
        # BASELINE SCORING (similarity-based)
        # ============================================================

        # NEW: Check if we have multi-source data (online sources)
        has_online_sources = bool(multi_source_data and multi_source_data.get("sources_used"))

        # Extract ticker symbols from answer (e.g., TSLA, AAPL, BTC, etc.)
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        answer_tickers = set(re.findall(ticker_pattern, answer))

        # Check if ticker is in passages
        passage_text = " ".join(passages).lower() if passages else ""
        passage_words = set(re.findall(r'\b\w+\b', passage_text)) - stopwords

        ticker_in_passages = False
        symbol_from_multi_source = multi_source_data.get("symbol", "").upper() if multi_source_data else ""

        if symbol_from_multi_source:
            # Check if the symbol from multi_source_data is mentioned in passages
            ticker_in_passages = symbol_from_multi_source.lower() in passage_text
            logger.debug(f"Symbol {symbol_from_multi_source} in passages: {ticker_in_passages}")

        # DECISION: Use online sources OR passages based on what's available
        if has_online_sources and not ticker_in_passages:
            # CASE 1: Ticker NOT in passages, but we have online sources
            # Prioritize online verification over passage overlap
            logger.debug(f"Grounding mode: ONLINE SOURCES (symbol {symbol_from_multi_source} not in passages)")

            # Base score from having verified online sources
            sources_used = multi_source_data.get("sources_used", [])
            num_sources = len(sources_used)

            # High base score for having multiple online sources
            if num_sources >= 3:
                base_score = 0.75  # 3+ sources = high confidence
            elif num_sources == 2:
                base_score = 0.65  # 2 sources = good confidence
            elif num_sources == 1:
                base_score = 0.55  # 1 source = moderate confidence
            else:
                base_score = 0.30  # Fallback

            # Bonus for data verification (check if answer uses the data)
            verification_bonus = 0.0

            # Check SEC filings
            sec_filings = multi_source_data.get("sec_filings", [])
            if sec_filings:
                verification_bonus += 0.10
                logger.debug(f"SEC filings available: +0.10 bonus")

            # Check fundamentals (FMP, revenue, market cap, etc.)
            fmp_fundamentals = multi_source_data.get("fmp_fundamentals", {})
            if fmp_fundamentals and fmp_fundamentals.get("metrics"):
                metrics = fmp_fundamentals.get("metrics", {})
                # Check if any fundamental metric appears in answer
                for metric_name, metric_value in metrics.items():
                    if metric_value and str(metric_value) in answer:
                        verification_bonus += 0.15
                        logger.debug(f"Fundamental metric {metric_name}={metric_value} found in answer: +0.15 bonus")
                        break

            # Check Finnhub quote data
            finnhub_data = multi_source_data.get("finnhub_quote")
            if finnhub_data:
                price = finnhub_data.get("c") or finnhub_data.get("price")
                if price and (str(price) in answer or f"{price:.2f}" in answer):
                    verification_bonus += 0.10
                    logger.debug(f"Finnhub price ${price} found in answer: +0.10 bonus")

            score = min(1.0, base_score + verification_bonus)
            # Apply fact penalty
            score = score * fact_penalty
            logger.debug(f"Grounding (ONLINE): base={base_score:.2f}, verification_bonus={verification_bonus:.2f}, fact_penalty={fact_penalty:.2f}, score={score:.2f}, sources={sources_used}")
            return score

        elif has_online_sources and ticker_in_passages:
            # CASE 2: Ticker IS in passages AND we have online sources
            # Hybrid scoring (combine both)
            logger.debug(f"Grounding mode: HYBRID (symbol {symbol_from_multi_source} found in both passages and online)")

            # Passage overlap component (weighted 40%)
            passage_overlap = len(answer_words & passage_words) / len(answer_words) if passage_words else 0.0
            passage_score = passage_overlap * 0.40

            # Online sources component (weighted 60%)
            sources_used = multi_source_data.get("sources_used", [])
            num_sources = len(sources_used)
            online_score = 0.60 * (0.5 + min(0.5, num_sources * 0.15))

            score = min(1.0, passage_score + online_score)
            # Apply fact penalty
            score = score * fact_penalty
            logger.debug(f"Grounding (HYBRID): passage_score={passage_score:.2f}, online_score={online_score:.2f}, fact_penalty={fact_penalty:.2f}, score={score:.2f}")
            return score

        else:
            # CASE 3: Traditional passage-based grounding (no online sources or old behavior)
            logger.debug(f"Grounding mode: PASSAGES ONLY (no multi-source data)")

            if not passage_words:
                # No passages retrieved - but if we have API facts, still give some credit
                overlap = 0.45 if api_facts else 0.20
            else:
                overlap = len(answer_words & passage_words) / len(answer_words)
                # Phase 3: Improved grounding - more generous for partial matches
                # Boost overlap score and add minimum floor for any overlap
                if overlap > 0:
                    # Any overlap gets minimum 0.30 (was 0.05), scales up to 1.0
                    overlap = min(1.0, 0.30 + (overlap * 0.70))
                else:
                    # No overlap but has passages - give small credit
                    overlap = 0.25 if passages else 0.20

            # Bonus for API facts (if provided and referenced)
            api_bonus = 0.0
            if api_facts:
                for key, value in api_facts.items():
                    if str(key).lower() in answer_lower or str(value).lower() in answer_lower:
                        api_bonus = 0.20
                        break

            score = min(1.0, overlap + api_bonus)
            # Apply fact penalty
            score = score * fact_penalty
            logger.debug(f"Grounding (PASSAGES): overlap={overlap:.2f}, api_bonus={api_bonus:.2f}, fact_penalty={fact_penalty:.2f}, score={score:.2f}")
            return score

    def compute_numerical_directional_score(self, answer: str, question: str,
                                              api_facts: Optional[Dict[str, Any]] = None,
                                              passages: Optional[List[str]] = None,
                                              multi_source_data: Optional[Dict[str, Any]] = None) -> float:
        """
        Compute numerical/directional consistency score.

        Enhanced with multi-source verification:
        - Verify numeric claims against multiple providers
        - Check directional consistency across sources
        - Detect provider disagreements

        If numeric claims exist (percentages, dollar amounts, ratios):
        - Try to verify against API facts or passage data
        - Check for internal consistency (e.g., percentages sum correctly)
        - NEW: Cross-verify with multi-source data

        If no numeric content:
        - Check directional/qualitative claims (up/down/flat, positive/negative)

        Returns: score in [0, 1]
        """
        if not answer or not answer.strip():
            return 0.0

        answer_lower = answer.lower()

        # Extract numbers from answer
        numbers = re.findall(r'[-+]?\d*\.?\d+%?', answer)

        if numbers:
            # Numeric mode: check consistency
            # Increased baseline score - assume numbers are correct unless proven otherwise
            score = 0.70  # Increased from 0.65 - higher baseline for numeric answers

            if api_facts:
                # Try to find matching numeric values in API facts
                for key, value in api_facts.items():
                    if isinstance(value, (int, float)):
                        value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
                        if value_str in answer or str(value) in answer:
                            score = 0.88  # Increased from 0.85 - strongly reward verified numbers
                            break

            # NEW: Multi-source numeric verification
            if multi_source_data:
                numeric_verified = False
                for data_type in ["equity_data", "crypto_data", "commodity_data"]:
                    if data_type in multi_source_data and multi_source_data[data_type]:
                        primary = multi_source_data[data_type].get("primary_data")
                        if primary and "price" in primary:
                            price = primary["price"]
                            # Check if price is mentioned in answer (with tolerance)
                            price_patterns = [
                                f"${price}",
                                f"${price:.2f}",
                                f"{price}",
                                str(int(price)) if price == int(price) else None
                            ]
                            if any(p and p in answer for p in price_patterns if p):
                                numeric_verified = True
                                score = max(score, 0.92)  # Increased from 0.90 - very high confidence for multi-source verification
                                logger.debug(f"Multi-source numeric verification: price ${price} found in answer")
                                break

                # Check for directional consistency with pct_change
                if not numeric_verified:
                    for data_type in ["equity_data", "crypto_data", "commodity_data"]:
                        if data_type in multi_source_data and multi_source_data[data_type]:
                            primary = multi_source_data[data_type].get("primary_data")
                            if primary and "pct_change" in primary:
                                pct_change = primary["pct_change"]
                                direction_positive = ["up", "increase", "gain", "growth", "rise", "higher", "positive", "improved"]
                                direction_negative = ["down", "decrease", "loss", "decline", "fall", "lower", "negative", "declined"]

                                has_positive = any(word in answer_lower for word in direction_positive)
                                has_negative = any(word in answer_lower for word in direction_negative)

                                # Check consistency
                                if pct_change > 0 and has_positive and not has_negative:
                                    score = max(score, 0.75)
                                    logger.debug(f"Directional consistency: positive pct_change matches positive language")
                                elif pct_change < 0 and has_negative and not has_positive:
                                    score = max(score, 0.75)
                                    logger.debug(f"Directional consistency: negative pct_change matches negative language")
                                elif (pct_change > 0 and has_negative) or (pct_change < 0 and has_positive):
                                    score = min(score, 0.3)  # Penalty for mismatch
                                    logger.warning(f"Directional inconsistency detected!")
                                break
        else:
            # Directional mode: look for qualitative direction words
            direction_positive = ["up", "increase", "gain", "growth", "rise", "higher", "positive", "improved"]
            direction_negative = ["down", "decrease", "loss", "decline", "fall", "lower", "negative", "declined"]
            direction_neutral = ["flat", "unchanged", "stable", "steady"]

            has_positive = any(word in answer_lower for word in direction_positive)
            has_negative = any(word in answer_lower for word in direction_negative)
            has_neutral = any(word in answer_lower for word in direction_neutral)

            # If only one direction is present, assume consistency
            direction_count = sum([has_positive, has_negative, has_neutral])
            if direction_count == 1:
                score = 0.7  # Consistent direction
            elif direction_count > 1:
                score = 0.4  # Mixed signals
            else:
                score = 0.5  # No clear direction

            # NEW: Verify direction with multi-source data
            if multi_source_data:
                for data_type in ["equity_data", "crypto_data", "commodity_data"]:
                    if data_type in multi_source_data and multi_source_data[data_type]:
                        primary = multi_source_data[data_type].get("primary_data")
                        if primary and "pct_change" in primary:
                            pct_change = primary["pct_change"]
                            if pct_change > 0.5 and has_positive:
                                score = max(score, 0.8)
                            elif pct_change < -0.5 and has_negative:
                                score = max(score, 0.8)
                            break

        logger.debug(f"Numerical/Directional: score={score:.2f}")
        return score

    def compute_temporal_score(self, answer: str, question: str,
                                 passages: Optional[List[str]] = None) -> float:
        """
        Compute temporal validity: does answer's implied period/date match the question?

        Look for temporal references:
        - "yesterday", "last quarter", "Q3", "2023", "last year", etc.
        - Check if question has temporal context
        - Penalize if dates are clearly mismatched or outdated

        Returns: score in [0, 1]
        """
        if not answer or not answer.strip():
            return 0.0

        answer_lower = answer.lower()
        question_lower = question.lower()

        # Extract temporal keywords
        temporal_keywords = ["yesterday", "today", "last quarter", "q1", "q2", "q3", "q4",
                              "last year", "this year", "month", "week", "2020", "2021", "2022", "2023", "2024", "2025"]

        answer_temporal = [kw for kw in temporal_keywords if kw in answer_lower]
        question_temporal = [kw for kw in temporal_keywords if kw in question_lower]

        if not answer_temporal and not question_temporal:
            # No temporal context - assume current/recent data is being used
            return 0.70  # Increased from 0.6 - give benefit of doubt

        if answer_temporal and question_temporal:
            # Check for overlap
            overlap = set(answer_temporal) & set(question_temporal)
            if overlap:
                return 0.95  # Increased from 0.9 - excellent temporal alignment
            else:
                # Check if years/quarters are close
                # For simplicity, if both have temporal terms but don't match, slight penalty
                return 0.55  # Increased from 0.5

        if question_temporal and not answer_temporal:
            # Question asks about time, answer doesn't specify - moderate penalty (but not too harsh)
            return 0.50  # Increased from 0.4 - might be using implied current data

        if answer_temporal and not question_temporal:
            # Answer provides time context without being asked - good practice
            return 0.75  # Increased from 0.7

        logger.debug(f"Temporal: score=0.5 (default)")
        return 0.5

    def compute_citation_score(self, answer: str, passages: List[str],
                                multi_source_data: Optional[Dict[str, Any]] = None) -> float:
        """
        Compute citation completeness: presence and credibility of sources.

        Enhanced with multi-source verification tracking:
        - Explicit source mentions (SEC, Reuters, Bloomberg, Yahoo Finance, company filings, etc.)
        - Hedging language when uncertain ("according to", "sources indicate")
        - Number of passages retrieved (more = better grounding potential)
        - NEW: Bonus for multi-provider verification

        Returns: score in [0, 1]
        """
        if not answer or not answer.strip():
            return 0.0

        answer_lower = answer.lower()

        # Credible source keywords
        credible_sources = [
            "sec.gov", "sec filing", "10-k", "10-q", "8-k",
            "reuters", "bloomberg", "yahoo finance", "finnhub",
            "company filing", "official report", "investor relations",
            "annual report", "quarterly report", "press release",
            # NEW: Multi-source providers
            "twelvedata", "coingecko", "financialmodelingprep", "yfinance"
        ]

        source_count = sum(1 for src in credible_sources if src in answer_lower)

        # Hedging/attribution phrases (good for transparency)
        hedging_phrases = ["according to", "sources indicate", "reported by", "as per", "data from", "based on", "verified by"]
        has_hedging = any(phrase in answer_lower for phrase in hedging_phrases)
        
        # Phase 3: Implicit citation detection - detect references to data without explicit citations
        implicit_citation_phrases = [
            "recent earnings", "latest report", "company's", "quarterly", "annual",
            "market data", "financial data", "trading data", "price data",
            "earnings report", "financial report", "company report", "official data"
        ]
        has_implicit_citation = any(phrase in answer_lower for phrase in implicit_citation_phrases)

        # Passage count bonus - increased reward for having retrieved passages
        passage_bonus = min(0.35, len(passages) * 0.07)  # Increased from 0.3 max and 0.05 per passage

        # Compute score - increased per-source reward
        source_score = min(0.6, source_count * 0.20)  # Increased from 0.5 max and 0.15 per source
        hedging_score = 0.25 if has_hedging else 0.0  # Increased from 0.2
        # Phase 3: Give partial credit for implicit citations
        implicit_citation_score = 0.15 if has_implicit_citation else 0.0

        # NEW: Multi-source provider bonus
        multi_source_bonus = 0.0
        if multi_source_data:
            sources_used = multi_source_data.get("sources_used", [])
            num_sources = len(sources_used)

            # Bonus for having multiple independent sources
            if num_sources >= 3:
                multi_source_bonus = 0.20  # Excellent citation
            elif num_sources == 2:
                multi_source_bonus = 0.15  # Good citation
            elif num_sources == 1:
                multi_source_bonus = 0.10  # Some citation

            logger.debug(f"Multi-source citation bonus: {num_sources} sources = +{multi_source_bonus:.2f}")

        score = min(1.0, source_score + hedging_score + implicit_citation_score + passage_bonus + multi_source_bonus)
        logger.debug(f"Citation: sources={source_count}, hedging={has_hedging}, implicit={has_implicit_citation}, passages={len(passages)}, multi_sources={len(multi_source_data.get('sources_used', [])) if multi_source_data else 0}, score={score:.2f}")
        return score

    def compute_entropy_score(self, entropy: Optional[float], threshold: float = 2.5) -> float:
        """
        Compute entropy confidence score: inverse-normalized uncertainty.

        Lower entropy = higher confidence.
        Score = 1 - min(entropy / (2 * threshold), 1.0)

        Returns: score in [0, 1], or None if entropy unavailable
        """
        if entropy is None:
            return None

        # Normalize entropy to [0, 1] range with more lenient threshold
        # Increased threshold from 2.0 to 2.5 - less sensitive to entropy variations
        # This means moderate entropy (e.g., 1.5) gets a better score
        normalized = min(entropy / (2 * threshold), 1.0)
        score = 1.0 - normalized

        # Apply a slight boost to reward low-moderate entropy more
        # This makes the score curve more favorable
        score = min(1.0, score * 1.05)  # 5% boost, capped at 1.0

        logger.debug(f"Entropy: raw={entropy:.3f}, normalized={normalized:.3f}, score={score:.2f}")
        return score

    def compute_fhri(self, answer: str, question: str, passages: List[str],
                      entropy: Optional[float] = None,
                      api_facts: Optional[Dict[str, Any]] = None,
                      hallu_threshold: float = 2.0,
                      scenario_override: Optional[str] = None,
                      multi_source_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compute FHRI and all sub-scores with scenario-aware weighting.

        Enhanced with multi-source data verification (NEW).

        Args:
            answer: The LLM's generated answer
            question: The user's question
            passages: Retrieved passages used for grounding
            entropy: Semantic entropy value (optional)
            api_facts: Dictionary of verified API facts (optional, legacy)
            hallu_threshold: Entropy threshold for hallucination detection
            scenario_override: Manual scenario selection (optional, e.g., "numeric_kpi")
            multi_source_data: NEW - Data from multiple providers (optional)

        Returns:
            Dict with keys:
                - fhri: float [0, 1]
                - subscores: Dict[str, Optional[float]] with G, N_or_D, T, C, E
                - available_components: List[str] of computed sub-scores
                - renormalized: bool indicating if weights were adjusted
                - scenario_detected: str scenario ID
                - scenario_name: str human-readable scenario name
                - scenario_weights: Dict[str, float] weights used for this scenario
                - data_sources_used: List[str] NEW - List of data providers used
        """
        # Import here to avoid circular dependency
        try:
            try:
                from scenario_detection import detect_scenario
            except ImportError:
                from src.scenario_detection import detect_scenario
            scenario_id, scenario_name, scenario_weights = detect_scenario(
                question, manual_override=scenario_override
            )
            scenario_key = (scenario_id or "default").lower()
            active_weights = SCENARIO_WEIGHT_OVERRIDES.get(scenario_key, scenario_weights)
            logger.info(
                f"Detected scenario: {scenario_name} → using weights {active_weights} "
                f"(override: {scenario_override})"
            )
        except (ImportError, Exception) as e:
            # Fallback if scenario_detection not available
            logger.warning(f"Scenario detection unavailable or error: {e}, using default weights")
            scenario_id = "default"
            scenario_name = "Default"
            scenario_weights = self.weights.copy()
            active_weights = self.weights.copy()
            scenario_key = "default"

        subscores = {}

        # Compute each sub-score (NOW with multi_source_data support)
        g_raw = self.compute_grounding_score(answer, passages, api_facts, multi_source_data)
        subscores["N_or_D"] = self.compute_numerical_directional_score(answer, question, api_facts, passages, multi_source_data)
        subscores["T"] = self.compute_temporal_score(answer, question, passages)
        c_raw = self.compute_citation_score(answer, passages, multi_source_data)
        subscores["E"] = self.compute_entropy_score(entropy, hallu_threshold)
        
        # Apply square root transform to G and C (Gemini's recommendation)
        # This addresses the "mediocrity trap" - makes partial matches count more fairly
        # Example: G=0.49 → 0.70, C=0.35 → 0.59
        if g_raw is not None:
            subscores["G"] = math.sqrt(g_raw)
            logger.debug(f"Applied square root transform to G: {g_raw:.3f} → {subscores['G']:.3f}")
        else:
            subscores["G"] = None
            
        if c_raw is not None:
            subscores["C"] = math.sqrt(c_raw)
            logger.debug(f"Applied square root transform to C: {c_raw:.3f} → {subscores['C']:.3f}")
        else:
            subscores["C"] = None

        # Identify available components
        available = [k for k, v in subscores.items() if v is not None]

        if not available:
            # All components failed - return minimal FHRI
            logger.warning("No FHRI components available, returning 0.0")
            return {
                "fhri": 0.0,
                "subscores": subscores,
                "available_components": [],
                "renormalized": False,
                "scenario_detected": scenario_id,
                "scenario_name": scenario_name,
                "scenario_weights": scenario_weights
            }

        # Renormalize weights over available components
        renormalized = len(available) < len(active_weights)
        if renormalized:
            logger.info(f"Renormalizing FHRI over {len(available)} components: {available}")
            total_weight = sum(active_weights[k] for k in available)
            adjusted_weights = {k: active_weights[k] / total_weight for k in available}
        else:
            adjusted_weights = active_weights.copy()

        # Compute weighted sum
        fhri_before_boost = sum(adjusted_weights[k] * subscores[k] for k in available)

        # Log detailed breakdown
        logger.info(f"FHRI subscores breakdown:")
        for k in available:
            contribution = adjusted_weights[k] * subscores[k]
            logger.info(f"  {k}: {subscores[k]:.3f} × {adjusted_weights[k]:.3f} = {contribution:.3f}")
        logger.info(f"  Base FHRI (before boost): {fhri_before_boost:.3f}")

        fhri = fhri_before_boost

        # Apply soft baseline bonus (ChatGPT's recommendation)
        # If answer is reasonably good in key dimensions, give a small boost
        # This rewards answers that are "pretty good" even if not perfect
        G_val = subscores.get("G")
        N_val = subscores.get("N_or_D")
        E_val = subscores.get("E")
        
        if G_val is not None and N_val is not None and E_val is not None:
            # Phase 1: Lowered thresholds to catch more edge cases
            # G > 0.35 (was 0.4), N > 0.45 (was 0.5), E > 0.35 (was 0.4)
            if G_val > 0.35 and N_val > 0.45 and E_val > 0.35:
                baseline_bonus = 0.05
                fhri = min(1.0, fhri + baseline_bonus)
                logger.info(f"  Soft baseline bonus applied: +{baseline_bonus:.3f} (G={G_val:.3f} > 0.35, N={N_val:.3f} > 0.45, E={E_val:.3f} > 0.35)")
            else:
                logger.debug(f"  No baseline bonus (G={G_val:.3f}, N={N_val:.3f}, E={E_val:.3f})")

        # Apply quality boost for moderate-to-good scores
        # This rewards well-grounded, verified answers
        if fhri >= 0.55:  # Lowered from 0.65 to boost more answers
            # Progressive boost: better scores get more boost
            # 0.55 → +5% boost, 1.0 → +12% boost
            boost_factor = 1 + (0.05 + (0.07 * ((fhri - 0.55) / 0.45)))
            fhri_boosted = fhri * boost_factor
            logger.info(f"  Quality boost applied: {fhri:.3f} × {boost_factor:.3f} = {fhri_boosted:.3f}")
            fhri = fhri_boosted
        else:
            logger.info(f"  No quality boost (score {fhri:.3f} < 0.55 threshold)")

        fhri = max(0.0, min(1.0, fhri))  # Clamp to [0, 1]

        logger.info(f"FHRI final: {fhri:.3f} from {available} (scenario: {scenario_name})")

        # NEW: Extract data sources used
        data_sources_used = []
        if multi_source_data:
            data_sources_used = multi_source_data.get("sources_used", [])

        scenario_threshold = get_scenario_threshold(scenario_key)
        high_risk_numeric = scenario_key in HIGH_RISK_SCENARIOS or is_high_risk_numeric_question(question)
        risk_metadata = evaluate_fhri_risk(fhri, scenario_key, question, override_threshold=scenario_threshold)

        return {
            "fhri": round(fhri, 3),
            "subscores": {k: (round(v, 3) if v is not None else None) for k, v in subscores.items()},
            "available_components": available,
            "renormalized": renormalized,
            "scenario_detected": scenario_id,
            "scenario_name": scenario_name,
            "scenario_weights": {k: round(v, 2) for k, v in active_weights.items()},
            "data_sources_used": data_sources_used,  # NEW
            "scenario_threshold": scenario_threshold,
            "high_risk_numeric": high_risk_numeric,
            "risk_metadata": risk_metadata,
        }


# Singleton instance for easy access
_default_scorer = None


def get_default_scorer() -> FHRIScorer:
    """Get or create the default FHRI scorer."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = FHRIScorer()
    return _default_scorer


def compute_fhri(answer: str, question: str, passages: List[str],
                  entropy: Optional[float] = None,
                  api_facts: Optional[Dict[str, Any]] = None,
                  hallu_threshold: float = 2.0,
                  scenario_override: Optional[str] = None,
                  multi_source_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to compute FHRI using default scorer with scenario-aware weighting.

    Enhanced with multi-source data verification (NEW).

    See FHRIScorer.compute_fhri for parameter details.
    """
    scorer = get_default_scorer()
    return scorer.compute_fhri(answer, question, passages, entropy, api_facts,
                               hallu_threshold, scenario_override, multi_source_data)
