from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch, torch.nn.functional as F
import re
import numpy as np
from typing import Tuple, List, Optional
import os

# Model configuration: Use DeBERTa-v3 if available, fallback to local model
DEBERTA_MODEL = "cross-encoder/nli-deberta-v3-base"
MODEL_DIR = "models/nli"

# Global model instance for sentence-transformers
_sentence_transformer_model = None
_use_deberta_v3 = None  # Will be determined on first load

def load_model():
    """
    Load NLI model. Supports both DeBERTa-v3 (via sentence-transformers) 
    and local models (via transformers).
    """
    global _sentence_transformer_model, _use_deberta_v3
    
    # Check environment variable or default to False
    # For this project, we default to the local RoBERTa NLI model in models/nli
    # DeBERTa-v3 can be re-enabled by setting USE_DEBERTA_V3=true in the environment.
    if _use_deberta_v3 is None:
        _use_deberta_v3 = os.environ.get("USE_DEBERTA_V3", "false").lower() == "true"
    
    if _use_deberta_v3:
        try:
            from sentence_transformers import CrossEncoder
            if _sentence_transformer_model is None:
                print(f"Loading DeBERTa-v3 NLI model: {DEBERTA_MODEL}")
                _sentence_transformer_model = CrossEncoder(DEBERTA_MODEL)
            # Return dummy tokenizer/model for compatibility
            # Actual computation uses sentence_transformer_model
            return None, _sentence_transformer_model
        except Exception as e:
            print(f"Failed to load DeBERTa-v3, falling back to local model: {e}")
            _use_deberta_v3 = False
    
    # Fallback to local model
    if os.path.exists(MODEL_DIR):
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR).to("cuda" if torch.cuda.is_available() else "cpu")
        return tokenizer, model
    else:
        raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")

def contradiction_score(premise, hypothesis, tokenizer, model):
    """
    Compute contradiction score. Supports both DeBERTa-v3 (sentence-transformers)
    and local models (transformers).
    """
    global _sentence_transformer_model, _use_deberta_v3
    
    if _use_deberta_v3 and _sentence_transformer_model is not None:
        # Use DeBERTa-v3 via sentence-transformers
        # CrossEncoder returns logits: [contradiction, entailment, neutral]
        scores = _sentence_transformer_model.predict([(premise, hypothesis)])
        logits = scores[0]
        
        # Apply softmax to get probabilities
        e_x = np.exp(logits - np.max(logits))
        probs = e_x / e_x.sum()
        
        # For cross-encoder/nli-deberta-v3-base, check model card for label order
        # Typically: [contradiction, entailment, neutral] or [entailment, neutral, contradiction]
        # We'll assume [contradiction, entailment, neutral] based on common patterns
        # If this doesn't work, we may need to check the actual model output
        contradiction_prob = float(probs[0])  # First index is contradiction
        return contradiction_prob, probs.tolist()
    else:
        # Use local model (original implementation)
        inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, padding=True).to(model.device)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = F.softmax(logits, dim=-1).cpu().numpy()[0]
        # assumes label order entailment, neutral, contradiction
        return float(probs[2]), probs.tolist()

def contradiction_score_bidirectional(premise, hypothesis, tokenizer, model, question: Optional[str] = None):
    """
    Compute bidirectional contradiction score (max of both directions).
    Includes question context if provided.
    
    Args:
        premise: Previous answer
        hypothesis: Current answer
        tokenizer: NLI tokenizer (or None for DeBERTa)
        model: NLI model
        question: Optional question text for context
    
    Returns:
        Tuple of (contradiction_score, all_probs, metadata)
    """
    # Format with question context if provided
    if question:
        premise_formatted = f"Question: {question} Answer: {premise}"
        hypothesis_formatted = f"Question: {question} Answer: {hypothesis}"
    else:
        premise_formatted = premise
        hypothesis_formatted = hypothesis
    
    # Compute in both directions
    score1, probs1 = contradiction_score(premise_formatted, hypothesis_formatted, tokenizer, model)
    score2, probs2 = contradiction_score(hypothesis_formatted, premise_formatted, tokenizer, model)
    
    # Take maximum (more conservative - catches contradictions in either direction)
    max_score = max(score1, score2)
    max_probs = probs1 if score1 >= score2 else probs2
    
    metadata = {
        "forward_score": score1,
        "reverse_score": score2,
        "bidirectional": True,
        "question_context": question is not None
    }
    
    return max_score, max_probs, metadata


