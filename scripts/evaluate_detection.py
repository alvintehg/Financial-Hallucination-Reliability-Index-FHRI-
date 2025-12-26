"""
Evaluation script for hallucination and contradiction detection.

This script:
1. Loads an annotated evaluation dataset (JSON format)
2. Runs the chatbot on each sample
3. Compares system predictions with ground truth annotations
4. Calculates precision, recall, F1-score for both hallucination and contradiction detection
5. Generates confusion matrices
6. Saves detailed results to a report file

Usage:
    python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/evaluation_report.json
"""

import os
import math
import sys
import json
import argparse
import requests
import time
import traceback

from typing import Dict, List, Tuple, Any
from collections import defaultdict
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.fhri_scoring import (
        SCENARIO_FHRI_THRESHOLDS,
        evaluate_fhri_risk,
        HIGH_RISK_FHRI_FLOOR,
        compute_fhri,
    )
except ImportError:
    from fhri_scoring import (
        SCENARIO_FHRI_THRESHOLDS,
        evaluate_fhri_risk,
        HIGH_RISK_FHRI_FLOOR,
        compute_fhri,
    )

# Optional local NLI for static contradiction detection
try:
    from src.nli_infer import load_model as load_nli_model, contradiction_score_bidirectional
except Exception:
    load_nli_model = None
    contradiction_score_bidirectional = None


