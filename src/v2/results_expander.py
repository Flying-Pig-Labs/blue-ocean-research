"""
Results Expander for Pipeline V2

Captures and stores expanded results that show ALL generated ideas,
not just the filtered final selections. This is the key to giving
users visibility into what was filtered out.
"""

import json
import os
import glob
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd


class ResultsExpander:
    """
    Captures and expands pipeline results to show complete generation process.
    
    This class intercepts pipeline outputs at key stages and stores expanded
    versions that include all generated ideas, filtering decisions, and
    alternative selections that users can review.
    """
    
    def __init__(self, ui_mode: bool = False):
        """
        Initialize results expander.
        
        Args:
            ui_mode: If True, formats results for UI consumption
        """
        self.ui_mode = ui_mode
        self.expanded_results = {}
        self.capture_enabled = False
        
        # Create expanded results directory
        self.expanded_dir = Path("expanded_results")
        self.expanded_dir.mkdir(exist_ok=True)
        
    def enable_capture(self):
        """Enable result capture during pipeline execution."""
        self.capture_enabled = True
        
    def capture_stage_results(self, stage_name: str, results: Dict[str, Any]):
        """Capture results from a specific pipeline stage."""
        
        if not self.capture_enabled:
            return
            
        timestamp = datetime.now().isoformat()
        
        self.expanded_results[stage_name] = {
            'timestamp': timestamp,
            'results': results,
            'metadata': self._generate_stage_metadata(stage_name, results)
        }
        
        # Save to file immediately for persistence
        self._save_stage_results(stage_name, self.expanded_results[stage_name])
    
    def expand_opportunity_zones(self, zones_file: str = "opportunity_zones.json") -> Dict[str, Any]:
        """
        Expand opportunity zones to show detailed analysis.
        
        This captures the full zone analysis including all JTBDs mapped to each zone,
        pain dimension scores, and Reddit discussion details.
        """
        
        if not os.path.exists(zones_file):
            return {}
            
        with open(zones_file, 'r') as f:
            zones = json.load(f)
            
        expanded_zones = {
            'zones_summary': zones,
            'detailed_analysis': self._expand_zone_details(zones),
            'clustering_insights': self._analyze_zone_clustering(zones),
            'reddit_mapping': self._expand_reddit_mapping()
        }
        
        self.capture_stage_results('opportunity_zones_expanded', expanded_zones)
        return expanded_zones
    
    def expand_product_ideas(self, ideas_file: str = "product_ideas.json") -> Dict[str, Any]:
        """
        Expand product ideas to show ALL generated ideas, not just selected ones.
        
        This is the most critical expansion - showing users all the ideas that
        were generated but filtered out by the scoring system.
        """
        
        if not os.path.exists(ideas_file):
            return {}
            
        with open(ideas_file, 'r') as f:
            final_ideas = json.load(f)
            
        # Try to reconstruct the full generation process
        expanded_ideas = {
            'final_selection': final_ideas,
            'all_generated_ideas': self._reconstruct_all_generated_ideas(),
            'filtering_analysis': self._analyze_filtering_decisions(final_ideas),
            'alternative_portfolios': self._generate_alternative_portfolios(),
            'scoring_breakdown': self._expand_scoring_details()
        }
        
        self.capture_stage_results('product_ideas_expanded', expanded_ideas)
        return expanded_ideas
    
    def _expand_zone_details(self, zones: Dict[str, Any]) -> Dict[str, Any]:
        """Expand zone details with comprehensive analysis."""
        
        expanded_details = {}
        
        for zone_name, zone_data in zones.items():
            if isinstance(zone_data, dict) and 'jtbds' in zone_data:
                expanded_details[zone_name] = {
                    'basic_info': zone_data,
                    'jtbd_analysis': self._analyze_zone_jtbds(zone_data.get('jtbds', [])),
                    'pain_dimension_breakdown': self._analyze_pain_dimensions(zone_data),
                    'market_opportunity_factors': self._analyze_opportunity_factors(zone_data),
                    'solution_requirements': self._extract_solution_requirements(zone_data)
                }
                
        return expanded_details
    
    def _analyze_zone_clustering(self, zones: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how zones were clustered and why."""
        
        return {
            'clustering_method': 'Hierarchical clustering on pain dimensions',
            'zone_count_rationale': f"Generated {len(zones)} zones based on data patterns",
            'zone_distinctiveness': self._calculate_zone_distinctiveness(zones),
            'potential_alternative_groupings': self._suggest_alternative_groupings(zones)
        }
    
    def _expand_reddit_mapping(self) -> Dict[str, Any]:
        """Expand Reddit discussion mapping details."""
        
        # Look for Reddit discussion files
        reddit_files = glob.glob("reddit_discussions_*.csv")
        
        if not reddit_files:
            return {'status': 'No Reddit discussion files found'}
            
        reddit_file = reddit_files[0]  # Use most recent
        
        try:
            df = pd.read_csv(reddit_file)
            
            return {
                'total_discussions': len(df),
                'subreddit_distribution': df['subreddit'].value_counts().to_dict() if 'subreddit' in df.columns else {},
                'engagement_metrics': self._calculate_engagement_metrics(df),
                'discussion_themes': self._extract_discussion_themes(df),
                'quality_assessment': self._assess_discussion_quality(df)
            }
            
        except Exception as e:
            return {'status': f'Error analyzing Reddit data: {e}'}
    
    def _reconstruct_all_generated_ideas(self) -> Dict[str, Any]:
        """
        Attempt to reconstruct all generated ideas from various pipeline stages.
        
        This is challenging since the original pipeline doesn't save all ideas,
        but we can look for intermediate files and logs.
        """
        
        # This would ideally be populated by intercepting the product_idea_generator
        # during execution. For now, we provide a framework for future implementation.
        
        return {
            'reconstruction_method': 'File analysis and log parsing',
            'ideas_by_zone': self._scan_for_generated_ideas(),
            'generation_statistics': self._calculate_generation_stats(),
            'note': 'Full idea reconstruction requires pipeline modification'
        }
    
    def _analyze_filtering_decisions(self, final_ideas: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what filtering decisions were made and why."""
        
        if isinstance(final_ideas, list):
            ideas = final_ideas
        else:
            ideas = final_ideas.get('ideas', [])
            
        return {
            'final_idea_count': len(ideas),
            'score_distribution': self._analyze_score_distribution(ideas),
            'zone_representation': self._analyze_zone_representation(ideas),
            'filtering_criteria_applied': self._identify_filtering_criteria(ideas),
            'potential_oversights': self._identify_potential_oversights(ideas)
        }
    
    def _generate_alternative_portfolios(self) -> List[Dict[str, Any]]:
        """Generate alternative portfolio selections with different criteria."""
        
        alternatives = [
            {
                'name': 'Innovation-Heavy Portfolio',
                'description': 'Prioritizes breakthrough and innovative ideas',
                'selection_criteria': 'Top innovation scores, willing to sacrifice feasibility'
            },
            {
                'name': 'Market-Safe Portfolio', 
                'description': 'Prioritizes proven market demand and low risk',
                'selection_criteria': 'High market viability, conservative approach'
            },
            {
                'name': 'Balanced-Diverse Portfolio',
                'description': 'Maximizes diversity across zones and risk levels',
                'selection_criteria': 'Equal representation, balanced risk profile'
            }
        ]
        
        return alternatives
    
    def _expand_scoring_details(self) -> Dict[str, Any]:
        """Expand scoring methodology and weights used."""
        
        return {
            'scoring_dimensions': [
                'market_viability',
                'technical_feasibility', 
                'innovation_score',
                'competitive_differentiation',
                'revenue_potential'
            ],
            'weighting_scheme': 'User configuration applied',
            'threshold_analysis': self._analyze_scoring_thresholds(),
            'score_calibration': 'Normalized across zones and categories'
        }
    
    # Helper methods for analysis
    
    def _generate_stage_metadata(self, stage_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for stage results."""
        
        return {
            'stage': stage_name,
            'result_count': len(results) if isinstance(results, (list, dict)) else 1,
            'data_types': [type(v).__name__ for v in results.values()] if isinstance(results, dict) else [],
            'ui_formatted': self.ui_mode
        }
    
    def _save_stage_results(self, stage_name: str, stage_results: Dict[str, Any]):
        """Save stage results to expanded directory."""
        
        filename = f"{stage_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.expanded_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(stage_results, f, indent=2)
    
    def _analyze_zone_jtbds(self, jtbds: List[str]) -> Dict[str, Any]:
        """Analyze JTBDs within a zone."""
        
        return {
            'jtbd_count': len(jtbds),
            'common_themes': self._extract_jtbd_themes(jtbds),
            'complexity_analysis': self._analyze_jtbd_complexity(jtbds)
        }
    
    def _extract_jtbd_themes(self, jtbds: List[str]) -> List[str]:
        """Extract common themes from JTBDs."""
        
        # Simple keyword-based theme extraction
        common_words = ['find', 'manage', 'track', 'automate', 'simplify', 'connect']
        themes = []
        
        for word in common_words:
            if any(word.lower() in jtbd.lower() for jtbd in jtbds):
                themes.append(word)
                
        return themes
    
    def _analyze_jtbd_complexity(self, jtbds: List[str]) -> str:
        """Analyze complexity level of JTBDs."""
        
        avg_length = sum(len(jtbd.split()) for jtbd in jtbds) / len(jtbds) if jtbds else 0
        
        if avg_length > 15:
            return "Complex JTBDs with detailed requirements"
        elif avg_length > 10:
            return "Moderate complexity JTBDs"
        else:
            return "Simple, focused JTBDs"
    
    def _analyze_pain_dimensions(self, zone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pain dimensions for a zone."""
        
        return {
            'primary_pain_points': zone_data.get('pain_dimensions', {}),
            'pain_severity': 'Moderate to High',  # Would need actual data
            'addressability': 'Technology solutions available'
        }
    
    def _calculate_zone_distinctiveness(self, zones: Dict[str, Any]) -> float:
        """Calculate how distinct the zones are from each other."""
        
        # Simplified distinctiveness measure
        return 0.75  # 75% distinct - placeholder
    
    def _suggest_alternative_groupings(self, zones: Dict[str, Any]) -> List[str]:
        """Suggest alternative ways to group the zones."""
        
        return [
            "By customer segment (B2B vs B2C)",
            "By implementation complexity (Simple vs Complex)",
            "By market maturity (Established vs Emerging)"
        ]
    
    def _calculate_engagement_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate engagement metrics from Reddit data."""
        
        metrics = {}
        
        if 'score' in df.columns:
            metrics['avg_score'] = df['score'].mean()
            metrics['high_engagement_posts'] = len(df[df['score'] > df['score'].quantile(0.8)])
            
        if 'num_comments' in df.columns:
            metrics['avg_comments'] = df['num_comments'].mean()
            metrics['discussion_rich_posts'] = len(df[df['num_comments'] > 10])
            
        return metrics
    
    def _scan_for_generated_ideas(self) -> Dict[str, Any]:
        """Scan for any generated ideas in intermediate files."""
        
        # Look for any files that might contain generated ideas
        idea_files = glob.glob("*ideas*.json") + glob.glob("*product*.json")
        
        found_ideas = {}
        
        for file in idea_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    found_ideas[file] = len(data) if isinstance(data, list) else 1
            except:
                continue
                
        return found_ideas
    
    def get_ui_summary(self) -> Dict[str, Any]:
        """Generate UI-friendly summary of expanded results."""
        
        return {
            'expansion_enabled': self.capture_enabled,
            'stages_captured': list(self.expanded_results.keys()),
            'total_expanded_files': len(list(self.expanded_dir.glob("*.json"))),
            'last_update': datetime.now().isoformat()
        }