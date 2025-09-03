"""
Canary deployment strategy for safe flavor rollout.
Implements gradual rollout with automated promotion and rollback based on health metrics.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum

from .feature_flags import get_feature_flag_manager, RolloutConfig
from .health_monitoring import HealthOrchestrator, HealthStatus
from .shadow_testing import ShadowTestOrchestrator

class CanaryStage(Enum):
    """Canary deployment stages."""
    PREPARATION = "preparation"
    SHADOW_TESTING = "shadow_testing"
    CANARY_START = "canary_start"
    GRADUAL_ROLLOUT = "gradual_rollout"
    FULL_ROLLOUT = "full_rollout"
    COMPLETE = "complete"
    ROLLED_BACK = "rolled_back"

@dataclass
class CanaryConfig:
    """Configuration for canary deployment."""
    flavor_name: str
    initial_percentage: float = 1.0
    increment_percentage: float = 5.0
    increment_interval_minutes: int = 60
    max_percentage: float = 100.0
    success_rate_threshold: float = 0.95
    max_error_rate: float = 0.05
    shadow_test_duration_minutes: int = 30
    health_check_interval_minutes: int = 5
    auto_promote: bool = True
    auto_rollback: bool = True

@dataclass
class CanaryState:
    """Current state of canary deployment."""
    flavor: str
    stage: CanaryStage
    current_percentage: float
    target_percentage: float
    start_time: str
    last_update_time: str
    next_check_time: str
    health_status: HealthStatus
    success_rate: float
    error_rate: float
    rollback_reason: Optional[str] = None

class CanaryDeploymentManager:
    """Manages canary deployment lifecycle."""
    
    def __init__(self):
        self.flag_manager = get_feature_flag_manager()
        self.health_orchestrator = HealthOrchestrator()
        self.shadow_orchestrator = ShadowTestOrchestrator()
        self.logger = logging.getLogger(__name__)
        
        # Active canary deployments
        self.active_canaries: Dict[str, CanaryState] = {}
        
        # Callbacks for different events
        self.promotion_callbacks: List[Callable] = []
        self.rollback_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
    
    def start_canary_deployment(self, config: CanaryConfig) -> bool:
        """Start a new canary deployment."""
        if config.flavor_name in self.active_canaries:
            self.logger.warning(f"Canary deployment already active for {config.flavor_name}")
            return False
        
        self.logger.info(f"Starting canary deployment for {config.flavor_name}")
        
        try:
            # Create or update feature flag
            flag_name = f"flavor_{config.flavor_name}"
            
            if flag_name not in self.flag_manager.flags:
                self.flag_manager.create_flag(
                    name=flag_name,
                    enabled=False,
                    rollout_percentage=0.0,
                    description=f"Canary deployment flag for {config.flavor_name} flavor"
                )
            
            # Initialize canary state
            now = datetime.now(timezone.utc)
            state = CanaryState(
                flavor=config.flavor_name,
                stage=CanaryStage.PREPARATION,
                current_percentage=0.0,
                target_percentage=config.initial_percentage,
                start_time=now.isoformat(),
                last_update_time=now.isoformat(),
                next_check_time=(now + timedelta(minutes=config.shadow_test_duration_minutes)).isoformat(),
                health_status=HealthStatus.UNKNOWN,
                success_rate=0.0,
                error_rate=0.0
            )
            
            self.active_canaries[config.flavor_name] = state
            
            # Start with shadow testing phase
            self._start_shadow_testing(config.flavor_name, config)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start canary deployment for {config.flavor_name}: {e}")
            return False
    
    def _start_shadow_testing(self, flavor: str, config: CanaryConfig):
        """Start shadow testing phase."""
        self.logger.info(f"Starting shadow testing for {flavor}")
        
        state = self.active_canaries[flavor]
        state.stage = CanaryStage.SHADOW_TESTING
        
        # Enable shadow testing
        shadow_flag = "shadow_run_enabled"
        if shadow_flag not in self.flag_manager.flags:
            self.flag_manager.create_flag(
                name=shadow_flag,
                enabled=True,
                rollout_percentage=100.0,
                description="Enable shadow run testing"
            )
        else:
            self.flag_manager.update_flag(shadow_flag, enabled=True, rollout_percentage=100.0)
    
    def _start_canary_rollout(self, flavor: str, config: CanaryConfig):
        """Start actual canary rollout."""
        self.logger.info(f"Starting canary rollout for {flavor}")
        
        state = self.active_canaries[flavor]
        state.stage = CanaryStage.CANARY_START
        
        # Enable the flavor flag at initial percentage
        flag_name = f"flavor_{flavor}"
        self.flag_manager.update_flag(
            flag_name,
            enabled=True,
            rollout_percentage=config.initial_percentage
        )
        
        state.current_percentage = config.initial_percentage
        state.target_percentage = config.initial_percentage
        
        # Schedule next check
        next_check = datetime.now(timezone.utc) + timedelta(minutes=config.health_check_interval_minutes)
        state.next_check_time = next_check.isoformat()
    
    def check_canary_health(self, flavor: str, config: CanaryConfig) -> bool:
        """Check health of canary deployment and decide on next action."""
        if flavor not in self.active_canaries:
            return False
        
        state = self.active_canaries[flavor]
        
        # Get current health metrics
        health_summary = self.health_orchestrator.get_health_summary()
        
        # Update state with health metrics
        state.health_status = HealthStatus(health_summary.get('overall_status', 'unknown'))
        state.success_rate = health_summary.get('success_rate', 0.0)
        state.error_rate = health_summary.get('error_rate', 1.0)
        
        # Check rollback conditions
        should_rollback, rollback_reason = self._should_rollback(state, config)
        
        if should_rollback:
            self.logger.warning(f"Canary rollback triggered for {flavor}: {rollback_reason}")
            self._rollback_canary(flavor, rollback_reason)
            return False
        
        # Check promotion conditions
        should_promote = self._should_promote(state, config)
        
        if should_promote and config.auto_promote:
            self._promote_canary(flavor, config)
        
        return True
    
    def _should_rollback(self, state: CanaryState, config: CanaryConfig) -> tuple[bool, Optional[str]]:
        """Determine if canary should be rolled back."""
        if not config.auto_rollback:
            return False, None
        
        # Check error rate
        if state.error_rate > config.max_error_rate:
            return True, f"Error rate {state.error_rate:.2%} exceeds threshold {config.max_error_rate:.2%}"
        
        # Check success rate
        if state.success_rate < config.success_rate_threshold and state.current_percentage > 0:
            return True, f"Success rate {state.success_rate:.2%} below threshold {config.success_rate_threshold:.2%}"
        
        # Check critical health status
        if state.health_status == HealthStatus.CRITICAL:
            return True, "System health is critical"
        
        return False, None
    
    def _should_promote(self, state: CanaryState, config: CanaryConfig) -> bool:
        """Determine if canary should be promoted to next stage."""
        # Must be healthy and meeting thresholds
        if state.health_status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            return False
        
        if state.success_rate < config.success_rate_threshold:
            return False
        
        if state.error_rate > config.max_error_rate:
            return False
        
        # Check if enough time has passed
        now = datetime.now(timezone.utc)
        next_check = datetime.fromisoformat(state.next_check_time.replace('Z', '+00:00'))
        
        if now < next_check:
            return False
        
        return True
    
    def _promote_canary(self, flavor: str, config: CanaryConfig):
        """Promote canary to next stage."""
        state = self.active_canaries[flavor]
        
        if state.stage == CanaryStage.SHADOW_TESTING:
            # Move to canary start
            self._start_canary_rollout(flavor, config)
            
        elif state.stage == CanaryStage.CANARY_START:
            # Move to gradual rollout
            state.stage = CanaryStage.GRADUAL_ROLLOUT
            self._increase_rollout_percentage(flavor, config)
            
        elif state.stage == CanaryStage.GRADUAL_ROLLOUT:
            if state.current_percentage >= config.max_percentage:
                # Move to complete
                state.stage = CanaryStage.COMPLETE
                self.logger.info(f"Canary deployment complete for {flavor}")
                self._notify_completion(flavor)
            else:
                # Increase percentage
                self._increase_rollout_percentage(flavor, config)
        
        # Notify promotion
        self._notify_promotion(flavor, state.stage)
    
    def _increase_rollout_percentage(self, flavor: str, config: CanaryConfig):
        """Increase rollout percentage for gradual deployment."""
        state = self.active_canaries[flavor]
        
        # Calculate next percentage
        next_percentage = min(
            state.current_percentage + config.increment_percentage,
            config.max_percentage
        )
        
        self.logger.info(
            f"Increasing rollout for {flavor} from {state.current_percentage}% to {next_percentage}%"
        )
        
        # Update feature flag
        flag_name = f"flavor_{flavor}"
        self.flag_manager.update_flag(flag_name, rollout_percentage=next_percentage)
        
        # Update state
        state.current_percentage = next_percentage
        state.target_percentage = next_percentage
        
        # Schedule next check
        next_check = datetime.now(timezone.utc) + timedelta(minutes=config.increment_interval_minutes)
        state.next_check_time = next_check.isoformat()
    
    def _rollback_canary(self, flavor: str, reason: str):
        """Rollback canary deployment."""
        if flavor not in self.active_canaries:
            return
        
        state = self.active_canaries[flavor]
        state.stage = CanaryStage.ROLLED_BACK
        state.rollback_reason = reason
        
        # Disable feature flag
        flag_name = f"flavor_{flavor}"
        self.flag_manager.update_flag(flag_name, enabled=False, rollout_percentage=0.0)
        
        self.logger.warning(f"Canary deployment rolled back for {flavor}: {reason}")
        
        # Notify rollback
        self._notify_rollback(flavor, reason)
    
    def monitor_active_canaries(self):
        """Monitor all active canary deployments."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                
                for flavor, state in list(self.active_canaries.items()):
                    if state.stage in [CanaryStage.COMPLETE, CanaryStage.ROLLED_BACK]:
                        continue
                    
                    # Check if it's time for health check
                    next_check = datetime.fromisoformat(state.next_check_time.replace('Z', '+00:00'))
                    
                    if current_time >= next_check:
                        # Get config (in practice, this would be stored)
                        config = CanaryConfig(flavor_name=flavor)  # Use defaults
                        
                        self.check_canary_health(flavor, config)
                
                # Sleep for a minute before next check
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in canary monitoring: {e}")
                time.sleep(30)
    
    def manual_promote(self, flavor: str) -> bool:
        """Manually promote canary to next stage."""
        if flavor not in self.active_canaries:
            self.logger.warning(f"No active canary for {flavor}")
            return False
        
        config = CanaryConfig(flavor_name=flavor)  # Use defaults
        self._promote_canary(flavor, config)
        return True
    
    def manual_rollback(self, flavor: str, reason: str = "Manual rollback") -> bool:
        """Manually rollback canary deployment."""
        if flavor not in self.active_canaries:
            self.logger.warning(f"No active canary for {flavor}")
            return False
        
        self._rollback_canary(flavor, reason)
        return True
    
    def get_canary_status(self, flavor: str) -> Optional[CanaryState]:
        """Get current status of canary deployment."""
        return self.active_canaries.get(flavor)
    
    def list_active_canaries(self) -> Dict[str, CanaryState]:
        """List all active canary deployments."""
        return self.active_canaries.copy()
    
    # Callback management
    def add_promotion_callback(self, callback: Callable):
        """Add callback for promotion events."""
        self.promotion_callbacks.append(callback)
    
    def add_rollback_callback(self, callback: Callable):
        """Add callback for rollback events."""
        self.rollback_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable):
        """Add callback for completion events."""
        self.completion_callbacks.append(callback)
    
    def _notify_promotion(self, flavor: str, stage: CanaryStage):
        """Notify promotion callbacks."""
        for callback in self.promotion_callbacks:
            try:
                callback(flavor, stage)
            except Exception as e:
                self.logger.error(f"Promotion callback error: {e}")
    
    def _notify_rollback(self, flavor: str, reason: str):
        """Notify rollback callbacks."""
        for callback in self.rollback_callbacks:
            try:
                callback(flavor, reason)
            except Exception as e:
                self.logger.error(f"Rollback callback error: {e}")
    
    def _notify_completion(self, flavor: str):
        """Notify completion callbacks."""
        for callback in self.completion_callbacks:
            try:
                callback(flavor)
            except Exception as e:
                self.logger.error(f"Completion callback error: {e}")

