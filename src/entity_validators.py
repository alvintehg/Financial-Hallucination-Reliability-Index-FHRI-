# src/entity_validators.py
"""
Entity and relation validators for fact-based grounding.

Checks that entities (tickers, companies, people) and their relations
(X announced Y, Z owns A) appear in retrieved passages or API data.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Set, Tuple

logger = logging.getLogger("entity_validators")


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract entities from text.

    Returns dict with:
        - tickers: List[str] - stock tickers (e.g., AAPL, TSLA)
        - companies: List[str] - company names (e.g., Apple Inc., Tesla)
        - people: List[str] - person names (e.g., Elon Musk)
        - dates: List[str] - date references (e.g., 2024, Q3)
    """
    entities = {
        "tickers": [],
        "companies": [],
        "people": [],
        "dates": []
    }

    # Extract tickers (2-5 uppercase letters, whole word)
    ticker_pattern = r'\b([A-Z]{2,5})\b'
    tickers = re.findall(ticker_pattern, text)
    # Filter out common abbreviations that aren't tickers
    stopwords = {"CEO", "CFO", "CTO", "USA", "USD", "EUR", "GBP", "API", "SEC", "ETF", "IPO", "P", "E", "Q", "TTM"}
    entities["tickers"] = [t for t in tickers if t not in stopwords]

    # Extract company names (simplified heuristic)
    # Look for capitalized words followed by Inc., Corp., Ltd., etc.
    company_pattern = r'([A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(?:Inc\.|Corp\.|Ltd\.|LLC|Co\.)'
    companies = re.findall(company_pattern, text)
    entities["companies"] = companies

    # Extract person names (simplified: two capitalized words)
    # This is a very basic heuristic and will have false positives
    person_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
    potential_people = re.findall(person_pattern, text)
    # Filter out common false positives
    name_stopwords = {"United States", "New York", "Wall Street", "Market Cap", "Stock Price"}
    entities["people"] = [p for p in potential_people if p not in name_stopwords]

    # Extract dates (years, quarters)
    date_pattern = r'\b(20\d{2}|Q[1-4](?:\s+20\d{2})?|FY20\d{2})\b'
    dates = re.findall(date_pattern, text)
    entities["dates"] = dates

    return entities


def extract_relations(text: str, entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Extract subject-verb-object relations from text.

    Returns list of dicts with:
        - subject: str
        - verb: str
        - object: str
        - relation_type: str

    This is a simplified heuristic approach (not full NLP parsing).
    """
    relations = []

    # Common financial verbs
    financial_verbs = [
        "announced", "reported", "released", "posted",
        "increased", "decreased", "grew", "fell",
        "acquired", "merged", "sold", "bought",
        "owns", "holds", "invests"
    ]

    # Pattern: [Entity] [verb] [value/entity]
    # Example: "Apple announced quarterly revenue of $90B"
    for entity in entities.get("tickers", []) + entities.get("companies", []):
        for verb in financial_verbs:
            # Simple pattern: entity + verb
            pattern = rf'\b{re.escape(entity)}\s+{verb}\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get context (next 10 words)
                start = match.start()
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                relations.append({
                    "subject": entity,
                    "verb": verb,
                    "object": context,  # Full context for now
                    "relation_type": "financial_event"
                })

    return relations


def validate_entity_grounding(
    answer: str,
    passages: List[str],
    api_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate that entities mentioned in answer appear in passages or API data.

    Args:
        answer: LLM-generated answer
        passages: Retrieved passages
        api_data: API/multi-source data

    Returns:
        Dict with:
            - entities_in_answer: Dict[str, List[str]]
            - entities_in_passages: Dict[str, List[str]]
            - entities_in_api: Dict[str, List[str]]
            - grounded_entities: int
            - ungrounded_entities: int
            - grounding_rate: float
    """
    # Extract entities from answer
    answer_entities = extract_entities(answer)

    # Extract entities from passages
    passage_text = " ".join(passages) if passages else ""
    passage_entities = extract_entities(passage_text)

    # Extract entities from API data (if available)
    api_entities = {"tickers": [], "companies": [], "people": [], "dates": []}
    if api_data:
        # Extract symbol from API data
        symbol = api_data.get("symbol", "")
        if symbol:
            api_entities["tickers"].append(symbol)

        # Check SEC filings for company names
        sec_filings = api_data.get("sec_filings", [])
        if sec_filings:
            for filing in sec_filings:
                # SEC filings typically have company name
                pass  # Could extract from filing metadata

    # Count grounded vs ungrounded entities
    grounded_tickers = set(answer_entities["tickers"]) & (
        set(passage_entities["tickers"]) | set(api_entities["tickers"])
    )
    ungrounded_tickers = set(answer_entities["tickers"]) - grounded_tickers

    grounded_companies = set(answer_entities["companies"]) & (
        set(passage_entities["companies"]) | set(api_entities["companies"])
    )
    ungrounded_companies = set(answer_entities["companies"]) - grounded_companies

    total_entities = len(answer_entities["tickers"]) + len(answer_entities["companies"])
    grounded_count = len(grounded_tickers) + len(grounded_companies)
    ungrounded_count = len(ungrounded_tickers) + len(ungrounded_companies)

    grounding_rate = grounded_count / total_entities if total_entities > 0 else 1.0

    return {
        "entities_in_answer": answer_entities,
        "entities_in_passages": passage_entities,
        "entities_in_api": api_entities,
        "grounded_entities": grounded_count,
        "ungrounded_entities": ungrounded_count,
        "grounding_rate": grounding_rate,
        "grounded_tickers": list(grounded_tickers),
        "ungrounded_tickers": list(ungrounded_tickers),
        "grounded_companies": list(grounded_companies),
        "ungrounded_companies": list(ungrounded_companies)
    }


def compute_entity_grounding_penalty(validation_result: Dict[str, Any]) -> float:
    """
    Compute grounding penalty based on entity validation.

    Returns:
        Penalty multiplier in [0, 1] where:
        - 1.0 = no penalty (all entities grounded or no entities)
        - 0.3 = maximum penalty (no entities grounded)
    """
    grounding_rate = validation_result.get("grounding_rate", 1.0)

    # If no entities mentioned, no penalty
    if grounding_rate == 1.0:
        return 1.0

    # Penalty based on grounding rate
    # 100% grounded → 1.0 (no penalty)
    # 50% grounded → 0.65
    # 0% grounded → 0.3
    penalty = 0.3 + (0.7 * grounding_rate)

    return penalty
