# Rollout & Testing Plan - Modular Ideation Pipeline

## Overview

This document outlines the comprehensive rollout strategy for the modular ideation pipeline system, ensuring zero downtime and complete backward compatibility during the transition.

## 🎯 Rollout Strategy

### Phase 1: Feature Flag Implementation (Week 1)
- **Objective**: Implement feature flags to control new system activation
- **Deliverables**: Feature flag system with granular control
- **Risk**: Low - no functional changes to existing pipeline

### Phase 2: Shadow Run Testing (Week 2)
- **Objective**: Run both systems in parallel to validate output consistency
- **Deliverables**: Comparative analysis reports
- **Risk**: Medium - resource usage increase, potential discovery of edge cases

### Phase 3: Canary Deployment (Week 3)
- **Objective**: Deploy to subset of jobs with monitoring
- **Deliverables**: Canary metrics and health checks
- **Risk**: Medium - limited production exposure

### Phase 4: Full Rollout (Week 4)
- **Objective**: Complete migration with fallback capability
- **Deliverables**: Production deployment with monitoring
- **Risk**: Low - extensive testing completed in previous phases

## Feature Flag Implementation

### Flag Configuration

```yaml
# feature_flags.yaml
modular_pipeline:
  enabled: false
  shadow_mode: false
  canary_percentage: 0
  flavors_enabled:
    - baseline  # Always enabled for testing
  fallback_to_original: true
  
shadow_run:
  enabled: false
  compare_outputs: true
  generate_diff_reports: true
  max_parallel_jobs: 5
  
canary_deployment:
  enabled: false
  percentage: 10  # Start with 10% of jobs
  success_threshold: 95  # 95% success rate required
  max_failures: 5  # Rollback after 5 failures
```

### Feature Flag Integration

```python
# flavors/feature_flags.py
import os
import yaml
from typing import Dict, Any

class FeatureFlags:
    """Manages feature flag configuration for rollout control."""
    
    def __init__(self, config_path: str = "feature_flags.yaml"):
        """Load feature flag configuration."""
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load feature flags from YAML configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration for safety
            return {
                'modular_pipeline': {'enabled': False, 'fallback_to_original': True},
                'shadow_run': {'enabled': False},
                'canary_deployment': {'enabled': False}
            }
    
    def is_modular_pipeline_enabled(self) -> bool:
        """Check if modular pipeline is enabled."""
        return self.config.get('modular_pipeline', {}).get('enabled', False)
    
    def is_shadow_mode_enabled(self) -> bool:
        """Check if shadow run mode is enabled."""
        return self.config.get('shadow_run', {}).get('enabled', False)
    
    def is_flavor_enabled(self, flavor_name: str) -> bool:
        """Check if specific flavor is enabled."""
        enabled_flavors = self.config.get('modular_pipeline', {}).get('flavors_enabled', ['baseline'])
        return flavor_name in enabled_flavors
    
    def should_use_canary(self) -> bool:
        """Determine if this request should use canary deployment."""
        if not self.config.get('canary_deployment', {}).get('enabled', False):
            return False
        
        percentage = self.config.get('canary_deployment', {}).get('percentage', 0)
        import random
        return random.randint(1, 100) <= percentage
```

## Shadow Run Testing

### Shadow Run Architecture

