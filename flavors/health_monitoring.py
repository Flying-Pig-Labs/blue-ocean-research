"""
Health monitoring and rollback capabilities for flavor rollout management.
Monitors system health, performance, and error rates during rollout.
"""

import os
import json
import logging
import time
import psutil
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from enum import Enum

from .feature_flags import get_feature_flag_manager, get_flavor_flags

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    timestamp: str
    status: HealthStatus

@dataclass
class SystemHealth:
    """Overall system health snapshot."""
    timestamp: str
    overall_status: HealthStatus
    metrics: List[HealthMetric]
    active_flavors: List[str]
    rollout_percentages: Dict[str, float]
    error_rate: float
    success_rate: float

@dataclass
class RolloutEvent:
    """Rollout event for audit trail."""
    timestamp: str
    event_type: str  # "rollout_start", "rollout_increase", "rollback", "health_alert"
    flavor: str
    details: Dict[str, Any]
    health_status: HealthStatus

class HealthMonitor:
    """Monitors system health during flavor rollout."""
    
    def __init__(self, metrics_dir: str = "health_metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Health tracking
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
        self.recent_errors = defaultdict(lambda: deque(maxlen=100))
        self.recent_successes = defaultdict(lambda: deque(maxlen=100))
        
        # Performance tracking
        self.execution_times = defaultdict(lambda: deque(maxlen=100))
        self.memory_usage = deque(maxlen=100)
        self.cpu_usage = deque(maxlen=100)
        
        # Feature flag manager
        self.flag_manager = get_feature_flag_manager()
        self.flavor_flags = get_flavor_flags()
    
    def record_pipeline_execution(self, flavor: str, success: bool, 
                                execution_time: float, error: Optional[str] = None):
        """Record pipeline execution result."""
        timestamp = time.time()
        
        if success:
            self.success_counts[flavor] += 1
            self.recent_successes[flavor].append(timestamp)
        else:
            self.error_counts[flavor] += 1
            self.recent_errors[flavor].append({
                'timestamp': timestamp,
                'error': error
            })
        
        self.execution_times[flavor].append(execution_time)
        
        # Log significant events
        if not success:
            self.logger.warning(f"Pipeline failure for flavor {flavor}: {error}")
    
    def record_system_metrics(self):
        """Record system-level metrics."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent
            
            self.cpu_usage.append(cpu_percent)
            self.memory_usage.append(memory_percent)
            
        except Exception as e:
            self.logger.warning(f"Failed to collect system metrics: {e}")
    
    def calculate_error_rate(self, flavor: str, window_minutes: int = 60) -> float:
        """Calculate error rate for a flavor within time window."""
        cutoff_time = time.time() - (window_minutes * 60)
        
        recent_errors = sum(1 for err in self.recent_errors[flavor] 
                          if err['timestamp'] > cutoff_time)
        recent_successes = sum(1 for ts in self.recent_successes[flavor] 
                             if ts > cutoff_time)
        
        total = recent_errors + recent_successes
        if total == 0:
            return 0.0
        
        return recent_errors / total
    
    def calculate_success_rate(self, flavor: str, window_minutes: int = 60) -> float:
        """Calculate success rate for a flavor within time window."""
        return 1.0 - self.calculate_error_rate(flavor, window_minutes)
    
    def get_average_execution_time(self, flavor: str) -> float:
        """Get average execution time for a flavor."""
        times = list(self.execution_times[flavor])
        if not times:
            return 0.0
        return sum(times) / len(times)
    
    def create_health_metrics(self) -> List[HealthMetric]:
        """Create current health metrics."""
        metrics = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # System metrics
        if self.cpu_usage:
            cpu_avg = sum(self.cpu_usage) / len(self.cpu_usage)
            metrics.append(HealthMetric(
                name="cpu_usage",
                value=cpu_avg,
                threshold_warning=70.0,
                threshold_critical=90.0,
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(cpu_avg, 70.0, 90.0)
            ))
        
        if self.memory_usage:
            mem_avg = sum(self.memory_usage) / len(self.memory_usage)
            metrics.append(HealthMetric(
                name="memory_usage",
                value=mem_avg,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(mem_avg, 80.0, 95.0)
            ))
        
        # Flavor-specific metrics
        active_flavors = self._get_active_flavors()
        
        for flavor in active_flavors:
            # Error rate
            error_rate = self.calculate_error_rate(flavor)
            metrics.append(HealthMetric(
                name=f"{flavor}_error_rate",
                value=error_rate * 100,
                threshold_warning=5.0,
                threshold_critical=10.0,
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(error_rate * 100, 5.0, 10.0)
            ))
            
            # Average execution time
            avg_time = self.get_average_execution_time(flavor)
            if avg_time > 0:
                metrics.append(HealthMetric(
                    name=f"{flavor}_avg_execution_time",
                    value=avg_time,
                    threshold_warning=300.0,  # 5 minutes
                    threshold_critical=600.0,  # 10 minutes
                    unit="seconds",
                    timestamp=timestamp,
                    status=self._get_metric_status(avg_time, 300.0, 600.0)
                ))
        
        return metrics
    
    def _get_metric_status(self, value: float, warning_threshold: float, 
                          critical_threshold: float) -> HealthStatus:
        """Determine health status based on thresholds."""
        if value >= critical_threshold:
            return HealthStatus.CRITICAL
        elif value >= warning_threshold:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def _get_active_flavors(self) -> List[str]:
        """Get list of active flavors from feature flags."""
        active_flavors = []
        
        for flag_name, flag in self.flag_manager.list_flags().items():
            if flag.enabled and flag.rollout_percentage > 0:
                # Extract flavor name from flag name
                if flag_name.startswith("flavor_"):
                    flavor = flag_name.replace("flavor_", "")
                    active_flavors.append(flavor)
        
        # Always include baseline if modular pipeline is enabled
        if self.flavor_flags.should_use_modular_pipeline():
            active_flavors.append("baseline")
        
        return active_flavors
    
    def get_rollout_percentages(self) -> Dict[str, float]:
        """Get current rollout percentages for all flavors."""
        percentages = {}
        
        for flag_name, flag in self.flag_manager.list_flags().items():
            if flag.enabled and flag_name.startswith("flavor_"):
                flavor = flag_name.replace("flavor_", "")
                percentages[flavor] = flag.rollout_percentage
        
        return percentages
    
    def assess_system_health(self) -> SystemHealth:
        """Assess overall system health."""
        # Update system metrics
        self.record_system_metrics()
        
        # Create health metrics
        metrics = self.create_health_metrics()
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        critical_count = sum(1 for m in metrics if m.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for m in metrics if m.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > 0:
            overall_status = HealthStatus.WARNING
        
        # Calculate overall success rate
        active_flavors = self._get_active_flavors()
        if active_flavors:
            success_rates = [self.calculate_success_rate(flavor) for flavor in active_flavors]
            overall_success_rate = sum(success_rates) / len(success_rates)
            overall_error_rate = 1.0 - overall_success_rate
        else:
            overall_success_rate = 1.0
            overall_error_rate = 0.0
        
        return SystemHealth(
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_status=overall_status,
            metrics=metrics,
            active_flavors=active_flavors,
            rollout_percentages=self.get_rollout_percentages(),
            error_rate=overall_error_rate,
            success_rate=overall_success_rate
        )
    
    def save_health_snapshot(self, health: SystemHealth):
        """Save health snapshot to file."""
        filename = f"health_{health.timestamp.replace(':', '-').replace('.', '_')}.json"
        filepath = self.metrics_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                # Convert dataclass to dict, handling enums
                health_dict = asdict(health)
                health_dict['overall_status'] = health.overall_status.value
                for metric in health_dict['metrics']:
                    metric['status'] = metric['status'].value if hasattr(metric['status'], 'value') else metric['status']
                
                json.dump(health_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save health snapshot: {e}")

class RollbackManager:
    """Manages automatic and manual rollback procedures."""
    
    def __init__(self, health_monitor: HealthMonitor):
        self.health_monitor = health_monitor
        self.flag_manager = get_feature_flag_manager()
        self.logger = logging.getLogger(__name__)
        
        # Rollback configuration
        self.rollback_triggers = {
            'error_rate_threshold': 0.15,  # 15% error rate
            'critical_metrics_threshold': 2,  # 2 or more critical metrics
            'consecutive_failures_threshold': 5  # 5 consecutive failures
        }
        
        # Event audit trail
        self.events = []
    
    def check_rollback_conditions(self, health: SystemHealth) -> Tuple[bool, List[str]]:
        """Check if rollback conditions are met."""
        should_rollback = False
        reasons = []
        
        # Check overall error rate
        if health.error_rate > self.rollback_triggers['error_rate_threshold']:
            should_rollback = True
            reasons.append(f"Error rate {health.error_rate:.2%} exceeds threshold {self.rollback_triggers['error_rate_threshold']:.2%}")
        
        # Check critical metrics count
        critical_metrics = [m for m in health.metrics if m.status == HealthStatus.CRITICAL]
        if len(critical_metrics) >= self.rollback_triggers['critical_metrics_threshold']:
            should_rollback = True
            reasons.append(f"{len(critical_metrics)} critical metrics detected")
        
        # Check overall system health
        if health.overall_status == HealthStatus.CRITICAL:
            should_rollback = True
            reasons.append("Overall system health is critical")
        
        return should_rollback, reasons
    
    def execute_emergency_rollback(self, reasons: List[str]):
        """Execute emergency rollback of all active flavors."""
        self.logger.warning(f"EMERGENCY ROLLBACK TRIGGERED: {'; '.join(reasons)}")
        
        # Record rollback event
        event = RolloutEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="emergency_rollback",
            flavor="all",
            details={"reasons": reasons},
            health_status=HealthStatus.CRITICAL
        )
        self.events.append(event)
        
        # Disable all flavor flags
        for flag_name, flag in self.flag_manager.list_flags().items():
            if flag_name.startswith("flavor_") or "modular" in flag_name.lower():
                try:
                    self.flag_manager.emergency_rollback(flag_name)
                    self.logger.info(f"Rolled back flag: {flag_name}")
                except Exception as e:
                    self.logger.error(f"Failed to rollback flag {flag_name}: {e}")
        
        # Send alerts (could integrate with monitoring systems)
        self._send_rollback_alert(reasons)
    
    def execute_gradual_rollback(self, flavor: str, target_percentage: float = 0.0):
        """Execute gradual rollback of a specific flavor."""
        flag_name = f"flavor_{flavor}"
        
        try:
            current_flag = self.flag_manager.get_flag_status(flag_name)
            if not current_flag:
                self.logger.warning(f"Flag {flag_name} not found for rollback")
                return
            
            self.logger.info(f"Gradual rollback of {flavor} to {target_percentage}%")
            
            # Record rollback event
            event = RolloutEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="gradual_rollback",
                flavor=flavor,
                details={
                    "from_percentage": current_flag.rollout_percentage,
                    "to_percentage": target_percentage
                },
                health_status=HealthStatus.WARNING
            )
            self.events.append(event)
            
            # Update flag
            if target_percentage == 0.0:
                self.flag_manager.update_flag(flag_name, enabled=False, rollout_percentage=0.0)
            else:
                self.flag_manager.update_flag(flag_name, rollout_percentage=target_percentage)
                
        except Exception as e:
            self.logger.error(f"Failed to execute gradual rollback for {flavor}: {e}")
    
    def _send_rollback_alert(self, reasons: List[str]):
        """Send rollback alert (placeholder for integration with alerting systems)."""
        alert_message = f"EMERGENCY ROLLBACK EXECUTED\nReasons: {'; '.join(reasons)}\nTime: {datetime.now()}"
        
        # Could integrate with:
        # - Slack/Teams notifications
        # - PagerDuty alerts
        # - Email notifications
        # - Monitoring dashboards
        
        self.logger.critical(alert_message)

class HealthOrchestrator:
    """Orchestrates health monitoring and rollback management."""
    
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.rollback_manager = RollbackManager(self.health_monitor)
        self.logger = logging.getLogger(__name__)
        
        # Monitoring configuration
        self.check_interval_seconds = 60  # Check health every minute
        self.snapshot_interval_seconds = 300  # Save snapshot every 5 minutes
        
        self.last_snapshot_time = 0
    
    def monitor_health_continuously(self):
        """Run continuous health monitoring with rollback protection."""
        self.logger.info("Starting continuous health monitoring")
        
        while True:
            try:
                # Assess system health
                health = self.health_monitor.assess_system_health()
                
                # Check for rollback conditions
                should_rollback, reasons = self.rollback_manager.check_rollback_conditions(health)
                
                if should_rollback:
                    self.rollback_manager.execute_emergency_rollback(reasons)
                
                # Save periodic snapshots
                current_time = time.time()
                if current_time - self.last_snapshot_time > self.snapshot_interval_seconds:
                    self.health_monitor.save_health_snapshot(health)
                    self.last_snapshot_time = current_time
                
                # Log health status
                if health.overall_status != HealthStatus.HEALTHY:
                    self.logger.warning(
                        f"System health: {health.overall_status.value}, "
                        f"error rate: {health.error_rate:.2%}, "
                        f"active flavors: {', '.join(health.active_flavors)}"
                    )
                
                time.sleep(self.check_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary."""
        health = self.health_monitor.assess_system_health()
        
        return {
            'overall_status': health.overall_status.value,
            'error_rate': health.error_rate,
            'success_rate': health.success_rate,
            'active_flavors': health.active_flavors,
            'rollout_percentages': health.rollout_percentages,
            'critical_metrics': [
                m.name for m in health.metrics 
                if m.status == HealthStatus.CRITICAL
            ],
            'warning_metrics': [
                m.name for m in health.metrics 
                if m.status == HealthStatus.WARNING
            ]
        }
    
    def manual_rollback(self, flavor: str, target_percentage: float = 0.0):
        """Execute manual rollback of a specific flavor."""
        self.rollback_manager.execute_gradual_rollback(flavor, target_percentage)
    
    def get_rollback_events(self) -> List[RolloutEvent]:
        """Get rollback event history."""
        return self.rollback_manager.events.copy()