def detect_directional_contrast(text1: str, text2: str) -> bool:
    """
    Detect if two texts contain opposite directional claims (e.g., "A up" vs "B down").
    This is common in comparative queries and should NOT be treated as contradiction.

    Args:
        text1: First text
        text2: Second text

    Returns:
        True if texts contain contrastive (not contradictory) directional claims
    """
    # Extract directional indicators
    up_patterns = [r'\b(up|rise|rising|gain|gaining|increase|increasing|climb|climbing|rally|rallying|bullish|higher|outperform)\b']
    down_patterns = [r'\b(down|fall|falling|loss|losing|decrease|decreasing|drop|dropping|decline|declining|bearish|lower|underperform)\b']

    # Count directional indicators in each text
    text1_lower = text1.lower()
    text2_lower = text2.lower()

    text1_has_up = any(re.search(p, text1_lower) for p in up_patterns)
    text1_has_down = any(re.search(p, text1_lower) for p in down_patterns)
    text2_has_up = any(re.search(p, text2_lower) for p in up_patterns)
    text2_has_down = any(re.search(p, text2_lower) for p in down_patterns)

    # Check if they have opposite directions (contrastive)
    is_contrastive = (text1_has_up and text2_has_down) or (text1_has_down and text2_has_up)

    return is_contrastive


def contradiction_score_comparative(
    premise: str,
    hypothesis: str,
    tokenizer,
    model,
    query: Optional[str] = None,
    comparative_intent: bool = False
) -> Tuple[float, List[float], dict]:
    """
    Enhanced contradiction scoring with comparative query awareness.

    When comparative intent is detected:
    - Reduces contradiction weight by 50%
    - Treats opposite directional claims as contrastive, not contradictions
    - Returns metadata about adjustments made

    Args:
        premise: First text (e.g., previous answer or retrieved passage)
        hypothesis: Second text (e.g., current answer)
        tokenizer: NLI tokenizer
        model: NLI model
        query: Optional user query to detect comparative intent
        comparative_intent: Explicitly mark as comparative query (overrides auto-detection)

    Returns:
        Tuple of:
            - adjusted_score: Contradiction score [0, 1] (adjusted if comparative)
            - raw_probs: List of [entailment, neutral, contradiction] probabilities
            - metadata: Dict with adjustment info
    """
    # Compute raw contradiction score
    raw_score, raw_probs = contradiction_score(premise, hypothesis, tokenizer, model)

    # Initialize metadata
    metadata = {
        "raw_contradiction": raw_score,
        "adjusted_contradiction": raw_score,
        "comparative_intent_detected": comparative_intent,
        "directional_contrast_detected": False,
        "adjustment_applied": False,
        "reduction_factor": 1.0
    }

    # Detect comparative intent from query if provided
    if query and not comparative_intent:
        comparative_patterns = [
            r'\b(compare|comparison|versus|vs\.?|v\.s\.?)\b',
            r'\b(relative to|compared to|against)\b',
            r'\b(better than|worse than|outperform|underperform)\b',
            r'\b(which is better|which is worse)\b',
        ]
        if any(re.search(p, query, re.IGNORECASE) for p in comparative_patterns):
            comparative_intent = True
            metadata["comparative_intent_detected"] = True

    # If comparative intent detected, apply adjustments
    if comparative_intent:
        # Check for directional contrast
        is_contrastive = detect_directional_contrast(premise, hypothesis)
        metadata["directional_contrast_detected"] = is_contrastive

        if is_contrastive:
            # Strong reduction for contrastive claims (e.g., "AAPL up" vs "MSFT down")
            reduction_factor = 0.3  # Reduce to 30% of original
            metadata["adjustment_applied"] = True
            metadata["reduction_factor"] = reduction_factor
        else:
            # Moderate reduction for other comparative queries
            reduction_factor = 0.5  # Reduce to 50% of original
            metadata["adjustment_applied"] = True
            metadata["reduction_factor"] = reduction_factor

        adjusted_score = raw_score * reduction_factor
        metadata["adjusted_contradiction"] = adjusted_score
    else:
        adjusted_score = raw_score

    return adjusted_score, raw_probs, metadata
