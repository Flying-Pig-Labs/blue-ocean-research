#!/usr/bin/env python3
"""
Enhanced JTBD Clustering Script with Improved HDBSCAN Parameters.

This enhanced version addresses the common issue of HDBSCAN classifying all
points as noise by implementing:
- Dynamic parameter tuning based on data characteristics
- Multiple clustering strategies with fallback options
- Visualization of embedding space and clusters
- Detailed diagnostics and debugging information
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import numpy as np
from dotenv import load_dotenv
import cohere
import openai
from hdbscan import HDBSCAN
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import warnings
warnings.filterwarnings('ignore')

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


class EnhancedJTBDClusterer:
    """Enhanced clusterer with improved HDBSCAN parameters and fallback strategies."""

    def __init__(self, debug: bool = False):
        """Initialize with debug mode option."""
        self.debug = debug
        
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

    def extract_pain_points(self, filepath: str) -> List[str]:
        """Extract individual pain points from hierarchical text file."""
        console.print("[cyan]📄 Extracting pain points from file...[/cyan]")
        
        pain_points = []
        current_category = ""
        
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("====") or line.startswith("CUSTOMER PAIN"):
                    continue
                
                # Check if it's a main category (numbered)
                if line[0].isdigit() and "." in line:
                    current_category = line.split(".", 1)[1].strip()
                    if current_category:
                        pain_points.append(current_category)
                
                # Check if it's a sub-point (starts with -)
                elif line.startswith("-"):
                    sub_point = line[1:].strip()
                    if sub_point:
                        # Combine with category for context
                        if current_category:
                            pain_points.append(f"{current_category}: {sub_point}")
                        else:
                            pain_points.append(sub_point)
        
        console.print(f"[green]✅ Extracted {len(pain_points)} individual pain points[/green]")
        
        if self.debug:
            console.print("\n[yellow]Sample pain points:[/yellow]")
            for i, pp in enumerate(pain_points[:5]):
                console.print(f"  {i+1}. {pp}")
        
        return pain_points

    def embed_texts(self, texts: List[str]) -> np.ndarray:
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
        
        # Normalize embeddings for better clustering
        embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        
        return embeddings_norm

    def analyze_embedding_space(self, embeddings: np.ndarray) -> Dict:
        """Analyze the embedding space to determine optimal clustering parameters."""
        console.print("[cyan]📊 Analyzing embedding space...[/cyan]")
        
        # Calculate pairwise distances
        distances = pairwise_distances(embeddings, metric='euclidean')
        
        # Get distance statistics
        np.fill_diagonal(distances, np.inf)  # Ignore self-distances
        min_distances = np.min(distances, axis=1)
        
        stats = {
            'n_samples': len(embeddings),
            'avg_min_distance': np.mean(min_distances),
            'std_min_distance': np.std(min_distances),
            'median_min_distance': np.median(min_distances),
            'percentile_5': np.percentile(min_distances, 5),
            'percentile_95': np.percentile(min_distances, 95)
        }
        
        if self.debug:
            console.print("\n[yellow]Embedding space statistics:[/yellow]")
            for key, value in stats.items():
                console.print(f"  {key}: {value:.4f}")
        
        return stats

    def tune_hdbscan_parameters(self, embeddings: np.ndarray, stats: Dict) -> Dict:
        """Dynamically tune HDBSCAN parameters based on data characteristics."""
        n_samples = stats['n_samples']
        
        # Start with very small min_cluster_size for small datasets
        if n_samples < 50:
            min_cluster_sizes = [2, 3, 4]
        elif n_samples < 100:
            min_cluster_sizes = [3, 4, 5]
        else:
            min_cluster_sizes = [5, 8, 10, 15]
        
        # Adjust min_samples based on density
        min_samples_options = [1, 2, 3]
        
        # Try different epsilon values based on distance statistics
        epsilon_options = [
            0,  # Let HDBSCAN decide
            stats['percentile_5'],
            stats['median_min_distance'] * 0.5,
            stats['median_min_distance']
        ]
        
        best_params = None
        best_score = -1
        best_n_clusters = 0
        
        console.print("[cyan]🔧 Tuning HDBSCAN parameters...[/cyan]")
        
        for min_cluster_size in min_cluster_sizes:
            for min_samples in min_samples_options:
                if min_samples > min_cluster_size:
                    continue
                    
                for epsilon in epsilon_options:
                    clusterer = HDBSCAN(
                        min_cluster_size=min_cluster_size,
                        min_samples=min_samples,
                        metric='euclidean',
                        cluster_selection_epsilon=epsilon,
                        cluster_selection_method='eom',
                        prediction_data=True
                    )
                    
                    labels = clusterer.fit_predict(embeddings)
                    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    n_noise = list(labels).count(-1)
                    
                    if n_clusters >= 2:
                        # Calculate silhouette score
                        mask = labels != -1
                        if sum(mask) > n_clusters:
                            try:
                                score = silhouette_score(embeddings[mask], labels[mask])
                                # Prefer solutions with more clusters and less noise
                                adjusted_score = score * (1 - n_noise/n_samples) * np.sqrt(n_clusters/10)
                                
                                if adjusted_score > best_score:
                                    best_score = adjusted_score
                                    best_params = {
                                        'min_cluster_size': min_cluster_size,
                                        'min_samples': min_samples,
                                        'cluster_selection_epsilon': epsilon,
                                        'n_clusters': n_clusters,
                                        'n_noise': n_noise,
                                        'silhouette_score': score
                                    }
                                    best_n_clusters = n_clusters
                            except:
                                pass
        
        if best_params:
            console.print(f"[green]✅ Found optimal parameters: {best_n_clusters} clusters[/green]")
            if self.debug:
                console.print(f"[yellow]Best parameters: {best_params}[/yellow]")
        else:
            console.print("[yellow]⚠️ No good HDBSCAN parameters found, will use fallback[/yellow]")
        
        return best_params

    def cluster_with_fallback(self, embeddings: np.ndarray, texts: List[str]) -> Tuple[np.ndarray, float, str]:
        """Cluster embeddings with multiple strategies and fallbacks."""
        console.print("[cyan]🧠 Clustering embeddings...[/cyan]")
        
        # First, analyze the embedding space
        stats = self.analyze_embedding_space(embeddings)
        
        # Try HDBSCAN with tuned parameters
        best_params = self.tune_hdbscan_parameters(embeddings, stats)
        
        if best_params and best_params['n_clusters'] >= 3:
            # Use the best HDBSCAN parameters
            clusterer = HDBSCAN(
                min_cluster_size=best_params['min_cluster_size'],
                min_samples=best_params['min_samples'],
                metric='euclidean',
                cluster_selection_epsilon=best_params['cluster_selection_epsilon'],
                cluster_selection_method='eom'
            )
            labels = clusterer.fit_predict(embeddings)
            method = "HDBSCAN (tuned)"
            silhouette = best_params['silhouette_score']
        else:
            # Fallback to K-means with elbow method
            console.print("[yellow]📊 Using K-means fallback clustering...[/yellow]")
            
            # Determine optimal k using elbow method
            max_k = min(15, len(embeddings) // 3)
            inertias = []
            silhouettes = []
            
            for k in range(2, max_k + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
                inertias.append(kmeans.inertia_)
                
                try:
                    sil_score = silhouette_score(embeddings, labels)
                    silhouettes.append(sil_score)
                except:
                    silhouettes.append(-1)
            
            # Find elbow point (maximize silhouette score)
            if silhouettes:
                best_k = np.argmax(silhouettes) + 2
                kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
                silhouette = silhouettes[best_k - 2]
                method = f"K-means (k={best_k})"
            else:
                # Last resort: use hierarchical clustering
                n_clusters = min(8, len(embeddings) // 5)
                agglo = AgglomerativeClustering(n_clusters=n_clusters)
                labels = agglo.fit_predict(embeddings)
                silhouette = -1
                method = f"Agglomerative (n={n_clusters})"
        
        # Print results
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        console.print(f"[green]✅ Clustering complete using {method}[/green]")
        console.print(f"[blue]📊 Found {n_clusters} clusters ({n_noise} noise points)[/blue]")
        console.print(f"[blue]📊 Silhouette score: {silhouette:.3f}[/blue]")
        
        return labels, silhouette, method

    def visualize_clusters(self, embeddings: np.ndarray, labels: np.ndarray, texts: List[str], output_file: str = "clusters_visualization.png"):
        """Create a 2D visualization of the clusters."""
        console.print("[cyan]📈 Creating cluster visualization...[/cyan]")
        
        # Reduce dimensions for visualization
        pca = PCA(n_components=2, random_state=42)
        embeddings_2d = pca.fit_transform(embeddings)
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        
        # Get unique labels
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in labels else 0)
        
        # Create color palette
        colors = plt.cm.rainbow(np.linspace(0, 1, n_clusters))
        
        # Plot each cluster
        for idx, label in enumerate(sorted(unique_labels)):
            if label == -1:
                # Plot noise points
                mask = labels == label
                plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                           c='gray', marker='x', s=50, alpha=0.5, label='Noise')
            else:
                # Plot cluster points
                mask = labels == label
                plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                           c=[colors[idx]], marker='o', s=100, alpha=0.7, 
                           label=f'Cluster {label}')
        
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        plt.title('JTBD Clusters Visualization (PCA)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Visualization saved to {output_file}[/green]")

    def label_clusters(self, clusters: Dict[int, List[str]]) -> Dict[int, Dict]:
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
                sample_size = min(15, len(texts))  # Increased sample size
                sample_texts = texts[:sample_size]

                prompt = f"""Analyze these customer pain points and provide:
1. A concise, descriptive label (3-5 words)
2. A brief summary of the common theme
3. The underlying job-to-be-done
4. Severity level (High/Medium/Low)

Pain points ({len(texts)} total, showing {sample_size} samples):
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
                                "content": "You are an expert at Jobs-to-be-Done analysis. Focus on identifying the core need behind the pain points.",
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

    def generate_opportunity_zones(self, labeled_clusters: Dict[int, Dict]) -> Dict:
        """Generate opportunity zones from clusters."""
        console.print("[cyan]🎯 Generating opportunity zones...[/cyan]")

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
                    {"role": "system", "content": "You are a product strategy expert. Focus on identifying high-impact opportunities that address multiple pain points."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                response_format={"type": "json_object"},
            )

            opportunity_zones = json.loads(response.choices[0].message.content)

            # Validate and normalize percentages
            total_percentage = sum(
                zone["importance_percentage"]
                for zone in opportunity_zones["opportunity_zones"]
            )
            if total_percentage != 100:
                console.print(
                    f"[yellow]Warning: Percentages sum to {total_percentage}%, adjusting...[/yellow]"
                )
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

    def display_results(self, labeled_clusters: Dict, opportunity_zones: Dict, method: str):
        """Display clustering results."""
        # Display clusters
        console.print(f"\n[bold cyan]📊 Cluster Analysis Results (Method: {method})[/bold cyan]\n")

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

        if opportunity_zones["opportunity_zones"]:
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
        labeled_clusters: Dict,
        opportunity_zones: Dict,
        output_file: str,
        method: str,
        silhouette: float
    ):
        """Save enhanced results with clustering metadata."""
        results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "clustering_method": method,
                "n_clusters": len(labeled_clusters),
                "n_pain_points": sum(c["size"] for c in labeled_clusters.values()),
                "silhouette_score": silhouette,
            },
            "clusters": labeled_clusters,
            "opportunity_zones": opportunity_zones,
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        console.print(f"\n[green]✅ Results saved to {output_file}[/green]")

    def run(self, input_file: str, output_file: str = "opportunity_zones.json", visualize: bool = True):
        """Main execution flow."""
        console.print(
            Panel.fit(
                "[bold green]Enhanced JTBD Clustering Analysis[/bold green]\n"
                "Using Cohere Embed v3 + Optimized Clustering + GPT-4o",
                border_style="green",
            )
        )

        # Extract individual pain points
        texts = self.extract_pain_points(input_file)

        # Embed texts
        embeddings = self.embed_texts(texts)

        # Cluster with fallback strategies
        labels, silhouette, method = self.cluster_with_fallback(embeddings, texts)

        # Visualize if requested
        if visualize:
            self.visualize_clusters(embeddings, labels, texts)

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
        self.display_results(labeled_clusters, opportunity_zones, method)

        # Save results
        self.save_results(labeled_clusters, opportunity_zones, output_file, method, silhouette)

        # Print noise points if any
        noise_count = list(labels).count(-1)
        if noise_count > 0:
            console.print(
                f"\n[yellow]Note: {noise_count} pain points were classified as noise[/yellow]"
            )
            if self.debug:
                console.print("\n[yellow]Noise points:[/yellow]")
                for i, label in enumerate(labels):
                    if label == -1:
                        console.print(f"  • {texts[i]}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced JTBD Clustering with optimized parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Cluster pain points with visualization
  python cluster_jtbd_enhanced.py pain_points.txt
  
  # Without visualization
  python cluster_jtbd_enhanced.py pain_points.txt --no-viz
  
  # Debug mode with detailed output
  python cluster_jtbd_enhanced.py pain_points.txt --debug
  
  # Custom output file
  python cluster_jtbd_enhanced.py pain_points.txt --output my_zones.json
        """,
    )

    parser.add_argument(
        "file", nargs="?", help="Path to pain points file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="opportunity_zones.json",
        help="Output JSON file (default: opportunity_zones.json)",
    )
    parser.add_argument(
        "--no-viz",
        action="store_true",
        help="Disable cluster visualization"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed output"
    )
    parser.add_argument("--test", action="store_true", help="Test API connections")

    args = parser.parse_args()

    # Initialize clusterer
    clusterer = EnhancedJTBDClusterer(debug=args.debug)

    if args.test:
        # Test mode
        console.print("[cyan]Testing API connections...[/cyan]")

        # Test Cohere
        try:
            response = clusterer.cohere_client.embed(
                texts=["Test embedding"], model="embed-english-v3.0"
            )
            console.print("[green]✅ Cohere API connected![/green]")
        except Exception as e:
            console.print(f"[red]❌ Cohere test failed: {e}[/red]")

        # Test OpenAI
        try:
            response = clusterer.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Say 'Connected!'"}],
                max_tokens=10,
            )
            console.print(
                f"[green]✅ OpenAI GPT-4o: {response.choices[0].message.content}[/green]"
            )
        except Exception as e:
            console.print(f"[red]❌ OpenAI test failed: {e}[/red]")

        return

    if not args.file:
        parser.print_help()
        sys.exit(1)

    # Run enhanced clustering
    clusterer.run(args.file, args.output, visualize=not args.no_viz)


if __name__ == "__main__":
    main()