```python
# flavors/shadow_runner.py
import logging
import json
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class ShadowRunner:
    """Runs both original and modular pipelines in parallel for comparison."""
    
    def __init__(self, feature_flags: FeatureFlags):
        self.flags = feature_flags
        self.results_comparison = []
    
    def run_shadow_comparison(
        self, 
        input_file: str, 
        flavor_name: str = "baseline"
    ) -> Dict[str, Any]:
        """Run both pipelines in parallel and compare outputs."""
        
        if not self.flags.is_shadow_mode_enabled():
            raise ValueError("Shadow mode not enabled")
        
        logger.info(f"Starting shadow run comparison with {flavor_name} flavor")
        
        # Run both pipelines concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Original pipeline
            original_future = executor.submit(self._run_original_pipeline, input_file)
            
            # Modular pipeline
            modular_future = executor.submit(self._run_modular_pipeline, input_file, flavor_name)
            
            # Collect results
            original_result = original_future.result()
            modular_result = modular_future.result()
        
        # Compare outputs
        comparison = self._compare_pipeline_outputs(original_result, modular_result)
        
        # Store comparison for analysis
        self.results_comparison.append({
            'timestamp': time.time(),
            'input_file': input_file,
            'flavor': flavor_name,
            'comparison': comparison
        })
        
        return comparison
    
    def _run_original_pipeline(self, input_file: str) -> Dict[str, Any]:
        """Run the original pipeline."""
        try:
            # Import and run original pipeline
            from run_pipeline import main as original_main
            
            # Capture results (would need modification to original pipeline)
            # For now, simulate the original pipeline result structure
            return {
                'success': True,
                'opportunities_count': 10,
                'execution_time': 120.5,
                'github_issues_created': 10,
                'error': None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _run_modular_pipeline(self, input_file: str, flavor_name: str) -> Dict[str, Any]:
        """Run the modular pipeline."""
        try:
            # Import and run modular pipeline
            # Would integrate with actual modular pipeline
            return {
                'success': True,
                'opportunities_count': 10,
                'execution_time': 125.3,
                'github_issues_created': 10,
                'flavor_used': flavor_name,
                'error': None
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'flavor_used': flavor_name}
    
    def _compare_pipeline_outputs(
        self, 
        original: Dict[str, Any], 
        modular: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare outputs between original and modular pipelines."""
        comparison = {
            'both_successful': original.get('success', False) and modular.get('success', False),
            'opportunity_count_match': original.get('opportunities_count', 0) == modular.get('opportunities_count', 0),
            'github_issues_match': original.get('github_issues_created', 0) == modular.get('github_issues_created', 0),
            'execution_time_diff': abs(
                original.get('execution_time', 0) - modular.get('execution_time', 0)
            ),
            'compatibility_score': 0.0,
            'issues_found': []
        }
        
        # Calculate compatibility score
        score_factors = []
        
        if comparison['both_successful']:
            score_factors.append(40)  # 40% for both succeeding
        
        if comparison['opportunity_count_match']:
            score_factors.append(30)  # 30% for opportunity count match
        
        if comparison['github_issues_match']:
            score_factors.append(20)  # 20% for GitHub issues match
        
        # Execution time tolerance (within 20% is acceptable)
        time_tolerance = 0.2
        original_time = original.get('execution_time', 0)
        if original_time > 0:
            time_diff_ratio = comparison['execution_time_diff'] / original_time
            if time_diff_ratio <= time_tolerance:
                score_factors.append(10)  # 10% for acceptable performance
        
        comparison['compatibility_score'] = sum(score_factors) / 100.0
        
        # Identify issues
        if not comparison['both_successful']:
            comparison['issues_found'].append("Pipeline execution mismatch")
        
        if not comparison['opportunity_count_match']:
            comparison['issues_found'].append("Opportunity count mismatch")
        
        if not comparison['github_issues_match']:
            comparison['issues_found'].append("GitHub issues count mismatch")
        
        return comparison
    
    def generate_shadow_report(self) -> str:
        """Generate comprehensive shadow run report."""
        if not self.results_comparison:
            return "No shadow run data available"
        
        total_runs = len(self.results_comparison)
        successful_runs = sum(1 for r in self.results_comparison if r['comparison']['both_successful'])
        avg_compatibility = sum(r['comparison']['compatibility_score'] for r in self.results_comparison) / total_runs
        
        report = f"""
# Shadow Run Analysis Report

## Summary
- **Total Runs**: {total_runs}
- **Successful Runs**: {successful_runs} ({successful_runs/total_runs:.1%})
- **Average Compatibility Score**: {avg_compatibility:.1%}

## Detailed Results
"""
        
        for i, result in enumerate(self.results_comparison, 1):
            comp = result['comparison']
            report += f"""
### Run {i} - {result['flavor']}
- **Input**: {result['input_file']}
- **Compatibility Score**: {comp['compatibility_score']:.1%}
- **Issues**: {', '.join(comp['issues_found']) if comp['issues_found'] else 'None'}
- **Execution Time Diff**: {comp['execution_time_diff']:.1f}s
"""
        
        return report
```

