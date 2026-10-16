# src/numeric_validators.py
"""
Numeric tolerance validators for FHRI scoring.

Provides strict numeric validation for financial claims with configurable
tolerances per field type (price, returns, EPS, revenue, market cap, P/E).
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger("numeric_validators")

# Numeric tolerance thresholds by field type
NUMERIC_TOLERANCES = {
    "price": 0.05,           # 5% tolerance for stock prices
    "pct_change": 0.10,      # 10% tolerance for % changes (e.g., -3.2% vs -3.5%)
    "returns": 0.15,         # 15% tolerance for returns (e.g., annual returns)
    "eps": 0.10,             # 10% tolerance for EPS
    "revenue": 0.10,         # 10% tolerance for revenue
    "market_cap": 0.10,      # 10% tolerance for market cap
    "pe_ratio": 0.15,        # 15% tolerance for P/E ratio
    "dividend_yield": 0.20,  # 20% tolerance for dividend yield
    "default": 0.10          # Default 10% tolerance
}


def extract_numeric_claims(text: str) -> List[Dict[str, Any]]:
    """
    Extract numeric claims from text.

    Returns list of dicts with:
        - value: float
        - unit: str (%, $, etc.)
        - context: str (surrounding words)
        - field_type: str (price, pct_change, etc.)
    """
    claims = []

    # Pattern: $XXX.XX (price)
    price_pattern = r'\$\s*([0-9,]+(?:\.[0-9]{1,2})?)'
    for match in re.finditer(price_pattern, text):
        value_str = match.group(1).replace(',', '')
        try:
            value = float(value_str)
            # Get context (10 words before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            claims.append({
                "value": value,
                "unit": "$",
                "context": context,
                "field_type": "price",
                "raw_match": match.group(0)
            })
        except ValueError:
            continue

    # Pattern: XX.XX% or XX% (percentage)
    pct_pattern = r'([-+]?\d+(?:\.\d+)?)\s*%'
    for match in re.finditer(pct_pattern, text):
        try:
            value = float(match.group(1))
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            # Infer field type from context
            field_type = "pct_change"
            context_lower = context.lower()
            if any(word in context_lower for word in ["return", "gain", "growth", "cagr"]):
                field_type = "returns"
            elif any(word in context_lower for word in ["yield", "dividend"]):
                field_type = "dividend_yield"

            claims.append({
                "value": value,
                "unit": "%",
                "context": context,
                "field_type": field_type,
                "raw_match": match.group(0)
            })
        except ValueError:
            continue

    # Pattern: EPS (earnings per share)
    eps_pattern = r'(?:EPS|earnings per share)[:\s]+\$?\s*([0-9]+(?:\.\d+)?)'
    for match in re.finditer(eps_pattern, text, re.IGNORECASE):
        try:
            value = float(match.group(1))
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            claims.append({
                "value": value,
                "unit": "$",
                "context": context,
                "field_type": "eps",
                "raw_match": match.group(0)
            })
        except ValueError:
            continue

    # Pattern: P/E ratio
    pe_pattern = r'(?:P/E|price[- ]to[- ]earnings)[:\s]+([0-9]+(?:\.\d+)?)'
    for match in re.finditer(pe_pattern, text, re.IGNORECASE):
        try:
            value = float(match.group(1))
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            claims.append({
                "value": value,
                "unit": "",
                "context": context,
                "field_type": "pe_ratio",
                "raw_match": match.group(0)
            })
        except ValueError:
            continue

    # Pattern: Market cap ($XXB, $XXTB, $XXM)
    mcap_pattern = r'\$\s*([0-9,]+(?:\.\d+)?)\s*([TBM])'
    for match in re.finditer(mcap_pattern, text):
        try:
            base_value = float(match.group(1).replace(',', ''))
            multiplier_str = match.group(2)

            # Convert to base currency
            multiplier = {"T": 1e12, "B": 1e9, "M": 1e6}[multiplier_str]
            value = base_value * multiplier

            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            # Check if this is market cap
            context_lower = context.lower()
            if "market cap" in context_lower or "capitalization" in context_lower:
                claims.append({
                    "value": value,
                    "unit": "$",
                    "context": context,
                    "field_type": "market_cap",
                    "raw_match": match.group(0)
                })
        except (ValueError, KeyError):
            continue

    logger.debug(f"Extracted {len(claims)} numeric claims from text")
    return claims


def validate_numeric_claim(
    claim: Dict[str, Any],
    reference_data: Dict[str, Any],
    tolerance_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    Validate a single numeric claim against reference data.

    Args:
        claim: Extracted claim dict with value, field_type, etc.
        reference_data: Ground truth data (e.g., from API or passages)
        tolerance_override: Optional custom tolerance (default: use NUMERIC_TOLERANCES)

    Returns:
        Dict with:
            - is_valid: bool
            - reference_value: float or None
            - claimed_value: float
            - relative_error: float or None
            - tolerance_used: float
            - field_type: str
    """
    field_type = claim.get("field_type", "default")
    claimed_value = claim["value"]

    # Get tolerance
    tolerance = tolerance_override if tolerance_override is not None else NUMERIC_TOLERANCES.get(field_type, NUMERIC_TOLERANCES["default"])

    # Look up reference value by field type
    reference_value = None

    if field_type == "price":
        # Try various price field names
        reference_value = reference_data.get("price") or reference_data.get("c") or reference_data.get("current_price")
    elif field_type == "pct_change":
        reference_value = reference_data.get("pct_change") or reference_data.get("change_percent")
    elif field_type == "eps":
        reference_value = reference_data.get("eps") or reference_data.get("earnings_per_share")
    elif field_type == "pe_ratio":
        reference_value = reference_data.get("pe_ratio") or reference_data.get("price_to_earnings")
    elif field_type == "market_cap":
        reference_value = reference_data.get("market_cap") or reference_data.get("marketCap")
    elif field_type == "dividend_yield":
        reference_value = reference_data.get("dividend_yield") or reference_data.get("dividendYield")
    elif field_type == "revenue":
        reference_value = reference_data.get("revenue") or reference_data.get("revenue_ttm")
    elif field_type == "returns":
        # For returns, we might not have direct comparison
        reference_value = reference_data.get("returns") or reference_data.get("annual_return")

    # Validate
    if reference_value is None:
        # No reference data available
        return {
            "is_valid": None,  # Unknown (cannot validate)
            "reference_value": None,
            "claimed_value": claimed_value,
            "relative_error": None,
            "tolerance_used": tolerance,
            "field_type": field_type,
            "validation_status": "no_reference"
        }

    # Compute relative error
    if reference_value == 0:
        # Avoid division by zero
        relative_error = abs(claimed_value) if claimed_value != 0 else 0.0
        is_valid = claimed_value == 0
    else:
        relative_error = abs(claimed_value - reference_value) / abs(reference_value)
        is_valid = relative_error <= tolerance

    return {
        "is_valid": is_valid,
        "reference_value": reference_value,
        "claimed_value": claimed_value,
        "relative_error": relative_error,
        "tolerance_used": tolerance,
        "field_type": field_type,
        "validation_status": "validated"
    }


