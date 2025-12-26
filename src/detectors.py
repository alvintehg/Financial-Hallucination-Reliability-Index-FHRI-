# src/detectors.py
"""
Lazy-initialized detector wrappers with timeouts and graceful fallbacks.

Provides thread-safe lazy initialization for:
- Semantic entropy detection (MCEncoder)
- NLI contradiction detection (cross-encoder)

Each detector has configurable timeouts and fails gracefully if unavailable.
"""

import logging
import threading
from typing import Optional, Tuple, Any, List
import time

logger = logging.getLogger("detectors")


class LazyMCEncoder:
    """Lazy-initialized MC-Dropout semantic entropy detector."""

    def __init__(self):
        self._encoder = None
        self._entropy_fn = None
        self._lock = threading.Lock()
        self._initialized = False
        self._failed = False

    def _initialize(self):
        """Initialize the MC encoder (called once on first use)."""
        if self._initialized or self._failed:
            return

        with self._lock:
            if self._initialized or self._failed:
                return

            try:
                logger.info("Initializing MC-Dropout encoder (lazy load)...")
                try:
                    from hallucination_entropy import MCEncoder, semantic_entropy_from_embeddings
                except ImportError:
                    from src.hallucination_entropy import MCEncoder, semantic_entropy_from_embeddings
                self._encoder = MCEncoder()
                self._entropy_fn = semantic_entropy_from_embeddings
                self._initialized = True
                logger.info("✓ MC-Dropout encoder loaded successfully")
            except Exception as e:
                logger.warning(f"✗ Failed to initialize MC encoder: {e}")
                self._failed = True
                self._encoder = None
                self._entropy_fn = None

    def is_available(self) -> bool:
        """Check if encoder is available (tries to initialize if needed)."""
        if not self._initialized and not self._failed:
            self._initialize()
        return self._initialized

    def compute_entropy(self, answer: str, mc_rounds: int = 6, timeout: float = 10.0) -> Optional[float]:
        """
        Compute semantic entropy for answer.

        Args:
            answer: Text to analyze
            mc_rounds: Number of MC-Dropout rounds
            timeout: Maximum time in seconds

        Returns:
            Entropy value or None if failed/timeout
        """
        if not self.is_available():
            logger.debug("MC encoder not available, skipping entropy computation")
            return None

        if not answer or not answer.strip():
            return None

        try:
            start_time = time.time()

            # Compute embeddings with MC-Dropout
            embs = self._encoder.embed([answer], mc_rounds=mc_rounds)

            # Check timeout
            if time.time() - start_time > timeout:
                logger.warning(f"Entropy computation exceeded timeout ({timeout}s)")
                return None

            # Compute entropy from embeddings
            ent_vals = self._entropy_fn(embs)
            ent = float(ent_vals[0]) if isinstance(ent_vals, (list, tuple)) else float(ent_vals)

            elapsed = time.time() - start_time
            logger.debug(f"Entropy computed: {ent:.3f} in {elapsed:.2f}s")
            return ent

        except Exception as e:
            logger.warning(f"Entropy computation failed: {e}")
            return None


class LazyNLIDetector:
    """Lazy-initialized NLI contradiction detector."""

    def __init__(self):
        self._tokenizer = None
        self._model = None
        self._lock = threading.Lock()
        self._initialized = False
        self._failed = False

    def _initialize(self):
        """Initialize the NLI model (called once on first use)."""
        if self._initialized or self._failed:
            return

        with self._lock:
            if self._initialized or self._failed:
                return

            try:
                logger.info("Initializing NLI contradiction detector (lazy load)...")
                try:
                    from nli_infer import load_model
                except ImportError:
                    from src.nli_infer import load_model
                self._tokenizer, self._model = load_model()
                self._initialized = True
                logger.info("✓ NLI detector loaded successfully")
            except Exception as e:
                logger.warning(f"✗ Failed to initialize NLI detector: {e}")
                self._failed = True
                self._tokenizer = None
                self._model = None

    def is_available(self) -> bool:
        """Check if detector is available (tries to initialize if needed)."""
        if not self._initialized and not self._failed:
            self._initialize()
        return self._initialized

    def compute_contradiction(self, premise: str, hypothesis: str, timeout: float = 5.0, 
                             question: Optional[str] = None, bidirectional: bool = True) -> Optional[Tuple[float, List[float], dict]]:
        """
        Compute contradiction score between premise and hypothesis.
        Supports bidirectional scoring and question context.

        Args:
            premise: First text (e.g., previous answer)
            hypothesis: Second text (e.g., current answer)
            timeout: Maximum time in seconds
            question: Optional question text for context-aware NLI
            bidirectional: If True, compute both directions and take max

        Returns:
            Tuple of (contradiction_score, all_probs, metadata) or None if failed/timeout
        """
        if not self.is_available():
            logger.debug("NLI detector not available, skipping contradiction computation")
            return None

        if not premise or not hypothesis:
            return None

        try:
            start_time = time.time()

            try:
                from nli_infer import contradiction_score_bidirectional, contradiction_score
            except ImportError:
                from src.nli_infer import contradiction_score_bidirectional, contradiction_score

            # Use bidirectional scoring if enabled
            if bidirectional:
                score, probs, metadata = contradiction_score_bidirectional(
                    premise, hypothesis, self._tokenizer, self._model, question
                )
            else:
                # Single direction (backward compatibility)
                if question:
                    premise_formatted = f"Question: {question} Answer: {premise}"
                    hypothesis_formatted = f"Question: {question} Answer: {hypothesis}"
                else:
                    premise_formatted = premise
                    hypothesis_formatted = hypothesis
                
                score, probs = contradiction_score(premise_formatted, hypothesis_formatted, self._tokenizer, self._model)
                metadata = {"bidirectional": False, "question_context": question is not None}

            elapsed = time.time() - start_time

            # Check timeout (post-computation check since NLI is usually fast)
            if elapsed > timeout:
                logger.warning(f"NLI computation exceeded timeout ({timeout}s)")
                return None

            logger.debug(f"Contradiction computed: {score:.3f} in {elapsed:.2f}s (bidirectional={bidirectional})")
            return float(score), probs, metadata

        except Exception as e:
            logger.warning(f"NLI contradiction computation failed: {e}")
            return None


# Global lazy instances
_mc_encoder = None
_nli_detector = None


def get_mc_encoder() -> LazyMCEncoder:
    """Get or create the global MC encoder instance."""
    global _mc_encoder
    if _mc_encoder is None:
        _mc_encoder = LazyMCEncoder()
    return _mc_encoder


def get_nli_detector() -> LazyNLIDetector:
    """Get or create the global NLI detector instance."""
    global _nli_detector
    if _nli_detector is None:
        _nli_detector = LazyNLIDetector()
    return _nli_detector
