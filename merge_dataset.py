import json

# Read the file as text first to handle the structure issue
with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Find where the first JSON object ends and the array starts
first_json_end = content.find('}\n\n[')
if first_json_end == -1:
    first_json_end = content.find('}\n[')
if first_json_end == -1:
    print("Could not find split point. Trying different approach...")
    # Try to parse first part
    try:
        first_part = content[:content.rfind('}')+1]
        dataset = json.loads(first_part)
        print(f"Loaded first part: {len(dataset.get('samples', []))} samples")
    except:
        print("Error parsing first part")
        exit(1)
else:
    # Split into two parts
    first_part = content[:first_json_end+1]
    second_part = content[first_json_end+1:].lstrip()
    
    # Remove leading newline and [
    if second_part.startswith('\n['):
        second_part = second_part[2:]
    elif second_part.startswith('['):
        second_part = second_part[1:]
    
    # Remove trailing ]
    if second_part.endswith(']'):
        second_part = second_part[:-1]
    if second_part.endswith('\n'):
        second_part = second_part[:-1]
    
    # Parse first part
    dataset = json.loads(first_part)
    existing_samples = dataset.get('samples', [])
    print(f"Existing samples: {len(existing_samples)}")
    
    # Parse second part (should be array of samples)
    try:
        # Add comma-separated samples
        new_samples_text = second_part.strip()
        if new_samples_text.startswith('{'):
            # Single object, wrap in array
            new_samples = [json.loads(new_samples_text)]
        else:
            # Try to parse as array
            new_samples = json.loads('[' + new_samples_text + ']')
        
        print(f"New samples found: {len(new_samples)}")
        
        # Merge
        dataset['samples'].extend(new_samples)
        dataset['metadata']['total_samples'] = len(dataset['samples'])
        dataset['metadata']['version'] = '2.0'
        
        print(f"Total samples after merge: {len(dataset['samples'])}")
        
        # Save
        with open('data/evaluation_dataset.json', 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print("Dataset merged successfully!")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing new samples: {e}")
        print(f"First 500 chars of new part: {second_part[:500]}")



























