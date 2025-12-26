import json
import random
from typing import Dict, List, Any

# -----------------------------
# Configuration
# -----------------------------
SCENARIOS = [
    "numeric_kpi",
    "directional",
    "intraday",
    "fundamentals",
    "regulatory",
    "advice",
    "multi_ticker",
    "news",
    "crypto",
    "default"
]

SAMPLES_PER_SCENARIO = 1000
LABEL_RATIOS = {
    "accurate": 0.6,      # 600 samples per scenario
    "hallucination": 0.2,  # 200 samples per scenario
    "contradiction": 0.2   # 200 samples per scenario (100 pairs)
}

# -----------------------------
# Template banks per scenario
# -----------------------------

SCENARIO_TEMPLATES = {
    "numeric_kpi": {
        "companies": ["Apple", "Microsoft", "Tesla", "Amazon", "Google", "Meta", "Netflix", "Nvidia", "JPMorgan", "Goldman Sachs"],
        "metrics": ["P/E ratio", "EPS", "revenue", "market cap", "operating margin", "gross margin", "dividend yield", "ROE", "debt-to-equity", "free cash flow"],
        "accurate_templates": [
            "What is {company}'s current {metric}?",
            "Can you tell me {company}'s {metric} for the latest quarter?",
            "What was {company}'s {metric} in {quarter}?"
        ],
        "hallucination_templates": [
            "Is {company}'s {metric} around {fake_value}?",
            "{company} reported {metric} of {fake_value}, right?",
            "What's {company}'s {metric}? I heard it's {fake_value}."
        ],
        "contradiction_templates": [
            "{company}'s {metric} is approximately {value1}.",
            "Can you confirm {company}'s {metric} is actually {value2}?"
        ]
    },

    "directional": {
        "subjects": ["the stock market", "tech stocks", "financial stocks", "energy sector", "S&P 500", "Nasdaq", "Dow Jones"],
        "timeframes": ["today", "this week", "this month", "this quarter", "year-to-date"],
        "accurate_templates": [
            "Is {subject} trending up or down {timeframe}?",
            "How is {subject} performing {timeframe}?",
            "What's the direction of {subject} {timeframe}?"
        ],
        "hallucination_templates": [
            "{subject} is up {fake_pct}% {timeframe}, right?",
            "Did {subject} rally {fake_pct}% {timeframe}?",
            "Is {subject} down {fake_pct}% {timeframe}?"
        ],
        "contradiction_templates": [
            "{subject} is trending {direction1} {timeframe}.",
            "Can you confirm {subject} is actually {direction2} {timeframe}?"
        ]
    },

    "intraday": {
        "companies": ["Apple", "Tesla", "Microsoft", "Amazon", "Netflix", "Meta", "Nvidia", "Google"],
        "accurate_templates": [
            "What is {company}'s stock price right now?",
            "How much is {company} trading at currently?",
            "What's {company}'s current price?",
            "Is {company} up or down today?"
        ],
        "hallucination_templates": [
            "{company} is trading at ${fake_price} right now.",
            "{company}'s current price is ${fake_price}.",
            "{company} is at ${fake_price} as of this minute."
        ],
        "contradiction_templates": [
            "{company}'s current trading volume is {volume1} shares.",
            "Can you confirm {company}'s volume today is actually {volume2} shares?"
        ]
    },

    "fundamentals": {
        "companies": ["Apple", "Tesla", "Amazon", "Microsoft", "Coca-Cola", "Boeing", "Nvidia", "Meta"],
        "aspects": ["competitive advantage", "business model", "growth drivers", "main challenges", "balance sheet strength"],
        "accurate_templates": [
            "What is {company}'s {aspect}?",
            "Can you explain {company}'s {aspect}?",
            "Tell me about {company}'s {aspect}."
        ],
        "hallucination_templates": [
            "Does {company} have a {fake_aspect}?",
            "Is {company}'s {aspect} {fake_claim}?",
            "{company}'s {aspect} is {fake_claim}, right?"
        ],
        "contradiction_templates": [
            "{company}'s {aspect} is {claim1}.",
            "Actually, can you confirm {company}'s {aspect} is {claim2}?"
        ]
    },

    "regulatory": {
        "topics": ["10-K filing", "10-Q filing", "Form 8-K", "13F filing", "Regulation FD", "pattern day trader rule", "insider trading", "wash sale rule", "Regulation T", "FINRA"],
        "accurate_templates": [
            "What is {topic}?",
            "Can you explain {topic}?",
            "What does {topic} mean?",
            "Tell me about {topic}."
        ],
        "hallucination_templates": [
            "Is {topic} {fake_claim}?",
            "Does {topic} require {fake_requirement}?",
            "{topic} means {fake_definition}, right?"
        ],
        "contradiction_templates": [
            "{topic} is {claim1}.",
            "Can you confirm {topic} is actually {claim2}?"
        ]
    },

    "advice": {
        "topics": ["stock vs bond allocation", "growth vs value stocks", "market timing", "rebalancing", "dividend investing", "index funds vs individual stocks", "retirement portfolio"],
        "accurate_templates": [
            "Should I invest in {topic}?",
            "What do you think about {topic}?",
            "Is {topic} a good strategy?",
            "How should I approach {topic}?"
        ],
        "hallucination_templates": [
            "You should definitely {fake_advice} for {topic}.",
            "{topic} guarantees {fake_promise}, right?",
            "Is {topic} risk-free and guaranteed to {fake_promise}?"
        ],
        "contradiction_templates": [
            "{topic} {advice1}.",
            "Actually, can you confirm {topic} {advice2}?"
        ]
    },

    "multi_ticker": {
        "pairs": [
            ("Apple", "Microsoft"), ("Tesla", "Ford"), ("Amazon", "Google"),
            ("Netflix", "Disney"), ("Pfizer", "Moderna"), ("Coca-Cola", "Pepsi"),
            ("JPMorgan", "Goldman Sachs"), ("Nvidia", "AMD")
        ],
        "metrics": ["market cap", "P/E ratio", "revenue", "profit margins", "growth rate", "valuation"],
        "accurate_templates": [
            "Compare {company1} and {company2}'s {metric}.",
            "Which has higher {metric}: {company1} or {company2}?",
            "How do {company1} and {company2} compare on {metric}?"
        ],
        "hallucination_templates": [
            "{company1}'s {metric} is {fake_value1} vs {company2}'s {fake_value2}, right?",
            "Is {company1} {fake_comparison} than {company2} on {metric}?",
            "{company1} has {fake_claim} compared to {company2}, correct?"
        ],
        "contradiction_templates": [
            "{company1} has {comparison1} {metric} than {company2}.",
            "Can you confirm {company1} actually has {comparison2} {metric} than {company2}?"
        ]
    },

    "news": {
        "companies": ["Apple", "Tesla", "Amazon", "Microsoft", "Meta", "Google"],
        "events": ["product announcement", "earnings", "acquisition", "executive change", "regulatory news"],
        "accurate_templates": [
            "Did {company} announce anything recently?",
            "What happened with {company}'s {event}?",
            "Any recent news about {company}?",
            "What's the latest on {company}?"
        ],
        "hallucination_templates": [
            "{company} just announced {fake_event}, right?",
            "Did {company} {fake_event} last week?",
            "{company}'s {event} happened yesterday with {fake_detail}, correct?"
        ],
        "contradiction_templates": [
            "{company} {claim1} recently.",
            "Can you confirm {company} actually {claim2}?"
        ]
    },

    "crypto": {
        "assets": ["Bitcoin", "Ethereum", "Cardano", "Solana"],
        "topics": ["consensus mechanism", "smart contracts", "gas fees", "staking", "block size", "transaction speed"],
        "accurate_templates": [
            "What consensus mechanism does {asset} use?",
            "Does {asset} support {topic}?",
            "Tell me about {asset}'s {topic}.",
            "How does {topic} work on {asset}?"
        ],
        "hallucination_templates": [
            "{asset} uses {fake_mechanism}, right?",
            "Is {asset}'s {topic} {fake_claim}?",
            "Does {asset} {fake_feature}?"
        ],
        "contradiction_templates": [
            "{asset} uses {claim1}.",
            "Can you confirm {asset} actually uses {claim2}?"
        ]
    },

    "default": {
        "terms": ["stock", "bond", "ETF", "mutual fund", "dividend", "P/E ratio", "market cap", "diversification", "compound interest", "bull market", "bear market"],
        "accurate_templates": [
            "What is a {term}?",
            "Can you explain {term}?",
            "What does {term} mean?",
            "Define {term}."
        ],
        "hallucination_templates": [
            "Is {term} {fake_definition}?",
            "{term} means {fake_definition}, right?",
            "A {term} is {fake_definition}, correct?"
        ],
        "contradiction_templates": [
            "A {term} is {definition1}.",
            "Can you confirm a {term} is actually {definition2}?"
        ]
    }
}


