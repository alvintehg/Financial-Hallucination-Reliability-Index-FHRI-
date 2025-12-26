#!/usr/bin/env python3
"""Quick script to sync Moomoo portfolio without prompts."""

from src.moomoo_integration import MoomooIntegration
import sys

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Syncing Moomoo Portfolio to portfolio.json")
    print("="*80 + "\n")

    try:
        with MoomooIntegration(host="127.0.0.1", port=11111) as moomoo:
            # Get positions
            print("[1/3] Fetching positions from Moomoo OpenD...")
            positions = moomoo.get_positions()

            if positions["status"] == "success":
                print(f"✓ Found {positions['count']} positions")
                for pos in positions["positions"]:
                    print(f"  - {pos['symbol']}: {pos['shares']} shares @ ${pos['cost_basis']:.2f}")
            else:
                print(f"✗ Error: {positions.get('message')}")
                sys.exit(1)

            # Sync to portfolio.json
            print("\n[2/3] Syncing to portfolio.json...")
            success = moomoo.sync_to_portfolio_json()

            if success:
                print("✓ Portfolio synced successfully!")
            else:
                print("✗ Sync failed")
                sys.exit(1)

            print("\n[3/3] Sync complete!")
            print("\nNext steps:")
            print("1. Restart your backend: python -m uvicorn src.server:app --port 8000 --reload")
            print("2. Refresh your dashboard: http://localhost:3000/dashboard")
            print("\n" + "="*80 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Is Moomoo desktop app running?")
        print("2. Is OpenD enabled? (Settings → API → OpenD)")
        print("3. OpenD settings: host=127.0.0.1, port=11111")
        print("4. Do you have positions in your Moomoo account?")
        sys.exit(1)
