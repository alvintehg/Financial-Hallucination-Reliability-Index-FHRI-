# src/advisory_services.py
"""
Advisory services for risk profiling, portfolio allocation, and thematic recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class RiskProfiler:
    """
    Risk profiling service that analyzes questionnaire responses and returns risk labels.
    """

    def __init__(self):
        self.risk_thresholds = {
            "conservative": (0, 35),
            "balanced": (35, 65),
            "aggressive": (65, 100)
        }

    def compute_risk_profile(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute risk profile from questionnaire answers.

        Args:
            answers: List of questionnaire responses, each with:
                {
                    "question_id": str,
                    "answer": str or int,
                    "score": int (optional, pre-scored)
                }

        Returns:
            {
                "risk_label": str (Conservative/Balanced/Aggressive),
                "score": float (0-100),
                "breakdown": dict with dimension scores
            }
        """
        try:
            if not answers:
                return {
                    "risk_label": "Balanced",
                    "score": 50.0,
                    "breakdown": {},
                    "warning": "No answers provided, defaulting to Balanced"
                }

            # Extract scores from answers
            total_score = 0
            count = 0
            dimension_scores = {
                "time_horizon": [],
                "risk_tolerance": [],
                "investment_experience": [],
                "financial_stability": []
            }

            for answer in answers:
                # If pre-scored, use the score
                if "score" in answer:
                    score = float(answer["score"])
                else:
                    # Auto-score based on answer patterns
                    score = self._auto_score_answer(answer)

                total_score += score
                count += 1

                # Categorize by question type
                question_id = answer.get("question_id", "").lower()
                if "time" in question_id or "horizon" in question_id:
                    dimension_scores["time_horizon"].append(score)
                elif "risk" in question_id or "loss" in question_id:
                    dimension_scores["risk_tolerance"].append(score)
                elif "experience" in question_id or "knowledge" in question_id:
                    dimension_scores["investment_experience"].append(score)
                elif "income" in question_id or "emergency" in question_id:
                    dimension_scores["financial_stability"].append(score)
                else:
                    # Default to risk tolerance
                    dimension_scores["risk_tolerance"].append(score)

            # Compute normalized score (0-100)
            normalized_score = (total_score / count) if count > 0 else 50.0

            # Determine risk label
            risk_label = "Balanced"
            for label, (min_score, max_score) in self.risk_thresholds.items():
                if min_score <= normalized_score < max_score:
                    risk_label = label.capitalize()
                    break

            # Compute dimension averages
            breakdown = {}
            for dimension, scores in dimension_scores.items():
                if scores:
                    breakdown[dimension] = sum(scores) / len(scores)

            logger.info(f"Risk profile computed: {risk_label} (score: {normalized_score:.1f})")

            return {
                "risk_label": risk_label,
                "score": round(normalized_score, 2),
                "breakdown": breakdown,
                "answers_processed": count
            }

        except Exception as e:
            logger.exception("Error computing risk profile:")
            return {
                "risk_label": "Balanced",
                "score": 50.0,
                "breakdown": {},
                "error": str(e)
            }

    def _auto_score_answer(self, answer: Dict[str, Any]) -> float:
        """
        Auto-score an answer based on content patterns.

        Returns score between 0-100.
        """
        answer_text = str(answer.get("answer", "")).lower()

        # Conservative patterns (low score)
        conservative_patterns = [
            "less than 1 year", "very uncomfortable", "none", "beginner",
            "minimal", "avoid", "safety", "preserve", "capital preservation"
        ]

        # Aggressive patterns (high score)
        aggressive_patterns = [
            "10+ years", "very comfortable", "experienced", "expert",
            "high", "maximize", "growth", "aggressive", "risk-seeking"
        ]

        # Count pattern matches
        conservative_count = sum(1 for p in conservative_patterns if p in answer_text)
        aggressive_count = sum(1 for p in aggressive_patterns if p in answer_text)

        # Base score: 50 (moderate)
        # Adjust by pattern matches
        score = 50.0
        score += aggressive_count * 15  # Each aggressive pattern adds 15 points
        score -= conservative_count * 15  # Each conservative pattern subtracts 15 points

        # Clamp to 0-100
        return max(0.0, min(100.0, score))


