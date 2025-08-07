# Opportunity Zones Discovery Pipeline - Session Summary

## Where We Started
We were trying to fix the broken JTBD clustering pipeline that was producing garbage results from EXA searches.

## What We Built
1. **`jobs_to_reddit.py`** - Extracts clean JTBDs from analysis_results.md using Claude, translates them to authentic Reddit search queries, and finds 545 real Reddit discussions
2. **`cluster_reddit_discussions.py`** - Embeds Reddit discussions using Cohere and clusters them with HDBSCAN

## Key Realization
We were "chasing our tail" - we already have the JTBDs and the Reddit discussions mapped to them. Clustering the discussions just rediscovers the JTBDs we started with!

## What "Opportunity Zones" Really Are
Strategic areas where multiple pain points converge - high-impact problem spaces where a solution would address multiple JTBDs at once.

## The Better Approach: Structured Opportunity Zone Discovery

### Core Concept
Instead of clustering Reddit posts randomly, we should:
1. Group Reddit discussions by their parent JTBD (we already have this!)
2. Extract specific pain dimensions from each discussion
3. Find overlap patterns - which JTBDs share common underlying problems
4. Define opportunity zones - areas where solving one problem helps multiple JTBDs

### Pain Dimension Taxonomy
```python
PAIN_DIMENSIONS = {
    "timing_coordination": ["schedule", "deadline", "timing", "delay", "simultaneous"],
    "financial_stress": ["cost", "mortgage", "fee", "expensive", "afford"],
    "communication_gaps": ["update", "response", "ghosted", "contact", "informed"],
    "process_complexity": ["confusing", "complicated", "understand", "steps", "documentation"],
    "trust_issues": ["lied", "scam", "manipulative", "dishonest", "sketchy"],
    "technology_gaps": ["manual", "paper", "automate", "system", "track"],
    "decision_anxiety": ["worried", "stressed", "nervous", "uncertain", "regret"],
    "market_dynamics": ["competitive", "outbid", "inventory", "fast", "missed"]
}
```

### Pipeline Structure
1. **Evidence Enrichment**: For each Reddit thread, extract problems and score against pain dimensions
2. **JTBD Vectorization**: Aggregate pain scores to create JTBD vectors
3. **Zone Discovery**: Cluster JTBDs by pain dimension similarity
4. **Solution Mapping**: Extract requirements and prioritize zones

### Example Opportunity Zone Output
```json
{
  "zone_id": "OZ_001",
  "name": "Transaction Coordination Platform",
  "jtbds_addressed": ["JTBD_001", "JTBD_002", "JTBD_007"],
  "evidence_strength": {
    "total_threads": 127,
    "total_engagement": 45678
  },
  "pain_dimensions": {
    "timing_coordination": 0.92,
    "communication_gaps": 0.87
  },
  "solution_requirements": [
    "Real-time timeline synchronization",
    "Multi-party communication hub"
  ]
}
```

## Current State of Files

### Working Pipeline
- `analysis_results.md` - Clean structured analysis from Stage 1 (4 parallel Anthropic calls)
- `jobs_to_reddit.py` - Extracts JTBDs and finds Reddit discussions (WORKING)
- `jtbds_20250806_203749.txt` - 25 clean JTBDs
- `reddit_discussions_20250806_203749.csv` - 545 Reddit threads with JTBD mapping
- `cluster_reddit_discussions.py` - Clusters discussions (works but not optimal approach)

### Data Available
- 25 JTBDs extracted from real estate market analysis
- 545 Reddit discussions with scores, comments, full text
- Each discussion already mapped to its source JTBD
- Cohere embeddings of all discussions

## Next Steps for Fresh Session

1. **Implement OpportunityZoneAnalyzer class** that:
   - Loads the existing JTBD → Reddit mapping
   - Extracts pain dimensions from each Reddit thread using Claude
   - Calculates JTBD vectors based on aggregated pain scores
   - Discovers opportunity zones through JTBD clustering
   - Outputs structured JSON with traceable lineage

2. **Key Innovation**: Don't cluster Reddit posts - instead:
   - Use Reddit as evidence for JTBD pain dimensions
   - Cluster JTBDs based on shared pain patterns
   - Define opportunity zones where multiple JTBDs converge

3. **Deliverable**: A structured dataset showing:
   - Which opportunity zones exist
   - Which JTBDs each zone addresses
   - Supporting Reddit evidence for each zone
   - Extracted solution requirements
   - Prioritization metrics

## Key Code Snippets to Preserve

### Reddit Query Translation (from jobs_to_reddit.py)
```python
prompt = f"""Transform this Jobs-to-be-Done into Reddit search queries for real estate discussions.
JTBD: {jtbd}
Generate 8 SHORT search queries (2-5 words) that real Reddit users would type.
Focus on emotional language, specific scenarios, common abbreviations..."""
```

### Text Preparation for Embedding (from cluster_reddit_discussions.py)
```python
def prepare_texts_for_embedding(self, df: pd.DataFrame) -> List[str]:
    texts = []
    for _, row in df.iterrows():
        text_parts = [
            f"Title: {row['title']}",
            f"Context: {row['jtbd'][:100]}",
            f"Content: {row['selftext'][:500]}",
            f"Subreddit: r/{row['subreddit']}",
            f"Engagement: {row['score']} upvotes, {row['num_comments']} comments"
        ]
        texts.append(" | ".join(text_parts))
```

## Resume Point
In the next session, implement the OpportunityZoneAnalyzer that uses the existing JTBD→Reddit mapping to discover strategic opportunity zones through structured pain dimension analysis.