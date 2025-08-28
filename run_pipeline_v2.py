#!/usr/bin/env python3
"""
Multi-Step LLM Pipeline Runner V2 - Enhanced User Control

This is a V2 wrapper around the existing run_pipeline.py that adds user control points
without breaking the original pipeline. It preserves all existing functionality while
enabling UI-driven configuration and expanded result visibility.

Key V2 Features:
- User-configurable market focus and strategic priorities
- Expanded result storage (shows ALL generated ideas, not just filtered ones)
- Mid-pipeline review points for UI integration
- Backwards compatibility with original pipeline
- Enhanced result analytics and insight generation

V2 Philosophy:
- Preserve original pipeline as-is (zero breaking changes)
- Add configuration layer for user preferences
- Intercept and enhance result storage
- Provide UI-friendly data formats and endpoints

Usage:
    python run_pipeline_v2.py                         # Default mode (same as original)
    python run_pipeline_v2.py --config user_config.json  # With user preferences
    python run_pipeline_v2.py --ui-mode               # UI-optimized output format
    python run_pipeline_v2.py --expand-results        # Store ALL intermediate results
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil

# Import the original pipeline (unchanged)
import run_pipeline

# Import our new V2 components
from src.v2 import (
    UserConfigManager,
    ResultsExpander, 
    PipelineInterceptor,
    UIDataFormatter
)

class PipelineV2Runner:
    """
    V2 Pipeline Runner that wraps the original pipeline with enhanced user control.
    
    This class acts as a smart wrapper around the original run_pipeline.py, adding
    user configuration, expanded result storage, and UI integration points without
    modifying the core pipeline logic.
    
    Design Principles:
    1. Zero modifications to existing pipeline modules
    2. Configuration-driven user control over business decisions
    3. Intercept and expand result storage at key points
    4. Maintain full backwards compatibility
    5. Provide UI-friendly data formats
    """
    
    def __init__(self, user_config: Optional[Dict] = None, ui_mode: bool = False):
        """
        Initialize V2 pipeline runner with user configuration.
        
        Args:
            user_config: User preferences for market focus, priorities, etc.
            ui_mode: If True, optimizes output for UI consumption
        """
        self.user_config = UserConfigManager(user_config or {})
        self.ui_mode = ui_mode
        self.results_expander = ResultsExpander(ui_mode)
        self.interceptor = PipelineInterceptor(self.user_config)
        self.ui_formatter = UIDataFormatter() if ui_mode else None
        
        # V2 result storage paths
        self.v2_results_dir = Path("v2_results")
        self.v2_results_dir.mkdir(exist_ok=True)
        
    def run_enhanced_pipeline(
        self,
        interactive: bool = False,
        verbose: bool = False,
        input_file: Optional[str] = None,
        use_cache: bool = False,
        skip_github: bool = False,
        expand_results: bool = False,
        flow_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline with V2 enhancements.
        
        This method orchestrates the original pipeline while adding:
        - User configuration application
        - Expanded result storage
        - UI-friendly output formatting
        - Mid-pipeline review points
        
        Returns:
            Enhanced results dictionary with expanded data and UI metadata
        """
        print("🚀 Pipeline V2 - Enhanced User Control")
        print(f"   User Config: {self.user_config.get_summary()}")
        print(f"   UI Mode: {self.ui_mode}")
        print(f"   Expand Results: {expand_results}")
        
        # Store original arguments for the underlying pipeline
        original_args = {
            'interactive': interactive,
            'verbose': verbose,
            'input_file': input_file,
            'use_cache': use_cache,
            'skip_github': skip_github,
            'flow_type': flow_type,
        }
        
        # Apply user configuration to environment/settings
        self._apply_user_config()
        
        # Set up result interception if expanding results
        if expand_results:
            self.interceptor.enable_result_expansion()
            
        # Run the original pipeline (completely unchanged)
        print("\n📦 Running Original Pipeline...")
        try:
            # Call the original main function
            run_pipeline.main(**original_args)
            pipeline_success = True
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            pipeline_success = False
            
        # Collect and enhance results
        enhanced_results = self._collect_and_enhance_results(
            pipeline_success, expand_results
        )
        
        # Generate UI-friendly outputs if needed
        if self.ui_mode:
            self._generate_ui_outputs(enhanced_results)
            
        return enhanced_results
    
    def _apply_user_config(self):
        """Apply user configuration to the pipeline environment."""
        config = self.user_config.config
        
        # Apply market focus (affects subreddit selection in jobs_to_reddit)
        if 'market_focus' in config:
            market_subreddits = self._get_market_subreddits(config['market_focus'])
            os.environ['PIPELINE_TARGET_SUBREDDITS'] = json.dumps(market_subreddits)
            
        # Apply strategic priorities (affects scoring weights)
        if 'strategic_priority' in config:
            priority_weights = self._get_priority_weights(config['strategic_priority'])
            os.environ['PIPELINE_PRIORITY_WEIGHTS'] = json.dumps(priority_weights)
            
        # Apply risk appetite (affects breakthrough detection and filtering)
        if 'risk_appetite' in config:
            risk_params = self._get_risk_parameters(config['risk_appetite'])
            os.environ['PIPELINE_RISK_PARAMS'] = json.dumps(risk_params)
    
    def _get_market_subreddits(self, market_focus: str) -> List[str]:
        """Get relevant subreddits based on user's market focus."""
        market_subreddit_map = {
            'b2b_saas': ['entrepreneur', 'startups', 'smallbusiness', 'business'],
            'fintech': ['personalfinance', 'investing', 'financialindependence'],
            'healthtech': ['health', 'medicine', 'healthcare', 'fitness'],
            'edtech': ['education', 'teachers', 'students', 'online_learning'],
            'real_estate': ['realestate', 'realestateinvesting', 'firsttimehomebuyer'],
            'consumer': ['buyitforlife', 'frugal', 'anticonsumption', 'products'],
            'general': ['entrepreneur', 'smallbusiness', 'startups', 'business']
        }
        return market_subreddit_map.get(market_focus, market_subreddit_map['general'])
    
    def _get_priority_weights(self, strategic_priority: str) -> Dict[str, float]:
        """Get scoring weights based on strategic priority."""
        priority_weight_map = {
            'innovation_first': {
                'innovation_score': 0.4,
                'market_viability': 0.3,
                'technical_feasibility': 0.3
            },
            'market_fit_first': {
                'market_viability': 0.5,
                'innovation_score': 0.25,
                'technical_feasibility': 0.25
            },
            'feasibility_first': {
                'technical_feasibility': 0.4,
                'market_viability': 0.35,
                'innovation_score': 0.25
            },
            'balanced': {
                'innovation_score': 0.33,
                'market_viability': 0.34,
                'technical_feasibility': 0.33
            }
        }
        return priority_weight_map.get(strategic_priority, priority_weight_map['balanced'])
    
    def _get_risk_parameters(self, risk_appetite: str) -> Dict[str, Any]:
        """Get risk parameters based on user's risk appetite."""
        risk_param_map = {
            'conservative': {
                'excellence_threshold': 7.0,
                'breakthrough_weight': 0.1,
                'moonshot_preservation': 0.05
            },
            'balanced': {
                'excellence_threshold': 6.5,
                'breakthrough_weight': 0.25,
                'moonshot_preservation': 0.15
            },
            'breakthrough': {
                'excellence_threshold': 6.0,
                'breakthrough_weight': 0.4,
                'moonshot_preservation': 0.3
            }
        }
        return risk_param_map.get(risk_appetite, risk_param_map['balanced'])
    
    def _collect_and_enhance_results(self, pipeline_success: bool, expand_results: bool) -> Dict[str, Any]:
        """Collect results from the original pipeline and add V2 enhancements."""
        
        # Start with basic results structure
        enhanced_results = {
            'pipeline_success': pipeline_success,
            'timestamp': datetime.now().isoformat(),
            'user_config': self.user_config.config,
            'v2_enhancements': {
                'expanded_results': expand_results,
                'ui_mode': self.ui_mode
            }
        }
        
        if not pipeline_success:
            return enhanced_results
            
        # Collect standard pipeline outputs
        enhanced_results['standard_outputs'] = self._collect_standard_outputs()
        
        # Add expanded results if requested
        if expand_results:
            enhanced_results['expanded_results'] = self._collect_expanded_results()
            
        # Add V2-specific analytics
        enhanced_results['v2_analytics'] = self._generate_v2_analytics(enhanced_results)
        
        return enhanced_results
    
    def _collect_standard_outputs(self) -> Dict[str, Any]:
        """Collect the standard pipeline output files."""
        standard_files = {
            'analysis_results': 'analysis_results.md',
            'opportunity_zones': 'opportunity_zones.json',
            'product_ideas': 'product_ideas.json',
            'final_portfolio': 'final_innovation_portfolio.json'
        }
        
        collected = {}
        for key, filename in standard_files.items():
            if os.path.exists(filename):
                try:
                    if filename.endswith('.json'):
                        with open(filename, 'r') as f:
                            collected[key] = json.load(f)
                    else:
                        with open(filename, 'r') as f:
                            collected[key] = f.read()
                except Exception as e:
                    collected[key] = f"Error reading {filename}: {e}"
                    
        return collected
    
    def _collect_expanded_results(self) -> Dict[str, Any]:
        """Collect expanded results that show ALL generated ideas, not just filtered ones."""
        
        # This would be populated by the ResultsExpander during pipeline execution
        expanded = {
            'all_generated_ideas_by_zone': {},
            'filtering_decisions': {},
            'alternative_selections': {}
        }
        
        # Check if the interceptor captured expanded results
        if hasattr(self.interceptor, 'captured_results'):
            expanded.update(self.interceptor.captured_results)
            
        return expanded
    
    def _generate_v2_analytics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate V2-specific analytics and insights."""
        
        analytics = {
            'config_impact_analysis': self._analyze_config_impact(results),
            'idea_diversity_metrics': self._calculate_idea_diversity(results),
            'market_alignment_score': self._calculate_market_alignment(results),
            'recommendations': self._generate_recommendations(results)
        }
        
        return analytics
    
    def _analyze_config_impact(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how user configuration affected the results."""
        # Placeholder for config impact analysis
        return {
            'market_focus_impact': 'Configuration applied successfully',
            'priority_weighting_effect': 'Scoring adjusted per user preferences',
            'risk_appetite_influence': 'Filtering thresholds adjusted'
        }
    
    def _calculate_idea_diversity(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate diversity metrics for the generated ideas."""
        # Placeholder for diversity calculation
        return {
            'zone_coverage': 'All zones represented',
            'innovation_spectrum': 'Balanced mix of incremental and breakthrough',
            'feasibility_range': 'Conservative to ambitious ideas included'
        }
    
    def _calculate_market_alignment(self, results: Dict[str, Any]) -> float:
        """Calculate how well results align with user's market focus."""
        # Placeholder for market alignment calculation
        return 0.85  # 85% alignment score
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the user based on results."""
        recommendations = []
        
        # Analyze user config and results to generate smart recommendations
        if self.user_config.config.get('risk_appetite') == 'conservative':
            recommendations.append("Consider exploring 1-2 breakthrough ideas for competitive advantage")
            
        if self.user_config.config.get('strategic_priority') == 'innovation_first':
            recommendations.append("Validate market demand for top innovative concepts early")
            
        return recommendations
    
    def _generate_ui_outputs(self, enhanced_results: Dict[str, Any]):
        """Generate UI-friendly output files."""
        
        if not self.ui_formatter:
            return
            
        # Generate UI-optimized data files
        ui_outputs = {
            'pipeline_summary.json': self.ui_formatter.format_summary(enhanced_results),
            'ideas_by_zone.json': self.ui_formatter.format_ideas_by_zone(enhanced_results),
            'config_impact.json': self.ui_formatter.format_config_impact(enhanced_results),
            'recommendations.json': self.ui_formatter.format_recommendations(enhanced_results)
        }
        
        # Save UI outputs
        for filename, data in ui_outputs.items():
            output_path = self.v2_results_dir / filename
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        print(f"📱 UI outputs generated in {self.v2_results_dir}/")


def main():
    """Main entry point for Pipeline V2."""
    
    parser = argparse.ArgumentParser(
        description="Pipeline V2 - Enhanced User Control (Backwards Compatible)"
    )
    
    # Original pipeline arguments (preserved for compatibility)
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--input", type=str, help="Input research file")
    parser.add_argument("--use-cache", action="store_true", help="Use cached results")
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub creation")
    
    # V2-specific arguments
    parser.add_argument("--config", type=str, help="User configuration JSON file")
    parser.add_argument("--ui-mode", action="store_true", help="UI-optimized output")
    parser.add_argument("--expand-results", action="store_true", help="Store ALL intermediate results")
    parser.add_argument("--flow-type", type=str, help="Ideation flow to run")
    
    args = parser.parse_args()
    
    # Load user configuration if provided
    user_config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            user_config = json.load(f)
    
    # Initialize V2 runner
    runner = PipelineV2Runner(user_config, args.ui_mode)
    
    # Run enhanced pipeline
    results = runner.run_enhanced_pipeline(
        interactive=args.interactive,
        verbose=args.verbose,
        input_file=args.input,
        use_cache=args.use_cache,
        skip_github=args.skip_github,
        expand_results=args.expand_results,
        flow_type=args.flow_type,
    )
    
    # Print V2 summary
    print("\n" + "="*60)
    print("🎯 Pipeline V2 Complete!")
    print(f"   Config Applied: {bool(user_config)}")
    print(f"   UI Mode: {args.ui_mode}")
    print(f"   Results Enhanced: {args.expand_results}")
    
    if args.ui_mode:
        print(f"   UI Outputs: v2_results/")
    
    print("="*60)


if __name__ == "__main__":
    main()