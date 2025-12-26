# View Timing Comparison

## Quick Command

```bash
python scripts/evaluate_with_timing.py \
    --dataset data/evaluation_dataset.json \
    --output results/evaluation_timed.json \
    --fhri_threshold 0.60
```

## What It Does

1. **Records start/end time** - Tracks total evaluation duration
2. **Detects GPU usage** - Records if GPU was used
3. **Saves timing history** - Stores in `results/evaluation_timings.json`
4. **Shows comparison** - Compares with previous runs

## Output

After running, you'll see:

```
[START] Evaluation started at: 2025-12-07 14:30:00
[END] Evaluation completed at: 2025-12-07 14:45:30
[TIME] Total elapsed time: 930.00 seconds (15.50 minutes)

PERFORMANCE COMPARISON
Previous Evaluation:
  Time: 1800.00 seconds (30.00 minutes)
  GPU: No

Current Evaluation:
  Time: 930.00 seconds (15.50 minutes)
  GPU: Yes

Comparison:
  Speedup: 1.94x
  Time saved: 870.00 seconds (14.50 minutes)
  [INFO] GPU acceleration enabled - 1.94x faster!
```

## View All Timing History

```bash
# View the timing history file
cat results/evaluation_timings.json
```

Or open `results/evaluation_timings.json` in a text editor to see all previous runs.

## Tips

- **First run:** Records baseline (CPU or GPU)
- **Second run:** Compares with first run
- **Multiple runs:** Compares with most recent previous run

This helps you see the performance improvement from GPU acceleration!

















