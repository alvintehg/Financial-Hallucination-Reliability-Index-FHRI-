# src/portfolio_analytics.py
"""
Portfolio analytics including backtesting and behavioral insights.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class PortfolioBacktester:
    """
    Portfolio backtesting service with performance metrics.
    """

    def __init__(self, data_fetcher=None):
        """
        Args:
            data_fetcher: Optional data fetcher for historical prices
        """
        self.data_fetcher = data_fetcher

    def backtest_portfolio(
        self,
        weights: Dict[str, float],
        start_date: str,
        end_date: str,
        rebalance_freq: str = "quarterly",
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Backtest a portfolio with given weights.

        Args:
            weights: Dict of {ticker: weight}, e.g., {"AAPL": 0.5, "MSFT": 0.5}
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            rebalance_freq: Rebalancing frequency ("monthly", "quarterly", "yearly", "none")
            initial_capital: Starting capital (default: $10,000)

        Returns:
            {
                "cagr": float (annualized return %),
                "volatility": float (annualized volatility %),
                "max_drawdown": float (%),
                "sharpe_ratio": float,
                "equity_curve": list of {date, value},
                "summary": str
            }
        """
        try:
            # Validate inputs
            if not weights:
                return {"error": "No weights provided"}

            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                return {"error": f"Weights must sum to 1.0, got {total_weight:.2f}"}

            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            if start_dt >= end_dt:
                return {"error": "Start date must be before end date"}

            # If we have a data fetcher, use it to get historical data
            if self.data_fetcher:
                return self._backtest_with_real_data(
                    weights, start_dt, end_dt, rebalance_freq, initial_capital
                )
            else:
                # Use simulated returns
                return self._backtest_with_simulated_data(
                    weights, start_dt, end_dt, rebalance_freq, initial_capital
                )

        except Exception as e:
            logger.exception("Error in backtesting:")
            return {
                "error": str(e),
                "weights": weights,
                "start_date": start_date,
                "end_date": end_date
            }

    def _backtest_with_simulated_data(
        self,
        weights: Dict[str, float],
        start_dt: datetime,
        end_dt: datetime,
        rebalance_freq: str,
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Backtest using simulated random walk returns.

        This is a simplified simulation for demonstration purposes.
        """
        try:
            # Simulate daily returns for each ticker
            # Assume average return of 8% annually with 15% volatility
            avg_daily_return = 0.08 / 252  # 252 trading days
            daily_volatility = 0.15 / math.sqrt(252)

            # Generate equity curve
            equity_curve = []
            current_value = initial_capital
            current_date = start_dt

            # Track daily returns for metrics
            daily_returns = []
            peak_value = initial_capital

            while current_date <= end_dt:
                # Simulate daily return as weighted average
                import random
                portfolio_return = 0.0

                for ticker, weight in weights.items():
                    # Simulate ticker return (normal distribution)
                    ticker_return = random.gauss(avg_daily_return, daily_volatility)
                    portfolio_return += weight * ticker_return

                # Update portfolio value
                current_value *= (1 + portfolio_return)

                # Track for drawdown
                if current_value > peak_value:
                    peak_value = current_value

                # Record equity point (weekly to reduce data size)
                if current_date.weekday() == 4:  # Friday
                    equity_curve.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "value": round(current_value, 2)
                    })

                daily_returns.append(portfolio_return)

                # Move to next trading day (skip weekends)
                current_date += timedelta(days=1)
                while current_date.weekday() >= 5:  # Skip Saturday/Sunday
                    current_date += timedelta(days=1)

            # Compute metrics
            final_value = current_value
            total_return = (final_value - initial_capital) / initial_capital

            # CAGR
            years = (end_dt - start_dt).days / 365.25
            cagr = ((final_value / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0.0

            # Volatility (annualized)
            if len(daily_returns) > 1:
                import statistics
                daily_vol = statistics.stdev(daily_returns)
                annualized_vol = daily_vol * math.sqrt(252) * 100
            else:
                annualized_vol = 0.0

            # Max Drawdown
            max_drawdown = 0.0
            peak = initial_capital
            for point in equity_curve:
                value = point["value"]
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Sharpe Ratio (assume 2% risk-free rate)
            risk_free_rate = 0.02
            if annualized_vol > 0:
                sharpe_ratio = (cagr / 100 - risk_free_rate) / (annualized_vol / 100)
            else:
                sharpe_ratio = 0.0

            summary = (
                f"Portfolio returned {cagr:.2f}% CAGR with {annualized_vol:.2f}% volatility "
                f"over {years:.1f} years. Max drawdown: {max_drawdown:.2f}%. "
                f"Sharpe ratio: {sharpe_ratio:.2f}."
            )

            result = {
                "cagr": round(cagr, 2),
                "volatility": round(annualized_vol, 2),
                "max_drawdown": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "final_value": round(final_value, 2),
                "total_return": round(total_return * 100, 2),
                "equity_curve": equity_curve,
                "summary": summary,
                "note": "Simulated backtest (not real historical data)"
            }

            logger.info(f"Backtest complete: CAGR={cagr:.2f}%, Vol={annualized_vol:.2f}%, Sharpe={sharpe_ratio:.2f}")

            return result

        except Exception as e:
            logger.exception("Error in simulated backtest:")
            return {"error": str(e)}

    def _backtest_with_real_data(
        self,
        weights: Dict[str, float],
        start_dt: datetime,
        end_dt: datetime,
        rebalance_freq: str,
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Backtest using real historical data from data fetcher.

        This would require integration with yfinance or similar.
        For now, delegates to simulated backtest.
        """
        # TODO: Implement real data backtesting
        logger.warning("Real data backtesting not yet implemented, using simulated data")
        return self._backtest_with_simulated_data(
            weights, start_dt, end_dt, rebalance_freq, initial_capital
        )


class BehavioralInsights:
    """
    Behavioral insights service that analyzes user actions and provides nudges.
    """

    def __init__(self):
        self.overtrading_threshold = 10  # trades per month
        self.loss_aversion_patterns = [
            "sell", "sold", "exit", "cut losses"
        ]
        self.timing_patterns = [
            "should i buy now", "best time to", "timing", "wait"
        ]

    def analyze_behavior(self, user_action_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze user behavior and provide insights/nudges.

        Args:
            user_action_log: List of user actions, each with:
                {
                    "timestamp": str (ISO format),
                    "action": str (e.g., "trade", "query", "portfolio_check"),
                    "details": dict (optional metadata)
                }

        Returns:
            {
                "nudges": list of insight strings,
                "metrics": dict with behavioral metrics,
                "risk_flags": list of behavioral risk flags
            }
        """
        try:
            if not user_action_log:
                return {
                    "nudges": [],
                    "metrics": {},
                    "risk_flags": [],
                    "note": "No action log provided"
                }

            nudges = []
            risk_flags = []
            metrics = {}

            # Analyze trading frequency
            trade_actions = [a for a in user_action_log if a.get("action") == "trade"]
            if len(trade_actions) > self.overtrading_threshold:
                nudges.append(
                    "🔄 **Over-trading detected**: You've made {count} trades recently. "
                    "Frequent trading can increase costs and reduce returns. "
                    "Consider a buy-and-hold strategy for long-term wealth building.".format(
                        count=len(trade_actions)
                    )
                )
                risk_flags.append("over_trading")

            metrics["trade_count"] = len(trade_actions)

            # Analyze loss aversion behavior
            query_actions = [a for a in user_action_log if a.get("action") == "query"]
            loss_aversion_queries = []

            for action in query_actions:
                query_text = action.get("details", {}).get("query", "").lower()
                if any(pattern in query_text for pattern in self.loss_aversion_patterns):
                    loss_aversion_queries.append(action)

            if len(loss_aversion_queries) > 3:
                nudges.append(
                    "⚠️ **Loss aversion pattern**: Multiple queries about selling or cutting losses. "
                    "Remember: short-term volatility is normal. Avoid panic selling during market dips "
                    "unless your investment thesis has fundamentally changed."
                )
                risk_flags.append("loss_aversion")

            metrics["loss_aversion_queries"] = len(loss_aversion_queries)

            # Analyze market timing attempts
            timing_queries = []

            for action in query_actions:
                query_text = action.get("details", {}).get("query", "").lower()
                if any(pattern in query_text for pattern in self.timing_patterns):
                    timing_queries.append(action)

            if len(timing_queries) > 2:
                nudges.append(
                    "⏰ **Market timing risk**: Several queries about optimal timing. "
                    "Research shows that timing the market is extremely difficult, even for professionals. "
                    "Consider dollar-cost averaging instead of trying to time entry/exit points."
                )
                risk_flags.append("timing_risk")

            metrics["timing_queries"] = len(timing_queries)

            # Analyze recency bias (frequent portfolio checks)
            portfolio_checks = [a for a in user_action_log if a.get("action") == "portfolio_check"]
            if len(portfolio_checks) > 20:
                nudges.append(
                    "📊 **Recency bias**: You're checking your portfolio very frequently. "
                    "Daily fluctuations are noise. Focus on long-term trends and avoid "
                    "making impulsive decisions based on short-term movements."
                )
                risk_flags.append("recency_bias")

            metrics["portfolio_checks"] = len(portfolio_checks)

            # If no issues detected, provide positive reinforcement
            if not nudges:
                nudges.append(
                    "✅ **Good investing behavior**: Your actions show disciplined investing habits. "
                    "Keep focusing on long-term goals and avoid emotional reactions to market volatility."
                )

            logger.info(f"Behavioral analysis: {len(nudges)} nudges, {len(risk_flags)} risk flags")

            return {
                "nudges": nudges[:3],  # Limit to top 3 nudges
                "metrics": metrics,
                "risk_flags": risk_flags,
                "actions_analyzed": len(user_action_log)
            }

        except Exception as e:
            logger.exception("Error analyzing behavior:")
            return {
                "nudges": [],
                "metrics": {},
                "risk_flags": [],
                "error": str(e)
            }
