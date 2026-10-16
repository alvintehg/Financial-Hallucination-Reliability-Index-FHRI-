# src/nli_answer_evidence.py
"""
NLI-based answer-vs-evidence contradiction scoring.

Uses NLI model to check if answer contradicts retrieved passages.
Implements veto mechanism for high-risk scenarios.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("nli_answer_evidence")


def compute_answer_evidence_nli(
    answer: str,
    passages: List[str],
    nli_detector,
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Compute NLI scores between answer (hypothesis) and passages (premises).

    For each passage, compute:
    - Entailment: passage logically supports answer
    - Contradiction: passage contradicts answer

    Args:
        answer: LLM-generated answer
        passages: Retrieved evidence passages
        nli_detector: LazyNLIDetector instance from detectors.py
        timeout: Timeout per NLI call (seconds)

    Returns:
        Dict with:
            - max_entailment: float (max entailment score across passages)
            - max_contradiction: float (max contradiction score across passages)
            - avg_entailment: float
            - avg_contradiction: float
            - passage_scores: List[Dict] with per-passage scores
    """
    if not passages or not answer:
        return {
            "max_entailment": 0.0,
            "max_contradiction": 0.0,
            "avg_entailment": 0.0,
            "avg_contradiction": 0.0,
            "passage_scores": []
        }

    if not nli_detector or not nli_detector.is_available():
        logger.warning("NLI detector not available, skipping answer-evidence scoring")
        return {
            "max_entailment": 0.0,
            "max_contradiction": 0.0,
            "avg_entailment": 0.0,
            "avg_contradiction": 0.0,
            "passage_scores": []
        }

    entailment_scores = []
    contradiction_scores = []
    passage_scores = []

    for idx, passage in enumerate(passages[:5]):  # Limit to top 5 passages to avoid timeout
        # Run NLI: premise=passage, hypothesis=answer
        try:
            result = nli_detector.compute_contradiction(
                premise=passage,
                hypothesis=answer,
                timeout=timeout,
                bidirectional=False  # Unidirectional: passage → answer
            )

            if result:
                # Result format: (contradiction_score, [entailment, neutral, contradiction], metadata)
                contradiction_score, probs, metadata = result
                entailment_score = probs[0]  # Entailment probability
                neutral_score = probs[1]
                contradiction_prob = probs[2]

                entailment_scores.append(entailment_score)
                contradiction_scores.append(contradiction_prob)

                passage_scores.append({
                    "passage_idx": idx,
                    "entailment": entailment_score,
                    "neutral": neutral_score,
                    "contradiction": contradiction_prob
                })

                logger.debug(f"Passage {idx}: entailment={entailment_score:.3f}, contradiction={contradiction_prob:.3f}")

        except Exception as e:
            logger.warning(f"NLI failed for passage {idx}: {e}")
            continue

    if not entailment_scores:
        return {
            "max_entailment": 0.0,
            "max_contradiction": 0.0,
            "avg_entailment": 0.0,
            "avg_contradiction": 0.0,
            "passage_scores": []
        }

    return {
        "max_entailment": max(entailment_scores),
        "max_contradiction": max(contradiction_scores),
        "avg_entailment": sum(entailment_scores) / len(entailment_scores),
        "avg_contradiction": sum(contradiction_scores) / len(contradiction_scores),
        "passage_scores": passage_scores
    }


def apply_nli_veto(
    fhri: float,
    nli_result: Dict[str, Any],
    scenario: str,
    veto_threshold: float = 0.7,
    moderate_threshold: float = 0.5,
    high_risk_scenarios: Optional[set] = None
) -> Tuple[float, bool, str]:
    """
    Apply NLI-based veto to FHRI score.

    For high-risk scenarios (numeric_kpi, regulatory), if contradiction ≥ veto_threshold,
    downscale FHRI by (1 - contradiction).

    Args:
        fhri: Current FHRI score
        nli_result: Result from compute_answer_evidence_nli
        scenario: Detected scenario (e.g., "numeric_kpi")
        veto_threshold: Contradiction threshold for hard veto (default 0.7)
        moderate_threshold: Contradiction threshold for soft penalty (default 0.5)
        high_risk_scenarios: Set of scenario IDs that trigger veto (default: numeric_kpi, regulatory)

    Returns:
        Tuple of (adjusted_fhri, vetoed, reason)
    """
    if high_risk_scenarios is None:
        high_risk_scenarios = {"numeric_kpi", "regulatory"}

    max_contradiction = nli_result.get("max_contradiction", 0.0)
    scenario_key = (scenario or "default").lower()

    if scenario_key not in high_risk_scenarios:
        # No veto for low-risk scenarios, but still apply soft penalty
        if max_contradiction >= moderate_threshold:
            # Soft penalty for moderate contradiction
            adjusted_fhri = fhri * (1 - max_contradiction * 0.3)
            return (adjusted_fhri, False, f"Soft contradiction penalty ({max_contradiction:.2f})")
        return (fhri, False, "")

    # High-risk scenario: apply stricter veto rules
    if max_contradiction >= veto_threshold:
        # HARD VETO: Multiply FHRI by (1 - contradiction)
        adjusted_fhri = fhri * (1 - max_contradiction)
        logger.warning(f"NLI veto triggered: max_contradiction={max_contradiction:.3f} ≥ {veto_threshold} for scenario={scenario_key}")
        return (adjusted_fhri, True, f"High contradiction detected ({max_contradiction:.2f})")

    elif max_contradiction >= moderate_threshold:
        # Moderate contradiction: downscale FHRI moderately
        adjusted_fhri = fhri * (1 - max_contradiction * 0.5)
        return (adjusted_fhri, False, f"Moderate contradiction penalty ({max_contradiction:.2f})")

    return (fhri, False, "")