def validate_all_numeric_claims(
    answer: str,
    reference_data: Dict[str, Any],
    require_all_valid: bool = False
) -> Dict[str, Any]:
    """
    Validate all numeric claims in answer against reference data.

    Args:
        answer: LLM-generated answer text
        reference_data: Ground truth data (multi_source_data or api_facts)
        require_all_valid: If True, all claims must be valid; otherwise, majority

    Returns:
        Dict with:
            - has_numeric_claims: bool
            - total_claims: int
            - validated_claims: int
            - valid_claims: int
            - invalid_claims: int
            - unknown_claims: int
            - validation_rate: float (% of claims validated)
            - accuracy_rate: float (% of validated claims that are valid)
            - all_valid: bool
            - any_invalid: bool
            - claims_details: List[Dict]
    """
    claims = extract_numeric_claims(answer)

    if not claims:
        return {
            "has_numeric_claims": False,
            "total_claims": 0,
            "validated_claims": 0,
            "valid_claims": 0,
            "invalid_claims": 0,
            "unknown_claims": 0,
            "validation_rate": 0.0,
            "accuracy_rate": 1.0,  # No claims = no errors
            "all_valid": True,
            "any_invalid": False,
            "claims_details": []
        }

    results = []
    for claim in claims:
        validation = validate_numeric_claim(claim, reference_data)
        results.append({
            "claim": claim,
            "validation": validation
        })

    # Compute metrics
    total_claims = len(results)
    validated_claims = sum(1 for r in results if r["validation"]["validation_status"] == "validated")
    valid_claims = sum(1 for r in results if r["validation"]["is_valid"] is True)
    invalid_claims = sum(1 for r in results if r["validation"]["is_valid"] is False)
    unknown_claims = sum(1 for r in results if r["validation"]["is_valid"] is None)

    validation_rate = validated_claims / total_claims if total_claims > 0 else 0.0
    accuracy_rate = valid_claims / validated_claims if validated_claims > 0 else 1.0

    all_valid = (invalid_claims == 0 and validated_claims > 0)
    any_invalid = (invalid_claims > 0)

    return {
        "has_numeric_claims": True,
        "total_claims": total_claims,
        "validated_claims": validated_claims,
        "valid_claims": valid_claims,
        "invalid_claims": invalid_claims,
        "unknown_claims": unknown_claims,
        "validation_rate": validation_rate,
        "accuracy_rate": accuracy_rate,
        "all_valid": all_valid,
        "any_invalid": any_invalid,
        "claims_details": results
    }


def compute_numeric_grounding_penalty(validation_result: Dict[str, Any]) -> float:
    """
    Compute grounding penalty based on numeric validation results.

    Returns:
        Penalty multiplier in [0, 1] where:
        - 1.0 = no penalty (all claims valid or no claims)
        - 0.2 = maximum penalty (all claims invalid)
    """
    if not validation_result["has_numeric_claims"]:
        return 1.0  # No claims = no penalty

    accuracy_rate = validation_result["accuracy_rate"]
    validation_rate = validation_result["validation_rate"]

    # If we can't validate any claims, apply moderate penalty
    if validation_rate == 0:
        return 0.6  # Moderate penalty for unverifiable claims

    # Penalty based on accuracy
    # 100% accurate → 1.0 (no penalty)
    # 50% accurate → 0.6
    # 0% accurate → 0.2
    penalty = 0.2 + (0.8 * accuracy_rate)

    return penalty
