# Cache Mismatch Fix

## Problem
When using `--use-cache`, the pipeline can fail at Stage 3 (Opportunity Zone Discovery) with "No Reddit discussions found for JTBD" warnings followed by "list index out of range" error.

### Root Cause
The cached JTBD and Reddit files can be from different runs:
- `jtbds_20250806_203749.txt` (older run with different JTBDs)
- `reddit_discussions_20250807_145916.csv` (newer run with different JTBDs)

The Reddit CSV contains discussions for JTBDs that don't exist in the older JTBD file, causing the opportunity zone analyzer to fail.

## Solution

### Option 1: Clear Cache and Regenerate (Recommended)
```bash
# Remove mismatched cached files
rm -f jtbds_*.txt reddit_discussions_*.csv reddit_analysis_*.xlsx

# Run pipeline without cache to generate matching files
python run_pipeline.py
```

### Option 2: Use Matching Cache Files
```bash
# Check timestamps to ensure files are from same run
ls -la jtbds_*.txt reddit_discussions_*.csv

# Files should have similar timestamps (within minutes)
# Example of matching files:
# jtbds_20250807_145916.txt
# reddit_discussions_20250807_145916.csv
```

### Option 3: Never Use Cache for Production
```bash
# Always run fresh for production
python run_pipeline.py  # No --use-cache flag
```

## Prevention

### Best Practices
1. **Always clear cache when switching research documents**
   ```bash
   python cleanup_pipeline.py
   ```

2. **Use cache only for same-day iterations**
   - Cache files older than 24 hours should be cleared
   - Different research documents need fresh extraction

3. **Check file timestamps before using cache**
   ```bash
   ls -la jtbds_*.txt reddit_discussions_*.csv | awk '{print $6, $7, $8, $9}'
   ```

4. **Consider implementing cache validation**
   - Future improvement: Add checksum validation
   - Ensure JTBD and Reddit files are from same run

## Technical Details

The opportunity zone analyzer expects:
1. Each JTBD in the JTBD file to have corresponding Reddit discussions
2. The Reddit CSV to reference JTBDs that exist in the JTBD file

When files are mismatched:
- JTBD file has one set of jobs (e.g., 25 JTBDs from Aug 6)
- Reddit CSV has discussions for different JTBDs (from Aug 7)
- Analyzer can't find matching discussions, returns empty vectors
- Clustering fails with "list index out of range"

## Quick Debug Commands

```bash
# Check if cache files match
head -5 jtbds_*.txt
head -5 reddit_discussions_*.csv | cut -d',' -f1

# Count entries
wc -l jtbds_*.txt reddit_discussions_*.csv

# Check file ages
stat -f "%Sm" -t "%Y-%m-%d %H:%M" jtbds_*.txt reddit_discussions_*.csv
```

## Automated Fix Script

Create `fix_cache_mismatch.sh`:
```bash
#!/bin/bash
# Check if JTBD and Reddit files have matching timestamps (within 5 minutes)

JTBD_FILE=$(ls -t jtbds_*.txt 2>/dev/null | head -1)
REDDIT_FILE=$(ls -t reddit_discussions_*.csv 2>/dev/null | head -1)

if [ -z "$JTBD_FILE" ] || [ -z "$REDDIT_FILE" ]; then
    echo "✅ No cache files found - will generate fresh"
    exit 0
fi

JTBD_TIME=$(stat -f "%m" "$JTBD_FILE")
REDDIT_TIME=$(stat -f "%m" "$REDDIT_FILE")
DIFF=$((REDDIT_TIME - JTBD_TIME))
DIFF_ABS=${DIFF#-}

if [ $DIFF_ABS -gt 300 ]; then
    echo "⚠️ Cache files are mismatched (>5 minutes apart)"
    echo "  JTBD: $JTBD_FILE"
    echo "  Reddit: $REDDIT_FILE"
    echo "Clearing cache..."
    rm -f jtbds_*.txt reddit_discussions_*.csv reddit_analysis_*.xlsx
    echo "✅ Cache cleared - will generate fresh"
else
    echo "✅ Cache files match - safe to use"
fi
```

## Summary

Cache mismatches occur when JTBD and Reddit files are from different pipeline runs. Always ensure cached files are from the same run or clear the cache to regenerate matching files.