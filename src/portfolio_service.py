# src/portfolio_service.py
"""
Portfolio management service for real-time portfolio tracking.

Features:
- Fetch live prices for portfolio holdings
- Calculate portfolio value, P&L, and allocations
- Support for multiple asset types (stocks, crypto)
- Uses existing data_sources.py infrastructure
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("portfolio_service")


class PortfolioService:
    """Service for managing and tracking portfolio holdings."""

    def __init__(self, api_keys: Dict[str, str], portfolio_file: Optional[str] = None):
        """
        Initialize portfolio service.

        Args:
            api_keys: Dict with API keys (finnhub_key, twelvedata_key, etc.)
            portfolio_file: Path to portfolio JSON file (default: portfolio.json in project root)
        """
        self.api_keys = api_keys

        # Default portfolio file location
        if portfolio_file is None:
            project_root = Path(__file__).parent.parent
            portfolio_file = project_root / "portfolio.json"

        self.portfolio_file = Path(portfolio_file)
        logger.info(f"Portfolio service initialized with file: {self.portfolio_file}")

    def load_holdings(self) -> Dict[str, Any]:
        """
        Load portfolio holdings from JSON file.

        Returns:
            Dict with holdings data
        """
        try:
            if not self.portfolio_file.exists():
                logger.warning(f"Portfolio file not found: {self.portfolio_file}")
                return {"holdings": [], "last_updated": None}

            with open(self.portfolio_file, 'r') as f:
                data = json.load(f)

            logger.info(f"Loaded {len(data.get('holdings', []))} holdings from file")
            return data

        except Exception as e:
            logger.exception(f"Error loading portfolio file: {e}")
            return {"holdings": [], "last_updated": None}

    def save_holdings(self, holdings: List[Dict[str, Any]]) -> bool:
        """
        Save portfolio holdings to JSON file.

        Args:
            holdings: List of holding dicts

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "holdings": holdings,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

            # Create parent directory if it doesn't exist
            self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(holdings)} holdings to file")
            return True

        except Exception as e:
            logger.exception(f"Error saving portfolio file: {e}")
            return False

    def get_live_portfolio(self) -> Dict[str, Any]:
        """
        Fetch live portfolio data with real-time prices.

        Returns:
            Dict with portfolio summary and holdings with live prices
        """
        try:
            # Import here to avoid circular imports
            try:
                from data_sources import fetch_all_sources
            except ImportError:
                from src.data_sources import fetch_all_sources

            # Load holdings
            portfolio_data = self.load_holdings()
            holdings = portfolio_data.get("holdings", [])

            if not holdings:
                logger.warning("No holdings found in portfolio")
                return self._empty_portfolio()

            # Fetch live prices for each holding
            live_holdings = []
            total_value = 0.0
            total_cost_basis = 0.0
            total_daily_change = 0.0

            for holding in holdings:
                symbol = holding.get("symbol")
                shares = holding.get("shares", 0)
                cost_basis = holding.get("cost_basis", 0)
                asset_type = holding.get("asset_type", "equity")

                if not symbol or shares <= 0:
                    logger.warning(f"Invalid holding: {holding}")
                    continue

                # Fetch live price
                try:
                    data = fetch_all_sources(symbol, asset_type, self.api_keys)

                    # Extract price based on asset type
                    if asset_type == "equity" and data.get("equity_data"):
                        price_data = data["equity_data"].get("primary_data")
                    elif asset_type == "crypto" and data.get("crypto_data"):
                        price_data = data["crypto_data"].get("primary_data")
                    else:
                        logger.warning(f"No price data found for {symbol}")
                        continue

                    if not price_data:
                        logger.warning(f"No price data for {symbol}")
                        continue

                    current_price = price_data.get("price", 0)
                    pct_change = price_data.get("pct_change", 0)
                    source = price_data.get("source", "Unknown")

                    # Calculate values
                    market_value = current_price * shares
                    total_cost = cost_basis * shares
                    unrealized_pnl = market_value - total_cost
                    unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
                    daily_change = (current_price * (pct_change / 100)) * shares

                    live_holdings.append({
                        "symbol": symbol,
                        "name": holding.get("name", symbol),
                        "asset_type": asset_type,
                        "shares": shares,
                        "cost_basis": round(cost_basis, 2),
                        "current_price": round(current_price, 2),
                        "market_value": round(market_value, 2),
                        "unrealized_pnl": round(unrealized_pnl, 2),
                        "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                        "daily_change": round(daily_change, 2),
                        "daily_change_pct": round(pct_change, 2),
                        "source": source,
                        "last_updated": price_data.get("ts_utc")
                    })

                    total_value += market_value
                    total_cost_basis += total_cost
                    total_daily_change += daily_change

                except Exception as e:
                    logger.exception(f"Error fetching price for {symbol}: {e}")
                    continue

            # Calculate portfolio-level metrics
            total_pnl = total_value - total_cost_basis
            total_pnl_pct = (total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
            total_daily_change_pct = (total_daily_change / total_value * 100) if total_value > 0 else 0

            # Calculate allocations
            for holding in live_holdings:
                holding["allocation_pct"] = round((holding["market_value"] / total_value * 100) if total_value > 0 else 0, 2)

            # Sort by market value descending
            live_holdings.sort(key=lambda x: x["market_value"], reverse=True)

            return {
                "summary": {
                    "total_value": round(total_value, 2),
                    "total_cost_basis": round(total_cost_basis, 2),
                    "total_pnl": round(total_pnl, 2),
                    "total_pnl_pct": round(total_pnl_pct, 2),
                    "daily_change": round(total_daily_change, 2),
                    "daily_change_pct": round(total_daily_change_pct, 2),
                    "positions_count": len(live_holdings),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                },
                "holdings": live_holdings,
                "status": "success"
            }

        except Exception as e:
            logger.exception(f"Error fetching live portfolio: {e}")
            return {
                "summary": self._empty_portfolio()["summary"],
                "holdings": [],
                "status": "error",
                "error": str(e)
            }

    def _empty_portfolio(self) -> Dict[str, Any]:
        """Return empty portfolio structure."""
        return {
            "summary": {
                "total_value": 0.0,
                "total_cost_basis": 0.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "daily_change": 0.0,
                "daily_change_pct": 0.0,
                "positions_count": 0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "holdings": [],
            "status": "empty"
        }

    def add_holding(self, symbol: str, shares: float, cost_basis: float,
                   name: Optional[str] = None, asset_type: str = "equity") -> bool:
        """
        Add a new holding to the portfolio.

        Args:
            symbol: Ticker symbol
            shares: Number of shares
            cost_basis: Average cost per share
            name: Display name (optional)
            asset_type: "equity" or "crypto"

        Returns:
            True if successful, False otherwise
        """
        try:
            portfolio_data = self.load_holdings()
            holdings = portfolio_data.get("holdings", [])

            # Check if holding already exists
            for holding in holdings:
                if holding["symbol"] == symbol:
                    logger.warning(f"Holding {symbol} already exists, use update_holding instead")
                    return False

            # Add new holding
            new_holding = {
                "symbol": symbol,
                "name": name or symbol,
                "shares": shares,
                "cost_basis": cost_basis,
                "asset_type": asset_type
            }

            holdings.append(new_holding)
            return self.save_holdings(holdings)

        except Exception as e:
            logger.exception(f"Error adding holding: {e}")
            return False

    def update_holding(self, symbol: str, shares: Optional[float] = None,
                      cost_basis: Optional[float] = None) -> bool:
        """
        Update an existing holding.

        Args:
            symbol: Ticker symbol
            shares: New number of shares (optional)
            cost_basis: New cost basis (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            portfolio_data = self.load_holdings()
            holdings = portfolio_data.get("holdings", [])

            # Find and update holding
            for holding in holdings:
                if holding["symbol"] == symbol:
                    if shares is not None:
                        holding["shares"] = shares
                    if cost_basis is not None:
                        holding["cost_basis"] = cost_basis
                    return self.save_holdings(holdings)

            logger.warning(f"Holding {symbol} not found")
            return False

        except Exception as e:
            logger.exception(f"Error updating holding: {e}")
            return False

    def remove_holding(self, symbol: str) -> bool:
        """
        Remove a holding from the portfolio.

        Args:
            symbol: Ticker symbol

        Returns:
            True if successful, False otherwise
        """
        try:
            portfolio_data = self.load_holdings()
            holdings = portfolio_data.get("holdings", [])

            # Filter out the holding
            new_holdings = [h for h in holdings if h["symbol"] != symbol]

            if len(new_holdings) == len(holdings):
                logger.warning(f"Holding {symbol} not found")
                return False

            return self.save_holdings(new_holdings)

        except Exception as e:
            logger.exception(f"Error removing holding: {e}")
            return False


if __name__ == "__main__":
    # Test the portfolio service
    import os
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    api_keys = {
        "finnhub_key": os.getenv("FINNHUB_API_KEY"),
        "twelvedata_key": os.getenv("TWELVEDATA_API_KEY"),
        "fmp_key": os.getenv("FMP_API_KEY"),
        "edgar_email": os.getenv("EDGAR_CONTACT_EMAIL")
    }

    service = PortfolioService(api_keys)

    print("\n" + "="*80)
    print("Testing Portfolio Service")
    print("="*80)

    # Test loading portfolio
    print("\n[TEST 1] Loading portfolio...")
    portfolio = service.get_live_portfolio()
    print(f"Status: {portfolio['status']}")
    print(f"Total Value: ${portfolio['summary']['total_value']:,.2f}")
    print(f"Total P&L: ${portfolio['summary']['total_pnl']:,.2f} ({portfolio['summary']['total_pnl_pct']:+.2f}%)")
    print(f"Daily Change: ${portfolio['summary']['daily_change']:,.2f} ({portfolio['summary']['daily_change_pct']:+.2f}%)")
    print(f"Positions: {portfolio['summary']['positions_count']}")

    if portfolio['holdings']:
        print("\nTop 5 Holdings:")
        for holding in portfolio['holdings'][:5]:
            print(f"  {holding['symbol']}: ${holding['market_value']:,.2f} ({holding['allocation_pct']:.1f}%) | "
                  f"P&L: ${holding['unrealized_pnl']:+,.2f} ({holding['unrealized_pnl_pct']:+.2f}%)")

    print("\n" + "="*80)