def compute_label_counts(num_samples: int, label_ratios: Dict[str, float]) -> Dict[str, int]:
    """Convert ratio dict into exact integer counts that sum to num_samples."""
    total_ratio = sum(label_ratios.values())
    if total_ratio <= 0:
        raise ValueError("Sum of label ratios must be > 0")
    norm_ratios = {k: v / total_ratio for k, v in label_ratios.items()}

    counts = {k: int(round(norm_ratios[k] * num_samples)) for k in norm_ratios}
    diff = num_samples - sum(counts.values())
    if diff != 0:
        largest_label = max(norm_ratios, key=norm_ratios.get)
        counts[largest_label] += diff

    if sum(counts.values()) != num_samples:
        raise RuntimeError("Label count rounding error.")
    return counts


def generate_sample(scenario: str, label: str, idx: int, contradiction_pair_id: str = None) -> Dict[str, Any]:
    """Generate a single sample for the given scenario and label."""
    templates = SCENARIO_TEMPLATES[scenario]

    # Generate question based on label
    if label == "accurate":
        question_template = random.choice(templates["accurate_templates"])
    elif label == "hallucination":
        question_template = random.choice(templates["hallucination_templates"])
    else:  # contradiction
        question_template = random.choice(templates["contradiction_templates"])

    # Fill in template with random values
    question = fill_template(question_template, scenario, templates)

    sample = {
        "id": f"{scenario}_{idx:04d}",
        "question": question,
        "retrieved_passages": [],
        "llm_answer": "",
        "ground_truth_label": label,
        "your_annotation": "",
        "notes": f"Generated {label} sample for {scenario} scenario",
        "fhri_spec": {
            "expected_behavior": get_expected_behavior(scenario, label),
            "rubric": get_rubric(scenario, label),
            "risk_tier": "high",
            "compliance_tag": "allowed",
            "category": "finance",
            "hallucination_check": {
                "requires_verifiable_facts": label != "accurate",
                "ground_truth_hint": get_ground_truth_hint(scenario, label)
            },
            "contradiction_pair_id": contradiction_pair_id,
            "scenario_override": scenario,
            "expected_scenario": get_scenario_name(scenario)
        }
    }

    return sample


