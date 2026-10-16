# src/adaptive_fhri.py
"""
Adaptive FHRI Reliability Computation with Auto-Learned Weights.

Features:
- Adaptive weight calibration based on recent chat stability
- Contradiction normalization with EMA smoothing
- Stability tracking over rolling window
- Auto-retuning when FHRI fluctuates excessively
- Enhanced output schema with stability metrics
- Semantic similarity pre-check for comparative queries
- Context-aware contradiction detection

FHRI = w₁·(1 - entropy_norm) + w₂·(1 - contradiction_norm) + w₃·grounding_score
       + w₄·numeric_consistency + w₅·temporal_consistency
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger("adaptive_fhri")

# Lazy import for sentence-transformers to avoid initialization overhead
_similarity_model = None

def get_similarity_model():
    """Lazy load sentence-transformers model for semantic similarity."""
    global _similarity_model
    if _similarity_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _similarity_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformers model for semantic similarity")
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers model: {e}")
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
    if model is None:
        return None

    try:
        embeddings = model.encode([text1, text2])
        # Compute cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    except Exception as e:
        logger.warning(f"Failed to compute semantic similarity: {e}")
        return None


class AdaptiveFHRIScorer:
    """
    Adaptive FHRI scorer with auto-learned weights and stability tracking.

    Maintains a rolling window of recent turns to:
    - Smooth contradiction scores with EMA
    - Detect identical-query drift
    - Auto-tune weights based on stability
    - Track FHRI trends over time
    """

    def __init__(
        self,
        window_size: int = 10,
        ema_alpha: float = 0.3,
        stability_threshold: float = 0.7,
        fluctuation_threshold: float = 0.15,
        weights_file: Optional[str] = None
    ):
        """
        Initialize adaptive FHRI scorer.

        Args:
            window_size: Number of recent turns to track (default: 10)
            ema_alpha: EMA smoothing factor for contradiction (default: 0.3)
            stability_threshold: Minimum stability index to avoid warnings (default: 0.7)
            fluctuation_threshold: Max FHRI change for same query before retuning (default: 0.15)
            weights_file: Optional path to persist learned weights
        """
        self.window_size = window_size
        self.ema_alpha = ema_alpha
        self.stability_threshold = stability_threshold
        self.fluctuation_threshold = fluctuation_threshold
        self.weights_file = weights_file

        # Default initial weights (matching original FHRI but with entropy+contradiction split)
        self.weights = {
            "entropy": 0.25,        # w₁: Inverse normalized entropy
            "contradiction": 0.20,   # w₂: Inverse normalized contradiction
            "grounding": 0.25,       # w₃: Grounding score
            "numeric": 0.20,         # w₄: Numeric consistency
            "temporal": 0.10         # w₅: Temporal consistency
        }

        # Load persisted weights if available
        if weights_file and Path(weights_file).exists():
            try:
                with open(weights_file, 'r') as f:
                    loaded = json.load(f)
                    self.weights.update(loaded.get("weights", {}))
                    logger.info(f"Loaded adaptive weights from {weights_file}: {self.weights}")
            except Exception as e:
                logger.warning(f"Failed to load weights from {weights_file}: {e}")

        # Rolling window buffers
        self.entropy_window = deque(maxlen=window_size)
        self.contradiction_window = deque(maxlen=window_size)
        self.contradiction_raw_window = deque(maxlen=3)  # Store last 3 raw contradiction scores
        self.fhri_window = deque(maxlen=window_size)
        self.query_history = deque(maxlen=window_size)  # (query_text, fhri) tuples for semantic comparison

        # EMA state for contradiction smoothing
        self.contradiction_ema = None

        # Retuning state
        self.total_turns = 0
        self.last_retune_turn = 0

        # Comparative query tracking
        self.last_query = None
        self.query_similarity_threshold = 0.75  # Threshold for semantic similarity check

    def _validate_weights(self):
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if not np.isclose(total, 1.0, atol=1e-6):
            logger.warning(f"Weights sum to {total:.4f}, normalizing to 1.0")
            for key in self.weights:
                self.weights[key] /= total

    def _save_weights(self):
        """Persist learned weights to file."""
        if not self.weights_file:
            return

        try:
            data = {
                "weights": self.weights,
                "last_updated": datetime.now().isoformat(),
                "total_turns": self.total_turns,
                "stability_index": self.compute_stability_index()
            }
            with open(self.weights_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved adaptive weights to {self.weights_file}")
        except Exception as e:
            logger.warning(f"Failed to save weights to {self.weights_file}: {e}")

    def compute_contradiction_smoothed(
        self,
        contradiction_raw: Optional[float],
        comparative_intent: bool = False,
        query_similarity: Optional[float] = None
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """
        Apply EMA smoothing to contradiction score with comparative query awareness.

        When comparative intent is detected or query similarity < 0.75:
        - Skip contradiction penalty (return lower smoothed score)

        Args:
            contradiction_raw: Raw NLI contradiction score [0, 1]
            comparative_intent: Whether query has comparative intent
            query_similarity: Semantic similarity to previous query [0, 1]

        Returns:
            Tuple of (smoothed_score, metadata_dict)
        """
        metadata = {
            "raw": contradiction_raw,
            "smoothed": None,
            "skip_penalty": False,
            "skip_reason": None
        }

        if contradiction_raw is None:
            return None, metadata

        # Cap to [0, 1]
        contradiction_capped = max(0.0, min(1.0, contradiction_raw))

        # Add to raw window for EMA calculation
        self.contradiction_raw_window.append(contradiction_capped)

        # Check if we should skip contradiction penalty
        skip_penalty = False
        if comparative_intent:
            skip_penalty = True
            metadata["skip_reason"] = "comparative_intent_detected"
        elif query_similarity is not None and query_similarity < self.query_similarity_threshold:
            skip_penalty = True
            metadata["skip_reason"] = f"low_query_similarity ({query_similarity:.2f} < {self.query_similarity_threshold})"

        # Apply EMA smoothing over last 3 turns
        if len(self.contradiction_raw_window) >= 2:
            # Use EMA with alpha=0.6 as specified
            recent_scores = list(self.contradiction_raw_window)
            ema_smoothed = recent_scores[0]
            for score in recent_scores[1:]:
                ema_smoothed = 0.6 * score + 0.4 * ema_smoothed
            smoothed = ema_smoothed
        else:
            # Not enough history, use raw score
            smoothed = contradiction_capped

        # If skip penalty, reduce smoothed score
        if skip_penalty:
            smoothed = smoothed * 0.5  # Reduce by 50%
            metadata["skip_penalty"] = True

        # Add to window
        self.contradiction_window.append(smoothed)
        metadata["smoothed"] = smoothed

        logger.debug(f"Contradiction: raw={contradiction_raw:.3f}, smoothed={smoothed:.3f}, "
                    f"skip_penalty={skip_penalty}, reason={metadata.get('skip_reason')}")
        return smoothed, metadata

    def compute_stability_index(self) -> float:
        """
        Compute stability index from rolling FHRI window.

        Stability = 1 - std(FHRI_window)

        Returns:
            Stability index [0, 1] where 1 = perfectly stable
        """
        if len(self.fhri_window) < 3:
            return 1.0  # Not enough data, assume stable

        fhri_std = np.std(list(self.fhri_window))
        stability = max(0.0, 1.0 - fhri_std)

        logger.debug(f"Stability index: {stability:.3f} (std={fhri_std:.3f}, n={len(self.fhri_window)})")
        return stability

    def detect_identical_query_drift(self, query: str, fhri: float) -> Tuple[bool, float, Optional[float]]:
        """
        Detect if identical/similar queries yield inconsistent FHRI scores.
        Uses semantic similarity to detect similar (not just identical) queries.

        Args:
            query: Current user query
            fhri: Current FHRI score

        Returns:
            Tuple of (drift_detected, max_delta, query_similarity_to_prev)
        """
        drift_detected = False
        max_delta = 0.0
        query_similarity = None

        # Check semantic similarity with previous queries
        for prev_query, prev_fhri in self.query_history:
            # Compute semantic similarity
            similarity = compute_semantic_similarity(query, prev_query)

            if similarity is not None and similarity > 0.85:  # High similarity threshold
                delta = abs(fhri - prev_fhri)
                max_delta = max(max_delta, delta)

                if delta > self.fluctuation_threshold:
                    drift_detected = True
                    logger.warning(f"Similar query drift detected (similarity={similarity:.2f}): "
                                 f"FHRI changed by {delta:.3f} (current={fhri:.3f}, prev={prev_fhri:.3f})")

        # Compute similarity to last query (for comparative intent detection)
        if self.last_query:
            query_similarity = compute_semantic_similarity(query, self.last_query)

        # Store current query
        self.query_history.append((query, fhri))
        self.last_query = query

        return drift_detected, max_delta, query_similarity

    def auto_retune_weights(self):
        """
        Auto-retune weights based on recent stability metrics.

        Rules:
        - If contradiction > 80% → decrease weight of contradiction by 0.3x
        - If answers repeat with low entropy → increase weight on grounding and numeric
        - If FHRI fluctuates > ±15% for same query → trigger retuning
        """
        if len(self.contradiction_window) < 5:
            logger.debug("Not enough data for retuning (need 5+ turns)")
            return

        # Get recent averages
        avg_contradiction = np.mean(list(self.contradiction_window))
        avg_entropy = np.mean(list(self.entropy_window)) if self.entropy_window else None
        stability = self.compute_stability_index()

        retuned = False

        # Rule 1: High contradiction → reduce contradiction weight
        if avg_contradiction > 0.80:
            old_weight = self.weights["contradiction"]
            self.weights["contradiction"] *= 0.7  # Reduce by 30%
            logger.info(f"High contradiction detected ({avg_contradiction:.2f}) → reducing weight "
                       f"from {old_weight:.3f} to {self.weights['contradiction']:.3f}")
            retuned = True

        # Rule 2: Low entropy (repetitive answers) → boost grounding and numeric
        if avg_entropy is not None and avg_entropy < 0.5:
            old_g = self.weights["grounding"]
            old_n = self.weights["numeric"]
            self.weights["grounding"] += 0.05
            self.weights["numeric"] += 0.05
            logger.info(f"Low entropy detected ({avg_entropy:.2f}) → boosting grounding "
                       f"({old_g:.3f}→{self.weights['grounding']:.3f}) and numeric "
                       f"({old_n:.3f}→{self.weights['numeric']:.3f})")
            retuned = True

        # Rule 3: Low stability → rebalance weights
        if stability < self.stability_threshold:
            # Rebalance by reducing volatile components
            logger.info(f"Low stability ({stability:.2f}) → rebalancing weights")

            # Reduce entropy and contradiction (more volatile)
            self.weights["entropy"] *= 0.85
            self.weights["contradiction"] *= 0.85

            # Increase grounding and numeric (more stable)
            self.weights["grounding"] *= 1.1
            self.weights["numeric"] *= 1.1

            retuned = True

        if retuned:
            # Renormalize
            self._validate_weights()

            # Save to file
            self._save_weights()

            # Update retune state
            self.last_retune_turn = self.total_turns

            logger.info(f"Weights retuned: {self.weights}")

    def compute_adaptive_fhri(
        self,
        answer: str,
        question: str,
        passages: List[str],
        entropy: Optional[float] = None,
        contradiction_raw: Optional[float] = None,
        grounding_score: Optional[float] = None,
        numeric_score: Optional[float] = None,
        temporal_score: Optional[float] = None,
        multi_source_data: Optional[Dict[str, Any]] = None,
        comparative_intent: bool = False
    ) -> Dict[str, Any]:
        """
        Compute adaptive FHRI with auto-learned weights and comparative query awareness.

        Args:
            answer: LLM-generated answer
            question: User query
            passages: Retrieved passages
            entropy: Semantic entropy value [0, ~3.5]
            contradiction_raw: Raw NLI contradiction score [0, 1]
            grounding_score: Pre-computed grounding score [0, 1]
            numeric_score: Pre-computed numeric consistency score [0, 1]
            temporal_score: Pre-computed temporal validity score [0, 1]
            multi_source_data: Optional multi-source verification data
            comparative_intent: Whether query has comparative intent

        Returns:
            Dict with:
                - fhri: float [0, 1]
                - fhri_label: str ("Very High", "High", "Moderate", "Low")
                - fhri_weights: Dict of current weights
                - contradiction_raw: float [0, 1] or None
                - contradiction_smoothed: float [0, 1] or None
                - stability_index: float [0, 1]
                - subscores: Dict of normalized sub-scores
                - retuned: bool indicating if weights were adjusted this turn
                - warnings: List[str] of stability warnings
        """
        self.total_turns += 1

        # Step 1: Compute query similarity to detect comparative queries
        query_similarity = None
        if self.last_query:
            query_similarity = compute_semantic_similarity(question, self.last_query)

        # Step 2: Normalize entropy to [0, 1] where 0 = high uncertainty, 1 = high confidence
        entropy_norm = None
        if entropy is not None:
            # Cap entropy at reasonable max (e.g., 3.5) and normalize
            entropy_capped = min(entropy, 3.5)
            entropy_norm = 1.0 - (entropy_capped / 3.5)  # Invert: lower entropy = higher score
            self.entropy_window.append(entropy)

        # Step 3: Smooth contradiction with EMA, comparative awareness, and semantic similarity
        contradiction_smoothed, contradiction_metadata = self.compute_contradiction_smoothed(
            contradiction_raw,
            comparative_intent=comparative_intent,
            query_similarity=query_similarity
        )
        contradiction_norm = None
        if contradiction_smoothed is not None:
            contradiction_norm = 1.0 - contradiction_smoothed  # Invert: lower contradiction = higher score

        # Step 4: Apply FHRI recalibration for grounded but divergent answers
        # If contradiction > 0.8 and grounding > 0.6, reduce contradiction weight
        dynamic_weights = self.weights.copy()
        weight_adjustments = []

        # NEW: Check if we have verified online sources (not just passages.txt)
        has_online_sources = bool(multi_source_data and multi_source_data.get("sources_used"))

        if contradiction_raw is not None and grounding_score is not None:
            if contradiction_raw > 0.8 and grounding_score > 0.6:
                # Grounded answer but high contradiction -> likely divergent framing
                if has_online_sources:
                    # More aggressive reduction when using verified online sources
                    dynamic_weights["contradiction"] *= 0.3
                    weight_adjustments.append("Reduced contradiction weight (verified online sources)")
                else:
                    dynamic_weights["contradiction"] *= 0.5
                    weight_adjustments.append("Reduced contradiction weight (grounded but divergent)")

        # If entropy < 0.4 (normalized), increase grounding weight
        if entropy_norm is not None and entropy_norm > 0.6:  # Low raw entropy = high norm entropy
            raw_entropy = entropy if entropy is not None else 0
            if raw_entropy < 0.4:
                dynamic_weights["grounding"] += 0.1
                weight_adjustments.append("Increased grounding weight (low entropy)")

        # Renormalize dynamic weights
        total_weight = sum(dynamic_weights.values())
        for k in dynamic_weights:
            dynamic_weights[k] /= total_weight

        # Step 5: Compute FHRI as weighted sum
        subscores = {
            "entropy": entropy_norm,
            "contradiction": contradiction_norm,
            "grounding": grounding_score,
            "numeric": numeric_score,
            "temporal": temporal_score
        }

        # Identify available components
        available = [k for k, v in subscores.items() if v is not None]

        if not available:
            logger.warning("No FHRI components available, returning minimal score")
            return {
                "fhri": 0.0,
                "fhri_label": "No Data",
                "fhri_weights": {k: round(v, 3) for k, v in dynamic_weights.items()},
                "contradiction_raw": contradiction_raw,
                "contradiction_smoothed": None,
                "stability_index": 1.0,
                "subscores": subscores,
                "retuned": False,
                "warnings": ["No FHRI components available"]
            }

        # Renormalize weights over available components
        total_weight = sum(dynamic_weights[k] for k in available)
        adjusted_weights = {k: dynamic_weights[k] / total_weight for k in available}

        # Compute weighted sum
        fhri = sum(adjusted_weights[k] * subscores[k] for k in available)
        fhri = max(0.0, min(1.0, fhri))  # Clamp to [0, 1]

        # Add to window
        self.fhri_window.append(fhri)

        # Step 6: Compute stability index
        stability_index = self.compute_stability_index()

        # Step 7: Detect identical query drift (now returns query_similarity too)
        drift_detected, max_drift, _ = self.detect_identical_query_drift(question, fhri)

        # Step 8: Auto-retune if needed (every 5 turns minimum)
        retuned = False
        if self.total_turns - self.last_retune_turn >= 5:
            self.auto_retune_weights()
            retuned = (self.total_turns == self.last_retune_turn)

        # Step 9: Generate warnings
        warnings = []
        if stability_index < self.stability_threshold:
            warnings.append(f"Model response consistency low — recalibrating weights (stability={stability_index:.2f})")

        if drift_detected:
            warnings.append(f"Similar query yielded different FHRI (drift={max_drift:.2f})")

        if contradiction_raw is not None and contradiction_raw > 0.9:
            if not comparative_intent:
                warnings.append(f"Very high raw contradiction ({contradiction_raw:.2f}) — may trigger recalibration")

        if weight_adjustments:
            warnings.extend(weight_adjustments)

        # Step 10: Determine FHRI label with label smoothing (±0.05)
        # Apply smoothing by using midpoint thresholds
        if fhri >= 0.825:  # 0.85 - 0.025 smoothing
            fhri_label = "Very High"
        elif fhri >= 0.625:  # 0.65 - 0.025
            fhri_label = "High"
        elif fhri >= 0.375:  # 0.40 - 0.025
            fhri_label = "Moderate"
        else:
            fhri_label = "Low"

        # Log detailed breakdown
        logger.info(f"Adaptive FHRI computed: {fhri:.3f} ({fhri_label})")
        logger.info(f"  Components: {available}")
        for k in available:
            contribution = adjusted_weights[k] * subscores[k]
            logger.info(f"    {k}: {subscores[k]:.3f} × {adjusted_weights[k]:.3f} = {contribution:.3f}")
        logger.info(f"  Stability: {stability_index:.3f}")
        logger.info(f"  Retuned: {retuned}")
        logger.info(f"  Comparative Intent: {comparative_intent}")
        logger.info(f"  Query Similarity: {query_similarity}")

        if warnings:
            for w in warnings:
                logger.warning(f"  ⚠ {w}")

        return {
            "fhri": round(fhri, 3),
            "fhri_label": fhri_label,
            "fhri_weights": {k: round(v, 3) for k, v in adjusted_weights.items()},
            "contradiction_raw": round(contradiction_raw, 3) if contradiction_raw is not None else None,
            "contradiction_smoothed": round(contradiction_smoothed, 3) if contradiction_smoothed is not None else None,
            "stability_index": round(stability_index, 3),
            "subscores": {k: (round(v, 3) if v is not None else None) for k, v in subscores.items()},
            "available_components": available,
            "retuned": retuned,
            "warnings": warnings,
            "total_turns": self.total_turns,
            "window_size": len(self.fhri_window),
            "comparative_intent": comparative_intent,
            "query_similarity": round(query_similarity, 3) if query_similarity is not None else None,
            "contradiction_metadata": contradiction_metadata
        }


# Singleton instance for session-level persistence
_default_adaptive_scorer = None


def get_default_adaptive_scorer(
    weights_file: Optional[str] = "data/adaptive_weights.json"
) -> AdaptiveFHRIScorer:
    """Get or create the default adaptive FHRI scorer."""
    global _default_adaptive_scorer
    if _default_adaptive_scorer is None:
        _default_adaptive_scorer = AdaptiveFHRIScorer(weights_file=weights_file)
        logger.info("Initialized default adaptive FHRI scorer")
    return _default_adaptive_scorer


def reset_adaptive_scorer():
    """Reset the singleton adaptive scorer (useful for testing)."""
    global _default_adaptive_scorer
    _default_adaptive_scorer = None
    logger.info("Reset adaptive FHRI scorer")
