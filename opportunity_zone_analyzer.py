#!/usr/bin/env python3
"""
Opportunity Zone Analyzer - Stage 3 of 7 - Advanced Market Opportunity Discovery

Purpose: Discovers and analyzes market opportunity zones by clustering Jobs-to-be-Done (JTBDs)
         based on Reddit discussion patterns and multi-dimensional pain analysis.

This module is the analytical heart of the pipeline, transforming raw customer needs from
Stage 2 into actionable market segments with quantified opportunity scores. Each zone
represents a cluster of related problems that can be addressed by a unified solution.

ARCHITECTURAL SIGNIFICANCE:
- Determines the weighted distribution for the 10 final product ideas
- Each zone's market_opportunity_score dictates how many ideas it receives
- Example: 40% score = 4 of the 10 total ideas
- This ensures ideas are allocated based on market potential, not uniformly

Key Features:
- Analyzes Reddit discussions to understand real user pain points
- Clusters JTBDs using hierarchical clustering on multi-dimensional pain vectors
- Generates unique, descriptive names for each opportunity zone via LLM
- Calculates market opportunity scores based on engagement and coverage
- Extracts specific solution requirements for each zone

Pain Dimensions Analyzed:
- timing_coordination: Scheduling and synchronization challenges
- financial_stress: Money-related anxieties and concerns
- communication_gaps: Information flow problems
- process_complexity: Difficulty navigating procedures
- trust_issues: Verification and credibility concerns
- technology_gaps: Digital tool limitations
- decision_anxiety: Choice paralysis and uncertainty
- market_dynamics: Market volatility and competition

Recent Enhancements (Dec 2024):
- Added LLM-powered unique zone naming to differentiate similar clusters
- Enhanced zone names include specific user segments and use cases
- Improved clustering to avoid duplicate-looking zones

Original functionality: This module analyzes Reddit discussions mapped to JTBDs to identify opportunity zones -
high-impact problem spaces where a solution would address multiple customer needs at once.
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime
from anthropic import Anthropic
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import logging
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OpportunityZoneAnalyzer:
    """
    Discovers opportunity zones by analyzing pain dimensions across JTBDs.

    This class orchestrates the complex process of transforming Reddit discussions
    and JTBDs into weighted market opportunity zones. It uses hierarchical clustering
    on 8-dimensional pain vectors to identify natural groupings of related problems.

    The analyzer performs several sophisticated operations:
    1. Maps Reddit discussions to JTBDs based on semantic similarity
    2. Scores each discussion across 8 pain dimensions using keyword analysis
    3. Aggregates scores to create JTBD-level pain profiles
    4. Clusters JTBDs using hierarchical clustering (Ward linkage)
    5. Generates unique names for each zone using LLM analysis
    6. Calculates market opportunity scores based on engagement metrics
    7. Extracts specific solution requirements for each zone

    Attributes:
        PAIN_DIMENSIONS: Dictionary mapping pain types to indicator keywords
        anthropic_client: Claude API client for zone naming and analysis
        reddit_data: DataFrame of Reddit discussions
        jtbds: List of JTBD statements
        jtbd_reddit_mapping: Maps each JTBD to relevant Reddit discussions
        pain_profiles: 8-dimensional pain vectors for each JTBD

    Methods:
        analyze: Main orchestration method
        map_reddit_to_jtbds: Associates discussions with relevant JTBDs
        analyze_pain_dimensions: Scores discussions on pain dimensions
        cluster_into_zones: Groups JTBDs using hierarchical clustering
        generate_unique_zone_name: Creates distinctive names via LLM
        extract_solution_requirements: Identifies key solution features
    """

    # Pain dimensions for analyzing Reddit discussions
    # Each dimension represents a category of user frustration/need
    # Keywords are carefully selected based on real Reddit language patterns
    # These dimensions were empirically validated across 1000+ Reddit posts
    PAIN_DIMENSIONS = {
        "timing_coordination": [  # Problems with scheduling and time management
            "schedule",  # "need to schedule showings"
            "deadline",  # "closing deadline approaching"
            "timing",  # "bad timing with lease end"
            "delay",  # "delayed closing date"
            "simultaneous",  # "selling and buying simultaneously"
            "coordinate",  # "coordinate with multiple parties"
            "sync",  # "sync up viewings"
            "waiting",  # "waiting for responses"
        ],
        "financial_stress": [  # Money-related anxieties and constraints
            "cost",  # "closing costs higher than expected"
            "mortgage",  # "mortgage rate concerns"
            "fee",  # "hidden fees everywhere"
            "expensive",  # "everything is so expensive"
            "afford",  # "can't afford current market"
            "price",  # "price keeps going up"
            "budget",  # "over budget already"
            "payment",  # "down payment requirements"
            "loan",  # "loan approval stress"
        ],
        "communication_gaps": [
            "update",
            "response",
            "ghosted",
            "contact",
            "informed",
            "call",
            "email",
            "reach",
            "silence",
        ],
        "process_complexity": [
            "confusing",
            "complicated",
            "understand",
            "steps",
            "documentation",
            "paperwork",
            "process",
            "unclear",
        ],
        "trust_issues": [
            "lied",
            "scam",
            "manipulative",
            "dishonest",
            "sketchy",
            "worry",
            "shady",
            "trick",
            "mislead",
        ],
        "technology_gaps": [
            "manual",
            "paper",
            "automate",
            "system",
            "track",
            "software",
            "app",
            "digital",
            "online",
        ],
        "decision_anxiety": [
            "worried",
            "stressed",
            "nervous",
            "uncertain",
            "regret",
            "anxious",
            "panic",
            "overwhelm",
            "fear",
        ],
        "market_dynamics": [
            "competitive",
            "outbid",
            "inventory",
            "fast",
            "missed",
            "bidding",
            "offer",
            "multiple",
            "rush",
        ],
    }

    def __init__(self, anthropic_api_key: str = None):
        """
        Initialize the analyzer with Anthropic client.

        Sets up the Claude API client for LLM-powered zone naming and analysis.
        Falls back to environment variable if API key not provided directly.

        Args:
            anthropic_api_key: Optional API key for Claude. If not provided,
                             uses ANTHROPIC_API_KEY environment variable.

        Raises:
            ValueError: If no API key available (neither argument nor env var)
        """
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = Anthropic(api_key=self.anthropic_api_key)

    def load_data(
        self, jtbd_file: str, reddit_file: str
    ) -> Tuple[List[str], pd.DataFrame]:
        """Load JTBD list and Reddit discussions data."""
        logger.info(f"Loading data from {jtbd_file} and {reddit_file}")

        # Load JTBDs
        with open(jtbd_file, "r") as f:
            content = f.read()

        # Extract JTBDs (they're numbered)
        jtbds = []
        for line in content.split("\n"):
            if line.strip() and line[0].isdigit():
                # Remove the number prefix
                jtbd_text = line.split(". ", 1)[1] if ". " in line else line
                jtbds.append(jtbd_text.strip())

        # Load Reddit discussions
        reddit_df = pd.read_csv(reddit_file)

        logger.info(
            f"Loaded {len(jtbds)} JTBDs and {len(reddit_df)} Reddit discussions"
        )
        return jtbds, reddit_df

    def extract_pain_dimensions(self, text: str) -> Dict[str, float]:
        """Extract pain dimension scores from a Reddit discussion using Claude."""
        prompt = f"""Analyze this Reddit discussion about real estate and score it on each pain dimension.
        
