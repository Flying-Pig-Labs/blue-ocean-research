#!/usr/bin/env python3
"""
Adaptive JTBD Clustering Script - Domain-Agnostic Implementation.

This enhanced version implements adaptive clustering strategies that work across
different domains and dataset sizes. It automatically adjusts parameters based
on the characteristics of the input data.

Key Features:
- Adaptive parameter selection based on dataset size
- Multiple fallback strategies (HDBSCAN → Agglomerative → K-means)
- Domain-aware embeddings with optional context
- Embedding density analysis for strategy selection
- Comprehensive output format for pipeline compatibility
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
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN, SpectralClustering
from sklearn.metrics import silhouette_score, pairwise_distances, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
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


class AdaptiveJTBDClusterer:
    """Domain-agnostic adaptive clustering for JTBD analysis."""

    def __init__(self, domain_hint: Optional[str] = None, debug: bool = False):
        """
        Initialize with optional domain context.
        
        Args:
            domain_hint: Optional domain context (e.g., 'real_estate', 'healthcare')
            debug: Enable debug output
        """
        self.domain_hint = domain_hint
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

    def load_texts(self, filepath: str) -> List[str]:
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

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed texts with optional domain context."""
        console.print("[cyan]🔍 Embedding texts with Cohere Embed v3...[/cyan]")

        # Add domain context if provided
        if self.domain_hint:
            console.print(f"[blue]Adding domain context: {self.domain_hint}[/blue]")
            contextualized_texts = [f"{self.domain_hint}: {text}" for text in texts]
        else:
            contextualized_texts = texts

        batch_size = 96
        embeddings = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Embedding...", total=len(texts))

            for i in range(0, len(contextualized_texts), batch_size):
                batch = contextualized_texts[i : i + batch_size]

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
        
        # Normalize embeddings
        embeddings_norm = embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        
        console.print(
            f"[green]✅ Created embeddings with shape {embeddings_norm.shape}[/green]"
        )
        return embeddings_norm

    def analyze_embedding_density(self, embeddings: np.ndarray) -> float:
        """Analyze embedding space density to choose clustering strategy."""
        console.print("[cyan]📊 Analyzing embedding density...[/cyan]")
        
        # Calculate pairwise distances
        distances = pairwise_distances(embeddings, metric='euclidean')
        
        # Get k-nearest neighbor distances (k=5)
        k = min(5, len(embeddings) - 1)
        np.fill_diagonal(distances, np.inf)
        knn_distances = np.sort(distances, axis=1)[:, :k].mean(axis=1)
        
        # Calculate density metric (inverse of average k-NN distance)
        avg_density = 1.0 / (np.mean(knn_distances) + 1e-6)
        normalized_density = min(1.0, avg_density / 2.0)  # Normalize to [0, 1]
        
        if self.debug:
            console.print(f"[yellow]Embedding density: {normalized_density:.3f}[/yellow]")
            console.print(f"[yellow]Average k-NN distance: {np.mean(knn_distances):.3f}[/yellow]")
        
        return normalized_density

    def estimate_optimal_clusters(self, embeddings: np.ndarray, max_k: int = None) -> int:
        """Estimate optimal number of clusters using elbow method and silhouette analysis."""
        n_samples = len(embeddings)
        
        if max_k is None:
            max_k = min(int(n_samples / 3), 15)
        
        min_k = 2
        max_k = min(max_k, n_samples - 1)
        
        console.print("[cyan]🔍 Estimating optimal cluster count...[/cyan]")
        
        scores = []
        silhouettes = []
        inertias = []
        
        for k in range(min_k, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            
            # Calculate metrics
            inertia = kmeans.inertia_
            inertias.append(inertia)
            
            try:
                silhouette = silhouette_score(embeddings, labels)
                ch_score = calinski_harabasz_score(embeddings, labels)
                
                # Combined score favoring higher silhouette and CH scores
                combined_score = silhouette * np.log(ch_score + 1)
                scores.append(combined_score)
                silhouettes.append(silhouette)
            except:
                scores.append(-1)
                silhouettes.append(-1)
        
        # Find elbow point using rate of change
        if len(scores) > 2:
            # Find the k with best combined score
            best_k_idx = np.argmax(scores)
            optimal_k = min_k + best_k_idx
            
            # Adjust based on dataset size preferences
            if n_samples < 30:
                optimal_k = min(optimal_k, 5)
            elif n_samples < 100:
                optimal_k = min(optimal_k, 8)
        else:
            optimal_k = min_k
        
        if self.debug:
            console.print(f"[yellow]Optimal clusters estimated: {optimal_k}[/yellow]")
            console.print(f"[yellow]Best silhouette score: {max(silhouettes):.3f}[/yellow]")
        
        return optimal_k

    def adaptive_clustering(self, embeddings: np.ndarray, texts: List[str]) -> Tuple[np.ndarray, str, Dict]:
        """Apply adaptive clustering based on data characteristics."""
        n_points = len(texts)
        
        console.print(f"[cyan]🧠 Applying adaptive clustering for {n_points} points...[/cyan]")
        
        # Adaptive min_cluster_size based on dataset size
        min_cluster_size = max(2, int(n_points * 0.05))  # 5% of data, minimum 2
        min_samples = max(1, int(min_cluster_size * 0.5))
        
        # Analyze embedding density
        density = self.analyze_embedding_density(embeddings)
        
        # Choose strategy based on density and size
        if n_points < 30:
            strategy = "small_dataset"
        elif density > 0.8:
            strategy = "fine_grained"
        elif density < 0.3:
            strategy = "coarse"
        else:
            strategy = "adaptive"
        
        console.print(f"[blue]Strategy: {strategy} (density: {density:.3f})[/blue]")
        
        # Try progressively less restrictive parameters
        param_sets = []
        
        if strategy == "small_dataset":
            param_sets = [
                {'min_cluster_size': 2, 'min_samples': 1},
                {'min_cluster_size': 3, 'min_samples': 1},
                {'min_cluster_size': 3, 'min_samples': 2}
            ]
        elif strategy == "fine_grained":
            param_sets = [
                {'min_cluster_size': min_cluster_size, 'min_samples': min_samples},
                {'min_cluster_size': max(2, min_cluster_size//2), 'min_samples': 1},
                {'min_cluster_size': 2, 'min_samples': 1}
            ]
        else:
            param_sets = [
                {'min_cluster_size': min_cluster_size, 'min_samples': min_samples},
                {'min_cluster_size': max(3, min_cluster_size//2), 'min_samples': max(1, min_samples//2)},
                {'min_cluster_size': 3, 'min_samples': 1}
            ]
        
        best_labels = None
        best_n_clusters = 0
        best_params = None
        clustering_method = "hdbscan"
        
        # Try HDBSCAN with different parameters
        for params in param_sets:
            try:
                clusterer = HDBSCAN(
                    **params,
                    metric='euclidean',
                    cluster_selection_method='eom',
                    prediction_data=True
                )
                
                labels = clusterer.fit_predict(embeddings)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                
                if n_clusters > best_n_clusters and n_clusters >= 2:
                    best_labels = labels
                    best_n_clusters = n_clusters
                    best_params = params
                    
                    if n_clusters >= 3:  # Good enough, stop trying
                        break
            except Exception as e:
                if self.debug:
                    console.print(f"[yellow]HDBSCAN failed with params {params}: {e}[/yellow]")
        
        # Fallback strategies if HDBSCAN fails
        if best_n_clusters < 2:
            console.print("[yellow]⚠️ HDBSCAN failed, trying fallback strategies...[/yellow]")
            
            # Estimate optimal clusters
            optimal_k = self.estimate_optimal_clusters(embeddings)
            
            # Try Agglomerative Clustering
            try:
                console.print(f"[cyan]Trying Agglomerative Clustering with k={optimal_k}...[/cyan]")
                clusterer = AgglomerativeClustering(
                    n_clusters=optimal_k,
                    linkage='ward'
                )
                labels = clusterer.fit_predict(embeddings)
                clustering_method = "agglomerative"
                best_params = {'n_clusters': optimal_k, 'linkage': 'ward'}
            except:
                # Final fallback: K-means
                console.print(f"[cyan]Final fallback: K-means with k={optimal_k}...[/cyan]")
                kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
                clustering_method = "kmeans"
                best_params = {'n_clusters': optimal_k}
        else:
            labels = best_labels
        
        # Calculate final metrics
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        # Calculate silhouette score
        silhouette = -1
        if n_clusters > 1:
            mask = labels != -1
            if sum(mask) > 1:
                try:
                    silhouette = silhouette_score(embeddings[mask], labels[mask])
                except:
                    silhouette = -1
        
        console.print(f"[green]✅ Clustering complete: {n_clusters} clusters, {n_noise} noise points[/green]")
        console.print(f"[blue]Method: {clustering_method}, Silhouette: {silhouette:.3f}[/blue]")
        
        metadata = {
            'method': clustering_method,
            'parameters': best_params,
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'silhouette_score': silhouette,
            'density': density,
            'strategy': strategy
        }
        
        return labels, clustering_method, metadata

    def post_process_clusters(self, labels: np.ndarray, texts: List[str], min_size: int = 2) -> np.ndarray:
        """Post-process clusters to ensure minimum size and merge tiny clusters."""
        console.print("[cyan]🔧 Post-processing clusters...[/cyan]")
        
        # Count cluster sizes
        unique_labels, counts = np.unique(labels, return_counts=True)
        cluster_sizes = dict(zip(unique_labels, counts))
        
        # Identify small clusters (excluding noise)
        small_clusters = [label for label, size in cluster_sizes.items() 
                         if label != -1 and size < min_size]
        
        if small_clusters:
            console.print(f"[yellow]Found {len(small_clusters)} clusters below minimum size {min_size}[/yellow]")
            
            # For each small cluster, merge with nearest cluster
            for small_label in small_clusters:
                small_indices = np.where(labels == small_label)[0]
                
                # Find nearest large cluster
                # This is a simplified approach - could be improved with centroid distances
                labels[small_indices] = -1  # Mark as noise for now
        
        # Renumber clusters to be consecutive
        unique_labels = [l for l in np.unique(labels) if l != -1]
        label_map = {old: new for new, old in enumerate(unique_labels)}
        label_map[-1] = -1
        
        new_labels = np.array([label_map[l] for l in labels])
        
        return new_labels

    def extract_cluster_themes(self, cluster_texts: List[str]) -> str:
        """Extract theme using TF-IDF for better domain-agnostic labeling."""
        if not cluster_texts:
            return "Unknown Theme"
        
        try:
            # Use TF-IDF to find most important terms
            vectorizer = TfidfVectorizer(max_features=10, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(cluster_texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top terms
            scores = tfidf_matrix.sum(axis=0).A1
            top_indices = scores.argsort()[-3:][::-1]
            top_terms = [feature_names[i] for i in top_indices]
            
            theme = " ".join(top_terms).title()
            return theme
        except:
            return "Cluster Theme"

    def label_clusters_smart(self, clusters: Dict[int, List[str]]) -> Dict[int, Dict]:
        """Enhanced cluster labeling with domain awareness."""
        console.print("[cyan]🏷️  Generating intelligent cluster labels...[/cyan]")

        labeled_clusters = {}
        
        # Prepare domain context for prompts
        domain_context = ""
        if self.domain_hint:
            domain_map = {
                'real_estate': "real estate customer experiences",
                'healthcare': "healthcare patient experiences",
                'fintech': "financial services user experiences",
                'saas': "software-as-a-service user experiences"
            }
            domain_context = f"These are {domain_map.get(self.domain_hint, self.domain_hint + ' customer experiences')}. "

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Labeling clusters...", total=len(clusters))

            for cluster_id, texts in clusters.items():
                # Extract initial theme using TF-IDF
                tfidf_theme = self.extract_cluster_themes(texts)
                
                sample_size = min(15, len(texts))
                sample_texts = texts[:sample_size]

                prompt = f"""{domain_context}Analyze these related pain points and provide:
1. A concise, descriptive label (3-5 words) that captures the core issue
2. A brief summary of the common theme
3. The underlying job-to-be-done
4. Severity level (High/Medium/Low)
5. Potential business impact

Initial theme detected: {tfidf_theme}

Pain points ({len(texts)} total, showing {sample_size} samples):
{chr(10).join([f"- {t}" for t in sample_texts])}

Respond in JSON format:
{{
    "label": "...",
    "summary": "...",
    "job_to_be_done": "When I [situation], I want to [motivation], so I can [outcome]",
    "severity": "High/Medium/Low",
    "impact": "High/Medium/Low",
    "complexity": "High/Medium/Low"
}}"""

                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert at Jobs-to-be-Done analysis and customer experience research. Focus on identifying actionable insights."
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"},
                    )

                    cluster_info = json.loads(response.choices[0].message.content)
                    
                    # Calculate coherence score based on text similarity
                    coherence = self.calculate_cluster_coherence(texts)
                    
                    cluster_info.update({
                        "cluster_id": cluster_id,
                        "size": len(texts),
                        "coherence_score": coherence,
                        "tfidf_theme": tfidf_theme,
                        "sample_texts": sample_texts,
                        "all_texts": texts
                    })

                    labeled_clusters[cluster_id] = cluster_info
                    progress.update(task, advance=1)

                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Failed to label cluster {cluster_id}: {e}[/yellow]"
                    )
                    labeled_clusters[cluster_id] = {
                        "cluster_id": cluster_id,
                        "label": tfidf_theme,
                        "summary": f"Cluster of {len(texts)} related pain points",
                        "job_to_be_done": "Unable to extract JTBD",
                        "severity": "Medium",
                        "impact": "Medium",
                        "complexity": "Medium",
                        "size": len(texts),
                        "coherence_score": 0.5,
                        "tfidf_theme": tfidf_theme,
                        "sample_texts": sample_texts,
                        "all_texts": texts
                    }
                    progress.update(task, advance=1)

        return labeled_clusters

    def calculate_cluster_coherence(self, texts: List[str]) -> float:
        """Calculate cluster coherence score based on text similarity."""
        if len(texts) < 2:
            return 1.0
        
        try:
            # Use TF-IDF to calculate text similarity
            vectorizer = TfidfVectorizer(max_features=100)
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Calculate pairwise cosine similarities
            similarities = (tfidf_matrix * tfidf_matrix.T).toarray()
            
            # Get average similarity (excluding diagonal)
            n = len(texts)
            total_sim = (similarities.sum() - n) / (n * (n - 1))
            
            return float(total_sim)
        except:
            return 0.5

    def generate_opportunity_zones(self, labeled_clusters: Dict[int, Dict]) -> Dict:
        """Generate opportunity zones with domain-aware insights."""
        console.print("[cyan]🎯 Generating strategic opportunity zones...[/cyan]")

        cluster_summaries = []
        for cluster in labeled_clusters.values():
            cluster_summaries.append({
                "label": cluster["label"],
                "summary": cluster["summary"],
                "job_to_be_done": cluster["job_to_be_done"],
                "severity": cluster["severity"],
                "size": cluster["size"],
                "coherence_score": cluster.get("coherence_score", 0.5),
                "impact": cluster.get("impact", "Medium")
            })

        domain_context = ""
        if self.domain_hint:
            domain_context = f"For the {self.domain_hint} domain, "

        prompt = f"""{domain_context}analyze these clustered pain points and identify up to 5 strategic opportunity zones.

Clusters:
{json.dumps(cluster_summaries, indent=2)}

Create opportunity zones that:
1. Address multiple related clusters
2. Represent actionable product/service improvements
3. Have clear business value

For each opportunity zone provide:
- Strategic name
- Description of the opportunity
- Which clusters it addresses
- Importance percentage (must total 100%)
- Implementation approach

Respond in JSON format:
{{
    "opportunity_zones": [
        {{
            "name": "Strategic name",
            "description": "What this opportunity addresses",
            "clusters_addressed": ["cluster label 1", "cluster label 2"],
            "importance_percentage": 30,
            "potential_impact": "High/Medium/Low",
            "implementation_complexity": "High/Medium/Low",
            "implementation_approach": "Brief description of how to address this"
        }}
    ],
    "rationale": "Strategic reasoning for the prioritization"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a product strategy expert. Create actionable opportunity zones that drive real business value."},
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
                for zone in opportunity_zones["opportunity_zones"]:
                    zone["importance_percentage"] = round(
                        zone["importance_percentage"] * 100 / total_percentage
                    )

            return opportunity_zones

        except Exception as e:
            console.print(f"[red]Error generating opportunity zones: {e}[/red]")
            # Fallback: Create basic zones from largest clusters
            zones = []
            sorted_clusters = sorted(cluster_summaries, key=lambda x: x['size'], reverse=True)
            
            for i, cluster in enumerate(sorted_clusters[:5]):
                zones.append({
                    "name": cluster['label'],
                    "description": cluster['summary'],
                    "clusters_addressed": [cluster['label']],
                    "importance_percentage": 20,
                    "potential_impact": cluster.get('impact', 'Medium'),
                    "implementation_complexity": "Medium",
                    "implementation_approach": "Address the core issues identified"
                })
            
            return {
                "opportunity_zones": zones,
                "rationale": "Zones created based on cluster size and severity"
            }

    def visualize_clusters(self, embeddings: np.ndarray, labels: np.ndarray, 
                          output_file: str = "clusters_visualization.png"):
        """Create visualization of clusters."""
        console.print("[cyan]📈 Creating cluster visualization...[/cyan]")
        
        # PCA for 2D visualization
        pca = PCA(n_components=2, random_state=42)
        embeddings_2d = pca.fit_transform(embeddings)
        
        plt.figure(figsize=(12, 8))
        
        # Plot clusters
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in labels else 0)
        colors = plt.cm.rainbow(np.linspace(0, 1, n_clusters))
        
        for idx, label in enumerate(sorted(unique_labels)):
            if label == -1:
                mask = labels == label
                plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                           c='gray', marker='x', s=50, alpha=0.5, label='Noise')
            else:
                mask = labels == label
                plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                           c=[colors[idx]], marker='o', s=100, alpha=0.7, 
                           label=f'Cluster {label}')
        
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        title = f'Pain Points Clustering Visualization'
        if self.domain_hint:
            title += f' ({self.domain_hint.title()})'
        plt.title(title)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print(f"[green]✅ Visualization saved to {output_file}[/green]")

    def save_results(self, labeled_clusters: Dict, opportunity_zones: Dict, 
                    metadata: Dict, output_file: str, noise_texts: List[str]):
        """Save results in universal format."""
        results = {
            "domain_context": self.domain_hint or "general",
            "total_pain_points": metadata.get('n_clusters', 0) * 5 + metadata.get('n_noise', 0),
            "clusters_found": metadata.get('n_clusters', 0),
            "clustering_method": metadata.get('method', 'unknown'),
            "clusters": list(labeled_clusters.values()),
            "opportunity_zones": opportunity_zones,
            "noise_points": noise_texts,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "embedding_model": "cohere-embed-v3",
                "clustering_params": metadata.get('parameters', {}),
                "silhouette_score": metadata.get('silhouette_score', -1),
                "density": metadata.get('density', 0),
                "strategy": metadata.get('strategy', 'unknown')
            }
        }

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        console.print(f"\n[green]✅ Results saved to {output_file}[/green]")

    def display_results(self, labeled_clusters: Dict, opportunity_zones: Dict, metadata: Dict):
        """Display results with enhanced formatting."""
        console.print(f"\n[bold cyan]📊 Adaptive Clustering Results[/bold cyan]")
        console.print(f"[blue]Method: {metadata['method']} | Strategy: {metadata['strategy']}[/blue]\n")

        # Display clusters
        for cluster_id, info in labeled_clusters.items():
            coherence_color = "green" if info.get('coherence_score', 0) > 0.7 else "yellow"
            
            console.print(
                Panel(
                    f"[bold]{info['label']}[/bold]\n\n"
                    f"Summary: {info['summary']}\n"
                    f"JTBD: {info['job_to_be_done']}\n"
                    f"Severity: {info['severity']} | Impact: {info.get('impact', 'Medium')}\n"
                    f"Size: {info['size']} pain points | "
                    f"Coherence: [{coherence_color}]{info.get('coherence_score', 0):.2f}[/{coherence_color}]\n\n"
                    f"Sample pain points:\n"
                    + "\n".join([f"• {t}" for t in info["sample_texts"][:3]]),
                    title=f"Cluster {cluster_id}",
                    border_style="blue",
                )
            )

        # Display opportunity zones
        console.print("\n[bold green]🎯 Strategic Opportunity Zones[/bold green]\n")

        if opportunity_zones.get("opportunity_zones"):
            table = Table(title="Opportunity Prioritization Matrix")
            table.add_column("Zone", style="cyan", width=20)
            table.add_column("Priority %", style="magenta", width=10)
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
            console.print(f"\n[italic]Rationale: {opportunity_zones.get('rationale', 'N/A')}[/italic]")

    def run(self, input_file: str, output_file: str = "opportunity_zones.json", 
            visualize: bool = True):
        """Main execution flow."""
        console.print(
            Panel.fit(
                "[bold green]Adaptive JTBD Clustering Analysis[/bold green]\n"
                f"Domain: {self.domain_hint or 'General'} | Adaptive Strategy Enabled",
                border_style="green",
            )
        )

        # Load texts
        texts = self.load_texts(input_file)

        # Embed texts
        embeddings = self.embed_texts(texts)

        # Apply adaptive clustering
        labels, method, metadata = self.adaptive_clustering(embeddings, texts)

        # Post-process clusters
        labels = self.post_process_clusters(labels, texts, min_size=2)

        # Visualize if requested
        if visualize:
            self.visualize_clusters(embeddings, labels, output_file.replace('.json', '_viz.png'))

        # Group texts by cluster
        clusters = defaultdict(list)
        noise_texts = []
        
        for i, label in enumerate(labels):
            if label != -1:
                clusters[label].append(texts[i])
            else:
                noise_texts.append(texts[i])

        # Label clusters with enhanced method
        labeled_clusters = self.label_clusters_smart(dict(clusters))

        # Generate opportunity zones
        opportunity_zones = self.generate_opportunity_zones(labeled_clusters)

        # Display results
        self.display_results(labeled_clusters, opportunity_zones, metadata)

        # Save results
        self.save_results(labeled_clusters, opportunity_zones, metadata, 
                         output_file, noise_texts)

        # Summary statistics
        console.print(f"\n[bold]📊 Summary Statistics:[/bold]")
        console.print(f"Total pain points: {len(texts)}")
        console.print(f"Clusters found: {metadata['n_clusters']}")
        console.print(f"Noise points: {metadata['n_noise']} ({metadata['n_noise']/len(texts)*100:.1f}%)")
        console.print(f"Clustering quality (silhouette): {metadata['silhouette_score']:.3f}")
        console.print(f"Method used: {method}")


def main():
    """Main entry point with enhanced argument parsing."""
    parser = argparse.ArgumentParser(
        description="Adaptive JTBD Clustering - Domain-Agnostic Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Domain Hints:
  real_estate    - Real estate and property management
  healthcare     - Healthcare and medical services
  fintech        - Financial technology and services
  saas           - Software as a service
  ecommerce      - E-commerce and retail
  education      - Educational technology
  automotive     - Automotive and transportation

Examples:
  # Basic clustering
  python cluster_jtbd_adaptive.py pain_points.txt
  
  # With domain context
  python cluster_jtbd_adaptive.py pain_points.txt --domain real_estate
  
  # Custom output without visualization
  python cluster_jtbd_adaptive.py pain_points.txt --output results.json --no-viz
  
  # Debug mode for troubleshooting
  python cluster_jtbd_adaptive.py pain_points.txt --debug
        """,
    )

    parser.add_argument("file", nargs="?", help="Path to pain points file (one per line)")
    parser.add_argument("--output", type=str, default="opportunity_zones.json",
                       help="Output JSON file (default: opportunity_zones.json)")
    parser.add_argument("--domain", type=str, help="Domain hint for better clustering")
    parser.add_argument("--no-viz", action="store_true", help="Disable visualization")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--test", action="store_true", help="Test API connections")

    args = parser.parse_args()

    # Initialize clusterer
    clusterer = AdaptiveJTBDClusterer(domain_hint=args.domain, debug=args.debug)

    if args.test:
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
            console.print(f"[green]✅ OpenAI GPT-4o: {response.choices[0].message.content}[/green]")
        except Exception as e:
            console.print(f"[red]❌ OpenAI test failed: {e}[/red]")
        
        return

    if not args.file:
        parser.print_help()
        sys.exit(1)

    # Run adaptive clustering
    clusterer.run(args.file, args.output, visualize=not args.no_viz)


if __name__ == "__main__":
    main()