#!/usr/bin/env python3
"""
Jobs-to-be-Done to Reddit Pipeline - Stage 2 of 7

Purpose: Extracts Jobs-to-be-Done from analysis results and finds authentic Reddit discussions
         to validate market needs with real user experiences.

This module is a critical bridge between theoretical analysis (Stage 1) and opportunity
identification (Stage 3). It replaced the EXA-based jobs_researcher.py in Dec 2024 to
eliminate external dependencies and improve reliability.

Key Responsibilities:
1. Extract 20-30 JTBDs from analysis using Claude Sonnet
2. Translate JTBDs to authentic Reddit search queries
3. Search 10+ targeted subreddits for real discussions
4. Export timestamped results for downstream processing

Dependencies:
- anthropic: Claude API for JTBD extraction and query translation
- praw: Reddit's official Python API wrapper
- pandas: Data manipulation and CSV export
- rich: Terminal UI and progress tracking

Integration Points:
- Input: docs/analysis_results.md from research_analyzer.py (Stage 1)
- Output: data/jtbds_TIMESTAMP.txt and data/reddit_discussions_TIMESTAMP.csv
- Called by: run_pipeline.py orchestrator
- Feeds into: opportunity_zone_analyzer.py (Stage 3)

Performance:
- Execution time: 3-5 minutes
- API calls: ~50 (1 for JTBD extraction, 20-30 for query translation, 20-30 for Reddit)
- Reddit posts collected: 500-1000
- Cost: ~$0.50 in Claude API fees

Usage:
    python jobs_to_reddit.py                     # Use default analysis_results.md
    python jobs_to_reddit.py --input custom.md   # Custom input file
    python jobs_to_reddit.py --max-jtbds 10      # Limit JTBD count
    python jobs_to_reddit.py --max-posts 100     # Limit Reddit posts per JTBD
"""

import os
import sys
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import praw
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Note: AWS secrets should already be loaded by run_pipeline.py
# If running standalone, uncomment the following:
# try:
#     from src.utils.secrets_manager import load_aws_secrets
#     load_aws_secrets(profile="mvp")
# except ImportError:
#     pass

console = Console()


