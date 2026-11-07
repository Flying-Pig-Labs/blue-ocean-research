# Pipeline Caching Documentation

## Overview

The multi-step LLM pipeline includes built-in caching functionality to save on API costs and processing time, particularly for the expensive JTBD extraction and Reddit research stages.

## How Caching Works

### Default Behavior (No Caching)
```bash
python run_pipeline.py
```
- Always generates fresh results
- Deletes old JTBD and Reddit files before creating new ones
- Ensures clean, up-to-date analysis
- Full cost: ~25 Claude API calls + ~150 Reddit API calls

### With Caching Enabled
```bash
python run_pipeline.py --use-cache
```
- Reuses existing JTBD files (`jtbds_*.txt`)
- Reuses existing Reddit discussion files (`reddit_discussions_*.csv`)
- Skips expensive LLM calls for JTBD extraction
- Skips rate-limited Reddit API calls
- Reduces Stage 2 from ~3 minutes to ~0 seconds

## Pipeline Stage Behavior

| Stage | Module | Caching Behavior |
|-------|--------|-----------------|
| 1 | research_analyzer | Always runs (input may change) |
| 2 | jobs_to_reddit | **CACHED** - Skips if files exist |
| 3 | opportunity_zone_analyzer | Uses cached JTBD/Reddit data |
| 4 | product_idea_generator | Uses cached opportunity zones |
| 5 | idea_consolidator | Uses cached product ideas |
| 6 | github_integration | Creates fresh repository |

## Cached Files

The following files are cached when `--use-cache` is enabled:
- `jtbds_YYYYMMDD_HHMMSS.txt` - Extracted Jobs-to-be-Done
- `reddit_discussions_YYYYMMDD_HHMMSS.csv` - Reddit discussion data
- `reddit_analysis_YYYYMMDD_HHMMSS.xlsx` - Reddit analysis workbook

## Cost Savings

Using cached files saves:
- **~25 Claude API calls** for JTBD extraction (~$0.50-$1.00)
- **~150 Reddit API calls** (rate-limited, saves time)
- **3-5 minutes** of processing time

## When to Use Caching

### Use Caching When:
- Testing downstream stages (3-6)
- Iterating on product idea generation
- Debugging GitHub integration
- Working with the same research document
- Running multiple experiments

### Don't Use Caching When:
- Input research document has changed
- Need fresh market insights
- Running production pipeline
- Been more than 24 hours since last run

## Docker/AWS Batch Considerations

When running in Docker/AWS Batch, caching is typically **not used** because:
1. Containers start fresh each time
2. No persistent storage between runs
3. Production runs should always be fresh

However, for local development with Docker:
```bash
# Mount local directory to preserve cache
docker run -v $(pwd):/app multi-step-llm-pipeline python run_pipeline.py --use-cache
```

## Cleaning Cache

To clean cached files:
```bash
python cleanup_pipeline.py
```

Or manually:
```bash
rm -f jtbds_*.txt reddit_discussions_*.csv reddit_analysis_*.xlsx
```

## Implementation Details

The caching logic is in `run_pipeline.py` lines 306-349:

```python
# Check if we should use cached files
jtbd_files = glob.glob("jtbds_*.txt") if use_cache else []
reddit_files = glob.glob("reddit_discussions_*.csv") if use_cache else []

if use_cache and jtbd_files and reddit_files:
    print(f"  📂 Using cached JTBD file: {jtbd_files[0]}")
    print(f"  📂 Using cached Reddit file: {reddit_files[0]}")
    jtbd_file = jtbd_files[0]
    reddit_file = reddit_files[0]
    stages_completed += 1
else:
    # Generate fresh files...
```

## Best Practices

1. **Development**: Use `--use-cache` liberally to save costs
2. **Testing**: Run without cache at least once per day
3. **Production**: Never use cache - always fresh
4. **CI/CD**: Disable caching in automated pipelines
5. **Debugging**: Use cache to isolate issues in specific stages

## Example Workflows

### Development Iteration
```bash
# First run - generate everything fresh
python run_pipeline.py

# Subsequent runs - use cache while tweaking Stage 4-6
python run_pipeline.py --use-cache

# Final validation - fresh run
python run_pipeline.py
```

### Testing Specific Stage
```bash
# Generate initial data
python run_pipeline.py

# Test just the GitHub integration repeatedly
python run_pipeline.py --use-cache --interactive
# (Skip to Stage 6 quickly)
```

### Cost-Conscious Development
```bash
# Monday: Fresh run
python run_pipeline.py

# Tuesday-Friday: Use cache
python run_pipeline.py --use-cache

# Next Monday: Fresh run again
python cleanup_pipeline.py
python run_pipeline.py
```

## Monitoring Cache Usage

Check cache file ages:
```bash
ls -la jtbds_*.txt reddit_discussions_*.csv | awk '{print $6, $7, $8, $9}'
```

## Troubleshooting

### Cache Not Working?
1. Check files exist: `ls jtbds_*.txt`
2. Verify `--use-cache` flag is set
3. Ensure file permissions allow reading
4. Check no cleanup script ran

### Stale Cache?
- Files older than 24 hours may have outdated insights
- Reddit discussions change rapidly
- Run `python cleanup_pipeline.py` to force fresh

### Partial Cache?
- If only JTBD or Reddit files exist (not both), cache won't be used
- Pipeline requires both files to skip Stage 2
- Delete incomplete cache: `rm jtbds_*.txt reddit_discussions_*.csv`

## Summary

The caching system provides significant cost savings during development and testing while ensuring production runs always use fresh data. Use it wisely to balance cost, time, and data freshness.