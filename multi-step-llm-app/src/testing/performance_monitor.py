"""
Performance Monitor

Tracks API calls, token usage, costs, and performance metrics for integration testing.
Provides detailed monitoring and cost estimation capabilities.
"""

import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import defaultdict

from ..utils.pipeline_logger import get_logger
from ..models.logging_models import ComponentType, ModelProvider


@dataclass
class APICallMetrics:
    """Metrics for a single API call"""
    timestamp: datetime
    component: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    duration_seconds: float
    estimated_cost: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "model": self.model,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "duration_seconds": self.duration_seconds,
            "estimated_cost": self.estimated_cost,
            "success": self.success,
            "error_message": self.error_message
        }


@dataclass
class SessionMetrics:
    """Metrics for a complete test session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    component_name: str = ""
    total_api_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_seconds: float = 0.0
    api_calls: List[APICallMetrics] = field(default_factory=list)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "component_name": self.component_name,
            "total_api_calls": self.total_api_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "duration_seconds": self.duration_seconds,
            "api_calls": [call.to_dict() for call in self.api_calls],
            "performance_data": self.performance_data
        }


class PerformanceMonitor:
    """Monitors performance metrics during integration testing"""
    
    def __init__(self, logger=None):
        """Initialize the performance monitor"""
        self.logger = logger or get_logger()
        self.active_sessions: Dict[str, SessionMetrics] = {}
        self.completed_sessions: Dict[str, SessionMetrics] = {}
        
        # Cost estimation tables (per 1K tokens)
        self.cost_tables = {
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
                "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            },
            "openai": {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            },
            "cohere": {
                "command": {"input": 0.015, "output": 0.015},
                "command-light": {"input": 0.003, "output": 0.003},
            }
        }
        
        # Performance tracking
        self._lock = threading.Lock()
        self.monitoring_enabled = True
        
        self.logger.info("Performance monitor initialized", ComponentType.MAIN_PIPELINE)
    
    def start_session(self, session_id: str, component_name: str = "") -> str:
        """Start a new monitoring session"""
        with self._lock:
            if session_id in self.active_sessions:
                self.logger.warning(f"Session {session_id} already active, stopping previous session")
                self.stop_session(session_id)
            
            session = SessionMetrics(
                session_id=session_id,
                start_time=datetime.now(),
                component_name=component_name
            )
            
            self.active_sessions[session_id] = session
            
            self.logger.info(f"Started monitoring session: {session_id}", ComponentType.MAIN_PIPELINE,
                           metadata={"component": component_name})
            
            return session_id
    
    def stop_session(self, session_id: str) -> Dict[str, Any]:
        """Stop a monitoring session and return metrics"""
        with self._lock:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session {session_id} not found in active sessions")
                return {}
            
            session = self.active_sessions[session_id]
            session.end_time = datetime.now()
            session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            
            # Calculate final metrics
            session.total_api_calls = len(session.api_calls)
            session.successful_calls = sum(1 for call in session.api_calls if call.success)
            session.failed_calls = session.total_api_calls - session.successful_calls
            session.total_tokens = sum(call.total_tokens for call in session.api_calls)
            session.total_cost = sum(call.estimated_cost for call in session.api_calls)
            
            # Move to completed sessions
            self.completed_sessions[session_id] = session
            del self.active_sessions[session_id]
            
            self.logger.info(f"Stopped monitoring session: {session_id}", ComponentType.MAIN_PIPELINE,
                           metadata={
                               "duration": session.duration_seconds,
                               "total_calls": session.total_api_calls,
                               "total_cost": session.total_cost,
                               "total_tokens": session.total_tokens
                           })
            
            return session.to_dict()
    
    def track_api_call(self, session_id: str, component: str, model: str, 
                      provider: str, prompt_tokens: int, completion_tokens: int,
                      duration: float, success: bool = True, 
                      error_message: Optional[str] = None) -> APICallMetrics:
        """Track an individual API call"""
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = self._estimate_cost(provider, model, prompt_tokens, completion_tokens)
        
        call_metrics = APICallMetrics(
            timestamp=datetime.now(),
            component=component,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_seconds=duration,
            estimated_cost=estimated_cost,
            success=success,
            error_message=error_message
        )
        
        with self._lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].api_calls.append(call_metrics)
            else:
                self.logger.warning(f"Attempted to track API call for inactive session: {session_id}")
        
        self.logger.info(f"Tracked API call for session {session_id}", ComponentType.MAIN_PIPELINE,
                       metadata={
                           "component": component,
                           "model": model,
                           "tokens": total_tokens,
                           "cost": estimated_cost,
                           "success": success
                       })
        
        return call_metrics
    
    def _estimate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate the cost of an API call"""
        provider_costs = self.cost_tables.get(provider.lower(), {})
        model_costs = provider_costs.get(model, {})
        
        if not model_costs:
            # Default fallback costs
            input_cost = 0.01  # $0.01 per 1K tokens
            output_cost = 0.01
        else:
            input_cost = model_costs.get("input", 0.01)
            output_cost = model_costs.get("output", 0.01)
        
        # Calculate cost (prices are per 1K tokens)
        prompt_cost = (prompt_tokens / 1000) * input_cost
        completion_cost = (completion_tokens / 1000) * output_cost
        
        return prompt_cost + completion_cost
    
    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific session"""
        with self._lock:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                # Calculate current metrics
                session.total_api_calls = len(session.api_calls)
                session.successful_calls = sum(1 for call in session.api_calls if call.success)
                session.failed_calls = session.total_api_calls - session.successful_calls
                session.total_tokens = sum(call.total_tokens for call in session.api_calls)
                session.total_cost = sum(call.estimated_cost for call in session.api_calls)
                if session.end_time:
                    session.duration_seconds = (session.end_time - session.start_time).total_seconds()
                else:
                    session.duration_seconds = (datetime.now() - session.start_time).total_seconds()
                
                return session.to_dict()
            elif session_id in self.completed_sessions:
                return self.completed_sessions[session_id].to_dict()
        
        return None
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all sessions"""
        all_sessions = {}
        
        with self._lock:
            for session_id, session in self.active_sessions.items():
                all_sessions[session_id] = session.to_dict()
            
            for session_id, session in self.completed_sessions.items():
                all_sessions[session_id] = session.to_dict()
        
        return all_sessions
    
    def generate_performance_summary(self, session_ids: List[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive performance summary"""
        if session_ids is None:
            # Include all sessions
            sessions_to_analyze = list(self.completed_sessions.values())
        else:
            sessions_to_analyze = []
            for session_id in session_ids:
                if session_id in self.completed_sessions:
                    sessions_to_analyze.append(self.completed_sessions[session_id])
                elif session_id in self.active_sessions:
                    sessions_to_analyze.append(self.active_sessions[session_id])
        
        if not sessions_to_analyze:
            return {"error": "No sessions found for analysis"}
        
        # Aggregate metrics
        total_sessions = len(sessions_to_analyze)
        total_api_calls = sum(session.total_api_calls for session in sessions_to_analyze)
        total_tokens = sum(session.total_tokens for session in sessions_to_analyze)
        total_cost = sum(session.total_cost for session in sessions_to_analyze)
        total_duration = sum(session.duration_seconds for session in sessions_to_analyze)
        
        successful_sessions = sum(1 for session in sessions_to_analyze 
                                if session.failed_calls == 0 and session.total_api_calls > 0)
        
        # Calculate averages
        avg_tokens_per_session = total_tokens / total_sessions if total_sessions > 0 else 0
        avg_cost_per_session = total_cost / total_sessions if total_sessions > 0 else 0
        avg_duration_per_session = total_duration / total_sessions if total_sessions > 0 else 0
        avg_api_calls_per_session = total_api_calls / total_sessions if total_sessions > 0 else 0
        
        # Component analysis
        component_metrics = defaultdict(lambda: {
            "sessions": 0, "api_calls": 0, "tokens": 0, "cost": 0.0, "duration": 0.0
        })
        
        for session in sessions_to_analyze:
            component = session.component_name or "unknown"
            component_metrics[component]["sessions"] += 1
            component_metrics[component]["api_calls"] += session.total_api_calls
            component_metrics[component]["tokens"] += session.total_tokens
            component_metrics[component]["cost"] += session.total_cost
            component_metrics[component]["duration"] += session.duration_seconds
        
        # Model usage analysis
        model_usage = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        
        for session in sessions_to_analyze:
            for api_call in session.api_calls:
                model_key = f"{api_call.provider}/{api_call.model}"
                model_usage[model_key]["calls"] += 1
                model_usage[model_key]["tokens"] += api_call.total_tokens
                model_usage[model_key]["cost"] += api_call.estimated_cost
        
        # Performance trends
        if len(sessions_to_analyze) > 1:
            sessions_by_time = sorted(sessions_to_analyze, key=lambda s: s.start_time)
            
            # Calculate trend indicators
            first_half = sessions_by_time[:len(sessions_by_time)//2]
            second_half = sessions_by_time[len(sessions_by_time)//2:]
            
            first_half_avg_cost = sum(s.total_cost for s in first_half) / len(first_half)
            second_half_avg_cost = sum(s.total_cost for s in second_half) / len(second_half)
            
            cost_trend = "improving" if second_half_avg_cost < first_half_avg_cost else "degrading"
        else:
            cost_trend = "insufficient_data"
        
        return {
            "summary": {
                "total_sessions": total_sessions,
                "successful_sessions": successful_sessions,
                "success_rate": (successful_sessions / total_sessions) * 100 if total_sessions > 0 else 0,
                "total_api_calls": total_api_calls,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "total_duration_seconds": total_duration
            },
            "averages": {
                "tokens_per_session": avg_tokens_per_session,
                "cost_per_session": avg_cost_per_session,
                "duration_per_session": avg_duration_per_session,
                "api_calls_per_session": avg_api_calls_per_session
            },
            "component_breakdown": dict(component_metrics),
            "model_usage": dict(model_usage),
            "performance_trends": {
                "cost_trend": cost_trend
            }
        }
    
    def export_metrics(self, output_file: str, session_ids: List[str] = None) -> bool:
        """Export metrics to a JSON file"""
        try:
            all_sessions = self.get_all_sessions()
            
            if session_ids:
                filtered_sessions = {k: v for k, v in all_sessions.items() if k in session_ids}
            else:
                filtered_sessions = all_sessions
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "sessions": filtered_sessions,
                "summary": self.generate_performance_summary(session_ids)
            }
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported metrics to {output_file}", ComponentType.MAIN_PIPELINE,
                           metadata={"sessions_exported": len(filtered_sessions)})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}", ComponentType.MAIN_PIPELINE)
            return False
    
    def clear_completed_sessions(self, older_than_hours: int = 24) -> int:
        """Clear completed sessions older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        with self._lock:
            sessions_to_remove = []
            for session_id, session in self.completed_sessions.items():
                if session.end_time and session.end_time < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.completed_sessions[session_id]
            
            self.logger.info(f"Cleared {len(sessions_to_remove)} old sessions", ComponentType.MAIN_PIPELINE)
            
            return len(sessions_to_remove)
    
    def get_cost_breakdown(self, session_id: str) -> Dict[str, Any]:
        """Get detailed cost breakdown for a session"""
        session_data = self.get_session_metrics(session_id)
        if not session_data:
            return {"error": f"Session {session_id} not found"}
        
        api_calls = session_data.get("api_calls", [])
        
        # Cost by component
        component_costs = defaultdict(float)
        # Cost by model
        model_costs = defaultdict(float)
        # Cost by provider
        provider_costs = defaultdict(float)
        
        for call in api_calls:
            component_costs[call["component"]] += call["estimated_cost"]
            model_costs[call["model"]] += call["estimated_cost"]
            provider_costs[call["provider"]] += call["estimated_cost"]
        
        return {
            "session_id": session_id,
            "total_cost": session_data["total_cost"],
            "breakdown": {
                "by_component": dict(component_costs),
                "by_model": dict(model_costs),
                "by_provider": dict(provider_costs)
            },
            "cost_per_token": session_data["total_cost"] / session_data["total_tokens"] 
                            if session_data["total_tokens"] > 0 else 0
        }