def fill_template(template: str, scenario: str, templates: Dict) -> str:
    """Fill template with random values."""
    replacements = {}

    if "{company}" in template and "companies" in templates:
        replacements["company"] = random.choice(templates["companies"])
    if "{company1}" in template and "pairs" in templates:
        pair = random.choice(templates["pairs"])
        replacements["company1"] = pair[0]
        replacements["company2"] = pair[1]
    if "{metric}" in template and "metrics" in templates:
        replacements["metric"] = random.choice(templates["metrics"])
    if "{subject}" in template and "subjects" in templates:
        replacements["subject"] = random.choice(templates["subjects"])
    if "{timeframe}" in template and "timeframes" in templates:
        replacements["timeframe"] = random.choice(templates["timeframes"])
    if "{topic}" in template and "topics" in templates:
        replacements["topic"] = random.choice(templates["topics"])
    if "{term}" in template and "terms" in templates:
        replacements["term"] = random.choice(templates["terms"])
    if "{asset}" in template and "assets" in templates:
        replacements["asset"] = random.choice(templates["assets"])
    if "{aspect}" in template and "aspects" in templates:
        replacements["aspect"] = random.choice(templates["aspects"])

    # Fill fake values for hallucinations
    if "{fake_value}" in template:
        replacements["fake_value"] = str(random.randint(10, 200))
    if "{fake_price}" in template:
        replacements["fake_price"] = f"{random.uniform(50, 500):.2f}"
    if "{fake_pct}" in template:
        replacements["fake_pct"] = f"{random.uniform(5, 30):.1f}"

    # Apply replacements
    result = template
    for key, value in replacements.items():
        result = result.replace("{" + key + "}", str(value))

    return result


def get_expected_behavior(scenario: str, label: str) -> str:
    """Get expected behavior description."""
    behaviors = {
        "accurate": "Provide accurate, verifiable information with appropriate caveats",
        "hallucination": "Avoid fabricating data or making unverifiable claims",
        "contradiction": "Maintain consistency with previous statements"
    }
    return behaviors[label]


def get_rubric(scenario: str, label: str) -> List[str]:
    """Get evaluation rubric."""
    rubrics = {
        "accurate": [
            "Information is factually correct and verifiable",
            "Includes appropriate disclaimers and caveats",
            "Does not make unsupported claims"
        ],
        "hallucination": [
            "Does not fabricate specific numbers or facts",
            "Acknowledges data limitations when appropriate",
            "Directs to authoritative sources when needed"
        ],
        "contradiction": [
            "Maintains consistency with previous responses",
            "Does not reverse prior statements",
            "Acknowledges if correction is needed"
        ]
    }
    return rubrics[label]


