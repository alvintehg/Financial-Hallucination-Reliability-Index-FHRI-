import json

# Load current dataset
with open(r'data\fhri_evaluation_dataset_full.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

print(f'Number of top-level items in samples: {len(current["samples"])}')
print(f'\nType of first 10 items:')
for i in range(min(10, len(current["samples"]))):
    item = current["samples"][i]
    if isinstance(item, list):
        print(f'  Item {i}: list with {len(item)} elements')
    elif isinstance(item, dict):
        print(f'  Item {i}: dict with keys: {list(item.keys())[:3]}...')
    else:
        print(f'  Item {i}: {type(item).__name__}')

# Count how many are lists vs dicts
num_lists = sum(1 for item in current["samples"] if isinstance(item, list))
num_dicts = sum(1 for item in current["samples"] if isinstance(item, dict))

print(f'\nSummary:')
print(f'  Lists: {num_lists}')
print(f'  Dicts: {num_dicts}')
print(f'  Total: {len(current["samples"])}')

if num_lists > 0:
    # Check the lengths of list items
    list_lengths = [len(item) for item in current["samples"] if isinstance(item, list)]
    print(f'\n  List lengths: min={min(list_lengths)}, max={max(list_lengths)}, avg={sum(list_lengths)/len(list_lengths):.1f}')
    print(f'  Total samples if flattened: {sum(list_lengths) + num_dicts}')
