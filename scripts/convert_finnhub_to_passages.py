#!/usr/bin/env python3
"""
Convert Finnhub JSON data to passages.txt format.
Run after fetching data from Finnhub in the UI.
"""

import os
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
FINNHUB_DIR = PROJECT_ROOT / "data" / "trusted_docs"
PASSAGES_FILE = PROJECT_ROOT / "data" / "passages.txt"

def convert_finnhub_to_passages():
    """Convert all Finnhub JSON files to text passages."""

    if not FINNHUB_DIR.exists():
        print(f"Error: {FINNHUB_DIR} not found")
        print("Please fetch data from Finnhub in the UI first")
        return

    passages = []

    # Read existing passages
    if PASSAGES_FILE.exists():
        print(f"Reading existing passages from {PASSAGES_FILE}...")
        existing = PASSAGES_FILE.read_text(encoding='utf-8').strip()
        if existing:
            passages.extend(existing.split('\n\n'))
            print(f"  Found {len(passages)} existing passages")

    # Process all JSON files
    json_files = list(FINNHUB_DIR.glob("*.json"))
    print(f"\nProcessing {len(json_files)} Finnhub files...")

    new_count = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('type') == 'news':
                # Convert news article to passage
                ticker = data.get('ticker', 'UNKNOWN')
                headline = data.get('headline', '')
                summary = data.get('summary', headline)
                source = data.get('source', 'Unknown')
                dt = datetime.fromtimestamp(data.get('datetime', 0))
                date_str = dt.strftime('%Y-%m-%d')

                passage = f"{ticker} News ({date_str}): {headline}. {summary} Source: {source}."

            elif data.get('type') == 'quote':
                # Convert stock quote to passage
                ticker = data.get('ticker', 'UNKNOWN')
                quote = data.get('quote', {})
                current = quote.get('c', 0)
                change = quote.get('d', 0)
                change_pct = quote.get('dp', 0)
                high = quote.get('h', 0)
                low = quote.get('l', 0)
                dt = datetime.fromtimestamp(data.get('datetime', 0))
                date_str = dt.strftime('%Y-%m-%d')

                passage = f"{ticker} Stock Quote ({date_str}): Current price ${current:.2f}, change ${change:.2f} ({change_pct:.2f}%). Day high: ${high:.2f}, low: ${low:.2f}."

            else:
                continue

            # Add if not duplicate
            if passage not in passages:
                passages.append(passage)
                new_count += 1

        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue

    print(f"\nAdded {new_count} new passages from Finnhub data")
    print(f"Total passages: {len(passages)}")

    # Write back to passages.txt
    print(f"\nWriting to {PASSAGES_FILE}...")
    PASSAGES_FILE.write_text('\n\n'.join(passages), encoding='utf-8')
    print("Done!")

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Rebuild the TF-IDF index:")
    print("   python -c \"from src.retrieval import rebuild_tfidf_index; rebuild_tfidf_index()\"")
    print("\n2. Or use the 'Rebuild Index' button in Streamlit UI")
    print("\n3. Your chatbot will now use real-time Finnhub data!")
    print("="*60)

if __name__ == "__main__":
    convert_finnhub_to_passages()