class JTBDRedditPipeline:
    """
    Orchestrates JTBD extraction and Reddit discussion discovery.

    This class manages the entire Stage 2 pipeline, coordinating between
    Claude API for intelligent extraction and PRAW for Reddit searching.
    It handles rate limiting, error recovery, and data formatting.

    Attributes:
        anthropic_client: Claude API client for JTBD operations
        reddit: PRAW Reddit instance for searching discussions

    Methods:
        extract_jtbds_from_analysis: Uses Claude to extract JTBDs from analysis
        translate_jtbd_to_reddit_queries: Converts JTBDs to search queries
        search_reddit_for_jtbd: Searches Reddit for relevant discussions
        run: Main orchestration method
    """

    def __init__(self):
        """
        Initialize API clients for Claude and Reddit.

        Sets up authenticated connections to both Anthropic Claude API and
        Reddit API. Handles missing credentials gracefully with clear error
        messages. Reddit connection failures are non-fatal (allows offline mode).

        Environment Variables Required:
            ANTHROPIC_API_KEY: Claude API key (mandatory)
            REDDIT_CLIENT_ID: Reddit app client ID (optional, has default)
            REDDIT_CLIENT_SECRET: Reddit app secret (optional, has default)
            REDDIT_USER_AGENT: Reddit user agent string (optional)

        Raises:
            SystemExit: If ANTHROPIC_API_KEY is missing
        """

        # Anthropic client for JTBD extraction and query translation
        # This is mandatory - without Claude, we can't extract JTBDs
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not found[/red]")
            sys.exit(1)

        self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)

        # Reddit client
        self.reddit = self._init_reddit()

    def _init_reddit(self):
        """
        Initialize Reddit connection using PRAW.

        Establishes authenticated connection to Reddit API using app credentials.
        Falls back to default Ocean Studio credentials if environment variables
        not set. Connection failures are non-fatal to allow offline development.

        Returns:
            praw.Reddit: Authenticated Reddit instance, or None if connection fails

        Note:
            Default credentials are read-only and rate-limited. For production,
            create your own Reddit app at https://www.reddit.com/prefs/apps
        """
        client_id = os.getenv("REDDIT_CLIENT_ID", "GGd87bgymw6r_8dZuJihLw")
        client_secret = os.getenv(
            "REDDIT_CLIENT_SECRET", "YSCmPQ5BXkV4_otAW_jXiFbrnCC5gA"
        )
        user_agent = os.getenv("REDDIT_USER_AGENT", "JTBD_Finder/1.0 by oceanstudio")

        try:
            reddit = praw.Reddit(
                client_id=client_id, client_secret=client_secret, user_agent=user_agent
            )
            # Test connection
            _ = reddit.user.me()
            console.print("[green]✅ Connected to Reddit API[/green]")
            return reddit
        except Exception as e:
            console.print(f"[yellow]⚠️ Reddit connection failed: {e}[/yellow]")
            console.print("[yellow]Will continue without Reddit search[/yellow]")
            return None

    def extract_jtbds_from_analysis(self, analysis_file: str) -> List[str]:
        """
        Extract Jobs-to-be-Done statements from analysis using Claude.

        Processes the analysis_results.md file to identify and extract 20-30
        specific JTBD statements that represent real customer needs. Uses
        Claude Sonnet for intelligent extraction with structured prompting.

        Args:
            analysis_file: Path to analysis results markdown file

        Returns:
            List[str]: 20-30 JTBD statements in standard format

        Raises:
            SystemExit: If file not found or Claude API fails

        JTBD Formats:
        1. "When I [situation], I want to [motivation], so I can [outcome]"
        2. "[Action verb] [object] without/while/before [constraint]"

        Example Output:
            ["Find affordable housing without sacrificing neighborhood quality",
             "When I relocate for work, I want to find housing quickly...",
             "Compare school districts before committing to a neighborhood"]
        """

        console.print(f"[cyan]📖 Loading analysis from {analysis_file}...[/cyan]")

        try:
            with open(analysis_file, "r") as f:
                analysis_content = f.read()
        except FileNotFoundError:
            console.print(f"[red]Error: {analysis_file} not found[/red]")
            sys.exit(1)

        prompt = f"""Based on this comprehensive market analysis, extract 20-30 specific Jobs-to-be-Done (JTBD) statements.

Each JTBD should follow one of these formats:
1. "When I [situation], I want to [motivation], so I can [expected outcome]"
2. "[Action verb] [object] without/while/before [constraint or context]"

Focus on extracting JTBDs that represent real customer needs from the pain points, personas, and verticals described.
Make them specific and actionable.

Analysis document:
{analysis_content}

Return ONLY a numbered list of JTBD statements, one per line. Nothing else."""

        console.print("[cyan]🤖 Extracting JTBDs with Claude...[/cyan]")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            jtbd_text = response.content[0].text.strip()

            # Parse the numbered list
            jtbds = []
            for line in jtbd_text.split("\n"):
                cleaned = line.strip()
                if cleaned and (cleaned[0].isdigit() or cleaned.startswith("-")):
                    # Remove numbering
                    if ". " in cleaned[:4]:
                        jtbd = cleaned.split(". ", 1)[1]
                    elif cleaned.startswith("- "):
                        jtbd = cleaned[2:]
                    else:
                        jtbd = cleaned

                    jtbd = jtbd.strip('"').strip("'").strip()
                    if len(jtbd) > 10:
                        jtbds.append(jtbd)

            console.print(f"[green]✅ Extracted {len(jtbds)} JTBDs[/green]")
            return jtbds

        except Exception as e:
            console.print(f"[red]Error extracting JTBDs: {e}[/red]")
            sys.exit(1)

    def extract_jtbds_from_analysis_content(self, analysis_content: str) -> List[str]:
        """
        Extract JTBDs directly from analysis content (helper to avoid re-reading file).
        
        Args:
            analysis_content: Raw analysis content string
            
        Returns:
            List[str]: 20-30 JTBD statements
        """
        console.print(f"[cyan]📖 Processing analysis content ({len(analysis_content)} chars)...[/cyan]")

        prompt = f"""Based on this comprehensive market analysis, extract 20-30 specific Jobs-to-be-Done (JTBD) statements.

Each JTBD should follow one of these formats:
1. "When I [situation], I want to [motivation], so I can [expected outcome]"
2. "[Action verb] [object] without/while/before [constraint or context]"

Focus on extracting JTBDs that represent real customer needs from the pain points, personas, and verticals described.
Make them specific and actionable.

Analysis document:
{analysis_content}

Return ONLY a numbered list of JTBD statements, one per line. Nothing else."""

        console.print("[cyan]🤖 Extracting JTBDs with Claude...[/cyan]")

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )

            jtbd_text = response.content[0].text.strip()

            # Parse the numbered list
            jtbds = []
            for line in jtbd_text.split("\n"):
                cleaned = line.strip()
                if cleaned and (cleaned[0].isdigit() or cleaned.startswith("-")):
                    # Remove numbering
                    if ". " in cleaned[:4]:
                        jtbd = cleaned.split(". ", 1)[1]
                    elif cleaned.startswith("- "):
                        jtbd = cleaned[2:]
                    else:
                        jtbd = cleaned

                    jtbd = jtbd.strip('"').strip("'").strip()
                    if len(jtbd) > 10:
                        jtbds.append(jtbd)

            console.print(f"[green]✅ Extracted {len(jtbds)} JTBDs[/green]")
            return jtbds

        except Exception as e:
            console.print(f"[red]Error extracting JTBDs: {e}[/red]")
            sys.exit(1)

    def discover_relevant_subreddits(self, analysis_content: str) -> List[str]:
        """
        Dynamically discover relevant subreddits based on the analysis content.
        
        Uses Claude to identify the top 10 subreddits where people would naturally
        discuss the pain points, challenges, and topics identified in the research.
        
        Args:
            analysis_content: Raw analysis content from research
            
        Returns:
            List[str]: List of 8-10 relevant subreddit names (without r/ prefix)
            
        Fallback:
            Returns hardcoded real estate subreddits if API fails
        """
        console.print("[cyan]🎯 Discovering relevant subreddits...[/cyan]")
        
        # Extract key context from analysis (first 2000 chars for efficiency)
        context_snippet = analysis_content[:2000]
        
        prompt = f"""You are a JSON generator specializing in Reddit communities. Based on the business analysis below, identify the TOP 10 subreddits where people would naturally discuss the underlying pain points, challenges, and dynamics described.

Analysis Context:
{context_snippet}

Requirements:
- Focus on subreddits where REAL USERS discuss problems related to this industry/domain
- Include both industry-specific and general communities (e.g., personal finance, productivity)
- Prioritize active communities with high engagement
- Use actual subreddit names (verify they exist)
- Return ONLY valid JSON - no explanations or additional text

Example JSON format you MUST return:
{{
    "subreddits": [
        "personalfinance",
        "SmallBusiness", 
        "entrepreneur",
        "investing",
        "technology",
        "productivity",
        "careerguidance",
        "consulting",
        "startups",
        "business"
    ]
}}

Return ONLY the JSON structure above with 10 relevant subreddit names. This is critical - no other text."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = response.content[0].text.strip()
            
            # Clean up response if wrapped in code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            import json
            subreddit_data = json.loads(response_text)
            subreddits = subreddit_data.get("subreddits", [])
            
            # Validate and clean subreddit names
            valid_subreddits = []
            for sub in subreddits[:10]:  # Max 10
                # Clean subreddit name (remove r/ prefix if present, special chars)
                clean_sub = str(sub).replace("r/", "").strip()
                if clean_sub and len(clean_sub) > 2 and len(clean_sub) < 25:
                    valid_subreddits.append(clean_sub)
            
            if len(valid_subreddits) >= 5:
                console.print(f"[green]✅ Discovered {len(valid_subreddits)} relevant subreddits[/green]")
                console.print(f"[dim]Subreddits: {', '.join(f'r/{sub}' for sub in valid_subreddits[:5])}...[/dim]")
                return valid_subreddits
            else:
                console.print(f"[yellow]⚠️ Only found {len(valid_subreddits)} valid subreddits, using fallback[/yellow]")
                raise ValueError("Insufficient valid subreddits")
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Subreddit discovery failed ({e}), using fallback[/yellow]")
            # Fallback to original hardcoded list
            return [
                "RealEstate",
                "FirstTimeHomeBuyer", 
                "realestateinvesting",
                "Mortgages",
                "personalfinance",
                "RealEstateAdvice",
                "realtors",
                "HousingMarket"
            ]

    def translate_jtbd_to_reddit_queries(self, jtbd: str) -> List[str]:
        """
        Translate a JTBD statement into authentic Reddit search queries.

        Converts formal JTBD statements into the casual language and search
        patterns typical of Reddit users. Generates 2-3 query variations
        to maximize relevant discussion discovery.

        Args:
            jtbd: Single JTBD statement to translate

        Returns:
            List[str]: 2-3 Reddit search queries

        Translation Strategy:
        - Remove formal language, use Reddit vernacular
        - Focus on pain points and frustrations
        - Include common Reddit phrases ("how do I", "anyone else", "tips for")
        - Target both questions and complaint formats

        Example:
            Input: "Find affordable housing without sacrificing quality"
            Output: ["affordable housing good neighborhood",
                    "how to find cheap rent safe area",
                    "budget apartment hunting tips"]
        """

        prompt = f"""Transform this Jobs-to-be-Done into Reddit search queries for real estate discussions.