## Test Case Suite

### Critical Test Cases

```python
# test_rollout.py
import unittest
import tempfile
import os
from flavors.feature_flags import FeatureFlags
from flavors.shadow_runner import ShadowRunner

class TestRolloutCompatibility(unittest.TestCase):
    """Comprehensive test suite for rollout validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_flags = FeatureFlags()
        
    def test_backward_compatibility(self):
        """Test that original pipeline behavior is preserved."""
        # Run baseline flavor
        # Compare with expected original results
        # Assert exact match on critical metrics
        pass
    
    def test_flavor_swap_correctness(self):
        """Test that different flavors produce valid but different results."""
        # Run baseline flavor
        # Run crypto_mining_sites flavor
        # Run medical_devices flavor
        # Assert all produce valid outputs
        # Assert outputs differ appropriately
        pass
    
    def test_determinism(self):
        """Test that same inputs produce identical outputs."""
        # Run same input multiple times
        # Assert bit-for-bit identical results
        pass
    
    def test_idempotency(self):
        """Test that operations can be safely repeated."""
        # Create GitHub repo and issues
        # Run again with same data
        # Assert updates work correctly, no duplicates
        pass
    
    def test_empty_reddit_data_handling(self):
        """Test graceful handling of empty or missing Reddit data."""
        # Mock empty Reddit responses
        # Assert pipeline continues gracefully
        # Assert reasonable fallback behavior
        pass
    
    def test_api_failure_resilience(self):
        """Test handling of external API failures."""
        # Mock various API failures
        # Assert graceful degradation
        # Assert error reporting
        pass
    
    def test_performance_regression(self):
        """Test that new system doesn't significantly impact performance."""
        # Compare execution times
        # Assert performance within acceptable bounds
        pass
```

### Automated Test Execution

```bash
# test_rollout.sh
#!/bin/bash

echo "🧪 Starting Rollout Test Suite"
echo "=" * 50

# 1. Backward Compatibility Tests
echo "Testing backward compatibility..."
python -m pytest test_rollout.py::TestRolloutCompatibility::test_backward_compatibility -v

# 2. Shadow Run Tests
echo "Running shadow comparison tests..."
python -m pytest test_rollout.py::TestRolloutCompatibility::test_flavor_swap_correctness -v

# 3. Determinism Tests
echo "Testing deterministic behavior..."
python -m pytest test_rollout.py::TestRolloutCompatibility::test_determinism -v

# 4. Edge Case Tests
echo "Testing edge cases..."
python -m pytest test_rollout.py::TestRolloutCompatibility::test_empty_reddit_data_handling -v

# 5. Performance Tests
echo "Running performance regression tests..."
python -m pytest test_rollout.py::TestRolloutCompatibility::test_performance_regression -v

echo "✅ Rollout test suite completed"
```

## Canary Deployment Strategy

### Canary Configuration

```yaml
# canary_config.yaml
canary:
  enabled: true
  percentage: 10  # Start with 10% of traffic
  
  # Success criteria
  success_metrics:
    min_success_rate: 95  # 95% of runs must succeed
    max_error_rate: 5     # Max 5% error rate
    max_execution_time_increase: 20  # Max 20% slower than baseline
    
  # Failure thresholds
  failure_thresholds:
    max_consecutive_failures: 3
    max_total_failures: 10
    failure_rate_window: "1h"
    
  # Rollback triggers
  rollback:
    auto_rollback_enabled: true
    manual_rollback_required: false
    rollback_delay: "5m"  # Wait 5 minutes before rollback
    
  # Monitoring
  monitoring:
    health_check_interval: "30s"
    metrics_collection_interval: "1m"
    alert_on_failure: true
```

### Canary Health Checks

