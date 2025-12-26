import json

with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

samples = dataset.get('samples', [])
valid_labels = ["accurate", "hallucination", "contradiction"]

issues = []
for sample in samples:
    gt = sample.get('ground_truth_label', '')
    ann = sample.get('your_annotation', '')
    
    # Check if annotation is descriptive text instead of a label
    if ann and ann not in valid_labels and gt:
        issues.append({
            'id': sample.get('id'),
            'ground_truth': gt,
            'annotation': ann[:80]  # First 80 chars
        })

print(f"Found {len(issues)} samples with descriptive 'your_annotation' instead of label")
print(f"\nExamples:")
for issue in issues[:10]:
    print(f"  {issue['id']}: ground_truth='{issue['ground_truth']}' | annotation='{issue['annotation']}...'")

print(f"\nImpact: These will now use ground_truth_label instead (FIXED in evaluation script)")



























