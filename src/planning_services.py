# src/planning_services.py
"""
Financial planning services including goal-based planning and fee/tax impact analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class GoalPlanner:
    """
    Goal-based financial planning service with Monte Carlo projections.
    """

    def __init__(self):
        pass

    def compute_goal_projection(
        self,
        target_amount: float,
        years: int,
        init_capital: float = 0.0,
        monthly_contrib: Optional[float] = None,
        expected_return: float = 0.07
    ) -> Dict[str, Any]:
        """
        Compute financial goal projections.

        Args:
            target_amount: Target amount to reach (e.g., $100,000)
            years: Time horizon in years
            init_capital: Initial capital (default: 0)
            monthly_contrib: Monthly contribution (if None, will be calculated)
            expected_return: Expected annual return (default: 7%)

        Returns:
            {
                "required_monthly": float (if monthly_contrib was None),
                "projection": list of {date, value} for each year,
                "target_amount": float,
                "final_value": float,
                "will_reach_goal": bool
            }
        """
        try:
            # Validate inputs
            if years <= 0:
                return {"error": "Years must be positive"}

            if target_amount <= 0:
                return {"error": "Target amount must be positive"}

            # Monthly return rate
            monthly_rate = expected_return / 12.0

            # If no monthly contribution provided, calculate required amount
            required_monthly = None
            if monthly_contrib is None:
                # Future value of annuity formula:
                # FV = P * [(1 + r)^n - 1] / r + PV * (1 + r)^n
                # Solve for P (monthly payment):
                # P = [FV - PV * (1 + r)^n] * r / [(1 + r)^n - 1]

                months = years * 12
                fv_of_initial = init_capital * ((1 + monthly_rate) ** months)

                if monthly_rate == 0:
                    # Special case: no growth
                    required_monthly = (target_amount - init_capital) / months
                else:
                    numerator = (target_amount - fv_of_initial) * monthly_rate
                    denominator = ((1 + monthly_rate) ** months) - 1

                    if denominator == 0:
                        required_monthly = 0.0
                    else:
                        required_monthly = numerator / denominator

                monthly_contrib = max(0.0, required_monthly)  # Can't be negative

            # Generate year-by-year projection
            projection = []
            current_value = init_capital
            months = years * 12

            # Add initial value
            projection.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "value": round(current_value, 2),
                "year": 0
            })

            # Project forward month-by-month, but report annually
            for month in range(1, months + 1):
                # Add monthly contribution
                current_value += monthly_contrib

                # Apply monthly return
                current_value *= (1 + monthly_rate)

                # Record at year boundaries
                if month % 12 == 0:
                    year = month // 12
                    future_date = datetime.now() + timedelta(days=365 * year)
                    projection.append({
                        "date": future_date.strftime("%Y-%m-%d"),
                        "value": round(current_value, 2),
                        "year": year
                    })

            final_value = current_value
            will_reach_goal = final_value >= target_amount

            result = {
                "target_amount": target_amount,
                "years": years,
                "init_capital": init_capital,
                "monthly_contrib": round(monthly_contrib, 2),
                "expected_return": expected_return,
                "projection": projection,
                "final_value": round(final_value, 2),
                "will_reach_goal": will_reach_goal,
                "shortfall": round(max(0, target_amount - final_value), 2)
            }

            if required_monthly is not None:
                result["required_monthly"] = round(required_monthly, 2)

            logger.info(f"Goal projection: ${final_value:,.2f} after {years} years (target: ${target_amount:,.2f})")

            return result

        except Exception as e:
            logger.exception("Error computing goal projection:")
            return {
                "error": str(e),
                "target_amount": target_amount,
                "years": years
            }


class FeeImpactAnalyzer:
    """
    Fee and tax impact analyzer for investment portfolios.
    """

    def __init__(self):
        pass

    def compute_fee_impact(
        self,
        principal: float,
        horizon_years: int,
        annual_fee_pct: float,
        exp_return_pct: float,
        dividend_withholding_pct: float = 0.0
    ) -> Dict[str, Any]:
        """
        Compute impact of fees and taxes on portfolio growth.

        Args:
            principal: Initial investment amount
            horizon_years: Investment time horizon in years
            annual_fee_pct: Annual fee percentage (e.g., 1.0 for 1%)
            exp_return_pct: Expected annual return percentage (e.g., 7.0 for 7%)
            dividend_withholding_pct: Dividend withholding tax (optional, default: 0%)

        Returns:
            {
                "final_with_fee": float,
                "final_no_fee": float,
                "delta": float (difference),
                "delta_pct": float (percentage difference),
                "total_fees_paid": float,
                "breakdown": list of yearly values
            }
        """
        try:
            # Validate inputs
            if horizon_years <= 0:
                return {"error": "Horizon must be positive"}

            if principal <= 0:
                return {"error": "Principal must be positive"}

            # Convert percentages to decimals
            annual_fee = annual_fee_pct / 100.0
            exp_return = exp_return_pct / 100.0
            dividend_withholding = dividend_withholding_pct / 100.0

            # Scenario 1: No fees
            value_no_fee = principal
            breakdown_no_fee = [{"year": 0, "value": principal}]

            for year in range(1, horizon_years + 1):
                # Apply return
                value_no_fee *= (1 + exp_return)

                # Apply dividend withholding (assumes dividend yield = 2% of portfolio)
                if dividend_withholding > 0:
                    dividend_yield = 0.02  # Assume 2% dividend yield
                    tax_on_dividends = value_no_fee * dividend_yield * dividend_withholding
                    value_no_fee -= tax_on_dividends

                breakdown_no_fee.append({"year": year, "value": round(value_no_fee, 2)})

            # Scenario 2: With fees
            value_with_fee = principal
            total_fees_paid = 0.0
            breakdown_with_fee = [{"year": 0, "value": principal, "fee_paid": 0.0}]

            for year in range(1, horizon_years + 1):
                # Apply return
                value_with_fee *= (1 + exp_return)

                # Deduct annual fee
                fee_paid = value_with_fee * annual_fee
                value_with_fee -= fee_paid
                total_fees_paid += fee_paid

                # Apply dividend withholding
                if dividend_withholding > 0:
                    dividend_yield = 0.02
                    tax_on_dividends = value_with_fee * dividend_yield * dividend_withholding
                    value_with_fee -= tax_on_dividends

                breakdown_with_fee.append({
                    "year": year,
                    "value": round(value_with_fee, 2),
                    "fee_paid": round(fee_paid, 2)
                })

            # Calculate delta
            delta = value_no_fee - value_with_fee
            delta_pct = (delta / value_no_fee * 100) if value_no_fee > 0 else 0.0

            result = {
                "principal": principal,
                "horizon_years": horizon_years,
                "annual_fee_pct": annual_fee_pct,
                "exp_return_pct": exp_return_pct,
                "dividend_withholding_pct": dividend_withholding_pct,
                "final_with_fee": round(value_with_fee, 2),
                "final_no_fee": round(value_no_fee, 2),
                "delta": round(delta, 2),
                "delta_pct": round(delta_pct, 2),
                "total_fees_paid": round(total_fees_paid, 2),
                "breakdown_with_fee": breakdown_with_fee,
                "breakdown_no_fee": breakdown_no_fee
            }

            logger.info(f"Fee impact: ${delta:,.2f} ({delta_pct:.1f}%) over {horizon_years} years")

            return result

        except Exception as e:
            logger.exception("Error computing fee impact:")
            return {
                "error": str(e),
                "principal": principal,
                "horizon_years": horizon_years
            }
