# Pipeline Optimizations

## 1. Pain Dimension Extraction (opportunity_zone_analyzer.py)

### Current Implementation:
- **75 API calls**: 25 JTBDs × 3 discussions each = 75 individual Claude API calls
- **Model**: Claude 3.5 Sonnet for reliability
- **Time**: ~2.5 minutes with rate limiting (0.2s sleep between calls)
- **Processing**: One API call per discussion (not batched)

### Why Not Batched:
- Reddit discussions are very large (often 500+ words)
- Batching multiple discussions exceeded token limits
- Individual processing ensures each discussion gets proper analysis
- More reliable JSON parsing with single discussion context

### Optimization Notes:
- Originally tried batching with Haiku model - had JSON parsing issues
- Tried batching with Sonnet - discussions too large for reliable batch processing
- Current approach: One call per discussion with Sonnet for best reliability
- Text limited to 2000 characters per discussion to prevent token overflow
- 0.2s delay between calls to avoid rate limiting

## 2. Cache Control (run_pipeline.py)

### Before:
- Always used cached files if they existed
- No way to force fresh data generation
- Confusing for production vs development

### After:
- Default: Always generates fresh data
- `--use-cache` flag: Explicitly use cached files for testing
- Clear separation between production and development modes

### Benefits:
- **Predictable behavior**: Fresh data by default
- **Faster testing**: Use cache when iterating on downstream stages
- **Clear intent**: Explicit flag shows you're using cached data

## 3. Credential Management

### Before:
- Each module loaded AWS secrets independently
- 6+ AWS Secrets Manager API calls per pipeline run
- Slower startup and potential rate limiting

### After:
- Credentials loaded once in `run_pipeline.py`
- All modules use environment variables
- Single AWS Secrets Manager session

### Benefits:
- **Fewer AWS API calls**: 1 vs 6+
- **Faster startup**: ~2 seconds saved
- **Centralized management**: All credential logic in one place
- **Better debugging**: Single point of failure for credentials

## 4. Pipeline Simplification (PRAW-based flow)

### Before:
- 7 stages with Exa API dependency
- Required expensive Exa subscription
- Theoretical competitive analysis

### After:
- 6 stages using PRAW (Reddit API)
- No Exa dependency
- Real user discussions and pain points

### Benefits:
- **Cost savings**: No Exa API subscription needed
- **Better data**: Real user frustrations vs theoretical analysis
- **Simpler flow**: Direct path from JTBDs to opportunity zones
- **More reliable**: Reddit API has generous free tier