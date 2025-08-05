#!/usr/bin/env python3
"""
Quick fix for cluster_jtbd.py - Implements adaptive parameters to handle all data sizes.

Usage:
    python cluster_jtbd_fix.py pain_points.txt
"""

import os
import sys
import json
import numpy as np
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
import cohere
import openai
from hdbscan import HDBSCAN
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Load environment variables
load_dotenv()

# Import and load AWS secrets if available
try:
    from src.utils.secrets_manager import load_aws_secrets
    load_aws_secrets(profile="mvp")
except ImportError:
    pass

# Initialize Rich console
console = Console()


# Copy the original JTBDClusterer class and modify the cluster_embeddings method
class JTBDClusterer:
    """Fixed version with adaptive clustering."""

    def __init__(self):
        """Initialize API clients."""
        # Cohere setup
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        if not self.cohere_api_key:
            console.print("[red]Error: COHERE_API_KEY not found![/red]")
            sys.exit(1)

        try:
            self.cohere_client = cohere.Client(self.cohere_api_key)
        except Exception as e:
            console.print(f"[red]Error initializing Cohere client: {e}[/red]")
            sys.exit(1)

        # OpenAI setup
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            console.print("[red]Error: OPENAI_API_KEY not found![/red]")
            sys.exit(1)

        try:
            openai.api_key = self.openai_api_key
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        except Exception as e:
            console.print(f"[red]Error initializing OpenAI client: {e}[/red]")
            sys.exit(1)

    def load_texts(self, filepath: str):
        """Load pain points from text file (one per line)."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                texts = [line.strip() for line in f if line.strip()]
            console.print(
                f"[green]✅ Loaded {len(texts)} pain points from {filepath}[/green]"
            )
            return texts
        except FileNotFoundError:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            sys.exit(1)

    def embed_texts(self, texts):
        """Embed texts using Cohere Embed v3."""
        console.print("[cyan]🔍 Embedding texts with Cohere Embed v3...[/cyan]")

        batch_size = 96
        embeddings = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Embedding...", total=len(texts))

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]

                try:
                    response = self.cohere_client.embed(
                        texts=batch,
                        model="embed-english-v3.0",
                        input_type="search_document",
                    )
                    embeddings.extend(response.embeddings)
                    progress.update(task, advance=len(batch))

                except Exception as e:
                    console.print(f"[red]Error during embedding: {e}[/red]")
                    sys.exit(1)

        embeddings_array = np.array(embeddings)
        console.print(
            f"[green]✅ Created embeddings with shape {embeddings_array.shape}[/green]"
        )
        return embeddings_array

    def cluster_embeddings(self, embeddings):
        """Fixed clustering with adaptive parameters and fallback strategies."""
        console.print("[cyan]🧠 Clustering with adaptive strategy...[/cyan]")

        # Normalize embeddings for better clustering
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        n_samples = len(embeddings)
        
        # Adaptive parameters based on dataset size
        if n_samples < 30:
            param_sets = [
                {'min_cluster_size': 2, 'min_samples': 1},
                {'min_cluster_size': 3, 'min_samples': 1},
                {'min_cluster_size': 3, 'min_samples': 2}
            ]
        elif n_samples < 50:
            param_sets = [
                {'min_cluster_size': 3, 'min_samples': 1},
                {'min_cluster_size': 4, 'min_samples': 1},
                {'min_cluster_size': 5, 'min_samples': 2}
            ]
        elif n_samples < 100:
            param_sets = [
                {'min_cluster_size': 4, 'min_samples': 2},
                {'min_cluster_size': 5, 'min_samples': 2},
                {'min_cluster_size': 6, 'min_samples': 3}
            ]
        else:
            param_sets = [
                {'min_cluster_size': max(5, n_samples // 50), 'min_samples': 3},
                {'min_cluster_size': max(4, n_samples // 60), 'min_samples': 2},
                {'min_cluster_size': 5, 'min_samples': 1}
            ]
        
        best_labels = None
        best_n_clusters = 0
        best_params = None
        best_silhouette = -1
        
        # Try HDBSCAN with different parameters
        console.print("[cyan]Trying HDBSCAN parameters...[/cyan]")
        for params in param_sets:
            try:
                clusterer = HDBSCAN(
                    **params,
                    metric='euclidean',
                    cluster_selection_method='eom',
                    cluster_selection_epsilon=0.0,
                    prediction_data=True
                )
                
                labels = clusterer.fit_predict(embeddings_norm)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                n_noise = list(labels).count(-1)
                
                if n_clusters >= 2:
                    # Calculate silhouette score
                    mask = labels != -1
                    if sum(mask) > n_clusters:
                        try:
                            silhouette = silhouette_score(embeddings_norm[mask], labels[mask])
                            # Prefer solutions with more clusters and less noise
                            score = silhouette * (1 - n_noise/n_samples) * np.sqrt(n_clusters/10)
                            
                            if score > best_silhouette:
                                best_silhouette = score
                                best_labels = labels
                                best_n_clusters = n_clusters
                                best_params = params
                        except:
                            pass
            except Exception as e:
                console.print(f"[yellow]HDBSCAN failed with params {params}: {e}[/yellow]")
        
        # If HDBSCAN found clusters, use them
        if best_n_clusters >= 2:
            console.print(f"[green]✅ HDBSCAN found {best_n_clusters} clusters with params: {best_params}[/green]")
            labels = best_labels
            silhouette = best_silhouette
        else:
            # Fallback to Agglomerative Clustering
            console.print("[yellow]⚠️ HDBSCAN failed, using Agglomerative Clustering fallback[/yellow]")
            
            # Estimate optimal number of clusters
            if n_samples < 30:
                n_clusters = min(5, max(3, n_samples // 6))
            elif n_samples < 100:
                n_clusters = min(8, max(4, n_samples // 10))
            else:
                n_clusters = min(15, max(5, n_samples // 20))
            
            try:
                clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
                labels = clusterer.fit_predict(embeddings_norm)
                
                # Calculate silhouette score
                silhouette = silhouette_score(embeddings_norm, labels)
                console.print(f"[green]✅ Agglomerative Clustering created {n_clusters} clusters[/green]")
            except:
                # Final fallback: K-means
                console.print("[yellow]⚠️ Using K-means as final fallback[/yellow]")
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings_norm)
                try:
                    silhouette = silhouette_score(embeddings_norm, labels)
                except:
                    silhouette = -1

        # Calculate final metrics
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        console.print(
            f"[green]✅ Found {n_clusters} clusters ({n_noise} noise points)[/green]"
        )
        console.print(f"[blue]📊 Silhouette score: {silhouette:.3f}[/blue]")

        return labels, silhouette

    def label_clusters(self, clusters):
        """Use GPT-4o to label each cluster."""
        console.print("[cyan]🏷️  Labeling clusters with GPT-4o...[/cyan]")

        labeled_clusters = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Labeling clusters...", total=len(clusters))

            for cluster_id, texts in clusters.items():
                # Prepare sample texts for GPT-4o
                sample_size = min(10, len(texts))
                sample_texts = texts[:sample_size]

                prompt = f"""Analyze these customer pain points and provide:
1. A concise, descriptive label (3-5 words)
2. A brief summary of the common theme
3. The underlying job-to-be-done
4. Severity level (High/Medium/Low)

Pain points:
{chr(10).join([f"- {t}" for t in sample_texts])}

Respond in JSON format:
{{
    "label": "...",
    "summary": "...",
    "job_to_be_done": "When I [situation], I want to [motivation], so I can [outcome]",
    "severity": "High/Medium/Low"
}}"""

                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert at Jobs-to-be-Done analysis.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"},
                    )

                    cluster_info = json.loads(response.choices[0].message.content)
                    cluster_info["cluster_id"] = cluster_id
                    cluster_info["size"] = len(texts)
                    cluster_info["sample_texts"] = sample_texts
                    cluster_info["all_texts"] = texts

                    labeled_clusters[cluster_id] = cluster_info
                    progress.update(task, advance=1)

                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Failed to label cluster {cluster_id}: {e}[/yellow]"
                    )
                    labeled_clusters[cluster_id] = {
                        "cluster_id": cluster_id,
                        "label": f"Cluster {cluster_id}",
                        "summary": "Unable to generate summary",
                        "job_to_be_done": "Unable to extract JTBD",
                        "severity": "Unknown",
                        "size": len(texts),
                        "sample_texts": sample_texts,
                        "all_texts": texts,
                    }
                    progress.update(task, advance=1)

        return labeled_clusters

    def generate_opportunity_zones(self, labeled_clusters):
        """Generate up to 5 opportunity zones with importance percentages."""
        console.print("[cyan]🎯 Generating opportunity zones...[/cyan]")

        # Prepare cluster summaries for analysis
        cluster_summaries = []
        for cluster in labeled_clusters.values():
            cluster_summaries.append(
                {
                    "label": cluster["label"],
                    "summary": cluster["summary"],
                    "job_to_be_done": cluster["job_to_be_done"],
                    "severity": cluster["severity"],
                    "size": cluster["size"],
                }
            )

        prompt = f"""Based on these clustered pain points, identify up to 5 opportunity zones for product development.

Clusters:
{json.dumps(cluster_summaries, indent=2)}

For each opportunity zone:
1. Give it a strategic name
2. Describe the opportunity
3. List which clusters it addresses (by label)
4. Assign an importance percentage

The percentages must total exactly 100%.