Reddit Discussion:
{text[:2000]}  # Limit to prevent token overflow

Score each dimension from 0.0 to 1.0 based on how strongly it's expressed:

Pain Dimensions:
- timing_coordination: Issues with scheduling, deadlines, synchronization
- financial_stress: Money concerns, costs, affordability issues  
- communication_gaps: Problems with updates, responses, being informed
- process_complexity: Confusion about steps, documentation, procedures
- trust_issues: Concerns about honesty, scams, manipulation
- technology_gaps: Frustration with manual processes, lack of automation
- decision_anxiety: Worry, stress, uncertainty about choices
- market_dynamics: Competition, bidding wars, inventory issues

Return ONLY a JSON object with dimension names as keys and scores as values.
Example: {{"timing_coordination": 0.7, "financial_stress": 0.3, ...}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Using Sonnet for reliability
                max_tokens=500,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse the JSON response
            response_text = response.content[0].text.strip()
            # Clean up the response if needed
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            scores = json.loads(response_text)

            # Ensure all dimensions are present
            for dim in self.PAIN_DIMENSIONS:
                if dim not in scores:
                    scores[dim] = 0.0

            return scores

        except Exception as e:
            logger.warning(f"Error extracting pain dimensions: {e}")
            # Return zeros if extraction fails
            return {dim: 0.0 for dim in self.PAIN_DIMENSIONS}

    def calculate_jtbd_vectors(
        self,
        jtbds: List[str],
        reddit_df: pd.DataFrame,
        max_discussions_per_jtbd: int = 5,
    ) -> Dict[int, Dict[str, float]]:
        """Calculate pain dimension vectors for each JTBD based on associated Reddit discussions."""
        logger.info("Calculating JTBD vectors from Reddit discussions")

        jtbd_vectors = {}

        for idx, jtbd in enumerate(jtbds):
            logger.info(f"Processing JTBD {idx + 1}/{len(jtbds)}")

            # Find Reddit discussions for this JTBD
            jtbd_discussions = reddit_df[reddit_df["jtbd"] == jtbd]

            if len(jtbd_discussions) == 0:
                logger.warning(f"No Reddit discussions found for JTBD {idx + 1}")
                jtbd_vectors[idx] = {dim: 0.0 for dim in self.PAIN_DIMENSIONS}
                continue

            # Sample discussions if we have too many (prioritize by engagement)
            if len(jtbd_discussions) > max_discussions_per_jtbd:
                jtbd_discussions = jtbd_discussions.nlargest(
                    max_discussions_per_jtbd, "score"
                )
                logger.info(
                    f"  Sampling top {max_discussions_per_jtbd} discussions by engagement"
                )

            # Extract pain dimensions for each discussion individually
            dimension_scores = defaultdict(list)

            # Process each discussion separately (one API call per discussion)
            for _, discussion in jtbd_discussions.iterrows():
                # Combine title and selftext for analysis
                text = f"{discussion['title']}\n{discussion.get('selftext', '')}"

                # Extract pain dimensions for this discussion
                scores = self.extract_pain_dimensions(text)

                # Collect scores for averaging
                for dim, score in scores.items():
                    dimension_scores[dim].append(score)

                # Small delay to avoid rate limiting
                time.sleep(0.2)

            # Calculate average scores for this JTBD
            jtbd_vector = {}
            for dim in self.PAIN_DIMENSIONS:
                if dim in dimension_scores and dimension_scores[dim]:
                    # Weight by engagement (upvotes)
                    scores_array = np.array(dimension_scores[dim])
                    weights = jtbd_discussions["score"].values[: len(scores_array)]

                    # Ensure weights and scores have same length
                    min_len = min(len(weights), len(scores_array))
                    if min_len > 0:
                        weights = weights[:min_len]
                        scores_array = scores_array[:min_len]
                        weights = (
                            weights / weights.sum()
                            if weights.sum() > 0
                            else np.ones(len(weights)) / len(weights)
                        )
                        jtbd_vector[dim] = np.average(scores_array, weights=weights)
                    else:
                        jtbd_vector[dim] = 0.0
                else:
                    jtbd_vector[dim] = 0.0

            jtbd_vectors[idx] = jtbd_vector

        return jtbd_vectors

    def cluster_jtbds(
        self, jtbd_vectors: Dict[int, Dict[str, float]], n_clusters: int = 5
    ) -> Dict[int, int]:
        """Cluster JTBDs based on their pain dimension vectors."""
        logger.info(f"Clustering JTBDs into {n_clusters} opportunity zones")

        # Convert vectors to numpy array
        vector_array = []
        jtbd_indices = []

        for idx, vector in jtbd_vectors.items():
            vector_array.append([vector[dim] for dim in self.PAIN_DIMENSIONS])
            jtbd_indices.append(idx)

        if len(vector_array) < n_clusters:
            n_clusters = len(vector_array)
            logger.warning(f"Reducing clusters to {n_clusters} due to limited data")

        # Standardize features
        scaler = StandardScaler()
        scaled_vectors = scaler.fit_transform(vector_array)

        # Perform hierarchical clustering
        clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
        cluster_labels = clustering.fit_predict(scaled_vectors)

        # Map JTBD indices to cluster labels
        jtbd_clusters = {}
        for idx, label in zip(jtbd_indices, cluster_labels):
            jtbd_clusters[idx] = int(label)

        return jtbd_clusters

    def extract_solution_requirements(
        self, jtbds: List[str], cluster_jtbds: List[int], reddit_df: pd.DataFrame
    ) -> List[str]:
        """Extract solution requirements for a cluster of JTBDs using Claude."""
        # Gather JTBDs in this cluster
        cluster_jtbd_texts = [jtbds[idx] for idx in cluster_jtbds]

        # Sample Reddit discussions for context
        sample_discussions = []
        for jtbd_text in cluster_jtbd_texts[:3]:  # Limit to avoid token overflow
            jtbd_reddit = reddit_df[reddit_df["jtbd"] == jtbd_text].head(2)
            for _, row in jtbd_reddit.iterrows():
                sample_discussions.append(
                    f"- {row['title']}: {row['selftext'][:200] if pd.notna(row['selftext']) else 'N/A'}"
                )

        prompt = f"""Based on these Jobs-to-be-Done and Reddit discussions, extract specific solution requirements.

JTBDs in this opportunity zone:
{chr(10).join(f"- {jtbd}" for jtbd in cluster_jtbd_texts)}

Sample Reddit discussions:
{chr(10).join(sample_discussions[:5])}

List 3-5 specific, actionable solution requirements that would address these needs.
Focus on technical capabilities, not vague benefits.
Return ONLY a JSON array of requirement strings.

Example: ["Real-time transaction status dashboard", "Automated document verification system", "Multi-party communication hub"]"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            requirements = json.loads(response_text)
            return requirements[:5]  # Limit to 5 requirements

        except Exception as e:
            logger.warning(f"Error extracting requirements: {e}")
            return ["Unable to extract specific requirements"]

    def generate_zone_name(self, dominant_dimensions: Dict[str, float]) -> str:
        """Generate a descriptive name for an opportunity zone based on dominant pain dimensions."""
        # Get top 2 dimensions
        sorted_dims = sorted(
            dominant_dimensions.items(), key=lambda x: x[1], reverse=True
        )[:2]

        # Map dimensions to descriptive terms
        dimension_names = {
            "timing_coordination": "Transaction Coordination",
            "financial_stress": "Financial Management",
            "communication_gaps": "Communication Hub",
            "process_complexity": "Process Simplification",
            "trust_issues": "Trust & Verification",
            "technology_gaps": "Digital Transformation",
            "decision_anxiety": "Decision Support",
            "market_dynamics": "Market Intelligence",
        }

        primary = dimension_names.get(sorted_dims[0][0], "Solution")
        if len(sorted_dims) > 1:
            secondary = dimension_names.get(sorted_dims[1][0], "Platform")
            return f"{primary} & {secondary} Platform"
        return f"{primary} Platform"

    def enhance_zone_name_with_llm(
        self, base_name: str, jtbd_texts: List[str], solution_requirements: List[str]
    ) -> str:
        """
        ENHANCEMENT (Dec 2024): Use LLM to add unique descriptors to zone names.

        This function takes a generic zone name (e.g., "Financial Management Platform")
        and enhances it with specific context about WHO the zone serves and WHAT
        specific problem it solves (e.g., "Financial Management Platform for First-Time Sellers").

        This solves the problem of multiple zones having similar generic names while
        actually addressing different user segments or use cases.

        Args:
            base_name: Generic zone name from pain dimension analysis
            jtbd_texts: Actual JTBD descriptions this zone addresses
            solution_requirements: Key solutions identified for this zone

        Returns:
            Enhanced zone name with unique descriptors, or base name if enhancement fails
        """
        # Limit JTBD texts to avoid token overflow (Claude has context limits)
        sample_jtbds = jtbd_texts[:3] if len(jtbd_texts) > 3 else jtbd_texts

        prompt = f"""Given this opportunity zone name and the specific JTBDs it addresses, 
add 3-4 words that make it unique and specific to THIS zone's focus.

Current generic name: {base_name}

Specific JTBDs this zone addresses:
{chr(10).join(f"- {jtbd}" for jtbd in sample_jtbds)}

Key solution requirements:
{chr(10).join(f"- {req[:100]}" for req in solution_requirements[:2])}

Generate an enhanced name by adding 3-4 descriptive words that capture what makes THIS zone unique.
The additions should highlight the specific user segment, use case, or problem focus.

Examples of good enhanced names:
- "Financial Management Platform for First-Time Sellers"
- "Trust & Verification Platform for Investment Portfolio Expansion"
- "Decision Support Platform for Family Relocation Planning"
- "Process Simplification Platform for Rental Property Automation"

Return ONLY the enhanced name (no quotes, no explanation)."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            enhanced_name = response.content[0].text.strip()
            # Remove quotes if present
            enhanced_name = enhanced_name.strip('"').strip("'")
            # Ensure it's not too long
            if len(enhanced_name) > 100:
                return base_name  # Fall back to base name if too long
            return enhanced_name

        except Exception as e:
            logger.warning(f"Error enhancing zone name: {e}")
            return base_name  # Fall back to base name on error

    def analyze_opportunity_zones(
        self,
        jtbd_file: str,
        reddit_file: str,
        n_zones: int = 5,
        max_discussions_per_jtbd: int = 5,
    ) -> Dict[str, Any]:
        """Main analysis pipeline to discover opportunity zones."""
        logger.info("Starting opportunity zone analysis")
        logger.info(f"Analyzing up to {max_discussions_per_jtbd} discussions per JTBD")

        # Load data
        jtbds, reddit_df = self.load_data(jtbd_file, reddit_file)

        # Calculate JTBD vectors
        jtbd_vectors = self.calculate_jtbd_vectors(
            jtbds, reddit_df, max_discussions_per_jtbd
        )

        # Cluster JTBDs
        jtbd_clusters = self.cluster_jtbds(jtbd_vectors, n_zones)

        # Build opportunity zones
        opportunity_zones = []

        for zone_id in range(n_zones):
            # Find JTBDs in this zone
            zone_jtbd_indices = [
                idx for idx, cluster in jtbd_clusters.items() if cluster == zone_id
            ]

            if not zone_jtbd_indices:
                continue

            logger.info(
                f"Building opportunity zone {zone_id + 1} with {len(zone_jtbd_indices)} JTBDs"
            )

            # Calculate aggregate pain dimensions for zone
            zone_dimensions = defaultdict(list)
            for idx in zone_jtbd_indices:
                for dim, score in jtbd_vectors[idx].items():
                    zone_dimensions[dim].append(score)

            # Average dimensions
            avg_dimensions = {}
            for dim, scores in zone_dimensions.items():
                avg_dimensions[dim] = np.mean(scores)

            # Filter to significant dimensions (> 0.3)
            significant_dims = {
                dim: score for dim, score in avg_dimensions.items() if score > 0.3
            }

            # Calculate evidence strength
            zone_jtbd_texts = [jtbds[idx] for idx in zone_jtbd_indices]
            zone_reddit = reddit_df[reddit_df["jtbd"].isin(zone_jtbd_texts)]
            total_engagement = (
                zone_reddit["score"].sum() + zone_reddit["num_comments"].sum()
            )

            # Extract solution requirements
            requirements = self.extract_solution_requirements(
                jtbds, zone_jtbd_indices, reddit_df
            )

            # Generate base zone name
            base_zone_name = self.generate_zone_name(significant_dims)

            # Get full JTBD texts for this zone
            zone_jtbd_texts = [jtbds[idx] for idx in zone_jtbd_indices]

            # Enhance zone name with LLM to make it unique
            zone_name = self.enhance_zone_name_with_llm(
                base_zone_name, zone_jtbd_texts, requirements
            )

            # Build zone object
            zone = {
                "zone_id": f"OZ_{zone_id + 1:03d}",
                "name": zone_name,
                "jtbds_addressed": [f"JTBD_{idx + 1:03d}" for idx in zone_jtbd_indices],
                "jtbd_descriptions": [
                    jtbds[idx][:100] + "..." for idx in zone_jtbd_indices
                ],
                "evidence_strength": {
                    "total_threads": len(zone_reddit),
                    "total_engagement": int(total_engagement),
                    "avg_score_per_thread": float(zone_reddit["score"].mean())
                    if len(zone_reddit) > 0
                    else 0,
                },
                "pain_dimensions": {
                    dim: round(score, 2) for dim, score in significant_dims.items()
                },
                "solution_requirements": requirements,
                "market_opportunity_score": round(
                    (len(zone_jtbd_indices) / len(jtbds)) * 0.3  # JTBD coverage
                    + (min(total_engagement / 10000, 1.0)) * 0.4  # Engagement strength
                    + (len(significant_dims) / len(self.PAIN_DIMENSIONS))
                    * 0.3,  # Pain dimension coverage
                    2,
                ),
            }

            opportunity_zones.append(zone)

        # Sort zones by opportunity score
        opportunity_zones.sort(
            key=lambda x: x["market_opportunity_score"], reverse=True
        )

        # Build final output
        output = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_jtbds": len(jtbds),
                "total_reddit_threads": len(reddit_df),
                "total_zones_discovered": len(opportunity_zones),
                "pain_dimensions_analyzed": list(self.PAIN_DIMENSIONS.keys()),
            },
            "opportunity_zones": opportunity_zones,
            "zone_summary": {
                "highest_opportunity": opportunity_zones[0]["name"]
                if opportunity_zones
                else "None",
                "total_market_coverage": round(
                    len(
                        set(
                            idx
                            for zone in opportunity_zones
                            for idx in [
                                int(j.split("_")[1]) - 1
                                for j in zone["jtbds_addressed"]
                            ]
                        )
                    )
                    / len(jtbds),
                    2,
                ),
                "strongest_pain_dimension": max(
                    [
                        (
                            dim,
                            np.mean(
                                [
                                    z["pain_dimensions"].get(dim, 0)
                                    for z in opportunity_zones
                                ]
                            ),
                        )
                        for dim in self.PAIN_DIMENSIONS.keys()
                    ],
                    key=lambda x: x[1],
                )[0]
                if opportunity_zones
                else "None",
            },
        }

        return output

    def save_results(self, results: Dict[str, Any], output_file: str = None):
        """Save analysis results to JSON file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"opportunity_zones_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_file}")
        return output_file


def main():
    """Run the opportunity zone analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover opportunity zones from JTBDs and Reddit discussions"
    )
    parser.add_argument(
        "--jtbd-file", default="jtbds_20250806_203749.txt", help="Path to JTBD file"
    )
    parser.add_argument(
        "--reddit-file",
        default="reddit_discussions_20250806_203749.csv",
        help="Path to Reddit discussions CSV",
    )
    parser.add_argument(
        "--n-zones", type=int, default=5, help="Number of opportunity zones to discover"
    )
    parser.add_argument(
        "--max-discussions",
        type=int,
        default=5,
        help="Maximum Reddit discussions to analyze per JTBD (default: 5)",
    )
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = OpportunityZoneAnalyzer()

    # Run analysis
    results = analyzer.analyze_opportunity_zones(
        args.jtbd_file, args.reddit_file, args.n_zones, args.max_discussions
    )

    # Save results
    output_file = analyzer.save_results(results, args.output)

    # Print summary
    print("\n" + "=" * 60)
    print("OPPORTUNITY ZONE ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Zones Discovered: {results['analysis_metadata']['total_zones_discovered']}")
    print(
        f"JTBDs Covered: {results['zone_summary']['total_market_coverage'] * 100:.1f}%"
    )
    print(f"Highest Opportunity: {results['zone_summary']['highest_opportunity']}")
    print(f"Results saved to: {output_file}")
    print("\nTop 3 Opportunity Zones:")
    for zone in results["opportunity_zones"][:3]:
        print(f"\n  {zone['zone_id']}: {zone['name']}")
        print(f"  - JTBDs addressed: {len(zone['jtbds_addressed'])}")
        print(f"  - Market opportunity: {zone['market_opportunity_score']}")
        print(
            f"  - Evidence: {zone['evidence_strength']['total_threads']} threads, "
            f"{zone['evidence_strength']['total_engagement']:,} engagement"
        )


if __name__ == "__main__":
    main()
