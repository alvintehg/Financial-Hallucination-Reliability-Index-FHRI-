"""
Utility functions for NLI contradiction detection.
Includes question similarity gating, numeric contradiction detection, and answer similarity checks.
"""

import re
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

# Try to import similarity model
_similarity_model = None

def get_similarity_model():
    """Lazy load sentence-transformers model for semantic similarity."""
    global _similarity_model
    if _similarity_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _similarity_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception as e:
            _similarity_model = False  # Mark as failed
    return _similarity_model if _similarity_model is not False else None

def compute_semantic_similarity(text1: str, text2: str) -> Optional[float]:
    """
    Compute cosine similarity between two texts using sentence embeddings.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Cosine similarity [0, 1] or None if model unavailable
    """
    model = get_similarity_model()
    if not model:
        return None
    
    try:
        embeddings = model.encode([text1, text2])
        # Compute cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    except Exception as e:
        return None

def check_entity_overlap(question1: str, question2: str) -> bool:
    """
    Check if two questions reference the same entities (tickers, macro variables, time frames).
    
    Args:
        question1: First question
        question2: Second question
    
    Returns:
        True if entities overlap, False otherwise
    """
    # Extract tickers (uppercase 2-5 letter codes)
    ticker_pattern = r'\b([A-Z]{2,5})\b'
    tickers1 = set(re.findall(ticker_pattern, question1))
    tickers2 = set(re.findall(ticker_pattern, question2))
    
    # Extract common financial terms
    financial_terms = [
        r'\b(GDP|inflation|unemployment|interest rate|Fed|Federal Reserve)\b',
        r'\b(EPS|P/E|P/E ratio|earnings|revenue|profit)\b',
        r'\b(bitcoin|BTC|ethereum|ETH|crypto|cryptocurrency)\b',
        r'\b(proof[ -]of[ -]stake|proof[ -]of[ -]work|PoS|PoW)\b',
    ]
    
    terms1 = set()
    terms2 = set()
    for pattern in financial_terms:
        terms1.update(re.findall(pattern, question1, re.IGNORECASE))
        terms2.update(re.findall(pattern, question2, re.IGNORECASE))
    
    # Extract time references
    time_patterns = [
        r'\b(last|latest|recent|previous|yesterday|today|this|quarter|Q[1-4]|202[0-9]|202[0-9])\b',
    ]
    time1 = set()
    time2 = set()
    for pattern in time_patterns:
        time1.update(re.findall(pattern, question1, re.IGNORECASE))
        time2.update(re.findall(pattern, question2, re.IGNORECASE))
    
    # Check for overlap
    has_ticker_overlap = bool(tickers1 & tickers2)
    has_term_overlap = bool(terms1 & terms2)
    has_time_overlap = bool(time1 & time2)
    
    # Entity overlap if any category overlaps
    return has_ticker_overlap or has_term_overlap or has_time_overlap