class PortfolioAllocator:
    """
    Portfolio allocation service that suggests ETF mixes based on risk profile.
    """

    def __init__(self):
        # Define allocation templates
        self.allocation_templates = {
            "conservative": {
                "equities": 30,
                "bonds": 60,
                "cash": 10,
                "etfs": [
                    {"ticker": "BND", "weight": 0.50, "role": "Core Bonds", "name": "Vanguard Total Bond Market ETF"},
                    {"ticker": "AGG", "weight": 0.10, "role": "Aggregate Bonds", "name": "iShares Core U.S. Aggregate Bond ETF"},
                    {"ticker": "VTI", "weight": 0.20, "role": "Total Stock Market", "name": "Vanguard Total Stock Market ETF"},
                    {"ticker": "VXUS", "weight": 0.10, "role": "International Equities", "name": "Vanguard Total International Stock ETF"},
                    {"ticker": "SHY", "weight": 0.10, "role": "Short-Term Treasuries (Cash Proxy)", "name": "iShares 1-3 Year Treasury Bond ETF"}
                ]
            },
            "balanced": {
                "equities": 60,
                "bonds": 35,
                "cash": 5,
                "etfs": [
                    {"ticker": "VTI", "weight": 0.40, "role": "Total Stock Market", "name": "Vanguard Total Stock Market ETF"},
                    {"ticker": "VXUS", "weight": 0.20, "role": "International Equities", "name": "Vanguard Total International Stock ETF"},
                    {"ticker": "BND", "weight": 0.30, "role": "Core Bonds", "name": "Vanguard Total Bond Market ETF"},
                    {"ticker": "VNQ", "weight": 0.05, "role": "Real Estate", "name": "Vanguard Real Estate ETF"},
                    {"ticker": "SHY", "weight": 0.05, "role": "Cash Equivalents", "name": "iShares 1-3 Year Treasury Bond ETF"}
                ]
            },
            "aggressive": {
                "equities": 85,
                "bonds": 10,
                "cash": 5,
                "etfs": [
                    {"ticker": "VTI", "weight": 0.50, "role": "Total Stock Market", "name": "Vanguard Total Stock Market ETF"},
                    {"ticker": "VXUS", "weight": 0.25, "role": "International Equities", "name": "Vanguard Total International Stock ETF"},
                    {"ticker": "VUG", "weight": 0.10, "role": "Growth Stocks", "name": "Vanguard Growth ETF"},
                    {"ticker": "BND", "weight": 0.10, "role": "Bonds", "name": "Vanguard Total Bond Market ETF"},
                    {"ticker": "SHY", "weight": 0.05, "role": "Cash Equivalents", "name": "iShares 1-3 Year Treasury Bond ETF"}
                ]
            }
        }

    def get_allocation(self, risk_label: str) -> Dict[str, Any]:
        """
        Get ETF allocation for a given risk profile.

        Args:
            risk_label: "Conservative", "Balanced", or "Aggressive"

        Returns:
            {
                "allocation": list of ETF allocations,
                "asset_mix": {equities: %, bonds: %, cash: %},
                "notes": str,
                "sources": list
            }
        """
        try:
            risk_key = risk_label.lower()

            if risk_key not in self.allocation_templates:
                logger.warning(f"Unknown risk label: {risk_label}, defaulting to balanced")
                risk_key = "balanced"

            template = self.allocation_templates[risk_key]

            allocation = []
            for etf in template["etfs"]:
                allocation.append({
                    "ticker": etf["ticker"],
                    "weight": etf["weight"],
                    "role": etf["role"],
                    "name": etf.get("name", etf["ticker"])
                })

            asset_mix = {
                "equities": template["equities"],
                "bonds": template["bonds"],
                "cash": template["cash"]
            }

            notes = self._generate_allocation_notes(risk_label, asset_mix)

            sources = [
                "Vanguard Asset Allocation Models",
                "BlackRock Portfolio Construction",
                "Academic research on risk-based allocation"
            ]

            logger.info(f"Generated {risk_label} allocation: {len(allocation)} ETFs")

            return {
                "allocation": allocation,
                "asset_mix": asset_mix,
                "notes": notes,
                "sources": sources,
                "risk_label": risk_label
            }

        except Exception as e:
            logger.exception("Error generating allocation:")
            return {
                "allocation": [],
                "asset_mix": {},
                "notes": f"Error generating allocation: {str(e)}",
                "sources": [],
                "error": str(e)
            }

    def _generate_allocation_notes(self, risk_label: str, asset_mix: Dict[str, int]) -> str:
        """Generate descriptive notes for the allocation."""
        notes_templates = {
            "conservative": (
                "This allocation prioritizes capital preservation with {bonds}% in bonds and only {equities}% in equities. "
                "Suitable for investors with short time horizons or low risk tolerance. Expected volatility: Low."
            ),
            "balanced": (
                "This allocation balances growth and stability with {equities}% equities and {bonds}% bonds. "
                "Suitable for investors with moderate risk tolerance and medium-to-long time horizons. "
                "Expected volatility: Moderate."
            ),
            "aggressive": (
                "This allocation maximizes growth potential with {equities}% in equities and minimal bond exposure. "
                "Suitable for long-term investors comfortable with market volatility. Expected volatility: High."
            )
        }

        template = notes_templates.get(risk_label.lower(), notes_templates["balanced"])
        return template.format(**asset_mix)


