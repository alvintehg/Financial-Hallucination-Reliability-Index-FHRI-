"""
Utility script to split a dataset into chunks for checkpoint-based evaluation.

Usage:
    # Split 10k dataset into two 5k chunks
    python scripts/split_dataset.py \
        --input data/fhri_evaluation_dataset_full.json \
        --output_dir data/chunks \
        --chunk_size 5000
"""

import os
import sys
import json
import argparse
from pathlib import Path

def split_dataset(input_path: str, output_dir: str, chunk_size: int = 5000):
    """Split dataset into chunks."""

    # Load dataset
    print(f"Loading dataset from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    samples = dataset.get("samples", [])

    # Flatten if dataset is grouped into lists
    if any(isinstance(item, list) for item in samples):
        flattened = []
        for item in samples:
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        samples = flattened

    total_samples = len(samples)
    num_chunks = (total_samples + chunk_size - 1) // chunk_size  # Ceiling division

    print(f"Total samples: {total_samples}")
    print(f"Chunk size: {chunk_size}")
    print(f"Number of chunks: {num_chunks}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Split into chunks
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_samples)
        chunk_samples = samples[start_idx:end_idx]

        chunk_dataset = {
            "metadata": {
                **dataset.get("metadata", {}),
                "chunk_info": {
                    "chunk_number": i + 1,
                    "total_chunks": num_chunks,
                    "start_index": start_idx,
                    "end_index": end_idx,
                    "chunk_size": len(chunk_samples)
                }
            },
            "samples": chunk_samples
        }

        output_path = os.path.join(output_dir, f"chunk_{i+1}_of_{num_chunks}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_dataset, f, indent=2, ensure_ascii=False)

        print(f"  Chunk {i+1}: [{start_idx}:{end_idx}] ({len(chunk_samples)} samples) -> {output_path}")

    print(f"\n[OK] Dataset split into {num_chunks} chunks in: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Split dataset into chunks")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input dataset path"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/chunks",
        help="Output directory for chunks"
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=5000,
        help="Number of samples per chunk (default: 5000)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] Input file not found: {args.input}")
        return

    split_dataset(args.input, args.output_dir, args.chunk_size)


if __name__ == "__main__":
    main()