def detect_numeric_contradiction(prev_answer: str, current_answer: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect numeric contradictions by parsing percentages and directionality.
    
    Args:
        prev_answer: Previous answer
        current_answer: Current answer
    
    Returns:
        Tuple of (is_contradiction, metadata)
    """
    metadata = {
        "numeric_contradiction": False,
        "sign_differs": False,
        "magnitude_differs": False,
        "prev_numeric_claims": [],
        "curr_numeric_claims": []
    }
    
    # Patterns for numeric claims
    numeric_patterns = [
        # Percentage patterns
        r'(\d+\.?\d*)\s*%',
        # Growth/shrink patterns
        r'(grew|grow|growth|increased|increase|rose|rise|up|gained|gain)\s+by\s+(\d+\.?\d*)\s*%?',
        r'(shrank|shrink|shrunk|decreased|decrease|fell|fall|down|lost|loss|dropped|drop|declined|decline)\s+by\s+(\d+\.?\d*)\s*%?',
        # Directional words
        r'\b(grew|grow|growth|increased|increase|rose|rise|up|gained|gain|bullish|higher)\b',
        r'\b(shrank|shrink|shrunk|decreased|decrease|fell|fall|down|lost|loss|dropped|drop|declined|decline|bearish|lower)\b',
    ]
    
    # Extract numeric claims from both answers
    prev_claims = []
    curr_claims = []
    
    # Extract percentages
    prev_percentages = re.findall(r'(\d+\.?\d*)\s*%', prev_answer)
    curr_percentages = re.findall(r'(\d+\.?\d*)\s*%', current_answer)
    
    # Extract directional indicators
    prev_has_growth = bool(re.search(r'\b(grew|grow|growth|increased|increase|rose|rise|up|gained|gain|bullish|higher)\b', prev_answer, re.IGNORECASE))
    prev_has_shrink = bool(re.search(r'\b(shrank|shrink|shrunk|decreased|decrease|fell|fall|down|lost|loss|dropped|drop|declined|decline|bearish|lower)\b', prev_answer, re.IGNORECASE))
    
    curr_has_growth = bool(re.search(r'\b(grew|grow|growth|increased|increase|rose|rise|up|gained|gain|bullish|higher)\b', current_answer, re.IGNORECASE))
    curr_has_shrink = bool(re.search(r'\b(shrank|shrink|shrunk|decreased|decrease|fell|fall|down|lost|loss|dropped|drop|declined|decline|bearish|lower)\b', current_answer, re.IGNORECASE))
    
    # Check for sign contradiction (growth vs shrink)
    if (prev_has_growth and curr_has_shrink) or (prev_has_shrink and curr_has_growth):
        metadata["sign_differs"] = True
        metadata["numeric_contradiction"] = True
    
    # Check for magnitude contradiction (if both have percentages)
    if prev_percentages and curr_percentages:
        try:
            prev_vals = [float(p) for p in prev_percentages]
            curr_vals = [float(c) for c in curr_percentages]
            
            # Check if magnitudes differ significantly (more than 50% difference)
            for pv in prev_vals:
                for cv in curr_vals:
                    if abs(pv - cv) > max(abs(pv), abs(cv)) * 0.5:  # 50% difference threshold
                        metadata["magnitude_differs"] = True
                        metadata["numeric_contradiction"] = True
        except ValueError:
            pass
    
    metadata["prev_numeric_claims"] = {
        "percentages": prev_percentages,
        "has_growth": prev_has_growth,
        "has_shrink": prev_has_shrink
    }
    metadata["curr_numeric_claims"] = {
        "percentages": curr_percentages,
        "has_growth": curr_has_growth,
        "has_shrink": curr_has_shrink
    }
    
    return metadata["numeric_contradiction"], metadata

def should_run_nli_contradiction_check(
    prev_question: Optional[str],
    current_question: str,
    prev_answer: Optional[str],
    current_answer: str,
    question_similarity_threshold: float = 0.7
) -> Tuple[bool, Dict[str, Any]]:
    """
    Determine if NLI contradiction check should run based on question similarity and entity overlap.
    
    Args:
        prev_question: Previous question (if available)
        current_question: Current question
        prev_answer: Previous answer
        current_answer: Current answer
        question_similarity_threshold: Minimum similarity to run NLI (default: 0.7)
    
    Returns:
        Tuple of (should_run, metadata)
    """
    metadata = {
        "should_run": True,
        "reason": "default",
        "question_similarity": None,
        "entity_overlap": False,
        "skip_reason": None
    }
    
    # If no previous question, we can't check similarity, but still run if prev_answer exists
    if not prev_question:
        if prev_answer:
            metadata["reason"] = "no_prev_question_but_has_prev_answer"
            return True, metadata
        else:
            metadata["should_run"] = False
            metadata["skip_reason"] = "no_prev_question_and_no_prev_answer"
            return False, metadata
    
    # Compute question similarity
    question_similarity = compute_semantic_similarity(prev_question, current_question)
    metadata["question_similarity"] = question_similarity
    
    # Check entity overlap
    entity_overlap = check_entity_overlap(prev_question, current_question)
    metadata["entity_overlap"] = entity_overlap
    
    # Decision logic: Run NLI if similarity >= threshold OR entity overlap
    if question_similarity is not None:
        if question_similarity >= question_similarity_threshold:
            metadata["should_run"] = True
            metadata["reason"] = f"high_similarity_{question_similarity:.2f}"
        elif entity_overlap:
            metadata["should_run"] = True
            metadata["reason"] = "entity_overlap"
        else:
            metadata["should_run"] = False
            metadata["skip_reason"] = f"low_similarity_{question_similarity:.2f}_no_entity_overlap"
    else:
        # If similarity computation failed, use entity overlap as fallback
        if entity_overlap:
            metadata["should_run"] = True
            metadata["reason"] = "entity_overlap_fallback"
        else:
            metadata["should_run"] = False
            metadata["skip_reason"] = "similarity_computation_failed_no_entity_overlap"
    
    return metadata["should_run"], metadata

def check_answer_similarity_contradiction(
    nli_score: float,
    prev_answer: str,
    current_answer: str,
    answer_similarity_threshold: float = 0.9,
    nli_threshold: float = 0.8
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """
    Check if high NLI score should be suppressed due to high answer similarity.
    
    Args:
        nli_score: NLI contradiction score
        prev_answer: Previous answer
        current_answer: Current answer
        answer_similarity_threshold: Minimum similarity to suppress (default: 0.9)
        nli_threshold: Minimum NLI score to check (default: 0.8)
    
    Returns:
        Tuple of (should_suppress, adjusted_score, metadata)
    """
    metadata = {
        "should_suppress": False,
        "answer_similarity": None,
        "reason": None
    }
    
    # Only check if NLI score is high
    if nli_score < nli_threshold:
        return False, nli_score, metadata
    
    # Compute answer similarity
    answer_similarity = compute_semantic_similarity(prev_answer, current_answer)
    metadata["answer_similarity"] = answer_similarity
    
    if answer_similarity is not None and answer_similarity >= answer_similarity_threshold:
        # High NLI but also high similarity - likely false positive
        metadata["should_suppress"] = True
        metadata["reason"] = f"high_nli_{nli_score:.2f}_but_high_similarity_{answer_similarity:.2f}"
        # Suppress by reducing score significantly
        adjusted_score = nli_score * 0.3  # Reduce to 30% of original
        return True, adjusted_score, metadata
    
    return False, nli_score, metadata



