class ThematicAdvisor:
    """
    Thematic and ESG portfolio advisor that suggests ETFs based on interest keywords.
    """

    def __init__(self, provider_manager=None):
        self.provider_manager = provider_manager

        # Define thematic ETF database
        self.thematic_etfs = {
            "esg": [
                {"ticker": "ESGU", "name": "iShares ESG Aware MSCI USA ETF", "theme": "ESG", "why": "Broad ESG screening with strong corporate governance"},
                {"ticker": "VSGX", "name": "Vanguard ESG International Stock ETF", "theme": "ESG", "why": "International diversification with ESG focus"},
                {"ticker": "SUSL", "name": "iShares ESG MSCI USA Leaders ETF", "theme": "ESG", "why": "Top ESG performers in U.S. market"}
            ],
            "clean_energy": [
                {"ticker": "ICLN", "name": "iShares Global Clean Energy ETF", "theme": "Clean Energy", "why": "Global renewable energy exposure"},
                {"ticker": "TAN", "name": "Invesco Solar ETF", "theme": "Solar Energy", "why": "Pure-play solar energy companies"},
                {"ticker": "QCLN", "name": "First Trust NASDAQ Clean Edge Green Energy Index Fund", "theme": "Clean Energy", "why": "Clean energy leaders and innovators"}
            ],
            "technology": [
                {"ticker": "QQQ", "name": "Invesco QQQ Trust", "theme": "Technology", "why": "Top NASDAQ-100 tech companies"},
                {"ticker": "VGT", "name": "Vanguard Information Technology ETF", "theme": "Technology", "why": "Broad tech sector exposure"},
                {"ticker": "ARKK", "name": "ARK Innovation ETF", "theme": "Disruptive Innovation", "why": "Actively managed disruptive tech fund"}
            ],
            "healthcare": [
                {"ticker": "VHT", "name": "Vanguard Health Care ETF", "theme": "Healthcare", "why": "Diversified healthcare sector exposure"},
                {"ticker": "XLV", "name": "Health Care Select Sector SPDR Fund", "theme": "Healthcare", "why": "S&P 500 healthcare companies"},
                {"ticker": "IBB", "name": "iShares Biotechnology ETF", "theme": "Biotechnology", "why": "Biotech innovation and growth"}
            ],
            "dividend": [
                {"ticker": "VYM", "name": "Vanguard High Dividend Yield ETF", "theme": "Dividend", "why": "High dividend-yielding stocks"},
                {"ticker": "SCHD", "name": "Schwab U.S. Dividend Equity ETF", "theme": "Dividend", "why": "Quality dividend growers"},
                {"ticker": "DGRO", "name": "iShares Core Dividend Growth ETF", "theme": "Dividend Growth", "why": "Companies with consistent dividend growth"}
            ],
            "emerging_markets": [
                {"ticker": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "theme": "Emerging Markets", "why": "Broad emerging market exposure"},
                {"ticker": "IEMG", "name": "iShares Core MSCI Emerging Markets ETF", "theme": "Emerging Markets", "why": "Low-cost emerging market access"},
                {"ticker": "EEM", "name": "iShares MSCI Emerging Markets ETF", "theme": "Emerging Markets", "why": "Established EM ETF with liquidity"}
            ],
            "crypto": [
                {"ticker": "BITO", "name": "ProShares Bitcoin Strategy ETF", "theme": "Cryptocurrency", "why": "Bitcoin futures exposure"},
                {"ticker": "BITI", "name": "ProShares Short Bitcoin Strategy ETF", "theme": "Cryptocurrency (Inverse)", "why": "Bet against Bitcoin"},
                {"ticker": "BLOK", "name": "Amplify Transformational Data Sharing ETF", "theme": "Blockchain", "why": "Blockchain technology companies"}
            ]
        }

    def get_thematic_recommendations(
        self,
        interest_keywords: List[str],
        use_rag: bool = False,
        passages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get thematic ETF recommendations based on interest keywords.

        Args:
            interest_keywords: List of keywords like ["esg", "clean energy", "tech"]
            use_rag: Whether to use RAG/LLM for enhanced recommendations
            passages: Optional passages from RAG retrieval

        Returns:
            {
                "etfs": list of ETF recommendations,
                "summary": str,
                "themes_matched": list
            }
        """
        try:
            # Match keywords to themes
            matched_etfs = []
            themes_matched = []

            for keyword in interest_keywords:
                keyword_lower = keyword.lower()

                # Exact theme matches
                for theme, etf_list in self.thematic_etfs.items():
                    if keyword_lower in theme or theme in keyword_lower:
                        for etf in etf_list:
                            # Add source
                            etf_with_source = etf.copy()
                            etf_with_source["source"] = f"Thematic database ({theme})"
                            matched_etfs.append(etf_with_source)

                        if theme not in themes_matched:
                            themes_matched.append(theme)

                # Partial matches in ETF names/themes
                for theme, etf_list in self.thematic_etfs.items():
                    for etf in etf_list:
                        etf_text = f"{etf['name']} {etf['theme']} {etf['why']}".lower()
                        if keyword_lower in etf_text:
                            etf_with_source = etf.copy()
                            etf_with_source["source"] = f"Thematic database ({theme})"
                            if etf_with_source not in matched_etfs:
                                matched_etfs.append(etf_with_source)

                            if theme not in themes_matched:
                                themes_matched.append(theme)

            # Remove duplicates (by ticker)
            seen_tickers = set()
            unique_etfs = []
            for etf in matched_etfs:
                if etf["ticker"] not in seen_tickers:
                    unique_etfs.append(etf)
                    seen_tickers.add(etf["ticker"])

            # Limit to top 8 recommendations
            unique_etfs = unique_etfs[:8]

            # Generate summary
            if unique_etfs:
                summary = f"Found {len(unique_etfs)} ETF(s) matching themes: {', '.join(themes_matched)}."
            else:
                summary = "No specific thematic ETFs matched. Consider broad market ETFs (VTI, VXUS) for diversification."

            # Optionally enhance with LLM
            if use_rag and self.provider_manager and passages:
                try:
                    summary = self._generate_llm_summary(interest_keywords, unique_etfs, passages)
                except Exception as e:
                    logger.warning(f"LLM summary generation failed: {e}")

            logger.info(f"Thematic recommendations: {len(unique_etfs)} ETFs for {len(themes_matched)} themes")

            return {
                "etfs": unique_etfs,
                "summary": summary,
                "themes_matched": themes_matched,
                "keywords_processed": interest_keywords
            }

        except Exception as e:
            logger.exception("Error generating thematic recommendations:")
            return {
                "etfs": [],
                "summary": f"Error: {str(e)}",
                "themes_matched": [],
                "error": str(e)
            }

    def _generate_llm_summary(
        self,
        keywords: List[str],
        etfs: List[Dict],
        passages: List[str]
    ) -> str:
        """Use LLM to generate enhanced summary."""
        try:
            etf_details = "\n".join([
                f"- {e['ticker']}: {e['name']} ({e['theme']}) - {e['why']}"
                for e in etfs
            ])

            context = "\n\n".join(passages[:3]) if passages else "No additional context."

            prompt = f"""You are a financial advisor. Summarize these thematic ETF recommendations in 2-3 sentences.

Interest keywords: {', '.join(keywords)}

Recommended ETFs:
{etf_details}

Context:
{context}

Provide a concise summary explaining why these ETFs match the investor's interests."""

            provider_name, summary, _ = self.provider_manager.generate(prompt, provider="auto", timeout=10)
            return summary.strip()

        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            return f"Matched {len(etfs)} ETF(s) for themes: {', '.join(keywords)}"


class EscalationService:
    """
    Human-in-the-loop escalation service for regulated advice.
    """

    def __init__(self, advisor_contact_email: str = None):
        self.advisor_contact_email = advisor_contact_email or "advisor@example.com"

    def escalate_to_human(self, topic: str) -> Dict[str, Any]:
        """
        Generate escalation message for human advisor.

        Args:
            topic: Topic requiring escalation (e.g., "tax planning", "estate planning")

        Returns:
            {
                "message": str,
                "contact_link": str (mailto link)
            }
        """
        message = (
            f"The topic '{topic}' may require personalized advice from a licensed financial planner. "
            "This chatbot provides general information only and does not constitute financial, legal, or tax advice. "
            "For regulated advice tailored to your specific situation, please connect with a licensed professional."
        )

        contact_link = f"mailto:{self.advisor_contact_email}?subject=Financial Advice Request: {topic}"

        return {
            "message": message,
            "contact_link": contact_link,
            "topic": topic,
            "disclaimer": "This is an automated response. No fiduciary relationship is established."
        }