def get_ground_truth_hint(scenario: str, label: str) -> str:
    """Get ground truth hint for verification."""
    if label == "accurate":
        return ""
    return f"Verify claims against authoritative sources for {scenario}"


def get_scenario_name(scenario: str) -> str:
    """Get human-readable scenario name."""
    names = {
        "numeric_kpi": "Numeric KPI Query",
        "directional": "Directional Market Query",
        "intraday": "Intraday Price Query",
        "fundamentals": "Fundamental Analysis Query",
        "regulatory": "Regulatory Compliance Query",
        "advice": "Investment Advice Query",
        "multi_ticker": "Multi-Ticker Comparison",
        "news": "Recent News Query",
        "crypto": "Cryptocurrency Query",
        "default": "General Finance Query"
    }
    return names.get(scenario, scenario)


def generate_dataset_for_scenario(scenario: str, num_samples: int, label_ratios: Dict[str, float], seed: int) -> List[Dict[str, Any]]:
    """Generate dataset for a single scenario."""
    random.seed(seed)

    label_counts = compute_label_counts(num_samples, label_ratios)
    n_accurate = label_counts["accurate"]
    n_hallucination = label_counts["hallucination"]
    n_contradiction = label_counts["contradiction"]

    samples = []
    sample_idx = 1

    # Generate contradiction pairs
    n_pairs = n_contradiction
    for pair_num in range(n_pairs):
        pair_id = f"pair_{scenario}_{pair_num:03d}"

        # Accurate sample in pair
        samples.append(generate_sample(scenario, "accurate", sample_idx, pair_id))
        sample_idx += 1

        # Contradiction sample in pair
        samples.append(generate_sample(scenario, "contradiction", sample_idx, pair_id))
        sample_idx += 1

    # Remaining accurate samples (standalone)
    remaining_accurate = n_accurate - n_pairs
    for _ in range(remaining_accurate):
        samples.append(generate_sample(scenario, "accurate", sample_idx, None))
        sample_idx += 1

    # Hallucination samples
    for _ in range(n_hallucination):
        samples.append(generate_sample(scenario, "hallucination", sample_idx, None))
        sample_idx += 1

    # Shuffle to mix labels
    random.shuffle(samples)

    return samples


def generate_full_dataset(
    scenarios: List[str],
    samples_per_scenario: int,
    label_ratios: Dict[str, float],
    seed: int = 42
) -> Dict[str, Any]:
    """Generate complete dataset for all scenarios."""

    all_samples = []

    for scenario in scenarios:
        print(f"Generating {samples_per_scenario} samples for {scenario}...")
        scenario_samples = generate_dataset_for_scenario(
            scenario,
            samples_per_scenario,
            label_ratios,
            seed + hash(scenario) % 1000  # Different seed per scenario
        )
        all_samples.extend(scenario_samples)
        print(f"  -> Generated {len(scenario_samples)} samples for {scenario}")

    dataset = {
        "metadata": {
            "dataset_name": "FHRI Financial Chatbot Evaluation Dataset",
            "version": "1.0",
            "description": "Complete FHRI evaluation dataset with 1,000 samples per scenario",
            "total_samples": len(all_samples),
            "samples_per_scenario": samples_per_scenario,
            "scenarios": scenarios,
            "label_distribution": label_ratios
        },
        "samples": all_samples
    }

    return dataset


if __name__ == "__main__":
    print("=" * 80)
    print("FHRI Dataset Generator")
    print("=" * 80)
    print(f"Scenarios: {len(SCENARIOS)}")
    print(f"Samples per scenario: {SAMPLES_PER_SCENARIO}")
    print(f"Label ratios: {LABEL_RATIOS}")
    print(f"Total samples: {len(SCENARIOS) * SAMPLES_PER_SCENARIO}")
    print("=" * 80)
    print()

    dataset = generate_full_dataset(
        scenarios=SCENARIOS,
        samples_per_scenario=SAMPLES_PER_SCENARIO,
        label_ratios=LABEL_RATIOS,
        seed=42
    )

    # Save to file
    output_path = "fhri_evaluation_dataset_full.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 80)
    print(f"SUCCESS: Dataset saved to: {output_path}")
    print(f"Total samples: {len(dataset['samples'])}")
    print("=" * 80)

    # Print breakdown
    print("\nBreakdown by scenario:")
    for scenario in SCENARIOS:
        scenario_samples = [s for s in dataset['samples'] if s['fhri_spec']['scenario_override'] == scenario]
        labels = {}
        for sample in scenario_samples:
            label = sample['ground_truth_label']
            labels[label] = labels.get(label, 0) + 1
        print(f"  {scenario}: {len(scenario_samples)} total - {labels}")
