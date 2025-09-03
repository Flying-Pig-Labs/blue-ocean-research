"""
Shadow run testing framework for parallel validation of modular pipeline.
Runs both original and new pipeline versions in parallel to ensure identical behavior.
"""

import os
import json
import logging
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from .feature_flags import get_flavor_flags
from .config_schema import FlavorRegistry

@dataclass
class ShadowRunResult:
    """Results from a shadow run test."""
    test_id: str
    original_success: bool
    modular_success: bool
    outputs_match: bool
    execution_time_original: float
    execution_time_modular: float
    differences: List[Dict[str, Any]]
    error_original: Optional[str]
    error_modular: Optional[str]
    timestamp: str

@dataclass
class ValidationMetrics:
    """Validation metrics for shadow testing."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    match_rate: float
    average_time_original: float
    average_time_modular: float
    performance_ratio: float  # modular_time / original_time

class ShadowTestRunner:
    """Executes shadow run tests comparing original and modular pipelines."""
    
    def __init__(self, results_dir: str = "shadow_test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.flavor_registry = FlavorRegistry()
    
    def prepare_test_environment(self, test_id: str) -> Tuple[Path, Path]:
        """Prepare isolated test environments for both pipeline versions."""
        test_dir = self.results_dir / test_id
        test_dir.mkdir(parents=True, exist_ok=True)
        
        original_dir = test_dir / "original"
        modular_dir = test_dir / "modular"
        
        original_dir.mkdir(exist_ok=True)
        modular_dir.mkdir(exist_ok=True)
        
        return original_dir, modular_dir
    
    def run_original_pipeline(self, work_dir: Path, input_args: Dict[str, Any]) -> Tuple[bool, float, Optional[str], Dict[str, Any]]:
        """Run the original pipeline and capture results."""
        start_time = datetime.now()
        
        try:
            # Change to work directory
            original_cwd = os.getcwd()
            os.chdir(work_dir)
            
            # Build command arguments
            cmd = ["python", "../../run_pipeline.py"]
            
            # Add arguments based on input_args
            if input_args.get("input_file"):
                cmd.extend(["--input", input_args["input_file"]])
            if input_args.get("output_dir"):
                cmd.extend(["--output", input_args["output_dir"]])
            if input_args.get("github_repo"):
                cmd.extend(["--repo", input_args["github_repo"]])
            
            # Run the original pipeline
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Collect outputs
            outputs = self._collect_pipeline_outputs(work_dir)
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                return True, execution_time, None, outputs
            else:
                return False, execution_time, result.stderr, {}
                
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            return False, (datetime.now() - start_time).total_seconds(), "Pipeline timed out", {}
        except Exception as e:
            os.chdir(original_cwd)
            return False, (datetime.now() - start_time).total_seconds(), str(e), {}
    
    def run_modular_pipeline(self, work_dir: Path, input_args: Dict[str, Any], flavor: str = "baseline") -> Tuple[bool, float, Optional[str], Dict[str, Any]]:
        """Run the modular pipeline and capture results."""
        start_time = datetime.now()
        
        try:
            # Change to work directory
            original_cwd = os.getcwd()
            os.chdir(work_dir)
            
            # Build command arguments
            cmd = ["python", "../../run_pipeline_modular.py", "--flavor", flavor]
            
            # Add arguments based on input_args
            if input_args.get("input_file"):
                cmd.extend(["--input", input_args["input_file"]])
            if input_args.get("output_dir"):
                cmd.extend(["--output", input_args["output_dir"]])
            if input_args.get("github_repo"):
                cmd.extend(["--repo", input_args["github_repo"]])
            
            # Run the modular pipeline
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Collect outputs
            outputs = self._collect_pipeline_outputs(work_dir)
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                return True, execution_time, None, outputs
            else:
                return False, execution_time, result.stderr, {}
                
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            return False, (datetime.now() - start_time).total_seconds(), "Pipeline timed out", {}
        except Exception as e:
            os.chdir(original_cwd)
            return False, (datetime.now() - start_time).total_seconds(), str(e), {}
    
    def _collect_pipeline_outputs(self, work_dir: Path) -> Dict[str, Any]:
        """Collect all pipeline outputs for comparison."""
        outputs = {}
        
        # Expected output files
        output_files = [
            "opportunity_zones_advanced.json",
            "product_ideas_comprehensive.json",
            "final_innovation_portfolio.json",
            "product_ideas_report_comprehensive.md"
        ]
        
        for filename in output_files:
            file_path = work_dir / filename
            if file_path.exists():
                try:
                    if filename.endswith('.json'):
                        with open(file_path, 'r') as f:
                            outputs[filename] = json.load(f)
                    else:
                        with open(file_path, 'r') as f:
                            outputs[filename] = f.read()
                except Exception as e:
                    self.logger.warning(f"Failed to read {filename}: {e}")
        
        return outputs
    
    def compare_outputs(self, original_outputs: Dict[str, Any], modular_outputs: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Compare outputs from both pipeline versions."""
        differences = []
        
        # Check if same files were generated
        original_files = set(original_outputs.keys())
        modular_files = set(modular_outputs.keys())
        
        if original_files != modular_files:
            differences.append({
                "type": "file_set_mismatch",
                "original_files": list(original_files),
                "modular_files": list(modular_files),
                "missing_in_modular": list(original_files - modular_files),
                "extra_in_modular": list(modular_files - original_files)
            })
        
        # Compare content of common files
        common_files = original_files & modular_files
        
        for filename in common_files:
            if filename.endswith('.json'):
                diff = self._compare_json_content(
                    original_outputs[filename],
                    modular_outputs[filename],
                    filename
                )
                if diff:
                    differences.extend(diff)
            else:
                # Text file comparison
                if original_outputs[filename] != modular_outputs[filename]:
                    differences.append({
                        "type": "text_content_mismatch",
                        "file": filename,
                        "original_length": len(original_outputs[filename]),
                        "modular_length": len(modular_outputs[filename])
                    })
        
        outputs_match = len(differences) == 0
        return outputs_match, differences
    
    def _compare_json_content(self, original: Any, modular: Any, context: str) -> List[Dict[str, Any]]:
        """Compare JSON content and identify differences."""
        differences = []
        
        if type(original) != type(modular):
            differences.append({
                "type": "type_mismatch",
                "context": context,
                "original_type": type(original).__name__,
                "modular_type": type(modular).__name__
            })
            return differences
        
        if isinstance(original, dict):
            original_keys = set(original.keys())
            modular_keys = set(modular.keys())
            
            if original_keys != modular_keys:
                differences.append({
                    "type": "key_mismatch",
                    "context": context,
                    "missing_in_modular": list(original_keys - modular_keys),
                    "extra_in_modular": list(modular_keys - original_keys)
                })
            
            # Compare common keys
            for key in original_keys & modular_keys:
                subdiff = self._compare_json_content(
                    original[key],
                    modular[key],
                    f"{context}.{key}"
                )
                differences.extend(subdiff)
        
        elif isinstance(original, list):
            if len(original) != len(modular):
                differences.append({
                    "type": "list_length_mismatch",
                    "context": context,
                    "original_length": len(original),
                    "modular_length": len(modular)
                })
            
            # Compare elements up to the shorter length
            for i in range(min(len(original), len(modular))):
                subdiff = self._compare_json_content(
                    original[i],
                    modular[i],
                    f"{context}[{i}]"
                )
                differences.extend(subdiff)
        
        else:
            # Primitive value comparison
            if original != modular:
                differences.append({
                    "type": "value_mismatch",
                    "context": context,
                    "original_value": original,
                    "modular_value": modular
                })
        
        return differences
    
    def run_shadow_test(self, test_config: Dict[str, Any], flavor: str = "baseline") -> ShadowRunResult:
        """Execute a single shadow run test."""
        test_id = f"shadow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(test_config).encode()).hexdigest()[:8]}"
        
        self.logger.info(f"Starting shadow test {test_id}")
        
        # Prepare test environments
        original_dir, modular_dir = self.prepare_test_environment(test_id)
        
        # Run both pipelines
        original_success, original_time, original_error, original_outputs = self.run_original_pipeline(
            original_dir, test_config
        )
        
        modular_success, modular_time, modular_error, modular_outputs = self.run_modular_pipeline(
            modular_dir, test_config, flavor
        )
        
        # Compare outputs
        outputs_match = False
        differences = []
        
        if original_success and modular_success:
            outputs_match, differences = self.compare_outputs(original_outputs, modular_outputs)
        
        # Create result
        result = ShadowRunResult(
            test_id=test_id,
            original_success=original_success,
            modular_success=modular_success,
            outputs_match=outputs_match,
            execution_time_original=original_time,
            execution_time_modular=modular_time,
            differences=differences,
            error_original=original_error,
            error_modular=modular_error,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Save result
        self._save_shadow_test_result(result)
        
        self.logger.info(f"Shadow test {test_id} completed: match={outputs_match}")
        
        return result
    
    def _save_shadow_test_result(self, result: ShadowRunResult):
        """Save shadow test result to file."""
        result_file = self.results_dir / f"{result.test_id}.json"
        
        try:
            with open(result_file, 'w') as f:
                json.dump(asdict(result), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save shadow test result: {e}")
    
    def run_shadow_test_batch(self, test_configs: List[Dict[str, Any]], 
                             flavor: str = "baseline", 
                             max_workers: int = 3) -> List[ShadowRunResult]:
        """Run multiple shadow tests in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_config = {
                executor.submit(self.run_shadow_test, config, flavor): config
                for config in test_configs
            }
            
            for future in as_completed(future_to_config):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Shadow test failed: {e}")
        
        return results
    
    def generate_validation_report(self, results: List[ShadowRunResult]) -> ValidationMetrics:
        """Generate validation metrics from shadow test results."""
        if not results:
            return ValidationMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0)
        
        total_runs = len(results)
        successful_runs = sum(1 for r in results if r.original_success and r.modular_success and r.outputs_match)
        failed_runs = total_runs - successful_runs
        match_rate = successful_runs / total_runs if total_runs > 0 else 0.0
        
        # Calculate average execution times
        original_times = [r.execution_time_original for r in results if r.original_success]
        modular_times = [r.execution_time_modular for r in results if r.modular_success]
        
        avg_time_original = sum(original_times) / len(original_times) if original_times else 0.0
        avg_time_modular = sum(modular_times) / len(modular_times) if modular_times else 0.0
        
        performance_ratio = avg_time_modular / avg_time_original if avg_time_original > 0 else 0.0
        
        return ValidationMetrics(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            match_rate=match_rate,
            average_time_original=avg_time_original,
            average_time_modular=avg_time_modular,
            performance_ratio=performance_ratio
        )

class ShadowTestOrchestrator:
    """Orchestrates shadow testing as part of the rollout process."""
    
    def __init__(self):
        self.runner = ShadowTestRunner()
        self.flavor_flags = get_flavor_flags()
        self.logger = logging.getLogger(__name__)
    
    def should_run_shadow_test(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if shadow testing should be enabled."""
        return self.flavor_flags.should_run_shadow_test(context)
    
    def create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create comprehensive test scenarios for validation."""
        scenarios = [
            {
                "name": "basic_test",
                "input_file": "test_input_basic.json",
                "output_dir": "test_output",
                "github_repo": None
            },
            {
                "name": "full_pipeline_test",
                "input_file": "test_input_comprehensive.json",
                "output_dir": "test_output_full",
                "github_repo": "test-org/test-repo"
            },
            {
                "name": "minimal_input_test",
                "input_file": "test_input_minimal.json",
                "output_dir": "test_output_minimal",
                "github_repo": None
            }
        ]
        
        return scenarios
    
    def execute_validation_suite(self, flavor: str = "baseline") -> ValidationMetrics:
        """Execute full validation suite for a flavor."""
        self.logger.info(f"Starting validation suite for flavor: {flavor}")
        
        # Create test scenarios
        test_scenarios = self.create_test_scenarios()
        
        # Run shadow tests
        results = self.runner.run_shadow_test_batch(test_scenarios, flavor)
        
        # Generate validation report
        metrics = self.runner.generate_validation_report(results)
        
        self.logger.info(
            f"Validation complete: {metrics.successful_runs}/{metrics.total_runs} successful, "
            f"match rate: {metrics.match_rate:.2%}"
        )
        
        return metrics
    
    def continuous_validation(self, flavor: str = "baseline", 
                            interval_hours: int = 24,
                            min_match_rate: float = 0.95):
        """Run continuous validation during rollout."""
        while True:
            try:
                metrics = self.execute_validation_suite(flavor)
                
                if metrics.match_rate < min_match_rate:
                    self.logger.warning(
                        f"Match rate {metrics.match_rate:.2%} below threshold {min_match_rate:.2%}. "
                        "Consider rollback."
                    )
                    # Could trigger automatic rollback here
                
                # Wait for next validation cycle
                asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Continuous validation error: {e}")
                asyncio.sleep(600)  # Wait 10 minutes before retry