class CanaryOrchestrator:
    """High-level orchestrator for canary deployments."""
    
    def __init__(self):
        self.canary_manager = CanaryDeploymentManager()
        self.logger = logging.getLogger(__name__)
    
    def deploy_flavor_with_canary(self, flavor_name: str, config: Optional[CanaryConfig] = None) -> bool:
        """Deploy a new flavor using canary strategy."""
        if not config:
            config = CanaryConfig(flavor_name=flavor_name)
        
        self.logger.info(f"Starting canary deployment for flavor: {flavor_name}")
        
        # Set up monitoring callbacks
        self.canary_manager.add_promotion_callback(self._log_promotion)
        self.canary_manager.add_rollback_callback(self._log_rollback)
        self.canary_manager.add_completion_callback(self._log_completion)
        
        # Start canary deployment
        return self.canary_manager.start_canary_deployment(config)
    
    def get_deployment_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive deployment dashboard data."""
        active_canaries = self.canary_manager.list_active_canaries()
        
        dashboard = {
            'active_deployments': len(active_canaries),
            'deployments': {},
            'summary': {
                'in_shadow_testing': 0,
                'in_canary_rollout': 0,
                'in_gradual_rollout': 0,
                'completed': 0,
                'rolled_back': 0
            }
        }
        
        for flavor, state in active_canaries.items():
            dashboard['deployments'][flavor] = {
                'stage': state.stage.value,
                'current_percentage': state.current_percentage,
                'health_status': state.health_status.value,
                'success_rate': state.success_rate,
                'error_rate': state.error_rate,
                'start_time': state.start_time,
                'rollback_reason': state.rollback_reason
            }
            
            # Update summary
            if state.stage == CanaryStage.SHADOW_TESTING:
                dashboard['summary']['in_shadow_testing'] += 1
            elif state.stage == CanaryStage.CANARY_START:
                dashboard['summary']['in_canary_rollout'] += 1
            elif state.stage == CanaryStage.GRADUAL_ROLLOUT:
                dashboard['summary']['in_gradual_rollout'] += 1
            elif state.stage == CanaryStage.COMPLETE:
                dashboard['summary']['completed'] += 1
            elif state.stage == CanaryStage.ROLLED_BACK:
                dashboard['summary']['rolled_back'] += 1
        
        return dashboard
    
    def _log_promotion(self, flavor: str, stage: CanaryStage):
        """Log promotion events."""
        self.logger.info(f"Canary promotion: {flavor} -> {stage.value}")
    
    def _log_rollback(self, flavor: str, reason: str):
        """Log rollback events."""
        self.logger.warning(f"Canary rollback: {flavor} - {reason}")
    
    def _log_completion(self, flavor: str):
        """Log completion events."""
        self.logger.info(f"Canary deployment completed: {flavor}")

# Global canary orchestrator instance
_canary_orchestrator = None

def get_canary_orchestrator() -> CanaryOrchestrator:
    """Get global canary orchestrator instance."""
    global _canary_orchestrator
    if _canary_orchestrator is None:
        _canary_orchestrator = CanaryOrchestrator()
    return _canary_orchestrator