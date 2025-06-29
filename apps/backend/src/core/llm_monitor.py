"""
LLM Request Monitoring and Analytics Service.
Tracks LLM usage patterns, costs, and provides optimization insights.
"""

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional


@dataclass
class LLMRequest:
    """Individual LLM request data."""

    timestamp: datetime
    agent_name: str
    method_name: str
    request_type: str  # "standard", "structured", "tool_calling"
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimate: Optional[float] = None
    duration_ms: float = 0
    session_id: Optional[str] = None
    retry_attempt: int = 0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class LLMStats:
    """Aggregate LLM statistics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost_estimate: float = 0
    avg_duration_ms: float = 0
    requests_by_agent: Dict[str, int] = field(default_factory=dict)
    requests_by_method: Dict[str, int] = field(default_factory=dict)
    requests_by_type: Dict[str, int] = field(default_factory=dict)
    retry_count: int = 0


class LLMMonitor:
    """LLM monitoring service for tracking requests and analyzing usage patterns."""

    # Gemini pricing (as of 2024) - rates per 1M tokens
    GEMINI_PRICING = {
        "gemini-2.5-flash-lite-preview-06-17": {
            "input": 0.075,  # $0.075 per 1M input tokens
            "output": 0.30,  # $0.30 per 1M output tokens
        },
        "gemini-2.5-flash-preview-05-20": {
            "input": 0.075,
            "output": 0.30,
        },
    }

    def __init__(self):
        self.requests: List[LLMRequest] = []
        self.session_requests: Dict[str, List[LLMRequest]] = defaultdict(list)
        self.enabled = os.getenv("LLM_MONITORING_ENABLED", "true").lower() == "true"

    def record_request(self, request: LLMRequest) -> None:
        """Record a new LLM request."""
        if not self.enabled:
            return

        self.requests.append(request)
        if request.session_id:
            self.session_requests[request.session_id].append(request)

    def estimate_cost(
        self, model_name: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Estimate cost based on token usage."""
        pricing = self.GEMINI_PRICING.get(
            model_name, self.GEMINI_PRICING["gemini-2.5-flash-lite-preview-06-17"]
        )

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def get_stats(self, session_id: Optional[str] = None) -> LLMStats:
        """Get aggregate statistics for all requests or a specific session."""
        requests = (
            self.session_requests.get(session_id, []) if session_id else self.requests
        )

        if not requests:
            return LLMStats()

        stats = LLMStats()
        durations = []

        for req in requests:
            stats.total_requests += 1
            if req.success:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1

            if req.total_tokens:
                stats.total_tokens += req.total_tokens

            if req.cost_estimate:
                stats.total_cost_estimate += req.cost_estimate

            if req.duration_ms > 0:
                durations.append(req.duration_ms)

            if req.retry_attempt > 0:
                stats.retry_count += 1

            # Track by agent
            stats.requests_by_agent[req.agent_name] = (
                stats.requests_by_agent.get(req.agent_name, 0) + 1
            )

            # Track by method
            stats.requests_by_method[req.method_name] = (
                stats.requests_by_method.get(req.method_name, 0) + 1
            )

            # Track by type
            stats.requests_by_type[req.request_type] = (
                stats.requests_by_type.get(req.request_type, 0) + 1
            )

        if durations:
            stats.avg_duration_ms = sum(durations) / len(durations)

        return stats

    def get_optimization_insights(
        self, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze usage patterns and provide optimization recommendations."""
        stats = self.get_stats(session_id)
        requests = (
            self.session_requests.get(session_id, []) if session_id else self.requests
        )

        insights = {
            "total_requests": stats.total_requests,
            "estimated_cost": round(stats.total_cost_estimate, 4),
            "retry_rate": (stats.retry_count / max(stats.total_requests, 1)) * 100,
            "avg_duration_ms": round(stats.avg_duration_ms, 2),
            "recommendations": [],
        }

        # Analyze patterns and generate recommendations
        if stats.retry_count > stats.total_requests * 0.1:  # >10% retry rate
            insights["recommendations"].append(
                {
                    "type": "high_retry_rate",
                    "message": f"High retry rate detected ({stats.retry_count} retries). Consider improving error handling or prompt design.",
                    "priority": "high",
                }
            )

        # Check for excessive tool calling
        tool_calling_requests = stats.requests_by_type.get("tool_calling", 0)
        if tool_calling_requests > stats.total_requests * 0.5:
            insights["recommendations"].append(
                {
                    "type": "excessive_tool_calling",
                    "message": f"High tool calling usage ({tool_calling_requests} requests). Consider consolidating tool calls or caching results.",
                    "priority": "medium",
                }
            )

        # Check for duplicate patterns
        method_counts = stats.requests_by_method
        max_method_count = max(method_counts.values()) if method_counts else 0
        if max_method_count > 3:
            most_used_method = max(method_counts, key=method_counts.get)
            insights["recommendations"].append(
                {
                    "type": "repeated_calls",
                    "message": f"Method '{most_used_method}' called {max_method_count} times. Consider caching or batching.",
                    "priority": "medium",
                }
            )

        # Cost optimization suggestions
        if stats.total_cost_estimate > 0.01:  # More than 1 cent per session
            insights["recommendations"].append(
                {
                    "type": "cost_optimization",
                    "message": f"Session cost: ${round(stats.total_cost_estimate, 4)}. Consider using smaller models for simple tasks.",
                    "priority": "low",
                }
            )

        return insights

    def print_summary(self, session_id: Optional[str] = None) -> None:
        """Print a formatted summary of LLM usage."""
        stats = self.get_stats(session_id)
        insights = self.get_optimization_insights(session_id)

        scope = f"Session {session_id}" if session_id else "Overall"
        print(f"\n=== LLM Usage Summary ({scope}) ===")
        print(f"Total Requests: {stats.total_requests}")
        print(f"Successful: {stats.successful_requests}")
        print(f"Failed: {stats.failed_requests}")
        print(f"Retries: {stats.retry_count}")
        print(f"Total Tokens: {stats.total_tokens:,}")
        print(f"Estimated Cost: ${stats.total_cost_estimate:.4f}")
        print(f"Avg Duration: {stats.avg_duration_ms:.1f}ms")

        print("\nRequests by Agent:")
        for agent, count in stats.requests_by_agent.items():
            print(f"  {agent}: {count}")

        print("\nRequests by Method:")
        for method, count in stats.requests_by_method.items():
            print(f"  {method}: {count}")

        print("\nRequests by Type:")
        for req_type, count in stats.requests_by_type.items():
            print(f"  {req_type}: {count}")

        if insights["recommendations"]:
            print("\n🔍 Optimization Recommendations:")
            for rec in insights["recommendations"]:
                priority_icon = {"high": "🚨", "medium": "⚠️", "low": "💡"}.get(
                    rec["priority"], "📝"
                )
                print(f"  {priority_icon} {rec['message']}")

        print("=" * 50)

    def clear_session(self, session_id: str) -> None:
        """Clear monitoring data for a specific session."""
        if session_id in self.session_requests:
            del self.session_requests[session_id]

    def clear_all(self) -> None:
        """Clear all monitoring data."""
        self.requests.clear()
        self.session_requests.clear()


# Global monitor instance
llm_monitor = LLMMonitor()


def track_llm_request(
    agent_name: str, method_name: str, request_type: str = "standard"
):
    """Decorator to automatically track LLM requests."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not llm_monitor.enabled:
                return await func(*args, **kwargs)

            start_time = time.time()
            request = LLMRequest(
                timestamp=datetime.now(),
                agent_name=agent_name,
                method_name=method_name,
                request_type=request_type,
            )

            # Try to extract session_id from args/kwargs
            if hasattr(args[0], "__dict__") and "session_id" in str(args[0].__dict__):
                request.session_id = getattr(args[0], "session_id", None)
            elif "state" in kwargs and isinstance(kwargs["state"], dict):
                request.session_id = kwargs["state"].get("session_id")
            elif len(args) > 1 and isinstance(args[1], dict):
                request.session_id = args[1].get("session_id")

            try:
                result = await func(*args, **kwargs)
                request.success = True

                # Try to extract token usage if available
                if hasattr(result, "usage_metadata"):
                    usage = result.usage_metadata
                    request.prompt_tokens = getattr(usage, "input_tokens", None)
                    request.completion_tokens = getattr(usage, "output_tokens", None)
                    request.total_tokens = getattr(usage, "total_tokens", None)

                    if request.prompt_tokens and request.completion_tokens:
                        # Estimate cost (model name would need to be passed or extracted)
                        model_name = "gemini-2.5-flash-lite-preview-06-17"  # default
                        request.cost_estimate = llm_monitor.estimate_cost(
                            model_name, request.prompt_tokens, request.completion_tokens
                        )

                return result

            except Exception as e:
                request.success = False
                request.error_message = str(e)
                raise
            finally:
                request.duration_ms = (time.time() - start_time) * 1000
                llm_monitor.record_request(request)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not llm_monitor.enabled:
                return func(*args, **kwargs)

            start_time = time.time()
            request = LLMRequest(
                timestamp=datetime.now(),
                agent_name=agent_name,
                method_name=method_name,
                request_type=request_type,
            )

            try:
                result = func(*args, **kwargs)
                request.success = True
                return result
            except Exception as e:
                request.success = False
                request.error_message = str(e)
                raise
            finally:
                request.duration_ms = (time.time() - start_time) * 1000
                llm_monitor.record_request(request)

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
