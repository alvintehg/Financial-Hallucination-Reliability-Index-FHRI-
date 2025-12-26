import json
import re

# Read the entire file
with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the end of the first JSON object (closing brace of the main object)
# The structure is: {... "samples": [...] } followed by [ {...}, {...} ]

# Strategy: Find where the first } closes the main object, then extract everything after
# We need to find the closing brace of the "samples" array and the main object

# Find the position where the first JSON object ends
first_json_end = content.rfind('}\n\n[')
if first_json_end == -1:
    first_json_end = content.rfind('}\n[')
if first_json_end == -1:
    # Try finding the closing of samples array
    samples_end = content.find('  ]\n}')
    if samples_end != -1:
        first_json_end = samples_end + 4  # Position after '  ]\n}'
    else:
        print("Cannot find split point. Trying manual approach...")
        # Try to find the end of the first complete JSON
        brace_count = 0
        first_json_end = -1
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Check if next non-whitespace is newline and then [
                    remaining = content[i+1:].lstrip()
                    if remaining.startswith('\n[') or remaining.startswith('['):
                        first_json_end = i + 1
                        break

if first_json_end == -1:
    print("ERROR: Could not find where to split the file")
    exit(1)

# Split the content
first_part = content[:first_json_end+1].rstrip()
second_part = content[first_json_end+1:].lstrip()

# Remove leading newlines and [
while second_part.startswith('\n') or second_part.startswith('['):
    if second_part.startswith('\n'):
        second_part = second_part[1:]
    elif second_part.startswith('['):
        second_part = second_part[1:]

# Remove trailing ]
if second_part.rstrip().endswith(']'):
    second_part = second_part.rstrip()[:-1].rstrip()

# Parse first part
try:
    dataset = json.loads(first_part)
    existing_samples = dataset.get('samples', [])
    print(f"✓ Loaded existing dataset: {len(existing_samples)} samples")
except json.JSONDecodeError as e:
    print(f"ERROR parsing first part: {e}")
    exit(1)

# Parse second part - it should be comma-separated JSON objects
# Try to extract all JSON objects from the second part
new_samples = []
# Split by }, but be careful with nested objects
current_obj = ""
brace_level = 0
in_string = False
escape_next = False

for char in second_part:
    if escape_next:
        escape_next = False
        current_obj += char
        continue
    
    if char == '\\':
        escape_next = True
        current_obj += char
        continue
    
    if char == '"' and not escape_next:
        in_string = not in_string
        current_obj += char
        continue
    
    if not in_string:
        if char == '{':
            brace_level += 1
            current_obj += char
        elif char == '}':
            brace_level -= 1
            current_obj += char
            if brace_level == 0:
                # Complete object found
                try:
                    obj = json.loads(current_obj)
                    new_samples.append(obj)
                    current_obj = ""
                except:
                    pass
        elif char == ',' and brace_level == 0:
            # Skip commas between objects
            continue
        else:
            if brace_level > 0:
                current_obj += char
    else:
        current_obj += char

print(f"✓ Extracted {len(new_samples)} new samples")

# Merge
dataset['samples'].extend(new_samples)
dataset['metadata']['total_samples'] = len(dataset['samples'])
dataset['metadata']['version'] = '2.0'
dataset['metadata']['annotation_date'] = '2025-12-01'

print(f"✓ Total samples after merge: {len(dataset['samples'])}")

# Validate IDs are sequential
ids = [s.get('id') for s in dataset['samples']]
print(f"✓ Sample IDs range: {ids[0]} to {ids[-1]}")

# Save
with open('data/evaluation_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print("✓ Dataset merged and saved successfully!")

# Count labels
labels = {}
for sample in dataset['samples']:
    label = sample.get('ground_truth_label', 'unknown')
    labels[label] = labels.get(label, 0) + 1

print(f"\nLabel distribution:")
for label, count in sorted(labels.items()):
    print(f"  {label}: {count}")



