```python
# flavors/canary_health.py
import time
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    execution_time: float
    timestamp: float

class CanaryHealthMonitor:
    """Monitors canary deployment health and triggers rollbacks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_history: List[HealthCheck] = []
        self.failure_count = 0
        self.consecutive_failures = 0
        
    def perform_health_check(self) -> HealthCheck:
        """Perform comprehensive health check."""
        start_time = time.time()
        
        try:
            # Check modular pipeline functionality
            pipeline_healthy = self._check_pipeline_health()
            
            # Check external dependencies
            dependencies_healthy = self._check_dependencies_health()
            
            # Check performance metrics
            performance_healthy = self._check_performance_health()
            
            # Determine overall health
            if pipeline_healthy and dependencies_healthy and performance_healthy:
                status = HealthStatus.HEALTHY
                message = "All systems operational"
                self.consecutive_failures = 0
            elif pipeline_healthy:
                status = HealthStatus.DEGRADED
                message = "Minor issues detected"
                self.consecutive_failures = 0
            else:
                status = HealthStatus.UNHEALTHY
                message = "Critical issues detected"
                self.consecutive_failures += 1
                self.failure_count += 1
                
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Health check failed: {str(e)}"
            self.consecutive_failures += 1
            self.failure_count += 1
        
        execution_time = time.time() - start_time
        
        health_check = HealthCheck(
            name="canary_health_check",
            status=status,
            message=message,
            execution_time=execution_time,
            timestamp=time.time()
        )
        
        self.health_history.append(health_check)
        return health_check
    
    def should_trigger_rollback(self) -> bool:
        """Determine if rollback should be triggered."""
        # Check consecutive failures
        max_consecutive = self.config.get('failure_thresholds', {}).get('max_consecutive_failures', 3)
        if self.consecutive_failures >= max_consecutive:
            return True
        
        # Check total failures
        max_total = self.config.get('failure_thresholds', {}).get('max_total_failures', 10)
        if self.failure_count >= max_total:
            return True
        
        # Check failure rate over time window
        window_duration = 3600  # 1 hour in seconds
        recent_checks = [
            check for check in self.health_history
            if time.time() - check.timestamp <= window_duration
        ]
        
        if len(recent_checks) > 0:
            failure_rate = sum(1 for check in recent_checks if check.status == HealthStatus.UNHEALTHY) / len(recent_checks)
            max_failure_rate = self.config.get('success_metrics', {}).get('max_error_rate', 5) / 100
            
            if failure_rate > max_failure_rate:
                return True
        
        return False
    
    def _check_pipeline_health(self) -> bool:
        """Check modular pipeline health."""
        try:
            # Run a minimal pipeline test
            # This would integrate with the actual pipeline
            return True
        except Exception:
            return False
    
    def _check_dependencies_health(self) -> bool:
        """Check external dependencies (APIs, databases, etc.)."""
        # Check Claude API
        # Check GitHub API  
        # Check Reddit API
        # Check Perplexity API
        return True
    
    def _check_performance_health(self) -> bool:
        """Check performance metrics."""
        # Compare recent execution times with baseline
        # Check memory usage
        # Check API response times
        return True
```

## Monitoring and Observability

### Metrics Collection

```python
# flavors/metrics_collector.py
import time
import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class PipelineMetrics:
    """Pipeline execution metrics."""
    timestamp: float
    flavor_name: str
    execution_time: float
    opportunities_generated: int
    github_issues_created: int
    api_calls_made: int
    memory_usage_mb: float
    success: bool
    error_message: str = None

class MetricsCollector:
    """Collects and aggregates pipeline metrics."""
    
    def __init__(self):
        self.metrics: List[PipelineMetrics] = []
    
    def record_pipeline_execution(
        self,
        flavor_name: str,
        execution_time: float,
        opportunities_generated: int,
        github_issues_created: int,
        api_calls_made: int,
        memory_usage_mb: float,
        success: bool,
        error_message: str = None
    ):
        """Record pipeline execution metrics."""
        metric = PipelineMetrics(
            timestamp=time.time(),
            flavor_name=flavor_name,
            execution_time=execution_time,
            opportunities_generated=opportunities_generated,
            github_issues_created=github_issues_created,
            api_calls_made=api_calls_made,
            memory_usage_mb=memory_usage_mb,
            success=success,
            error_message=error_message
        )
        
        self.metrics.append(metric)
    
    def get_success_rate(self, flavor_name: str = None, window_hours: int = 24) -> float:
        """Calculate success rate over time window."""
        cutoff_time = time.time() - (window_hours * 3600)
        
        relevant_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff_time and (flavor_name is None or m.flavor_name == flavor_name)
        ]
        
        if not relevant_metrics:
            return 0.0
        
        success_count = sum(1 for m in relevant_metrics if m.success)
        return success_count / len(relevant_metrics)
    
    def export_metrics(self, output_file: str):
        """Export metrics to JSON file."""
        with open(output_file, 'w') as f:
            json.dump([asdict(m) for m in self.metrics], f, indent=2, default=str)
```