Respond in JSON format:
{{
    "opportunity_zones": [
        {{
            "name": "Strategic name",
            "description": "What this opportunity addresses",
            "clusters_addressed": ["cluster label 1", "cluster label 2"],
            "importance_percentage": 30,
            "potential_impact": "High/Medium/Low",
            "implementation_complexity": "High/Medium/Low"
        }}
    ],
    "rationale": "Brief explanation of the prioritization"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a product strategy expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                response_format={"type": "json_object"},
            )

            opportunity_zones = json.loads(response.choices[0].message.content)

            # Validate percentages sum to 100
            total_percentage = sum(
                zone["importance_percentage"]
                for zone in opportunity_zones["opportunity_zones"]
            )
            if total_percentage != 100:
                console.print(
                    f"[yellow]Warning: Percentages sum to {total_percentage}%, adjusting...[/yellow]"
                )
                # Normalize to 100%
                for zone in opportunity_zones["opportunity_zones"]:
                    zone["importance_percentage"] = round(
                        zone["importance_percentage"] * 100 / total_percentage
                    )

            return opportunity_zones

        except Exception as e:
            console.print(f"[red]Error generating opportunity zones: {e}[/red]")
            return {
                "opportunity_zones": [],
                "rationale": "Error generating opportunity zones",
            }

    def display_results(self, labeled_clusters, opportunity_zones):
        """Display clustering results in a nice format."""
        # Display clusters
        console.print("\n[bold cyan]📊 Cluster Analysis Results[/bold cyan]\n")

        for cluster_id, info in labeled_clusters.items():
            console.print(
                Panel(
                    f"[bold]{info['label']}[/bold]\n\n"
                    f"Summary: {info['summary']}\n"
                    f"JTBD: {info['job_to_be_done']}\n"
                    f"Severity: {info['severity']}\n"
                    f"Size: {info['size']} pain points\n\n"
                    f"Sample pain points:\n"
                    + "\n".join([f"• {t}" for t in info["sample_texts"][:3]]),
                    title=f"Cluster {cluster_id}",
                    border_style="blue",
                )
            )

        # Display opportunity zones
        console.print("\n[bold green]🎯 Opportunity Zones[/bold green]\n")

        table = Table(title="Strategic Opportunity Zones")
        table.add_column("Zone", style="cyan", width=20)
        table.add_column("Importance", style="magenta", width=10)
        table.add_column("Impact", style="green", width=10)
        table.add_column("Complexity", style="yellow", width=10)
        table.add_column("Description", style="white", width=40)

        for zone in opportunity_zones["opportunity_zones"]:
            table.add_row(
                zone["name"],
                f"{zone['importance_percentage']}%",
                zone["potential_impact"],
                zone["implementation_complexity"],
                zone["description"],
            )

        console.print(table)
        console.print(f"\n[italic]Rationale: {opportunity_zones['rationale']}[/italic]")

    def save_results(
        self,
        labeled_clusters,
        opportunity_zones,
        output_file="opportunity_zones.json",
    ):
        """Save results to JSON file."""
        # Convert numpy types to Python types for JSON serialization
        import numpy as np
        
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        # Convert cluster IDs to strings and numpy types to Python types
        labeled_clusters_clean = {}
        for k, v in labeled_clusters.items():
            labeled_clusters_clean[str(k)] = convert_numpy(v)
        
        results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "n_clusters": len(labeled_clusters),
                "n_pain_points": sum(c["size"] for c in labeled_clusters.values()),
            },
            "clusters": labeled_clusters_clean,
            "opportunity_zones": convert_numpy(opportunity_zones),
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        console.print(f"\n[green]✅ Results saved to {output_file}[/green]")

    def run(self, input_file, output_file="opportunity_zones.json"):
        """Main execution flow for JTBD clustering."""
        console.print(
            Panel.fit(
                "[bold green]JTBD Clustering Analysis (Fixed)[/bold green]\n"
                "Using Cohere Embed v3 + Adaptive Clustering + GPT-4o",
                border_style="green",
            )
        )

        # Load texts
        texts = self.load_texts(input_file)

        # Embed texts
        embeddings = self.embed_texts(texts)

        # Cluster embeddings with adaptive strategy
        labels, silhouette = self.cluster_embeddings(embeddings)

        # Group texts by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            if label != -1:  # Skip noise points
                clusters[label].append(texts[i])

        # Label clusters
        labeled_clusters = self.label_clusters(dict(clusters))

        # Generate opportunity zones
        opportunity_zones = self.generate_opportunity_zones(labeled_clusters)

        # Display results
        self.display_results(labeled_clusters, opportunity_zones)

        # Save results
        self.save_results(labeled_clusters, opportunity_zones, output_file)

        # Print noise points if any
        noise_count = list(labels).count(-1)
        if noise_count > 0:
            console.print(
                f"\n[yellow]Note: {noise_count} pain points were classified as noise[/yellow]"
            )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fixed JTBD Clustering with adaptive parameters"
    )
    parser.add_argument("file", help="Path to pain points text file")
    parser.add_argument(
        "--output",
        type=str,
        default="opportunity_zones.json",
        help="Output JSON file (default: opportunity_zones.json)",
    )
    
    args = parser.parse_args()
    
    # Run clustering
    clusterer = JTBDClusterer()
    clusterer.run(args.file, args.output)


if __name__ == "__main__":
    main()