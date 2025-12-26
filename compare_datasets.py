import json
from collections import Counter

# Load datasets
with open(r'data\fhri_evaluation_dataset_full.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

with open(r'data\fhri_evaluation_dataset_full_backup.json', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# Flatten if needed
def flatten_samples(samples):
    if samples and isinstance(samples[0], list):
        flattened = []
        for item in samples:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened
    return samples

current_samples = flatten_samples(current['samples'])
backup_samples = flatten_samples(backup['samples'])

# Count by scenario
current_scenarios = Counter([s.get('fhri_spec', {}).get('scenario_override', 'unknown') for s in current_samples])
backup_scenarios = Counter([s.get('fhri_spec', {}).get('scenario_override', 'unknown') for s in backup_samples])

# Count by label
current_labels = Counter([s.get('ground_truth_label', 'unknown') for s in current_samples])
backup_labels = Counter([s.get('ground_truth_label', 'unknown') for s in backup_samples])

print("="*70)
print("DATASET COMPARISON")
print("="*70)
print(f"\nBACKUP: {len(backup_samples)} samples")
print(f"CURRENT: {len(current_samples)} samples")
print(f"DIFFERENCE: {len(current_samples) - len(backup_samples)} samples")

print("\n" + "="*70)
print("BREAKDOWN BY SCENARIO")
print("="*70)
print(f"{'Scenario':<20} {'Backup':<10} {'Current':<10} {'Diff':<10}")
print("-"*70)
for scenario in sorted(backup_scenarios.keys()):
    backup_count = backup_scenarios[scenario]
    current_count = current_scenarios.get(scenario, 0)
    diff = current_count - backup_count
    print(f"{scenario:<20} {backup_count:<10} {current_count:<10} {diff:<10}")

print("\n" + "="*70)
print("BREAKDOWN BY LABEL")
print("="*70)
print(f"{'Label':<20} {'Backup':<10} {'Current':<10} {'Diff':<10}")
print("-"*70)
for label in sorted(backup_labels.keys()):
    backup_count = backup_labels[label]
    current_count = current_labels.get(label, 0)
    diff = current_count - backup_count
    print(f"{label:<20} {backup_count:<10} {current_count:<10} {diff:<10}")