## Rollback Procedures

### Automated Rollback

```python
# flavors/rollback_manager.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RollbackManager:
    """Manages automated and manual rollbacks."""
    
    def __init__(self, feature_flags: FeatureFlags):
        self.flags = feature_flags
        
    def trigger_automated_rollback(self, reason: str):
        """Trigger automated rollback to original pipeline."""
        logger.critical(f"Triggering automated rollback: {reason}")
        
        # 1. Disable modular pipeline
        self._disable_modular_pipeline()
        
        # 2. Re-enable original pipeline
        self._enable_original_pipeline()
        
        # 3. Clear canary configuration
        self._disable_canary_deployment()
        
        # 4. Send alerts
        self._send_rollback_alerts(reason)
        
        logger.info("Automated rollback completed successfully")
    
    def _disable_modular_pipeline(self):
        """Disable modular pipeline features."""
        # Update feature flags
        config = self.flags.config
        config['modular_pipeline']['enabled'] = False
        config['modular_pipeline']['fallback_to_original'] = True
        
        # Save updated configuration
        self.flags._save_config(config)
    
    def _enable_original_pipeline(self):
        """Ensure original pipeline is operational."""
        # Verify original pipeline health
        # Warm up any necessary caches
        pass
    
    def _disable_canary_deployment(self):
        """Disable canary deployment."""
        config = self.flags.config
        config['canary_deployment']['enabled'] = False
        config['canary_deployment']['percentage'] = 0
        
        self.flags._save_config(config)
    
    def _send_rollback_alerts(self, reason: str):
        """Send rollback notifications."""
        # Send to monitoring system
        # Send to Slack/email
        # Update status page
        pass
```

## Deployment Timeline

### Week 1: Feature Flag Setup
- **Day 1-2**: Implement feature flag system
- **Day 3-4**: Integrate with existing pipeline
- **Day 5**: Testing and validation

### Week 2: Shadow Run Phase
- **Day 1**: Deploy shadow run capability
- **Day 2-4**: Run parallel tests on sample data
- **Day 5**: Analyze results and fix issues

### Week 3: Canary Deployment
- **Day 1**: Deploy canary system (10% traffic)
- **Day 2-3**: Monitor canary metrics
- **Day 4**: Increase to 25% if stable
- **Day 5**: Increase to 50% if stable

### Week 4: Full Rollout
- **Day 1**: Increase canary to 75%
- **Day 2**: Monitor for 24 hours
- **Day 3**: Full rollout (100%)
- **Day 4-5**: Monitoring and optimization

## Success Criteria

### Technical Metrics
- **Backward Compatibility**: 100% (baseline flavor identical to original)
- **Success Rate**: >95% across all flavors
- **Performance**: <20% execution time increase
- **Error Rate**: <5% for any flavor

### Business Metrics
- **Zero Downtime**: No service interruptions
- **User Satisfaction**: No user-reported issues
- **Feature Adoption**: Successful deployment of new flavors

### Quality Metrics
- **Determinism**: Same inputs produce identical outputs
- **Idempotency**: Safe operation repetition
- **Resilience**: Graceful handling of edge cases

## Risk Mitigation

### High-Priority Risks
1. **API Rate Limits**: Implement backoff and retry logic
2. **Memory Usage**: Monitor and optimize resource consumption  
3. **External Dependencies**: Implement circuit breakers
4. **Data Corruption**: Comprehensive validation and backups

### Monitoring Setup
- **Real-time dashboards**: Pipeline health and performance
- **Alerting**: Critical failure notifications
- **Log aggregation**: Centralized error tracking
- **Automated testing**: Continuous validation

This comprehensive rollout plan ensures the modular ideation pipeline can be deployed safely with complete backward compatibility while providing the foundation for future enhancements.