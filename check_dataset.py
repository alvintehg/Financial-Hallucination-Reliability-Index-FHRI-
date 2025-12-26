import json

with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

samples = dataset.get('samples', [])
print(f"Total samples: {len(samples)}")
print(f"Metadata says: {dataset.get('metadata', {}).get('total_samples', 'N/A')}")

# Count labels
labels = {}
us_stocks = []
hallucination_samples = []
contradiction_pairs = {}

for sample in samples:
    label = sample.get('ground_truth_label', 'unknown')
    labels[label] = labels.get(label, 0) + 1
    
    # Check for US stock mentions
    question = sample.get('question', '').lower()
    us_stock_tickers = ['aapl', 'msft', 'googl', 'tsla', 'amzn', 'meta', 'nvda', 'jpm', 'v', 'jnj', 'wmt', 'netflix', 'nflx', 'dis', 'disney', 'sp500', 's&p 500', 'nasdaq', 'dow jones']
    if any(ticker in question for ticker in us_stock_tickers):
        us_stocks.append(sample.get('id'))
    
    # Check hallucination samples
    if label == 'hallucination':
        hallucination_samples.append(sample.get('id'))
    
    # Check contradiction pairs
    pair_id = sample.get('fhri_spec', {}).get('contradiction_pair_id')
    if pair_id:
        if pair_id not in contradiction_pairs:
            contradiction_pairs[pair_id] = []
        contradiction_pairs[pair_id].append(sample.get('id'))

print(f"\nLabel distribution:")
for label, count in sorted(labels.items()):
    print(f"  {label}: {count}")

print(f"\nUS Stock-related samples: {len(us_stocks)}")
print(f"  Examples: {us_stocks[:10]}")

print(f"\nHallucination samples: {len(hallucination_samples)}")
if hallucination_samples:
    print(f"  IDs: {hallucination_samples[:10]}")

print(f"\nContradiction pairs: {len(contradiction_pairs)}")
for pair_id, sample_ids in list(contradiction_pairs.items())[:10]:
    print(f"  {pair_id}: {sample_ids}")

# Check for issues
print(f"\n=== Validation ===")
issues = []

# Check ID sequence
ids = [s.get('id') for s in samples]
expected_ids = [f"fhri_{i:03d}" for i in range(1, len(samples) + 1)]
missing_ids = set(expected_ids) - set(ids)
if missing_ids:
    issues.append(f"Missing IDs: {sorted(missing_ids)[:10]}")

# Check contradiction pairs
for pair_id, sample_ids in contradiction_pairs.items():
    if len(sample_ids) < 2:
        issues.append(f"Pair {pair_id} has only {len(sample_ids)} sample(s): {sample_ids}")

if issues:
    print("Issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("No major issues found!")



























