import json

# Read the full dataset
with open('data/evaluation_dataset.json', 'r') as f:
    data = json.load(f)

# Filter samples with id in range fhri_060 to fhri_088
samples = data['samples']
subset_samples = [sample for sample in samples if 'fhri_060' <= sample['id'] <= 'fhri_088']

# Sort by id to maintain order
subset_samples.sort(key=lambda x: x['id'])

# Create new dataset structure with only the subset
subset_data = {
    'metadata': data['metadata'].copy(),
    'annotation_guidelines': data['annotation_guidelines'],
    'instructions_for_annotation': data['instructions_for_annotation'],
    'samples': subset_samples
}

# Update metadata to reflect subset
subset_data['metadata']['total_samples'] = len(subset_samples)
subset_data['metadata']['description'] = f"Subset of samples fhri_060 to fhri_088 - {data['metadata']['description']}"

# Write subset to new file
with open('data/evaluation_subset_60_88.json', 'w') as f:
    json.dump(subset_data, f, indent=2)

print(f"Created subset with {len(subset_samples)} samples")
print(f"ID range: {subset_samples[0]['id']} to {subset_samples[-1]['id']}")
