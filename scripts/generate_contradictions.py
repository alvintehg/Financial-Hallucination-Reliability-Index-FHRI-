"""
Synthetic contradiction pairs generator for testing NLI contradiction detection.

This script generates finance-specific contradiction pairs for testing the
NLI-based contradiction detection module. It creates pairs of statements where
the second statement contradicts the first.

Usage:
    python scripts/generate_contradictions.py --output data/contradiction_pairs.json --count 50
"""

import json
import argparse
import os
from typing import List, Dict, Any


class ContradictionGenerator:
    """Generates synthetic contradiction pairs for financial domain."""

    def __init__(self):
        self.templates = self._create_templates()

    def _create_templates(self) -> List[Dict[str, Any]]:
        """Create templates for contradiction generation."""
        return [
            # Revenue contradictions
            {
                "category": "revenue",
                "statement_1": "Apple reported Q3 2024 revenue of ${amount}B",
                "statement_2": "Apple's Q3 2024 revenue was ${contradicting_amount}B",
                "variations": [
                    ("$85.8", "$95.2"),
                    ("$85.8", "$75.3"),
                    ("$119.6", "$98.4"),
                ]
            },
            {
                "category": "revenue_growth",
                "statement_1": "{company} revenue grew {percent}% year-over-year",
                "statement_2": "{company} revenue declined {contradicting_percent}% compared to last year",
                "variations": [
                    ("Microsoft", "17", "5"),
                    ("Apple", "5", "3"),
                    ("Tesla", "12", "2"),
                ]
            },
            # Performance contradictions
            {
                "category": "stock_performance",
                "statement_1": "{company} stock returned {percent}% in Q3",
                "statement_2": "{company} stock had negative returns of {contradicting_percent}% in Q3",
                "variations": [
                    ("Microsoft", "8.5", "2.3"),
                    ("Apple", "3.2", "1.5"),
                    ("Amazon", "6.7", "4.2"),
                ]
            },
            {
                "category": "market_comparison",
                "statement_1": "{company} outperformed the S&P 500 by {percent} percentage points",
                "statement_2": "{company} underperformed the S&P 500 by {contradicting_percent} percentage points",
                "variations": [
                    ("Apple", "3.2", "1.8"),
                    ("Microsoft", "4.3", "2.1"),
                    ("Netflix", "5.6", "3.2"),
                ]
            },
            # Sector performance contradictions
            {
                "category": "sector_performance",
                "statement_1": "The {sector} sector returned {percent}% in Q3 2024",
                "statement_2": "The {sector} sector saw losses of {contradicting_percent}% in Q3 2024",
                "variations": [
                    ("energy", "1.8", "2.5"),
                    ("healthcare", "2.1", "1.3"),
                    ("technology", "6.5", "0.8"),
                ]
            },
            # Product segment contradictions
            {
                "category": "product_segment",
                "statement_1": "{company} {segment} sales reached ${amount}B",
                "statement_2": "{company} {segment} sales were only ${contradicting_amount}B",
                "variations": [
                    ("Apple", "iPhone", "39.3", "28.7"),
                    ("Microsoft", "Cloud", "25.9", "18.4"),
                    ("Amazon", "AWS", "23.1", "17.8"),
                ]
            },
            # Growth rate contradictions
            {
                "category": "growth_rate",
                "statement_1": "{segment} grew {percent}% year-over-year",
                "statement_2": "{segment} growth was only {contradicting_percent}% compared to last year",
                "variations": [
                    ("Azure cloud services", "31", "18"),
                    ("iPhone sales", "12", "5"),
                    ("AWS revenue", "28", "14"),
                ]
            },
            # Market index contradictions
            {
                "category": "market_index",
                "statement_1": "The S&P 500 returned {percent}% in Q3 2024",
                "statement_2": "The S&P 500 declined {contradicting_percent}% in Q3 2024",
                "variations": [
                    ("4.2", "1.5"),
                    ("5.8", "2.3"),
                    ("3.7", "0.9"),
                ]
            },
            # Risk/volatility contradictions
            {
                "category": "volatility",
                "statement_1": "Market volatility remained {level} in Q3",
                "statement_2": "Market volatility was {contradicting_level} in Q3",
                "variations": [
                    ("elevated", "low"),
                    ("low", "high"),
                    ("moderate", "extremely high"),
                ]
            },
            # Portfolio performance contradictions
            {
                "category": "portfolio_returns",
                "statement_1": "The portfolio returned {percent}% with moderate volatility",
                "statement_2": "The portfolio had returns of only {contradicting_percent}% with high volatility",
                "variations": [
                    ("12.3", "6.8"),
                    ("9.8", "4.2"),
                    ("15.6", "7.3"),
                ]
            },
            # Diversification contradictions
            {
                "category": "diversification",
                "statement_1": "Portfolio diversification reduces risk",
                "statement_2": "Portfolio diversification increases overall portfolio risk",
                "variations": [("", "")]
            },
            # Rebalancing contradictions
            {
                "category": "rebalancing",
                "statement_1": "Quarterly rebalancing improves risk-adjusted returns by {percent}%",
                "statement_2": "Quarterly rebalancing reduces risk-adjusted returns by {contradicting_percent}%",
                "variations": [
                    ("0.5-1.0", "0.3-0.8"),
                    ("1.2", "0.5"),
                ]
            },
            # Interest rate contradictions
            {
                "category": "interest_rates",
                "statement_1": "Interest rates {action} in Q3 2024",
                "statement_2": "Interest rates {contradicting_action} in Q3 2024",
                "variations": [
                    ("increased", "decreased"),
                    ("remained stable", "rose sharply"),
                    ("declined", "increased"),
                ]
            },
            # Analyst rating contradictions
            {
                "category": "analyst_rating",
                "statement_1": "{company} received {rating} ratings from analysts",
                "statement_2": "{company} was rated {contradicting_rating} by most analysts",
                "variations": [
                    ("Apple", "buy", "sell"),
                    ("Microsoft", "outperform", "underperform"),
                    ("Tesla", "strong buy", "hold"),
                ]
            },
            # Earnings contradictions
            {
                "category": "earnings",
                "statement_1": "{company} earnings {action} expectations",
                "statement_2": "{company} earnings {contradicting_action} forecasts",
                "variations": [
                    ("Apple", "exceeded", "missed"),
                    ("Microsoft", "met", "fell short of"),
                    ("Amazon", "beat", "disappointed"),
                ]
            },
        ]

    def generate_pairs(self, count: int = 50) -> List[Dict[str, Any]]:
        """Generate contradiction pairs."""
        pairs = []
        pair_id = 1

        # Cycle through templates and variations
        while len(pairs) < count:
            for template in self.templates:
                if len(pairs) >= count:
                    break

                category = template["category"]
                stmt1_template = template["statement_1"]
                stmt2_template = template["statement_2"]
                variations = template["variations"]

                for variation in variations:
                    if len(pairs) >= count:
                        break

                    # Generate statement pair
                    if category in ["revenue"]:
                        stmt1 = stmt1_template.replace("{amount}", variation[0])
                        stmt2 = stmt2_template.replace("{contradicting_amount}", variation[1])
                    elif category in ["revenue_growth", "stock_performance", "market_comparison"]:
                        stmt1 = stmt1_template.format(company=variation[0], percent=variation[1])
                        stmt2 = stmt2_template.format(company=variation[0], contradicting_percent=variation[2])
                    elif category == "sector_performance":
                        stmt1 = stmt1_template.format(sector=variation[0], percent=variation[1])
                        stmt2 = stmt2_template.format(sector=variation[0], contradicting_percent=variation[2])
                    elif category == "product_segment":
                        stmt1 = stmt1_template.format(company=variation[0], segment=variation[1], amount=variation[2])
                        stmt2 = stmt2_template.format(company=variation[0], segment=variation[1], contradicting_amount=variation[3])
                    elif category == "growth_rate":
                        stmt1 = stmt1_template.format(segment=variation[0], percent=variation[1])
                        stmt2 = stmt2_template.format(segment=variation[0], contradicting_percent=variation[2])
                    elif category == "market_index":
                        stmt1 = stmt1_template.format(percent=variation[0])
                        stmt2 = stmt2_template.format(contradicting_percent=variation[1])
                    elif category == "volatility":
                        stmt1 = stmt1_template.format(level=variation[0])
                        stmt2 = stmt2_template.format(contradicting_level=variation[1])
                    elif category == "portfolio_returns":
                        stmt1 = stmt1_template.format(percent=variation[0])
                        stmt2 = stmt2_template.format(contradicting_percent=variation[1])
                    elif category == "diversification":
                        stmt1 = stmt1_template
                        stmt2 = stmt2_template
                    elif category == "rebalancing":
                        stmt1 = stmt1_template.format(percent=variation[0])
                        stmt2 = stmt2_template.format(contradicting_percent=variation[1])
                    elif category == "interest_rates":
                        stmt1 = stmt1_template.format(action=variation[0])
                        stmt2 = stmt2_template.format(contradicting_action=variation[1])
                    elif category == "analyst_rating":
                        stmt1 = stmt1_template.format(company=variation[0], rating=variation[1])
                        stmt2 = stmt2_template.format(company=variation[0], contradicting_rating=variation[2])
                    elif category == "earnings":
                        stmt1 = stmt1_template.format(company=variation[0], action=variation[1])
                        stmt2 = stmt2_template.format(company=variation[0], contradicting_action=variation[2])
                    else:
                        continue

                    pair = {
                        "id": f"contra_{pair_id:03d}",
                        "category": category,
                        "statement_1": stmt1,
                        "statement_2": stmt2,
                        "label": "contradiction",
                        "expected_score": "> 0.6",
                        "notes": f"Synthetic {category} contradiction pair"
                    }

                    pairs.append(pair)
                    pair_id += 1

        return pairs[:count]

    def generate_non_contradiction_pairs(self, count: int = 25) -> List[Dict[str, Any]]:
        """Generate non-contradiction (neutral/entailment) pairs for comparison."""
        pairs = []

        # Paraphrases (entailment)
        entailments = [
            {
                "id": "entail_001",
                "category": "paraphrase",
                "statement_1": "Apple reported Q3 2024 revenue of $85.8 billion",
                "statement_2": "Apple Inc. achieved $85.8B in Q3 2024 revenue",
                "label": "entailment",
                "expected_score": "< 0.3",
                "notes": "Paraphrase - should NOT be detected as contradiction"
            },
            {
                "id": "entail_002",
                "category": "paraphrase",
                "statement_1": "Microsoft's cloud services grew 31% year-over-year",
                "statement_2": "Azure grew 31% compared to the previous year",
                "label": "entailment",
                "expected_score": "< 0.3",
                "notes": "Paraphrase with slight rewording"
            },
            {
                "id": "entail_003",
                "category": "paraphrase",
                "statement_1": "Portfolio diversification reduces risk",
                "statement_2": "Diversifying your investments lowers portfolio risk",
                "label": "entailment",
                "expected_score": "< 0.3",
                "notes": "Semantic equivalence"
            },
        ]

        # Neutral (unrelated)
        neutrals = [
            {
                "id": "neutral_001",
                "category": "unrelated",
                "statement_1": "Apple reported Q3 2024 revenue of $85.8 billion",
                "statement_2": "Microsoft's cloud services grew 31%",
                "label": "neutral",
                "expected_score": "< 0.4",
                "notes": "Different companies - no contradiction"
            },
            {
                "id": "neutral_002",
                "category": "unrelated",
                "statement_1": "The S&P 500 returned 4.2% in Q3",
                "statement_2": "Portfolio diversification is a risk management strategy",
                "label": "neutral",
                "expected_score": "< 0.4",
                "notes": "Different topics - no contradiction"
            },
        ]

        pairs.extend(entailments[:count // 2])
        pairs.extend(neutrals[:count - len(pairs)])

        return pairs

    def save_pairs(self, output_path: str, contradiction_count: int = 50):
        """Generate and save contradiction pairs."""
        print("=" * 60)
        print("GENERATING SYNTHETIC CONTRADICTION PAIRS")
        print("=" * 60)
        print(f"Contradiction pairs: {contradiction_count}")
        print(f"Non-contradiction pairs: {contradiction_count // 2}")
        print("=" * 60)

        # Generate pairs
        contradiction_pairs = self.generate_pairs(count=contradiction_count)
        non_contradiction_pairs = self.generate_non_contradiction_pairs(count=contradiction_count // 2)

        all_pairs = contradiction_pairs + non_contradiction_pairs

        dataset = {
            "metadata": {
                "dataset_name": "Synthetic Financial Contradiction Pairs",
                "version": "1.0",
                "description": "Automatically generated contradiction pairs for testing NLI-based contradiction detection",
                "total_pairs": len(all_pairs),
                "contradiction_pairs": len(contradiction_pairs),
                "non_contradiction_pairs": len(non_contradiction_pairs),
                "categories": list(set(p["category"] for p in all_pairs))
            },
            "usage_instructions": [
                "1. These pairs can be used to test the NLI contradiction detection module",
                "2. Feed statement_1 as 'prev_assistant_turn' and statement_2 as current answer",
                "3. Check if contradiction_score matches expected_score threshold",
                "4. For pairs labeled 'contradiction', expect score > 0.6",
                "5. For pairs labeled 'entailment' or 'neutral', expect score < 0.4"
            ],
            "pairs": all_pairs
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Generated {len(all_pairs)} pairs")
        print(f"  Contradictions: {len(contradiction_pairs)}")
        print(f"  Non-contradictions: {len(non_contradiction_pairs)}")
        print(f"\n✓ Saved to: {output_path}")
        print("=" * 60)

        # Print sample
        print("\nSample Contradiction Pair:")
        sample = contradiction_pairs[0]
        print(f"  ID: {sample['id']}")
        print(f"  Category: {sample['category']}")
        print(f"  Statement 1: {sample['statement_1']}")
        print(f"  Statement 2: {sample['statement_2']}")
        print(f"  Expected: {sample['expected_score']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic contradiction pairs")
    parser.add_argument(
        "--output",
        type=str,
        default="data/contradiction_pairs.json",
        help="Path to save generated pairs"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of contradiction pairs to generate (default: 50)"
    )

    args = parser.parse_args()

    generator = ContradictionGenerator()
    generator.save_pairs(output_path=args.output, contradiction_count=args.count)


if __name__ == "__main__":
    main()
