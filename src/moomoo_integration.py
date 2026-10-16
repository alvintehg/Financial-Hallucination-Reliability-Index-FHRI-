# src/moomoo_integration.py
"""
Moomoo OpenD API integration for real-time portfolio syncing.

Features:
- Connect to local Moomoo OpenD daemon
- Fetch real-time positions and holdings
- Sync positions to portfolio.json
- Support for stocks and ETFs
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
from pathlib import Path

logger = logging.getLogger("moomoo_integration")


class MoomooIntegration:
    """Service for integrating with Moomoo OpenD API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        """
        Initialize Moomoo integration.

        Args:
            host: OpenD host (default: 127.0.0.1)
            port: OpenD port (default: 11111)
        """
        self.host = host
        self.port = port
        self.ctx = None
        self.connected = False

        logger.info(f"Moomoo integration initialized for {host}:{port}")

    def connect(self) -> bool:
        """
        Connect to Moomoo OpenD daemon.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            from moomoo import OpenQuoteContext, OpenSecTradeContext, TrdEnv, TrdMarket

            # For US stocks, use OpenSecTradeContext
            self.ctx = OpenSecTradeContext(host=self.host, port=self.port)

            # Test connection
            ret, data = self.ctx.unlock_trade("YOUR_PASSWORD")  # User needs to set password
            if ret != 0:
                logger.warning(f"Failed to unlock trade: {data}")
                # Continue anyway as we can still read positions

            self.connected = True
            logger.info("Successfully connected to Moomoo OpenD")
            return True

        except ImportError:
            logger.error("moomoo-api package not installed. Run: pip install moomoo-api")
            return False
        except Exception as e:
            logger.exception(f"Failed to connect to Moomoo OpenD: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from Moomoo OpenD."""
        if self.ctx:
            try:
                self.ctx.close()
                logger.info("Disconnected from Moomoo OpenD")
            except:
                pass
        self.connected = False

    def get_positions(self) -> Dict[str, Any]:
        """
        Fetch current positions from Moomoo.

        Returns:
            Dict with positions data or error info
        """
        if not self.connected:
            if not self.connect():
                return {"status": "error", "message": "Not connected to Moomoo OpenD"}

        try:
            # Fetch positions
            ret, data = self.ctx.position_list_query()

            if ret != 0:
                logger.error(f"Failed to fetch positions: {data}")
                return {"status": "error", "message": str(data)}

            positions = []
            if data is not None and not data.empty:
                for idx, row in data.iterrows():
                    position = {
                        "symbol": row.get("code", ""),
                        "name": row.get("stock_name", row.get("code", "")),
                        "shares": float(row.get("qty", 0)),
                        "can_sell_qty": float(row.get("can_sell_qty", 0)),
                        "market_value": float(row.get("market_val", 0)),
                        "cost_basis": float(row.get("cost_price", 0)),
                        "current_price": float(row.get("last_price", 0)),
                        "unrealized_pnl": float(row.get("pl_val", 0)),
                        "unrealized_pnl_pct": float(row.get("pl_ratio", 0)) * 100,
                        "currency": row.get("currency", "USD"),
                        "market": row.get("market", "US"),
                    }
                    positions.append(position)

            result = {
                "status": "success",
                "positions": positions,
                "count": len(positions),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"Fetched {len(positions)} positions from Moomoo")
            return result

        except Exception as e:
            logger.exception(f"Error fetching positions: {e}")
            return {"status": "error", "message": str(e)}

    def sync_to_portfolio_json(self, portfolio_file: Optional[str] = None) -> bool:
        """
        Sync Moomoo positions to portfolio.json.

        Args:
            portfolio_file: Path to portfolio.json (default: project_root/portfolio.json)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get positions from Moomoo
            result = self.get_positions()

            if result["status"] != "success":
                logger.error(f"Cannot sync: {result.get('message')}")
                return False

            positions = result["positions"]

            if not positions:
                logger.warning("No positions to sync")
                return False

            # Convert to portfolio.json format
            holdings = []
            for pos in positions:
                # Extract just the ticker symbol (remove market prefix if present)
                symbol = pos["symbol"]
                if "." in symbol:
                    symbol = symbol.split(".")[0]

                holding = {
                    "symbol": symbol,
                    "name": pos["name"],
                    "shares": pos["shares"],
                    "cost_basis": pos["cost_basis"],
                    "asset_type": "equity"
                }
                holdings.append(holding)

            # Prepare portfolio data
            portfolio_data = {
                "holdings": holdings,
                "last_updated": result["last_updated"],
                "synced_from": "moomoo",
                "sync_method": "opend_api"
            }

            # Determine portfolio file path
            if portfolio_file is None:
                project_root = Path(__file__).parent.parent
                portfolio_file = project_root / "portfolio.json"
            else:
                portfolio_file = Path(portfolio_file)

            # Backup existing portfolio
            if portfolio_file.exists():
                backup_file = portfolio_file.with_suffix('.json.backup')
                import shutil
                shutil.copy(portfolio_file, backup_file)
                logger.info(f"Backed up existing portfolio to {backup_file}")

            # Write new portfolio
            with open(portfolio_file, 'w') as f:
                json.dump(portfolio_data, f, indent=2)

            logger.info(f"Successfully synced {len(holdings)} holdings to {portfolio_file}")
            return True

        except Exception as e:
            logger.exception(f"Error syncing to portfolio.json: {e}")
            return False

    def get_account_info(self) -> Dict[str, Any]:
        """
        Fetch account information.

        Returns:
            Dict with account data
        """
        if not self.connected:
            if not self.connect():
                return {"status": "error", "message": "Not connected"}

        try:
            ret, data = self.ctx.accinfo_query()

            if ret != 0:
                return {"status": "error", "message": str(data)}

            if data is not None and not data.empty:
                row = data.iloc[0]
                account_info = {
                    "status": "success",
                    "cash": float(row.get("cash", 0)),
                    "power": float(row.get("power", 0)),
                    "total_assets": float(row.get("total_assets", 0)),
                    "market_value": float(row.get("market_val", 0)),
                    "available_funds": float(row.get("available_funds", 0)),
                    "currency": row.get("currency", "USD")
                }
                return account_info

            return {"status": "error", "message": "No account data returned"}

        except Exception as e:
            logger.exception(f"Error fetching account info: {e}")
            return {"status": "error", "message": str(e)}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


if __name__ == "__main__":
    # Test the integration
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("\n" + "="*80)
    print("Testing Moomoo OpenD Integration")
    print("="*80)

    print("\n[SETUP] Make sure:")
    print("1. Moomoo OpenD is running (from Moomoo desktop app)")
    print("2. OpenD is configured with host=127.0.0.1, port=11111")
    print("3. You have some positions in your Moomoo account")
    print("\nPress Enter to continue...")
    input()

    with MoomooIntegration(host="127.0.0.1", port=11111) as moomoo:
        # Test 1: Get positions
        print("\n[TEST 1] Fetching positions from Moomoo...")
        positions = moomoo.get_positions()

        if positions["status"] == "success":
            print(f"✓ Success! Found {positions['count']} positions:")
            for pos in positions["positions"][:5]:  # Show first 5
                print(f"  - {pos['symbol']}: {pos['shares']} shares @ ${pos['cost_basis']:.2f}")
                print(f"    Market Value: ${pos['market_value']:.2f} | P&L: ${pos['unrealized_pnl']:.2f}")
        else:
            print(f"✗ Failed: {positions.get('message')}")

        # Test 2: Get account info
        print("\n[TEST 2] Fetching account information...")
        account = moomoo.get_account_info()

        if account["status"] == "success":
            print(f"✓ Success!")
            print(f"  Cash: ${account['cash']:,.2f}")
            print(f"  Total Assets: ${account['total_assets']:,.2f}")
            print(f"  Market Value: ${account['market_value']:,.2f}")
        else:
            print(f"✗ Failed: {account.get('message')}")

        # Test 3: Sync to portfolio.json
        print("\n[TEST 3] Syncing positions to portfolio.json...")
        success = moomoo.sync_to_portfolio_json()

        if success:
            print("✓ Successfully synced to portfolio.json!")
            print("  You can now restart the backend to see live data")
        else:
            print("✗ Sync failed")

    print("\n" + "="*80)
    print("Tests completed!")
    print("="*80)