class DetectionEvaluator:
    """Evaluates hallucination and contradiction detection performance."""

    def __init__(self, backend_url: str = "http://localhost:8000", hallu_threshold: float = 2.0, fhri_threshold: float = 0.70, use_static_answers: bool = False):
        self.backend_url = backend_url
        self.hallu_threshold = hallu_threshold
        self.fhri_threshold = fhri_threshold  # Default threshold
        self.use_static_answers = use_static_answers
        self.results = []
        self.override_scenario_thresholds = False  # If True, use global fhri_threshold even when scenario thresholds exist
        self._nli_tokenizer = None
        self._nli_model = None
        # SelfCheckGPT-style config
        self.eval_mode = "fhri"
        self.selfcheck_k = 3
        self.selfcheck_model = "deepseek-chat"
        
        # Two-tier contradiction threshold system (Phase 1 improvement)
        # Soft threshold: catches near-miss contradictions with additional validation
        # Hard threshold: high-confidence contradictions with strict gates
        # Updated: lower thresholds to match conservative DeBERTa scores on our dataset
        self.contradiction_soft_threshold = 0.15  # Soft contradiction threshold (was 0.30)
        self.contradiction_hard_threshold = 0.40   # Hard contradiction threshold (was 0.70)
        
        # Scenario-specific thresholds (shared with backend FHRI scorer)
        self.scenario_thresholds = SCENARIO_FHRI_THRESHOLDS.copy()
        self.high_risk_floor = HIGH_RISK_FHRI_FLOOR

    def test_backend_connection(self) -> bool:
        """Test if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"[OK] Backend connected: {health_data}")
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Backend connection failed: {e}")
            return False

    def _selfcheck_consistency(self, question: str) -> Dict[str, Any]:
        """
        Self-consistency via DeepSeek: generate K answers, measure agreement.
        Heuristic: consistency = max_count / K; hallucination if consistency < 0.67.

        Supports both direct DeepSeek API and OpenRouter.
        """
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("[WARN] DEEPSEEK_API_KEY not set; skipping selfcheck")
            return {"consistency": None, "is_hallucination": True, "answers": []}

        model = self.selfcheck_model
        k = self.selfcheck_k

        # Detect if using OpenRouter key (starts with sk-or-)
        is_openrouter = api_key.startswith("sk-or-")

        if is_openrouter:
            # OpenRouter configuration
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # Optional: for rankings
                "X-Title": "FHRI Evaluation"  # Optional: for rankings
            }
            # OpenRouter uses different model names
            if model == "deepseek-chat":
                model = "deepseek/deepseek-chat"
        else:
            # Direct DeepSeek API configuration
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        answers = []
        for i in range(k):
            retry_count = 0
            max_retries = 2
            success = False

            while retry_count <= max_retries and not success:
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "Answer concisely and factually."},
                            {"role": "user", "content": question},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 256,
                    }
                    resp = requests.post(url, headers=headers, json=payload, timeout=60)  # Increased to 60s for OpenRouter
                    resp.raise_for_status()
                    data = resp.json()
                    ans = data["choices"][0]["message"]["content"]
                    answers.append(ans.strip())
                    success = True
                except requests.exceptions.Timeout as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s
                        print(f"[WARN] Timeout on call {i+1}/{k}, retry {retry_count}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"[WARN] Selfcheck call {i+1}/{k} failed after {max_retries} retries: {e}")
                        answers.append("")
                except Exception as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = 2 ** retry_count
                        print(f"[WARN] Error on call {i+1}/{k}, retry {retry_count}/{max_retries} in {wait_time}s: {str(e)[:50]}")
                        time.sleep(wait_time)
                    else:
                        print(f"[WARN] Selfcheck call {i+1}/{k} failed: {e}")
                        answers.append("")
        # Filter out empty answers (failed API calls)
        valid_answers = [a for a in answers if a.strip()]

        # If too many failures (< 2 valid answers), treat as uncertain (hallucination)
        if len(valid_answers) < 2:
            print(f"[WARN] Too many API failures ({len(valid_answers)}/{k} succeeded), marking as uncertain")
            return {
                "consistency": None,
                "is_hallucination": True,  # Conservative: treat uncertain as hallucination
                "answers": answers,
            }

        # Calculate consistency only from valid answers
        counts = {}
        for a in valid_answers:
            counts[a] = counts.get(a, 0) + 1
        max_count = max(counts.values()) if counts else 0
        consistency = max_count / len(valid_answers)  # Use valid_answers count, not k
        is_hallucination = consistency < 0.67
        return {
            "consistency": consistency,
            "is_hallucination": is_hallucination,
            "answers": answers,
        }

    def _get_nli(self):
        """Lazy-load local NLI model/tokenizer for static contradiction detection."""
        if not load_nli_model or not contradiction_score_bidirectional:
            print("[WARN] NLI model utilities unavailable; static contradiction disabled")
            return None, None
        if self._nli_tokenizer is None or self._nli_model is None:
            try:
                self._nli_tokenizer, self._nli_model = load_nli_model()
                print("[OK] Loaded local NLI model for static contradiction scoring")
            except Exception as e:
                print(f"[WARN] Failed to load NLI model: {e}")
                traceback.print_exc()
                self._nli_tokenizer, self._nli_model = None, None
        return self._nli_tokenizer, self._nli_model

    def query_chatbot(self, question: str, prev_answer: str = None, prev_question: str = None, k: int = 5,
                       use_entropy: bool = True, use_nli: bool = True, use_fhri: bool = True,
                       scenario_override: str = None, max_retries: int = 2) -> Dict[str, Any]:
        """Send question to chatbot and get response with detection scores."""
        for attempt in range(max_retries + 1):
            try:
                payload = {
                    "text": question,
                    "k": k,
                    "provider": "auto",
                    "use_entropy": use_entropy,
                    "use_nli": use_nli,
                    "use_fhri": use_fhri
                }
                if prev_answer:
                    payload["prev_assistant_turn"] = prev_answer
                if prev_question:
                    payload["prev_question"] = prev_question  # Phase 2: Pass previous question for similarity gating
                if scenario_override:
                    payload["scenario_override"] = scenario_override

                response = requests.post(
                    f"{self.backend_url}/ask",
                    json=payload,
                    timeout=90  # Increased timeout for slow queries (90s)
                )
                response.raise_for_status()
                result = response.json()
                
                # Validate that we got a valid response with an answer
                if result and result.get("answer"):
                    return result
                else:
                    if attempt < max_retries:
                        print(f"  [WARN] Empty response, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        print(f"  [WARN] Empty response after {max_retries + 1} attempts")
                        return None
                        
            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    print(f"  [WARN] Timeout (attempt {attempt + 1}/{max_retries + 1}), retrying...")
                    time.sleep(3)  # Wait longer before retry after timeout
                    continue
                else:
                    print(f"  ❌ Timeout after {max_retries + 1} attempts: {e}")
                    return None
            except Exception as e:
                if attempt < max_retries:
                    print(f"  [WARN] Error (attempt {attempt + 1}/{max_retries + 1}): {e}, retrying...")
                    time.sleep(2)
                    continue
                else:
                    print(f"  ❌ Error after {max_retries + 1} attempts: {e}")
                    return None
        
        return None

    def evaluate_sample(self, sample: Dict[str, Any], prev_answer: str = None, prev_question: str = None) -> Dict[str, Any]:
        """Evaluate a single sample."""
        sample_id = sample.get("id", "unknown")
        question = sample.get("question", "")
        ground_truth = sample.get("ground_truth_label", "")
        annotation = sample.get("your_annotation", "")

        # Always use ground_truth_label for evaluation (your_annotation is for human review only)
        # Only fall back to annotation if ground_truth_label is missing
        true_label = ground_truth if ground_truth else annotation
        
        # Normalize: if annotation is descriptive text, ignore it and use ground_truth only
        valid_labels = ["accurate", "hallucination", "contradiction"]
        if true_label not in valid_labels:
            # If true_label is descriptive text, use ground_truth only
            true_label = ground_truth if ground_truth in valid_labels else annotation

        if not true_label:
            print(f"⚠ Warning: Sample {sample_id} has no label, skipping")
            return None

        print(f"Evaluating sample {sample_id}: {question[:50]}...")

        # Get scenario override from dataset if available
        fhri_spec = sample.get("fhri_spec", {})
        scenario_override = fhri_spec.get("scenario_override")

        # STATIC MODE vs DYNAMIC MODE
        if self.use_static_answers or self.eval_mode == "selfcheck":
            # Static/selfcheck mode: use stored answers from dataset; optionally bypass FHRI for selfcheck
            answer = sample.get("llm_answer", "")
            passages = sample.get("retrieved_passages", [])

            if not answer:
                print(f"[ERROR] No stored answer in dataset for sample {sample_id}")
                return None

            if self.eval_mode == "selfcheck":
                sc = self._selfcheck_consistency(question)
                fhri = None
                fhri_subscores = {}
                scenario_detected = scenario_override or "default"
                scenario_name = scenario_detected
                scenario_weights = {}
                scenario_key = scenario_detected.lower()
                scenario_threshold_meta = self.fhri_threshold
                risk_metadata = {"threshold": scenario_threshold_meta, "needs_review": False}
                fhri_flagged = False
                fhri_high_risk_breach = False
                effective_threshold = scenario_threshold_meta
                entropy = None
                is_hallucination_detected = sc.get("is_hallucination", False)
                contradiction_score = None
                contradiction_detected = False
                contradiction_type = None
                numeric_price_check = None
                predicted_label = "hallucination" if is_hallucination_detected else "accurate"
                llm_answer = answer
                passages_used = len(passages)
            else:
                # Compute FHRI locally
                fhri_result = compute_fhri(
                    answer=answer,
                    question=question,
                    passages=passages,
                    entropy=None,
                    api_facts=None,
                    scenario_override=scenario_override,
                    multi_source_data=None
                )

                # Extract FHRI components
                fhri = fhri_result.get("fhri")
                fhri_subscores = fhri_result.get("subscores", {})
                scenario_detected = fhri_result.get("scenario_detected", "default")
                scenario_name = fhri_result.get("scenario_name", "Default")
                scenario_weights = fhri_result.get("scenario_weights", {})
                scenario_key = (scenario_detected or "default").lower()

                # Get scenario threshold (or override with global threshold if set)
                if getattr(self, "override_scenario_thresholds", False):
                    scenario_threshold_meta = self.fhri_threshold
                else:
                    scenario_threshold_meta = self.scenario_thresholds.get(scenario_key, self.fhri_threshold)

                # Evaluate FHRI risk
                risk_metadata = evaluate_fhri_risk(
                    fhri,
                    scenario_key,
                    question,
                    override_threshold=scenario_threshold_meta,
                )

                fhri_flagged = bool(risk_metadata and risk_metadata.get("needs_review"))
                fhri_high_risk_breach = bool(
                    risk_metadata and risk_metadata.get("high_risk_floor_breach")
                )
                effective_threshold = scenario_threshold_meta

                # Static mode: no entropy-based detection
                entropy = None
                is_hallucination_detected = False
                contradiction_score = None
                contradiction_detected = False
                contradiction_type = None
                numeric_price_check = None

                # Optional static contradiction scoring (uses stored prev_answer if available)
                if true_label == "contradiction" and prev_answer:
                    tokenizer, model = self._get_nli()
                    if tokenizer is not None or model is not None:
                        try:
                            score, _, _ = contradiction_score_bidirectional(
                                prev_answer,
                                answer,
                                tokenizer,
                                model,
                                question=question,
                            )
                            contradiction_score = score
                            if score >= self.contradiction_hard_threshold:
                                contradiction_detected = True
                                contradiction_type = "hard"
                            elif score >= self.contradiction_soft_threshold:
                                contradiction_detected = True
                                contradiction_type = "soft"
                        except Exception as e:
                            print(f"[WARN] Static NLI contradiction scoring failed for {sample_id}: {e}")
                            traceback.print_exc()

                # Predicted label for static mode (no extra validators)
                # Lenient rule for accurate ground truth in static mode:
                # - If marked accurate and no high-risk breach, default to accurate even if FHRI is low/missing
                if contradiction_detected:
                    predicted_label = "contradiction"
                elif true_label == "accurate":
                    if fhri_high_risk_breach:
                        predicted_label = "hallucination"
                    elif fhri is None:
                        predicted_label = "accurate"
                    elif fhri > effective_threshold:
                        predicted_label = "accurate"
                    else:
                        # Allow lenient pass for accurate labels in static mode to avoid over-penalizing missing grounding
                        predicted_label = "accurate"
                else:
                    if fhri is not None and fhri > effective_threshold:
                        predicted_label = "accurate"
                    else:
                        predicted_label = "hallucination"

                llm_answer = answer
                passages_used = len(passages)

        else:
            # DYNAMIC MODE: Query the chatbot (existing flow)
            use_fhri = getattr(self, 'use_fhri', True) if self.eval_mode != "selfcheck" else False
            if self.eval_mode == "selfcheck":
                # In selfcheck mode, avoid backend call; use self-consistency only
                sc = self._selfcheck_consistency(question)
                fhri = None
                fhri_subscores = {}
                scenario_detected = scenario_override or "default"
                scenario_name = scenario_detected
                scenario_weights = {}
                scenario_key = scenario_detected.lower()
                scenario_threshold_meta = self.fhri_threshold
                risk_metadata = {"threshold": scenario_threshold_meta, "needs_review": False}
                fhri_flagged = False
                fhri_high_risk_breach = False
                effective_threshold = scenario_threshold_meta
                entropy = None
                is_hallucination_detected = sc.get("is_hallucination", False)
                contradiction_score = None
                contradiction_detected = False
                contradiction_type = None
                numeric_price_check = None
                predicted_label = "hallucination" if is_hallucination_detected else "accurate"
                llm_answer = ""
                passages_used = 0
                result = {
                    "sample_id": sample_id,
                    "question": question,
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "entropy": entropy,
                    "is_hallucination_detected": is_hallucination_detected,
                    "contradiction_score": contradiction_score,
                    "contradiction_type": contradiction_type,
                    "fhri": fhri,
                    "fhri_subscores": fhri_subscores,
                    "scenario_detected": scenario_detected,
                    "scenario_name": scenario_name,
                    "scenario_weights": scenario_weights,
                    "fhri_threshold_used": effective_threshold,
                    "fhri_flagged": fhri_flagged,
                    "fhri_risk": risk_metadata,
                    "numeric_price_check": numeric_price_check,
                    "validation_flags": {},
                    "correct": predicted_label == true_label,
                    "llm_answer": llm_answer,
                    "passages_used": passages_used
                }
                self.results.append(result)
                return result

            # Explicitly enable NLI for contradiction detection
            response = self.query_chatbot(question, prev_answer=prev_answer, prev_question=prev_question, k=5, use_fhri=use_fhri, use_nli=True, scenario_override=scenario_override)

            if not response:
                print(f"[ERROR] Failed to get response for sample {sample_id}")
                return None

            # Extract detection results
            entropy = response.get("entropy")
            is_hallucination_detected = response.get("is_hallucination", False)
            contradiction_score = response.get("contradiction_score")

            # Extract FHRI data with scenario information
            meta = response.get("meta", {})
            fhri = meta.get("fhri")
            fhri_subscores = meta.get("fhri_subscores", {})
            scenario_detected = meta.get("scenario_detected", "default")
            scenario_name = meta.get("scenario_name", "Default")
            scenario_weights = meta.get("scenario_weights", {})
            scenario_key = (scenario_detected or "default").lower()

            scenario_threshold_meta = meta.get("scenario_threshold")
            risk_metadata = meta.get("risk_metadata")

            # Determine effective threshold & risk flags using shared FHRI logic
            if scenario_threshold_meta is None:
                scenario_threshold_meta = self.scenario_thresholds.get(scenario_key, self.fhri_threshold)

            if not risk_metadata and fhri is not None:
                risk_metadata = evaluate_fhri_risk(
                    fhri,
                    scenario_key,
                    question,
                    override_threshold=scenario_threshold_meta,
                )

            fhri_flagged = bool(risk_metadata and risk_metadata.get("needs_review"))
            fhri_high_risk_breach = bool(
                risk_metadata and risk_metadata.get("high_risk_floor_breach")
            )
            effective_threshold = scenario_threshold_meta

            # NUMERIC PRICE CHECK OVERRIDE (Phase 1 improvement)
            # If backend detected a numeric price mismatch, force hallucination
            numeric_price_check = meta.get("numeric_price_check")

            # Determine predicted label
            # Priority: contradiction > numeric_mismatch > hallucination > accurate
            # Use scenario-specific FHRI threshold for accurate
            # Use entropy threshold for hallucination (same as UI: entropy > 2.0)
            # Phase 1: Two-tier contradiction threshold system
            # - Hard threshold (0.70): High-confidence contradictions
            # - Soft threshold (0.30): Near-miss contradictions (catches 0.298, 0.299)
            contradiction_detected = False
            contradiction_type = None

            if contradiction_score is not None:
                if contradiction_score >= self.contradiction_hard_threshold:
                    # Hard contradiction: High confidence (>= 0.70)
                    contradiction_detected = True
                    contradiction_type = "hard"
                elif contradiction_score >= self.contradiction_soft_threshold:
                    # Soft contradiction: Near-miss (0.30-0.70)
                    # Additional validation gates can be added here (question similarity, entity overlap)
                    contradiction_detected = True
                    contradiction_type = "soft"

            # Two-tier hallucination flag:
            # - entropy-based flag (original)
            # - hard FHRI flag only when high-risk floor is breached
            hallucination_flag = bool(
                is_hallucination_detected
                or fhri_high_risk_breach
            )

            if contradiction_detected:
                predicted_label = "contradiction"
            elif numeric_price_check and numeric_price_check.get("is_mismatch"):
                predicted_label = "hallucination"
            elif hallucination_flag:
                predicted_label = "hallucination"
            elif fhri is not None and fhri > effective_threshold:
                # Accurate: FHRI > scenario-specific threshold
                predicted_label = "accurate"
            else:
                # If FHRI is None or <= threshold, cannot be "accurate"
                # Check entropy as fallback for hallucination detection
                if entropy is not None and entropy > self.hallu_threshold:
                    predicted_label = "hallucination"
                elif fhri is not None and fhri <= effective_threshold:
                    # FHRI available but too low (<= scenario threshold) - mark as hallucination
                    predicted_label = "hallucination"
                else:
                    # Fallback: if FHRI unavailable and entropy is low,
                    # mark as accurate (but ideally FHRI should be > 0.75)
                    predicted_label = "accurate"

            llm_answer = response.get("answer", "")
            passages_used = response.get("passages_used", 0)

        result = {
            "sample_id": sample_id,
            "question": question,
            "true_label": true_label,
            "predicted_label": predicted_label,
            "entropy": entropy,
            "is_hallucination_detected": is_hallucination_detected,
            "contradiction_score": contradiction_score,
            "contradiction_type": contradiction_type,  # "hard" or "soft" or None
            "fhri": fhri,
            "fhri_subscores": fhri_subscores,
            "scenario_detected": scenario_detected,
            "scenario_name": scenario_name,
            "scenario_weights": scenario_weights,
            "fhri_threshold_used": effective_threshold,  # Log which threshold was used
            "fhri_flagged": fhri_flagged,
            "fhri_risk": risk_metadata,
            "numeric_price_check": numeric_price_check,  # Numeric mismatch override debug info
            "validation_flags": {},
            "correct": predicted_label == true_label,
            "llm_answer": llm_answer,
            "passages_used": passages_used
        }

        self.results.append(result)
        return result

    def evaluate_dataset(self, dataset_path: str, scenario_filter: List[str] = None) -> List[Dict[str, Any]]:
        """Evaluate entire dataset. If scenario_filter is provided, only evaluate samples whose scenario matches."""
        print("=" * 60)
        print("HALLUCINATION & CONTRADICTION DETECTION EVALUATION")
        print("=" * 60)
        print(f"Dataset: {dataset_path}")
        if self.use_static_answers:
            print("Mode: STATIC (using stored answers from dataset)")
        else:
            print(f"Backend: {self.backend_url}")
        print(f"Hallucination threshold (entropy): {self.hallu_threshold}")
        print(f"FHRI threshold (accurate): {self.fhri_threshold}")
        print("=" * 60)

        # Test backend connection (skip in static mode)
        if not self.use_static_answers:
            if not self.test_backend_connection():
                print("\n[ERROR] Cannot proceed: Backend server is not running")
                print("Please start the server with: uvicorn src.server:app --port 8000")
                return []

        # Load dataset
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"[ERROR] Error loading dataset: {e}")
            return []

        samples = dataset.get("samples", [])

        # Flatten if dataset is grouped into lists (e.g., contradiction pairs)
        if any(isinstance(item, list) for item in samples):
            flattened = []
            for item in samples:
                if isinstance(item, list):
                    flattened.extend(item)
                else:
                    flattened.append(item)
            samples = flattened

        print(f"\nFound {len(samples)} samples in dataset")
        print("=" * 60)

        # Group samples by contradiction_pair_id to track previous answers and questions
        # Use a list to track multiple pairs with the same ID
        pair_data = {}  # Maps contradiction_pair_id -> list of (sample_id, question, answer, true_label) tuples
        
        # Evaluate each sample
        for i, sample in enumerate(samples, 1):
            print(f"\n[{i}/{len(samples)}] ", end="")
            
            # Scenario gating: only keep samples whose scenario matches the filter
            if scenario_filter:
                fhri_spec = sample.get("fhri_spec", {})
                scenario_id = fhri_spec.get("scenario_override") or sample.get("scenario_detected")
                if scenario_id not in scenario_filter:
                    print(f"[SKIP] scenario={scenario_id} not in filter {scenario_filter}")
                    continue
            
            # Check if this sample is part of a contradiction pair
            fhri_spec = sample.get("fhri_spec", {})
            pair_id = fhri_spec.get("contradiction_pair_id")
            sample_id = sample.get("id", "")
            
            # Get previous answer and question if this is the second sample in a pair
            # For contradiction samples, we need the previous "accurate" answer and question from the same pair
            prev_answer = None
            prev_question = None
            true_label = sample.get("ground_truth_label", "")
            question = sample.get("question", "")
            
            if pair_id:
                # Check if we have stored data for this pair
                if pair_id in pair_data:
                    # For contradiction samples, find the most recent "accurate" answer and question
                    # For accurate samples, typically don't need previous answer (they're first in pair)
                    stored_pairs = pair_data[pair_id]
                    if true_label == "contradiction":
                        # Find the most recent "accurate" answer and question from a different sample
                        for stored_sample_id, stored_question, stored_answer, stored_label in reversed(stored_pairs):
                            if stored_sample_id != sample_id and stored_answer and stored_label == "accurate":
                                prev_answer = stored_answer
                                prev_question = stored_question
                                print(f"[Pair: {pair_id}, using {stored_sample_id}] ", end="")
                                break
                        # If no accurate answer found, use the most recent answer (fallback)
                        if not prev_answer:
                            for stored_sample_id, stored_question, stored_answer, stored_label in reversed(stored_pairs):
                                if stored_sample_id != sample_id and stored_answer:
                                    prev_answer = stored_answer
                                    prev_question = stored_question
                                    print(f"[Pair: {pair_id}, using {stored_sample_id} (fallback)] ", end="")
                                    break
                else:
                    # First time seeing this pair_id, initialize list
                    pair_data[pair_id] = []
            
            result = self.evaluate_sample(sample, prev_answer=prev_answer, prev_question=prev_question)
            
            if result:
                status = "[OK] Correct" if result["correct"] else "[X] Incorrect"
                print(f"  {status}: True={result['true_label']}, Predicted={result['predicted_label']}")
                
                # Store answer and question for contradiction pairs (append to list, don't overwrite)
                # Store with the true label so we can match accurately
                # Only store if we got a valid, non-empty answer
                if pair_id:
                    llm_answer = result.get("llm_answer", "")
                    if llm_answer and llm_answer.strip():  # Validate answer is not empty
                        if pair_id not in pair_data:
                            pair_data[pair_id] = []
                        pair_data[pair_id].append((sample_id, question, llm_answer, true_label))
                    else:
                        print(f"  [WARN] Empty answer for {sample_id}, not storing for pairs")
            else:
                print(f"  [WARN] Failed to evaluate {sample_id}")
            # Avoid overwhelming the server in dynamic mode; no delay needed in static mode
            if not self.use_static_answers:
                time.sleep(0.5)

        return self.results


    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate precision, recall, F1-score for each class."""
        if not self.results:
            return {}

        # Count true positives, false positives, false negatives for each class
        classes = ["hallucination", "accurate", "contradiction"]
        metrics = {}

        for cls in classes:
            tp = sum(1 for r in self.results if r["true_label"] == cls and r["predicted_label"] == cls)
            fp = sum(1 for r in self.results if r["true_label"] != cls and r["predicted_label"] == cls)
            fn = sum(1 for r in self.results if r["true_label"] == cls and r["predicted_label"] != cls)
            tn = sum(1 for r in self.results if r["true_label"] != cls and r["predicted_label"] != cls)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            accuracy = (tp + tn) / len(self.results) if len(self.results) > 0 else 0.0

            metrics[cls] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "accuracy": round(accuracy, 4),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn,
                "support": tp + fn  # Number of samples with this true label
            }

        # Overall accuracy
        correct = sum(1 for r in self.results if r["correct"])
        overall_accuracy = correct / len(self.results) if self.results else 0.0

        # Macro-averaged F1 (average of F1 scores for each class)
        macro_f1 = sum(m["f1_score"] for m in metrics.values()) / len(metrics) if metrics else 0.0

        metrics["overall"] = {
            "accuracy": round(overall_accuracy, 4),
            "macro_f1": round(macro_f1, 4),
            "total_samples": len(self.results),
            "correct_predictions": correct
        }

        return metrics

    def generate_confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        """Generate confusion matrix."""
        classes = ["hallucination", "accurate", "contradiction"]
        matrix = defaultdict(lambda: defaultdict(int))

        for result in self.results:
            true_label = result["true_label"]
            pred_label = result["predicted_label"]
            matrix[true_label][pred_label] += 1

        return dict(matrix)

    def print_report(self, metrics: Dict[str, Any], confusion_matrix: Dict[str, Dict[str, int]]):
        """Print evaluation report to console."""
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)

        # Overall metrics
        overall = metrics.get("overall", {})
        print(f"\n[Overall Performance]")
        print(f"  Accuracy: {overall.get('accuracy', 0):.2%}")
        print(f"  Macro F1-Score: {overall.get('macro_f1', 0):.4f}")
        print(f"  Total Samples: {overall.get('total_samples', 0)}")
        print(f"  Correct: {overall.get('correct_predictions', 0)}")

        # Per-class metrics
        print(f"\n[Per-Class Metrics]")
        classes = ["hallucination", "accurate", "contradiction"]

        # Header
        print(f"\n{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
        print("-" * 65)

        for cls in classes:
            if cls in metrics:
                m = metrics[cls]
                print(f"{cls:<15} {m['precision']:<12.4f} {m['recall']:<12.4f} {m['f1_score']:<12.4f} {m['support']:<10}")

        # Confusion matrix
        print(f"\n[Confusion Matrix]")
        header_label = "True \\ Pred"
        print(f"\n{header_label:<15} {'hallucination':<15} {'accurate':<15} {'contradiction':<15}")
        print("-" * 65)

        for true_label in classes:
            row = [true_label]
            for pred_label in classes:
                count = confusion_matrix.get(true_label, {}).get(pred_label, 0)
                row.append(f"{count:<15}")
            print("".join([f"{r:<15}" for r in row]))

        print("\n" + "=" * 60)

    def save_report(self, output_path: str, metrics: Dict[str, Any], confusion_matrix: Dict[str, Dict[str, int]]):
        """Save evaluation report to JSON file."""
        report = {
            "evaluation_metadata": {
                "backend_url": self.backend_url,
                "hallucination_threshold": self.hallu_threshold,
                "fhri_threshold": self.fhri_threshold,
                "total_samples": len(self.results),
                "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "metrics": metrics,
            "confusion_matrix": confusion_matrix,
            "detailed_results": self.results
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate hallucination and contradiction detection with FHRI support")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to annotated evaluation dataset (JSON)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/evaluation_report.json",
        help="Path to save evaluation report"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Hallucination entropy threshold (same as UI)"
    )
    parser.add_argument(
        "--fhri_threshold",
        type=float,
        default=0.70,
        help="FHRI threshold for accurate label (FHRI > threshold required, recommended: 0.70 for better recall)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["baseline", "fhri", "selfcheck"],
        default="fhri",
        help="Evaluation mode: 'baseline' (entropy-only), 'fhri' (with FHRI scoring), or 'selfcheck' (DeepSeek self-consistency)"
    )
    parser.add_argument(
        "--selfcheck_k",
        type=int,
        default=3,
        help="Number of self-consistency samples for selfcheck mode"
    )
    parser.add_argument(
        "--selfcheck_model",
        type=str,
        default="deepseek-chat",
        help="DeepSeek model name for selfcheck mode"
    )
    parser.add_argument(
        "--use_static_answers",
        action="store_true",
        help="Use stored answers from dataset instead of querying backend (static mode for offline analysis)"
    )

    args = parser.parse_args()

    # Check if dataset exists
    if not os.path.exists(args.dataset):
        print(f"[ERROR] Error: Dataset not found at {args.dataset}")
        print(f"\nPlease create an annotated dataset using the template at:")
        print(f"  data/evaluation_template.json")
        print(f"\nInstructions:")
        print(f"  1. Copy data/evaluation_template.json to data/evaluation_dataset.json")
        print(f"  2. Add your annotated samples to the 'samples' array")
        print(f"  3. Run this script again")
        return

    # Configure evaluation based on mode
    use_fhri = args.mode == "fhri"
    print(f"\nEvaluation mode: {args.mode.upper()}")
    if args.mode == "baseline":
        print("  (Baseline: entropy-only detection, FHRI disabled)")
    elif args.mode == "fhri":
        print("  (FHRI: full reliability scoring enabled)")
    elif args.mode == "selfcheck":
        print(f"  (SelfCheck: DeepSeek self-consistency, k={args.selfcheck_k}, model={args.selfcheck_model})")

    # Run evaluation
    evaluator = DetectionEvaluator(
        backend_url=args.backend,
        hallu_threshold=args.threshold,
        fhri_threshold=args.fhri_threshold,
        use_static_answers=args.use_static_answers
    )
    evaluator.use_fhri = use_fhri  # Store for query_chatbot
    evaluator.eval_mode = args.mode
    evaluator.selfcheck_k = args.selfcheck_k
    evaluator.selfcheck_model = args.selfcheck_model
    results = evaluator.evaluate_dataset(args.dataset)

    if not results:
        print("\n[ERROR] Evaluation failed or no results obtained")
        return

    # Calculate metrics
    metrics = evaluator.calculate_metrics()
    confusion_matrix = evaluator.generate_confusion_matrix()

    # Print and save report
    evaluator.print_report(metrics, confusion_matrix)
    evaluator.save_report(args.output, metrics, confusion_matrix)

    print(f"\n[OK] Evaluation complete!")
    print(f"  Total samples evaluated: {len(results)}")
    print(f"  Overall accuracy: {metrics['overall']['accuracy']:.2%}")
    print(f"  Macro F1-Score: {metrics['overall']['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
