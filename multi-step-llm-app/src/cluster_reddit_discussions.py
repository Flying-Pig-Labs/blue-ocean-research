#!/usr/bin/env python3
"""
Cluster Reddit Discussions using Cohere Embeddings
Finds patterns in real user discussions from Reddit threads

This module:
1. Loads Reddit discussions from CSV
2. Embeds titles and content using Cohere
3. Clusters using HDBSCAN to find discussion patterns
4. Labels clusters with GPT-4 for interpretation
5. Generates insights about user pain points

Usage:
    python cluster_reddit_discussions.py
    python cluster_reddit_discussions.py --input reddit_discussions_20250806_203749.csv
    python cluster_reddit_discussions.py --min-cluster-size 10
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import hdbscan
import cohere
import openai
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AWS secrets if available
try:
    from src.utils.secrets_manager import load_aws_secrets
    load_aws_secrets(profile="mvp")
except ImportError:
    pass

console = Console()


class RedditClusterer:
    """Cluster Reddit discussions to find patterns"""
    
    def __init__(self):
        """Initialize API clients"""
        
        # Cohere for embeddings
        self.cohere_key = os.getenv("COHERE_API_KEY")
        if not self.cohere_key:
            console.print("[red]Error: COHERE_API_KEY not found[/red]")
            sys.exit(1)
        self.cohere_client = cohere.Client(self.cohere_key)
        
        # OpenAI for cluster labeling
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            console.print("[red]Error: OPENAI_API_KEY not found[/red]")
            sys.exit(1)
        openai.api_key = self.openai_key
    
    def load_reddit_data(self, csv_file: str) -> pd.DataFrame:
        """Load Reddit discussions from CSV"""
        
        console.print(f"[cyan]📖 Loading Reddit discussions from {csv_file}...[/cyan]")
        
        try:
            df = pd.read_csv(csv_file)
            console.print(f"[green]✅ Loaded {len(df)} Reddit discussions[/green]")
            
            # Show data overview
            console.print(f"[dim]Columns: {', '.join(df.columns)}[/dim]")
            console.print(f"[dim]Subreddits: {df['subreddit'].nunique()} unique[/dim]")
            console.print(f"[dim]Average score: {df['score'].mean():.1f}[/dim]")
            
            return df
            
        except FileNotFoundError:
            console.print(f"[red]Error: {csv_file} not found[/red]")
            sys.exit(1)
    
    def prepare_texts_for_embedding(self, df: pd.DataFrame) -> List[str]:
        """Prepare texts for embedding"""
        
        texts = []
        
        for _, row in df.iterrows():
            # Combine title, selftext, and metadata for rich embedding
            text_parts = []
            
            # Title is most important
            text_parts.append(f"Title: {row['title']}")
            
            # Add JTBD context
            if pd.notna(row.get('jtbd')):
                text_parts.append(f"Context: {row['jtbd'][:100]}")
            
            # Add post content if available
            if pd.notna(row.get('selftext')) and len(str(row['selftext'])) > 10:
                content = str(row['selftext'])[:500]  # Limit length
                text_parts.append(f"Content: {content}")
            
            # Add subreddit as context
            text_parts.append(f"Subreddit: r/{row['subreddit']}")
            
            # Add engagement metrics as signals
            text_parts.append(f"Engagement: {row['score']} upvotes, {row['num_comments']} comments")
            
            combined = " | ".join(text_parts)
            texts.append(combined)
        
        console.print(f"[green]✅ Prepared {len(texts)} texts for embedding[/green]")
        return texts
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed texts using Cohere"""
        
        console.print("[cyan]🔍 Creating embeddings with Cohere...[/cyan]")
        
        # Process in batches (Cohere has a limit)
        batch_size = 96
        all_embeddings = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Embedding texts...", total=len(texts))
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                
                try:
                    response = self.cohere_client.embed(
                        texts=batch,
                        model="embed-english-v3.0",
                        input_type="clustering"  # Optimized for clustering
                    )
                    
                    all_embeddings.extend(response.embeddings)
                    progress.advance(task, len(batch))
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Embedding failed for batch {i//batch_size}: {e}[/yellow]")
                    # Create zero embeddings for failed batch
                    all_embeddings.extend([[0] * 1024 for _ in batch])
                    progress.advance(task, len(batch))
        
        embeddings = np.array(all_embeddings)
        console.print(f"[green]✅ Created embeddings with shape {embeddings.shape}[/green]")
        
        return embeddings
    
    def cluster_embeddings(self, embeddings: np.ndarray, min_cluster_size: int = 10) -> np.ndarray:
        """Cluster embeddings using HDBSCAN"""
        
        console.print(f"[cyan]🧠 Clustering with HDBSCAN (min_size={min_cluster_size})...[/cyan]")
        
        # Normalize embeddings (L2 normalization makes euclidean distance equivalent to cosine)
        from sklearn.preprocessing import normalize
        embeddings_normalized = normalize(embeddings, norm='l2')
        
        # Cluster with HDBSCAN
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=3,
            metric='euclidean',  # On normalized vectors, this is equivalent to cosine
            cluster_selection_method='eom',
            cluster_selection_epsilon=0.5  # Help find more clusters
        )
        
        cluster_labels = clusterer.fit_predict(embeddings_normalized)
        
        # Statistics
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        console.print(f"[green]✅ Found {n_clusters} clusters ({n_noise} noise points)[/green]")
        
        # Calculate silhouette score if we have clusters
        if n_clusters >= 2:
            mask = cluster_labels != -1
            if mask.sum() > 1:
                score = silhouette_score(embeddings_normalized[mask], cluster_labels[mask])
                console.print(f"[cyan]📊 Silhouette score: {score:.3f}[/cyan]")
        
        return cluster_labels
    
    def label_cluster(self, df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
        """Use GPT-4 to label a cluster"""
        
        cluster_df = df[df['cluster'] == cluster_id]
        
        # Get top posts by score
        top_posts = cluster_df.nlargest(min(10, len(cluster_df)), 'score')
        
        # Prepare context for GPT
        posts_text = []
        for _, post in top_posts.iterrows():
            posts_text.append(f"- {post['title']} (r/{post['subreddit']}, {post['score']} upvotes)")
            if pd.notna(post.get('selftext')) and len(str(post['selftext'])) > 20:
                posts_text.append(f"  Content: {str(post['selftext'])[:200]}...")
        
        prompt = f"""Analyze these Reddit discussions and identify the common theme or pain point.

Posts in this cluster:
{chr(10).join(posts_text)}

Provide a JSON response with:
{{
    "theme": "Brief theme description (10-15 words)",
    "pain_point": "The core problem users are experiencing",
    "user_sentiment": "Overall emotional tone (frustrated/anxious/confused/seeking help/etc)",
    "common_scenario": "Typical situation these users are in",
    "potential_solution": "What would help these users"
}}"""
        
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to label cluster {cluster_id}: {e}[/yellow]")
            return {
                "theme": f"Cluster {cluster_id}",
                "pain_point": "Unable to identify",
                "user_sentiment": "Unknown",
                "common_scenario": "Various",
                "potential_solution": "Further analysis needed"
            }
    
    def analyze_clusters(self, df: pd.DataFrame, cluster_labels: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze all clusters"""
        
        # Add cluster labels to dataframe
        df['cluster'] = cluster_labels
        
        # Get unique clusters (excluding noise)
        unique_clusters = [c for c in set(cluster_labels) if c != -1]
        unique_clusters.sort()
        
        console.print(f"[cyan]🏷️ Labeling {len(unique_clusters)} clusters...[/cyan]")
        
        cluster_analysis = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing clusters...", total=len(unique_clusters))
            
            for cluster_id in unique_clusters:
                cluster_df = df[df['cluster'] == cluster_id]
                
                # Get cluster statistics
                stats = {
                    "cluster_id": cluster_id,
                    "size": len(cluster_df),
                    "avg_score": cluster_df['score'].mean(),
                    "total_comments": cluster_df['num_comments'].sum(),
                    "top_subreddits": cluster_df['subreddit'].value_counts().head(3).to_dict(),
                    "top_jtbds": cluster_df['jtbd'].value_counts().head(3).index.tolist() if 'jtbd' in cluster_df.columns else []
                }
                
                # Get semantic label
                label_info = self.label_cluster(df, cluster_id)
                stats.update(label_info)
                
                # Get sample posts
                top_posts = cluster_df.nlargest(3, 'score')[['title', 'score', 'subreddit']].to_dict('records')
                stats['sample_posts'] = top_posts
                
                cluster_analysis.append(stats)
                progress.advance(task)
        
        # Sort by size
        cluster_analysis.sort(key=lambda x: x['size'], reverse=True)
        
        return cluster_analysis
    
    def display_results(self, cluster_analysis: List[Dict[str, Any]], df: pd.DataFrame):
        """Display clustering results"""
        
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]REDDIT DISCUSSION CLUSTERS[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
        
        for i, cluster in enumerate(cluster_analysis[:10], 1):  # Show top 10 clusters
            # Create panel for each cluster
            content = f"""[yellow]Theme:[/yellow] {cluster['theme']}
[yellow]Pain Point:[/yellow] {cluster['pain_point']}
[yellow]User Sentiment:[/yellow] {cluster['user_sentiment']}
[yellow]Common Scenario:[/yellow] {cluster['common_scenario']}
[yellow]Potential Solution:[/yellow] {cluster['potential_solution']}

[dim]Size: {cluster['size']} posts | Avg Score: {cluster['avg_score']:.0f} | Total Comments: {cluster['total_comments']}[/dim]

[cyan]Top Subreddits:[/cyan]"""
            
            for sub, count in cluster['top_subreddits'].items():
                content += f"\n  • r/{sub}: {count} posts"
            
            if cluster['sample_posts']:
                content += "\n\n[cyan]Sample Posts:[/cyan]"
                for post in cluster['sample_posts'][:3]:
                    content += f"\n  • [{post['score']}↑] {post['title'][:60]}..."
            
            console.print(Panel(
                content,
                title=f"Cluster {i}: {cluster['theme'][:50]}",
                border_style="blue"
            ))
        
        # Summary statistics
        console.print(f"\n[yellow]Overall Statistics:[/yellow]")
        console.print(f"  • Total posts: {len(df)}")
        console.print(f"  • Posts in clusters: {len(df[df['cluster'] != -1])}")
        console.print(f"  • Noise points: {len(df[df['cluster'] == -1])}")
        console.print(f"  • Number of clusters: {len(cluster_analysis)}")
        
        # Top themes
        console.print(f"\n[yellow]Top Themes Identified:[/yellow]")
        for i, cluster in enumerate(cluster_analysis[:5], 1):
            console.print(f"  {i}. {cluster['theme']} ({cluster['size']} posts)")
    
    def save_results(self, df: pd.DataFrame, cluster_analysis: List[Dict[str, Any]], embeddings: np.ndarray):
        """Save clustering results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save clustered dataframe
        csv_file = f"reddit_clustered_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        console.print(f"[green]✅ Saved clustered data to {csv_file}[/green]")
        
        # Save cluster analysis
        json_file = f"reddit_cluster_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(cluster_analysis, f, indent=2, default=str)
        console.print(f"[green]✅ Saved cluster analysis to {json_file}[/green]")
        
        # Save to Excel with multiple sheets
        xlsx_file = f"reddit_cluster_report_{timestamp}.xlsx"
        with pd.ExcelWriter(xlsx_file, engine='openpyxl') as writer:
            # Clustered data
            df.to_excel(writer, sheet_name='All Posts', index=False)
            
            # Cluster summary if we have clusters
            if cluster_analysis:
                summary_df = pd.DataFrame(cluster_analysis)
                # Only include columns that exist
                summary_cols = []
                for col in ['cluster_id', 'size', 'theme', 'pain_point', 'user_sentiment', 'avg_score']:
                    if col in summary_df.columns:
                        summary_cols.append(col)
                if summary_cols:
                    summary_df[summary_cols].to_excel(writer, sheet_name='Cluster Summary', index=False)
                
                # Top posts per cluster
                for i, cluster in enumerate(cluster_analysis[:5]):  # Top 5 clusters
                    cluster_df = df[df['cluster'] == cluster['cluster_id']].nlargest(min(20, len(df[df['cluster'] == cluster['cluster_id']])), 'score')
                    if not cluster_df.empty:
                        cluster_df[['title', 'subreddit', 'score', 'num_comments', 'url']].to_excel(
                            writer, 
                            sheet_name=f"Cluster {i+1}",
                            index=False
                        )
        
        console.print(f"[green]✅ Saved detailed report to {xlsx_file}[/green]")
        
        # Save embeddings for future use
        np.save(f"reddit_embeddings_{timestamp}.npy", embeddings)
        console.print(f"[green]✅ Saved embeddings to reddit_embeddings_{timestamp}.npy[/green]")
        
        return csv_file, json_file, xlsx_file
    
    def run(self, input_file: str, min_cluster_size: int = 10):
        """Run the complete clustering pipeline"""
        
        console.print(Panel.fit(
            "[bold green]Reddit Discussion Clustering Pipeline[/bold green]\n"
            "Finding patterns in user discussions using Cohere embeddings",
            border_style="green"
        ))
        
        # Step 1: Load data
        console.print("\n[bold]Step 1: Loading Reddit data[/bold]")
        df = self.load_reddit_data(input_file)
        
        # Step 2: Prepare texts
        console.print("\n[bold]Step 2: Preparing texts for embedding[/bold]")
        texts = self.prepare_texts_for_embedding(df)
        
        # Step 3: Create embeddings
        console.print("\n[bold]Step 3: Creating embeddings[/bold]")
        embeddings = self.embed_texts(texts)
        
        # Step 4: Cluster
        console.print("\n[bold]Step 4: Clustering discussions[/bold]")
        cluster_labels = self.cluster_embeddings(embeddings, min_cluster_size)
        
        # Step 5: Analyze clusters
        console.print("\n[bold]Step 5: Analyzing clusters[/bold]")
        cluster_analysis = self.analyze_clusters(df, cluster_labels)
        
        # Step 6: Display results
        self.display_results(cluster_analysis, df)
        
        # Step 7: Save results
        console.print("\n[bold]Step 7: Saving results[/bold]")
        csv_file, json_file, xlsx_file = self.save_results(df, cluster_analysis, embeddings)
        
        console.print(f"\n[bold green]✅ Clustering complete![/bold green]")
        console.print(f"\n[cyan]Output files:[/cyan]")
        console.print(f"  • Clustered data: {csv_file}")
        console.print(f"  • Cluster analysis: {json_file}")
        console.print(f"  • Detailed report: {xlsx_file}")
        
        return df, cluster_analysis


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Cluster Reddit discussions using Cohere embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use most recent Reddit discussions file
  python cluster_reddit_discussions.py
  
  # Specify input file
  python cluster_reddit_discussions.py --input reddit_discussions_20250806.csv
  
  # Adjust cluster size
  python cluster_reddit_discussions.py --min-cluster-size 15
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        help="Input CSV file with Reddit discussions"
    )
    
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=10,
        help="Minimum cluster size for HDBSCAN (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Find input file
    if not args.input:
        # Look for most recent reddit_discussions file
        import glob
        files = glob.glob("reddit_discussions_*.csv")
        if files:
            args.input = max(files)
            console.print(f"[dim]Using most recent file: {args.input}[/dim]")
        else:
            console.print("[red]No Reddit discussions file found. Run jobs_to_reddit.py first.[/red]")
            sys.exit(1)
    
    # Run clustering
    clusterer = RedditClusterer()
    clusterer.run(args.input, args.min_cluster_size)


if __name__ == "__main__":
    main()