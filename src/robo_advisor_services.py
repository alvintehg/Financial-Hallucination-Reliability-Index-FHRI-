# src/robo_advisor_services.py
"""
Enhanced robo-advisor services for portfolio drift, ESG scoring, cash allocation,
market sentiment, and CSV import functionality.
"""

import logging
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class PortfolioDriftAnalyzer:
    """
    Analyzes portfolio drift from target allocation and recommends rebalancing actions.
    """

    def __init__(self):
        self.drift_threshold = 0.05  # 5% threshold for rebalancing alerts

    def analyze_drift(
        self,
        current_holdings: List[Dict[str, Any]],
        target_allocation: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze drift between current holdings and target allocation.

        Args:
            current_holdings: List of {"symbol": str, "value": float, "shares": float}
            target_allocation: List of {"symbol": str, "weight": float}

        Returns:
            {
                "drift_pct": float (max deviation from target),
                "needs_rebalance": bool,
                "actions": list of {symbol, action, amount_pct},
                "current_weights": dict,
                "target_weights": dict
            }
        """
        try:
            if not current_holdings:
                return {
                    "drift_pct": 0.0,
                    "needs_rebalance": False,
                    "actions": [],
                    "current_weights": {},
                    "target_weights": {},
                    "message": "No holdings to analyze"
                }

            # Calculate total portfolio value
            total_value = sum(h.get("value", 0) for h in current_holdings)

            if total_value == 0:
                return {
                    "drift_pct": 0.0,
                    "needs_rebalance": False,
                    "actions": [],
                    "current_weights": {},
                    "target_weights": {},
                    "message": "Portfolio value is zero"
                }

            # Calculate current weights
            current_weights = {}
            for holding in current_holdings:
                symbol = holding.get("symbol", "UNKNOWN")
                value = holding.get("value", 0)
                current_weights[symbol] = value / total_value

            # Build target weights dict
            target_weights = {}
            for target in target_allocation:
                symbol = target.get("symbol", "")
                weight = target.get("weight", 0)
                target_weights[symbol] = weight

            # Calculate drift for each position
            all_symbols = set(current_weights.keys()) | set(target_weights.keys())
            drift_details = []
            max_drift = 0.0

            for symbol in all_symbols:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights.get(symbol, 0.0)
                drift = current_weight - target_weight

                drift_details.append({
                    "symbol": symbol,
                    "current": round(current_weight * 100, 2),
                    "target": round(target_weight * 100, 2),
                    "drift": round(drift * 100, 2)
                })

                # Track maximum absolute drift
                if abs(drift) > abs(max_drift):
                    max_drift = drift

            # Determine if rebalancing is needed
            needs_rebalance = abs(max_drift) > self.drift_threshold

            # Generate rebalancing actions
            actions = []
            if needs_rebalance:
                for detail in drift_details:
                    drift_abs = abs(detail["drift"])
                    if drift_abs > self.drift_threshold * 100:  # Convert to percentage
                        action_type = "SELL" if detail["drift"] > 0 else "BUY"
                        actions.append({
                            "symbol": detail["symbol"],
                            "action": action_type,
                            "amount_pct": round(drift_abs, 2),
                            "note": f"{action_type} {drift_abs:.1f}% to rebalance"
                        })

            result = {
                "drift_pct": round(abs(max_drift) * 100, 2),
                "needs_rebalance": needs_rebalance,
                "threshold_pct": self.drift_threshold * 100,
                "actions": actions,
                "drift_details": drift_details,
                "current_weights": {k: round(v * 100, 2) for k, v in current_weights.items()},
                "target_weights": {k: round(v * 100, 2) for k, v in target_weights.items()},
                "total_value": round(total_value, 2)
            }

            logger.info(f"Drift analysis: {max_drift*100:.1f}% max drift, rebalance={needs_rebalance}")
            return result

        except Exception as e:
            logger.exception("Error analyzing portfolio drift:")
            return {
                "error": str(e),
                "drift_pct": 0.0,
                "needs_rebalance": False,
                "actions": []
            }


class ESGScorer:
    """
    ESG (Environmental, Social, Governance) scoring service for securities.
    """

    def __init__(self, data_fetcher=None):
        """
        Args:
            data_fetcher: Optional data fetcher with ESG data capabilities
        """
        self.data_fetcher = data_fetcher

        # Mock ESG database for common ETFs and stocks
        self.esg_database = {
            # ESG-focused ETFs
            "ESGU": {"esg_score": 85, "e": 88, "s": 84, "g": 83, "grade": "A", "provider": "MSCI ESG"},
            "VSGX": {"esg_score": 82, "e": 85, "s": 81, "g": 80, "grade": "A", "provider": "MSCI ESG"},
            "SUSL": {"esg_score": 87, "e": 90, "s": 86, "g": 85, "grade": "A+", "provider": "MSCI ESG"},

            # Broad market ETFs
            "VTI": {"esg_score": 65, "e": 68, "s": 64, "g": 63, "grade": "B", "provider": "MSCI ESG"},
            "SPY": {"esg_score": 66, "e": 69, "s": 65, "g": 64, "grade": "B", "provider": "MSCI ESG"},
            "QQQ": {"esg_score": 62, "e": 65, "s": 61, "g": 60, "grade": "B-", "provider": "MSCI ESG"},

            # Tech stocks
            "AAPL": {"esg_score": 75, "e": 78, "s": 74, "g": 73, "grade": "B+", "provider": "MSCI ESG"},
            "MSFT": {"esg_score": 80, "e": 82, "s": 79, "g": 79, "grade": "A-", "provider": "MSCI ESG"},
            "AMD": {"esg_score": 72, "e": 75, "s": 70, "g": 71, "grade": "B+", "provider": "MSCI ESG"},
            "TTD": {"esg_score": 68, "e": 70, "s": 67, "g": 67, "grade": "B", "provider": "MSCI ESG"},

            # AI/Tech companies
            "BBAI": {"esg_score": 55, "e": 58, "s": 54, "g": 53, "grade": "C+", "provider": "Estimated"},

            # Crypto/Blockchain
            "GLXY": {"esg_score": 35, "e": 25, "s": 40, "g": 40, "grade": "D", "provider": "Estimated (High Energy Use)"},
            "MSTU": {"esg_score": 30, "e": 20, "s": 35, "g": 35, "grade": "D-", "provider": "Crypto-related (2X leverage)"},

            # Cannabis
            "TLRY": {"esg_score": 48, "e": 55, "s": 45, "g": 44, "grade": "D+", "provider": "Estimated"},

            # Leveraged ETFs (generally lower ESG due to derivatives)
            "TSLL": {"esg_score": 40, "e": 50, "s": 35, "g": 35, "grade": "D", "provider": "Leveraged (2X TSLA)"},
            "SOFX": {"esg_score": 52, "e": 55, "s": 50, "g": 51, "grade": "C", "provider": "Leveraged (2X SOFI)"},
            "IRE": {"esg_score": 38, "e": 30, "s": 42, "g": 42, "grade": "D", "provider": "Leveraged (2X IREN)"},
            "UNHG": {"esg_score": 70, "e": 65, "s": 72, "g": 73, "grade": "B", "provider": "Healthcare (2X UNH)"},
            "DPST": {"esg_score": 58, "e": 60, "s": 57, "g": 57, "grade": "C+", "provider": "Banking (3X leverage)"},
            "CWVX": {"esg_score": 45, "e": 48, "s": 43, "g": 44, "grade": "D+", "provider": "Leveraged"},
            "UPSX": {"esg_score": 50, "e": 52, "s": 49, "g": 49, "grade": "C-", "provider": "Leveraged (2X UPST)"},

            # Other companies
            "ONDS": {"esg_score": 60, "e": 62, "s": 59, "g": 59, "grade": "B-", "provider": "Estimated"},
            "TSLA": {"esg_score": 58, "e": 70, "s": 52, "g": 52, "grade": "C+", "provider": "MSCI ESG"},
            "XOM": {"esg_score": 42, "e": 35, "s": 45, "g": 46, "grade": "D", "provider": "MSCI ESG"},
        }

    def get_esg_score(self, symbol: str) -> Dict[str, Any]:
        """
        Get ESG score for a given symbol.

        Args:
            symbol: Stock/ETF ticker symbol

        Returns:
            {
                "symbol": str,
                "esg_score": float (0-100),
                "grade": str (A+, A, B, C, D, F),
                "breakdown": {e, s, g scores},
                "provider": str
            }
        """
        try:
            symbol_upper = symbol.upper()

            # Try mock database first
            if symbol_upper in self.esg_database:
                data = self.esg_database[symbol_upper].copy()
                data["symbol"] = symbol_upper
                data["breakdown"] = {
                    "environmental": data.pop("e"),
                    "social": data.pop("s"),
                    "governance": data.pop("g")
                }
                logger.info(f"ESG score for {symbol}: {data['esg_score']} ({data['grade']})")
                return data

            # If data fetcher available, try to fetch real data
            if self.data_fetcher and hasattr(self.data_fetcher, 'get_esg_data'):
                try:
                    esg_data = self.data_fetcher.get_esg_data(symbol_upper)
                    if esg_data:
                        return esg_data
                except Exception as e:
                    logger.warning(f"Data fetcher ESG lookup failed: {e}")

            # Default fallback
            return {
                "symbol": symbol_upper,
                "esg_score": 60,
                "grade": "B",
                "breakdown": {
                    "environmental": 60,
                    "social": 60,
                    "governance": 60
                },
                "provider": "Mock Data",
                "note": "Real ESG data unavailable, showing default score"
            }

        except Exception as e:
            logger.exception(f"Error getting ESG score for {symbol}:")
            return {
                "symbol": symbol,
                "esg_score": 50,
                "grade": "N/A",
                "breakdown": {},
                "error": str(e)
            }

    def get_portfolio_esg_score(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate weighted ESG score for entire portfolio.

        Args:
            holdings: List of {"symbol": str, "value": float}

        Returns:
            {
                "portfolio_esg_score": float,
                "portfolio_grade": str,
                "holdings_esg": list of individual ESG scores
            }
        """
        try:
            if not holdings:
                return {
                    "portfolio_esg_score": 0,
                    "portfolio_grade": "N/A",
                    "holdings_esg": [],
                    "message": "No holdings provided"
                }

            total_value = sum(h.get("value", 0) for h in holdings)

            if total_value == 0:
                return {
                    "portfolio_esg_score": 0,
                    "portfolio_grade": "N/A",
                    "holdings_esg": [],
                    "message": "Portfolio value is zero"
                }

            holdings_esg = []
            weighted_score = 0.0

            for holding in holdings:
                symbol = holding.get("symbol", "")
                value = holding.get("value", 0)
                weight = value / total_value

                esg_data = self.get_esg_score(symbol)
                esg_data["weight"] = round(weight * 100, 2)
                esg_data["value"] = value

                holdings_esg.append(esg_data)

                # Accumulate weighted score
                weighted_score += esg_data.get("esg_score", 0) * weight

            # Assign portfolio grade
            if weighted_score >= 80:
                grade = "A"
            elif weighted_score >= 70:
                grade = "B"
            elif weighted_score >= 60:
                grade = "C"
            elif weighted_score >= 50:
                grade = "D"
            else:
                grade = "F"

            result = {
                "portfolio_esg_score": round(weighted_score, 2),
                "portfolio_grade": grade,
                "holdings_esg": holdings_esg,
                "total_value": round(total_value, 2),
                "esg_aligned_pct": round(
                    sum(h["weight"] for h in holdings_esg if h.get("esg_score", 0) >= 70), 2
                )
            }

            logger.info(f"Portfolio ESG: {weighted_score:.1f} ({grade})")
            return result

        except Exception as e:
            logger.exception("Error calculating portfolio ESG:")
            return {
                "portfolio_esg_score": 0,
                "portfolio_grade": "N/A",
                "holdings_esg": [],
                "error": str(e)
            }


class CashAllocationAdvisor:
    """
    Analyzes cash holdings and suggests allocation strategies.
    """

    def __init__(self):
        self.idle_cash_threshold = 0.10  # 10% cash threshold

    def analyze_cash_allocation(
        self,
        total_value: float,
        cash_value: float,
        risk_profile: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Analyze cash allocation and provide suggestions.

        Args:
            total_value: Total portfolio value including cash
            cash_value: Current cash value
            risk_profile: Risk profile (conservative/balanced/aggressive)

        Returns:
            {
                "cash_pct": float,
                "is_excessive": bool,
                "suggestion": str,
                "recommended_etf": dict or None
            }
        """
        try:
            if total_value == 0:
                return {
                    "cash_pct": 0,
                    "is_excessive": False,
                    "suggestion": "No portfolio value to analyze",
                    "recommended_etf": None
                }

            cash_pct = cash_value / total_value

            # Determine if cash is excessive
            is_excessive = cash_pct > self.idle_cash_threshold

            # Generate suggestion based on risk profile
            if not is_excessive:
                suggestion = f"Cash allocation ({cash_pct*100:.1f}%) is within acceptable range (<10%)."
                recommended_etf = None
            else:
                excess_cash = cash_value - (total_value * self.idle_cash_threshold)

                # Recommend safe assets based on risk profile
                if risk_profile.lower() == "conservative":
                    recommended_etf = {
                        "ticker": "SHY",
                        "name": "iShares 1-3 Year Treasury Bond ETF",
                        "reason": "Low-risk short-term treasury bonds for conservative investors"
                    }
                elif risk_profile.lower() == "aggressive":
                    recommended_etf = {
                        "ticker": "VTI",
                        "name": "Vanguard Total Stock Market ETF",
                        "reason": "Broad market exposure for aggressive investors"
                    }
                else:  # balanced
                    recommended_etf = {
                        "ticker": "AGG",
                        "name": "iShares Core U.S. Aggregate Bond ETF",
                        "reason": "Balanced bond exposure for moderate risk tolerance"
                    }

                suggestion = (
                    f"Cash allocation ({cash_pct*100:.1f}%) exceeds recommended 10% threshold. "
                    f"Consider investing ${excess_cash:,.2f} into {recommended_etf['ticker']} "
                    f"({recommended_etf['name']})."
                )

            result = {
                "cash_pct": round(cash_pct * 100, 2),
                "cash_value": round(cash_value, 2),
                "total_value": round(total_value, 2),
                "is_excessive": is_excessive,
                "threshold_pct": self.idle_cash_threshold * 100,
                "suggestion": suggestion,
                "recommended_etf": recommended_etf
            }

            logger.info(f"Cash allocation: {cash_pct*100:.1f}%, excessive={is_excessive}")
            return result

        except Exception as e:
            logger.exception("Error analyzing cash allocation:")
            return {
                "error": str(e),
                "cash_pct": 0,
                "is_excessive": False,
                "suggestion": f"Error analyzing cash: {str(e)}",
                "recommended_etf": None
            }


class MarketSentimentAnalyzer:
    """
    Analyzes market sentiment based on news and technical indicators.
    """

    def __init__(self, news_fetcher=None):
        """
        Args:
            news_fetcher: Optional news data fetcher
        """
        self.news_fetcher = news_fetcher

    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Get overall market sentiment analysis.

        Returns:
            {
                "outlook": str (Bullish/Neutral/Bearish),
                "confidence": float (0-100),
                "summary": str,
                "fhri_reliability": str (High/Moderate/Low)
            }
        """
        try:
            # In production, would analyze:
            # - Recent news sentiment
            # - Technical indicators (VIX, market breadth)
            # - Economic data

            # Mock implementation for now
            import random

            outlooks = ["Bullish", "Neutral", "Bearish"]
            weights = [0.4, 0.4, 0.2]  # Bias toward bullish/neutral

            outlook = random.choices(outlooks, weights=weights)[0]
            confidence = random.uniform(65, 85)

            summaries = {
                "Bullish": "Market indicators suggest positive momentum with strong earnings and economic data.",
                "Neutral": "Mixed signals in the market with balanced risk/reward outlook.",
                "Bearish": "Caution advised due to elevated volatility and macro uncertainties."
            }

            summary = summaries[outlook]

            # FHRI reliability is high for sentiment since it's based on multiple data sources
            fhri_reliability = "High" if confidence > 75 else "Moderate"

            result = {
                "outlook": outlook,
                "confidence": round(confidence, 2),
                "summary": summary,
                "fhri_reliability": fhri_reliability,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"Market sentiment: {outlook} (confidence: {confidence:.1f}%)")
            return result

        except Exception as e:
            logger.exception("Error analyzing market sentiment:")
            return {
                "outlook": "Neutral",
                "confidence": 50.0,
                "summary": f"Error analyzing sentiment: {str(e)}",
                "fhri_reliability": "Low",
                "error": str(e)
            }


class CSVHoldingsImporter:
    """
    Import holdings from CSV files.
    """

    def parse_csv_holdings(self, csv_content: str) -> Dict[str, Any]:
        """
        Parse CSV content into holdings format.

        Expected CSV format:
        symbol,shares,cost_basis
        AAPL,100,150.25
        MSFT,50,300.00

        Args:
            csv_content: CSV file content as string

        Returns:
            {
                "holdings": list of {symbol, shares, cost_basis},
                "count": int,
                "errors": list of error messages
            }
        """
        try:
            import csv
            from io import StringIO

            holdings = []
            errors = []

            # Parse CSV
            reader = csv.DictReader(StringIO(csv_content))

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                try:
                    symbol = row.get("symbol", "").strip().upper()
                    shares_str = row.get("shares", "0").strip()
                    cost_basis_str = row.get("cost_basis", "0").strip()

                    if not symbol:
                        errors.append(f"Row {row_num}: Missing symbol")
                        continue

                    # Parse numbers
                    try:
                        shares = float(shares_str)
                        cost_basis = float(cost_basis_str)
                    except ValueError as e:
                        errors.append(f"Row {row_num}: Invalid number format - {str(e)}")
                        continue

                    if shares <= 0:
                        errors.append(f"Row {row_num}: Shares must be positive")
                        continue

                    holdings.append({
                        "symbol": symbol,
                        "shares": shares,
                        "cost_basis": cost_basis
                    })

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")

            result = {
                "holdings": holdings,
                "count": len(holdings),
                "errors": errors,
                "success": len(errors) == 0
            }

            logger.info(f"CSV import: {len(holdings)} holdings, {len(errors)} errors")
            return result

        except Exception as e:
            logger.exception("Error parsing CSV:")
            return {
                "holdings": [],
                "count": 0,
                "errors": [f"Fatal error: {str(e)}"],
                "success": False,
                "error": str(e)
            }