JTBD: {jtbd}

Generate 8 SHORT search queries (2-5 words) that real Reddit users would type.
Focus on:
- Emotional language ("frustrated", "stressed", "help")
- Specific scenarios ("closing delayed", "two mortgages")
- Common abbreviations and casual language
- Real estate terminology

Examples of good queries:
- "closing delayed help"
- "bridge loan worth it"
- "sell before buying"
- "two mortgages stressed"

Return ONLY 8 queries, one per line. Keep them SHORT and authentic."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}],
            )

            queries_text = response.content[0].text.strip()
            queries = []

            for line in queries_text.split("\n"):
                cleaned = line.strip()
                if cleaned:
                    # Remove numbering
                    if cleaned[0].isdigit() and "." in cleaned[:3]:
                        cleaned = cleaned.split(".", 1)[1].strip()
                    cleaned = cleaned.lstrip("- •").strip()
                    if cleaned and len(cleaned) > 2:
                        queries.append(cleaned)

            return queries[:8]

        except Exception as e:
            console.print(f"[yellow]Warning: Query translation failed: {e}[/yellow]")
            # Simple fallback
            words = jtbd.lower().split()[:5]
            return [" ".join(words[i : i + 3]) for i in range(0, len(words) - 2, 2)][:3]

    def search_reddit_for_jtbd(
        self, jtbd: str, queries: List[str], target_subreddits: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Search Reddit for discussions matching JTBD using dynamic or fallback subreddits"""

        if not self.reddit:
            return []

        # Use provided subreddits or fallback to hardcoded list
        if not target_subreddits:
            target_subreddits = [
                "RealEstate",
                "FirstTimeHomeBuyer",
                "realestateinvesting", 
                "Mortgages",
                "personalfinance",
                "RealEstateAdvice",
                "realtors",
                "HousingMarket",
            ]

        results = []

        # Search each subreddit with top queries
        for subreddit_name in target_subreddits[:5]:  # Top 5 subreddits
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                for query in queries[:3]:  # Top 3 queries per subreddit
                    try:
                        for submission in subreddit.search(
                            query,
                            limit=2,  # 2 results per query
                            sort="relevance",
                            time_filter="year",
                        ):
                            results.append(
                                {
                                    "jtbd": jtbd,
                                    "query": query,
                                    "subreddit": subreddit_name,
                                    "title": submission.title,
                                    "url": f"https://reddit.com{submission.permalink}",
                                    "score": submission.score,
                                    "num_comments": submission.num_comments,
                                    "created_utc": datetime.fromtimestamp(
                                        submission.created_utc
                                    ),
                                    "selftext": submission.selftext[:500]
                                    if submission.selftext
                                    else "",
                                    "author": str(submission.author)
                                    if submission.author
                                    else "[deleted]",
                                }
                            )

                        time.sleep(0.2)  # Rate limiting

                    except Exception:
                        continue

            except Exception:
                continue

        return results

    def process_all_jtbds(self, jtbds: List[str], target_subreddits: List[str] = None) -> pd.DataFrame:
        """Process all JTBDs and find Reddit discussions using dynamic subreddits"""

        all_results = []

        console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        console.print(f"[bold cyan]PROCESSING {len(jtbds)} JOBS-TO-BE-DONE[/bold cyan]")
        console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing JTBDs...", total=len(jtbds))

            for i, jtbd in enumerate(jtbds, 1):
                progress.update(
                    task, description=f"[cyan]Processing JTBD {i}/{len(jtbds)}..."
                )

                # Translate to Reddit queries
                queries = self.translate_jtbd_to_reddit_queries(jtbd)

                # Search Reddit
                if self.reddit:
                    results = self.search_reddit_for_jtbd(jtbd, queries, target_subreddits)
                    all_results.extend(results)

                progress.advance(task)

                # Show progress
                if i % 5 == 0:
                    console.print(
                        f"[dim]Processed {i}/{len(jtbds)} JTBDs, found {len(all_results)} threads so far[/dim]"
                    )

        # Convert to DataFrame
        df = pd.DataFrame(all_results)

        if not df.empty:
            # Remove duplicates
            df = df.drop_duplicates(subset=["url"])
            # Sort by relevance
            df = df.sort_values(["score", "num_comments"], ascending=[False, False])

        return df

    def save_results(self, df: pd.DataFrame, jtbds: List[str]):
        """Save results to multiple formats"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JTBDs
        jtbd_file = f"data/jtbds_{timestamp}.txt"
        with open(jtbd_file, "w") as f:
            f.write("# Jobs-to-be-Done extracted from analysis\n\n")
            for i, jtbd in enumerate(jtbds, 1):
                f.write(f"{i}. {jtbd}\n")
        console.print(f"[green]✅ Saved {len(jtbds)} JTBDs to {jtbd_file}[/green]")

        if not df.empty:
            # Save Reddit results to CSV
            csv_file = f"data/reddit_discussions_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            console.print(
                f"[green]✅ Saved {len(df)} Reddit discussions to {csv_file}[/green]"
            )

            # Save to Excel with analysis
            xlsx_file = f"data/reddit_analysis_{timestamp}.xlsx"
            with pd.ExcelWriter(xlsx_file, engine="openpyxl") as writer:
                # All discussions
                df.to_excel(writer, sheet_name="All Discussions", index=False)

                # Top discussions per JTBD
                top_per_jtbd = (
                    df.groupby("jtbd")
                    .apply(
                        lambda x: x.nlargest(5, "score")[
                            ["title", "subreddit", "score", "url"]
                        ]
                    )
                    .reset_index(level=0)
                )
                top_per_jtbd.to_excel(writer, sheet_name="Top per JTBD", index=False)

                # Subreddit analysis
                subreddit_stats = (
                    df.groupby("subreddit")
                    .agg({"score": ["mean", "sum", "count"], "num_comments": "sum"})
                    .round(1)
                )
                subreddit_stats.to_excel(writer, sheet_name="Subreddit Stats")

            console.print(f"[green]✅ Saved analysis to {xlsx_file}[/green]")

        return jtbd_file, csv_file if not df.empty else None

    def print_summary(self, df: pd.DataFrame, jtbds: List[str]):
        """Print summary of results"""

        console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        console.print(f"[bold cyan]SUMMARY[/bold cyan]")
        console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")

        console.print(f"[green]JTBDs extracted:[/green] {len(jtbds)}")

        if not df.empty:
            console.print(f"[green]Reddit threads found:[/green] {len(df)}")
            console.print(
                f"[green]Unique subreddits:[/green] {df['subreddit'].nunique()}"
            )
            console.print(f"[green]Average score:[/green] {df['score'].mean():.1f}")
            console.print(f"[green]Total comments:[/green] {df['num_comments'].sum()}")

            # Top threads
            console.print(f"\n[yellow]Top 5 Most Relevant Threads:[/yellow]")
            for _, row in df.head(5).iterrows():
                console.print(
                    f"\nr/{row['subreddit']} - ↑{row['score']} 💬{row['num_comments']}"
                )
                console.print(
                    f"  {row['title'][:80]}{'...' if len(row['title']) > 80 else ''}"
                )
                console.print(f"  [dim]{row['url'][:60]}...[/dim]")

            # Top subreddits
            console.print(f"\n[yellow]Most Active Subreddits:[/yellow]")
            top_subs = df["subreddit"].value_counts().head(5)
            for sub, count in top_subs.items():
                console.print(f"  r/{sub}: {count} threads")
        else:
            console.print(
                "[yellow]No Reddit threads found (API may be unavailable)[/yellow]"
            )

    def run(self, input_file: str = "docs/analysis_results.md", max_jtbds: int = None):
        """Run the complete pipeline"""

        console.print(
            Panel.fit(
                "[bold green]Jobs-to-be-Done to Reddit Pipeline[/bold green]\n"
                "Extracting JTBDs and finding real user discussions",
                border_style="green",
            )
        )

        # Step 1: Read analysis file and discover relevant subreddits
        console.print("\n[bold]Step 1: Loading analysis and discovering relevant communities[/bold]")
        
        # Read analysis file once for both JTBD extraction and subreddit discovery
        try:
            with open(input_file, "r") as f:
                analysis_content = f.read()
        except FileNotFoundError:
            console.print(f"[red]Error: {input_file} not found[/red]")
            sys.exit(1)
        
        # Discover relevant subreddits based on analysis content
        target_subreddits = self.discover_relevant_subreddits(analysis_content)
        
        # Extract JTBDs using existing method (but pass content to avoid re-reading)
        jtbds = self.extract_jtbds_from_analysis_content(analysis_content)

        if max_jtbds:
            jtbds = jtbds[:max_jtbds]
            console.print(f"[dim]Limited to {max_jtbds} JTBDs as requested[/dim]")

        # Show sample JTBDs
        console.print("\n[cyan]Sample JTBDs:[/cyan]")
        for i, jtbd in enumerate(jtbds[:3], 1):
            console.print(f"  {i}. {jtbd[:80]}{'...' if len(jtbd) > 80 else ''}")
        if len(jtbds) > 3:
            console.print(f"  ... and {len(jtbds) - 3} more")

        # Step 2: Find Reddit discussions
        console.print("\n[bold]Step 2: Finding Reddit discussions[/bold]")
        df = self.process_all_jtbds(jtbds, target_subreddits)

        # Step 3: Save results
        console.print("\n[bold]Step 3: Saving results[/bold]")
        jtbd_file, reddit_file = self.save_results(df, jtbds)

        # Step 4: Print summary
        self.print_summary(df, jtbds)

        console.print(f"\n[bold green]✅ Pipeline complete![/bold green]")
        console.print(f"\n[cyan]Output files:[/cyan]")
        console.print(f"  • JTBDs: {jtbd_file}")
        if reddit_file:
            console.print(f"  • Reddit discussions: {reddit_file}")

        console.print(
            f"\n[cyan]💡 Next step: Analyze Reddit discussions for insights[/cyan]"
        )

        return jtbds, df


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="Extract JTBDs and find Reddit discussions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default analysis file
  python jobs_to_reddit.py
  
  # Custom input file
  python jobs_to_reddit.py --input my_analysis.md
  
  # Limit number of JTBDs
  python jobs_to_reddit.py --max-jtbds 10
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        default="docs/analysis_results.md",
        help="Input analysis file (default: docs/analysis_results.md)",
    )

    parser.add_argument(
        "--max-jtbds", type=int, help="Maximum number of JTBDs to process"
    )

    args = parser.parse_args()

    # Run pipeline
    pipeline = JTBDRedditPipeline()
    pipeline.run(args.input, args.max_jtbds)


if __name__ == "__main__":
    main()
