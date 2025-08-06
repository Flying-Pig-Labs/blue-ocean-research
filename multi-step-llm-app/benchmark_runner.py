#!/usr/bin/env python3
"""
Benchmark Runner - Test different model configurations per step in isolation
Allows comparing model performance, cost, and quality across variations
"""

import os
import yaml
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import argparse
from pathlib import Path

from config_loader import ConfigLoader


class BenchmarkRunner:
    """Run benchmarks for pipeline steps with different model configurations."""
    
    def __init__(self, step_name: str, benchmark_dir: str = "test/benchmarks"):
        """Initialize benchmark runner for a specific step."""
        self.step_name = step_name
        self.benchmark_dir = Path(benchmark_dir) / step_name
        self.results_dir = self.benchmark_dir / "results"
        
        if not self.benchmark_dir.exists():
            raise ValueError(f"Benchmark directory not found: {self.benchmark_dir}")
        
        self.config_file = self.benchmark_dir / "config.yml"
        if not self.config_file.exists():
            raise ValueError(f"Benchmark config not found: {self.config_file}")
        
        # Load benchmark configuration
        with open(self.config_file, 'r') as f:
            self.benchmark_config = yaml.safe_load(f)
        
        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)
    
    def run_all_options(self, dry_run: bool = False) -> Dict[str, Dict[str, Any]]:
        """Run all benchmark options and collect results."""
        print(f"🚀 Running benchmark: {self.benchmark_config['benchmark_name']}")
        print(f"📝 Description: {self.benchmark_config['description']}")
        print(f"🎯 Step: {self.step_name}")
        print(f"📊 Options: {len(self.benchmark_config['options'])}")
        print("-" * 60)
        
        results = {}
        
        for option_name, option_config in self.benchmark_config['options'].items():
            print(f"\n🔄 Running option: {option_name}")
            print(f"   Name: {option_config['name']}")
            print(f"   Description: {option_config['description']}")
            
            if dry_run:
                print("   [DRY RUN - Skipping actual execution]")
                continue
            
            try:
                start_time = time.time()
                result = self._run_single_option(option_name, option_config)
                end_time = time.time()
                
                # Add timing and metadata
                result['metadata'] = {
                    'option_name': option_name,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_seconds': end_time - start_time,
                    'timestamp': datetime.now().isoformat(),
                }
                
                results[option_name] = result
                
                # Save individual result to file
                result_file = self.results_dir / f"{option_name}.txt"
                self._save_result_file(result_file, result, option_config)
                
                print(f"   ✅ Completed in {result['metadata']['duration_seconds']:.2f}s")
                print(f"   📁 Result saved to: {result_file}")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
                results[option_name] = {
                    'error': str(e),
                    'metadata': {
                        'option_name': option_name,
                        'timestamp': datetime.now().isoformat(),
                        'failed': True
                    }
                }
        
        # Save summary report
        summary_file = self.results_dir / "benchmark_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'benchmark_name': self.benchmark_config['benchmark_name'],
                'step_name': self.step_name,
                'run_timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)
        
        print(f"\n📊 Benchmark complete! Summary saved to: {summary_file}")
        return results
    
    def _run_single_option(self, option_name: str, option_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single benchmark option."""
        # Create a modified config loader with overrides
        modified_config = self._apply_config_overrides(option_config.get('overrides', {}))
        
        # Import the step module and run it with the mock input
        if self.step_name == 'research_analyzer':
            return self._run_research_analyzer(modified_config)
        elif self.step_name == 'jobs_researcher':
            return self._run_jobs_researcher(modified_config)
        elif self.step_name == 'cluster_jtbd':
            return self._run_cluster_jtbd(modified_config)
        elif self.step_name == 'value_curve_mapper':
            return self._run_value_curve_mapper(modified_config)
        elif self.step_name == 'product_idea_generator':
            return self._run_product_idea_generator(modified_config)
        elif self.step_name == 'idea_consolidator':
            return self._run_idea_consolidator(modified_config)
        elif self.step_name == 'github_integration':
            return self._run_github_integration(modified_config)
        else:
            raise ValueError(f"Unknown step: {self.step_name}")
    
    def _apply_config_overrides(self, overrides: Dict[str, Any]) -> ConfigLoader:
        """Create a modified ConfigLoader with benchmark overrides including prompts."""
        # Load the original config
        config_loader = ConfigLoader()
        
        # Apply overrides to the config (including model settings and prompts)
        for section, section_overrides in overrides.items():
            if section in config_loader.config.get('models', {}):
                for task, task_overrides in section_overrides.items():
                    if task in config_loader.config['models'][section]:
                        # Update all settings (model, temperature, max_tokens, prompt, etc.)
                        config_loader.config['models'][section][task].update(task_overrides)
        
        return config_loader
    
    def _run_research_analyzer(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run research analyzer with mock input."""
        from research_analyzer import ResearchAnalyzer
        
        # Load mock input
        mock_file = self.benchmark_dir / self.benchmark_config['mock_input']
        if not mock_file.exists():
            raise FileNotFoundError(f"Mock input file not found: {mock_file}")
        
        with open(mock_file, 'r') as f:
            mock_data = json.load(f)
        
        # Create analyzer with modified config
        analyzer = ResearchAnalyzer()
        analyzer.config_loader = config_loader
        
        # Run the analysis
        result = analyzer.process_research_document(mock_data)
        
        return {
            'output': result,
            'input_file': str(mock_file),
            'token_usage': 'N/A - would need API integration',
            'model_configs': {
                'verticals': config_loader.get_model_settings('research_analysis', 'verticals'),
                'personas': config_loader.get_model_settings('research_analysis', 'personas'),
                'pain_points': config_loader.get_model_settings('research_analysis', 'pain_points'),
                'solution_types': config_loader.get_model_settings('research_analysis', 'solution_types')
            }
        }
    
    def _run_jobs_researcher(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run jobs researcher with mock input."""
        # Implementation placeholder - would need to mock EXA API calls
        return {
            'output': 'Jobs researcher benchmark - requires EXA API integration',
            'model_configs': {
                'jtbd_synthesis': config_loader.get_model_settings('jtbd_synthesis')
            }
        }
    
    def _run_cluster_jtbd(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run JTBD clustering with mock input."""
        # Implementation placeholder - would need to mock Cohere embeddings
        return {
            'output': 'JTBD clustering benchmark - requires Cohere API integration',
            'model_configs': {
                'embeddings': config_loader.get_model_config('clustering', 'embeddings'),
                'naming': config_loader.get_model_settings('clustering', 'naming')
            }
        }
    
    def _run_value_curve_mapper(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run value curve mapping with mock input."""
        # Implementation placeholder
        return {
            'output': 'Value curve mapping benchmark - requires EXA API integration',
            'model_configs': {
                'analysis': config_loader.get_model_settings('value_curve', 'analysis'),
                'synthesis': config_loader.get_model_settings('value_curve', 'synthesis')
            }
        }
    
    def _run_product_idea_generator(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run product idea generator with mock input."""
        # Implementation placeholder
        return {
            'output': 'Product idea generation benchmark - requires OpenAI o1 integration',
            'model_configs': {
                'generation': config_loader.get_model_settings('product_ideas', 'generation'),
                'enrichment': config_loader.get_model_settings('product_ideas', 'enrichment')
            }
        }
    
    def _run_idea_consolidator(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run idea consolidation with mock input."""
        # Implementation placeholder
        return {
            'output': 'Idea consolidation benchmark - requires Anthropic API integration',
            'model_configs': {
                'analysis': config_loader.get_model_settings('consolidation', 'analysis')
            }
        }
    
    def _run_github_integration(self, config_loader: ConfigLoader) -> Dict[str, Any]:
        """Run GitHub integration with mock input."""
        # Implementation placeholder - no model configs for this step
        return {
            'output': 'GitHub integration benchmark - requires GitHub API and input files',
            'model_configs': {
                'naming': config_loader.get_model_settings('github_naming')
            }
        }
    
    def _save_result_file(self, result_file: Path, result: Dict[str, Any], option_config: Dict[str, Any]):
        """Save detailed result to a text file for manual review."""
        with open(result_file, 'w') as f:
            f.write(f"# Benchmark Result: {option_config['name']}\n")
            f.write(f"Description: {option_config['description']}\n")
            f.write(f"Timestamp: {result['metadata']['timestamp']}\n")
            f.write(f"Duration: {result['metadata']['duration_seconds']:.2f} seconds\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("## Model Configurations Used:\n")
            for config_name, config_values in result.get('model_configs', {}).items():
                f.write(f"\n### {config_name}:\n")
                for key, value in config_values.items():
                    f.write(f"  {key}: {value}\n")
            
            f.write("\n" + "=" * 60 + "\n\n")
            f.write("## Output:\n")
            if isinstance(result.get('output'), dict):
                f.write(json.dumps(result['output'], indent=2))
            else:
                f.write(str(result.get('output', 'No output')))
            
            if 'error' in result:
                f.write(f"\n\n## Error:\n{result['error']}")


def main():
    """CLI interface for benchmark runner."""
    parser = argparse.ArgumentParser(description='Run pipeline step benchmarks')
    parser.add_argument('step', nargs='?', help='Step name to benchmark (e.g., research_analyzer)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be run without executing')
    parser.add_argument('--list-steps', action='store_true', help='List available benchmark steps')
    
    args = parser.parse_args()
    
    if args.list_steps:
        benchmark_dir = Path('test/benchmarks')
        if benchmark_dir.exists():
            steps = [d.name for d in benchmark_dir.iterdir() if d.is_dir()]
            print("Available benchmark steps:")
            for step in sorted(steps):
                print(f"  - {step}")
        else:
            print("No benchmark directory found")
        return
    
    try:
        runner = BenchmarkRunner(args.step)
        results = runner.run_all_options(dry_run=args.dry_run)
        
        if not args.dry_run:
            print("\n📈 Benchmark Results Summary:")
            for option_name, result in results.items():
                if 'error' in result:
                    print(f"  ❌ {option_name}: Failed - {result['error']}")
                else:
                    duration = result['metadata']['duration_seconds']
                    print(f"  ✅ {option_name}: Completed in {duration:.2f}s")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    main()