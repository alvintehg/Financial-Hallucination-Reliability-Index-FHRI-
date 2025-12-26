#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import holdings from Moomoo CSV export."""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def parse_moomoo_csv(csv_path):
    """Parse Moomoo CSV export and convert to portfolio.json format."""
    holdings = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            symbol = row['Symbol'].strip()
            name = row['Name'].strip()
            quantity = float(row['Quantity'])
            avg_cost = float(row['Average Cost'])

            # Skip if quantity is 0
            if quantity <= 0:
                continue

            holding = {
                "symbol": symbol,
                "name": name,
                "shares": quantity,
                "cost_basis": avg_cost,
                "asset_type": "equity"
            }

            holdings.append(holding)
            print(f"✓ {symbol}: {quantity} shares @ ${avg_cost:.2f}")

    return holdings

def update_portfolio_json(holdings, portfolio_path='portfolio.json'):
    """Update portfolio.json with new holdings."""
    # Backup existing portfolio
    if Path(portfolio_path).exists():
        backup_path = f"portfolio_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(portfolio_path, 'r') as f:
            backup_data = json.load(f)
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        print(f"\n✓ Backup created: {backup_path}")

    # Write new portfolio
    portfolio_data = {
        "holdings": holdings,
        "last_updated": datetime.now().isoformat(),
        "source": "moomoo_csv_import",
        "synced_from": "manual_csv"
    }

    with open(portfolio_path, 'w') as f:
        json.dump(portfolio_data, f, indent=2)

    print(f"\n✓ Portfolio updated: {portfolio_path}")
    print(f"✓ Total holdings: {len(holdings)}")

    # Calculate total cost
    total_cost = sum(h['shares'] * h['cost_basis'] for h in holdings)
    print(f"✓ Total cost basis: ${total_cost:.2f}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Moomoo CSV Import")
    print("="*80 + "\n")

    # Find the CSV file
    csv_file = None
    for f in Path('.').glob('Positions-*.csv'):
        csv_file = f
        break

    if not csv_file:
        print("✗ Error: No Positions CSV file found in current directory")
        print("\nPlease:")
        print("1. Export your portfolio from Moomoo as CSV")
        print("2. Place the CSV file in this directory")
        print("3. Run this script again")
        sys.exit(1)

    print(f"Found CSV file: {csv_file.name}\n")
    print("Parsing holdings...")

    try:
        holdings = parse_moomoo_csv(csv_file)

        if not holdings:
            print("\n✗ No holdings found in CSV")
            sys.exit(1)

        print(f"\n{'='*80}")
        update_portfolio_json(holdings)
        print("="*80)

        print("\n✅ Import complete!")
        print("\nNext steps:")
        print("1. Restart backend: python -m uvicorn src.server:app --port 8000 --reload")
        print("2. Refresh dashboard: http://localhost:3000/dashboard")
        print("3. Check your portfolio now shows live data!")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
