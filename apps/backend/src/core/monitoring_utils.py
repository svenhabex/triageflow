"""
Monitoring utilities for production LLM usage tracking.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from .llm_monitor import LLMStats, llm_monitor


class ProductionMonitor:
    """Production-ready monitoring utilities for LLM usage."""

    @staticmethod
    def log_session_completion(session_id: str) -> Dict[str, Any]:
        """Log completion of a session and return monitoring data."""
        stats = llm_monitor.get_stats(session_id)
        insights = llm_monitor.get_optimization_insights(session_id)

        # Create a production-friendly summary
        summary = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "total_tokens": stats.total_tokens,
                "estimated_cost_usd": round(stats.total_cost_estimate, 4),
                "avg_duration_ms": round(stats.avg_duration_ms, 2),
                "retry_count": stats.retry_count,
                "retry_rate_percent": round(
                    (stats.retry_count / max(stats.total_requests, 1)) * 100, 1
                ),
            },
            "breakdown": {
                "by_agent": dict(stats.requests_by_agent),
                "by_method": dict(stats.requests_by_method),
                "by_type": dict(stats.requests_by_type),
            },
            "optimization": {
                "total_recommendations": len(insights.get("recommendations", [])),
                "high_priority_issues": len(
                    [
                        r
                        for r in insights.get("recommendations", [])
                        if r["priority"] == "high"
                    ]
                ),
                "cost_efficiency_score": ProductionMonitor._calculate_efficiency_score(
                    stats, insights
                ),
            },
        }

        # Log for production monitoring (could be sent to logging service)
        print(
            f"[LLM_MONITOR] Session {session_id} completed: {stats.total_requests} requests, ${stats.total_cost_estimate:.4f}"
        )

        return summary

    @staticmethod
    def _calculate_efficiency_score(stats: LLMStats, insights: Dict[str, Any]) -> float:
        """Calculate an efficiency score from 0-100 based on usage patterns."""
        score = 100.0

        # Deduct points for high retry rate
        retry_rate = (stats.retry_count / max(stats.total_requests, 1)) * 100
        if retry_rate > 10:
            score -= min(retry_rate * 2, 30)  # Max 30 point deduction

        # Deduct points for high cost
        if stats.total_cost_estimate > 0.02:  # More than 2 cents per session
            score -= min(stats.total_cost_estimate * 1000, 20)  # Max 20 point deduction

        # Deduct points for high priority issues
        high_priority_count = len(
            [r for r in insights.get("recommendations", []) if r["priority"] == "high"]
        )
        score -= high_priority_count * 15  # 15 points per high priority issue

        # Deduct points for slow response times
        if stats.avg_duration_ms > 3000:  # Slower than 3 seconds
            score -= min(
                (stats.avg_duration_ms - 3000) / 100, 25
            )  # Max 25 point deduction

        return max(0.0, round(score, 1))

    @staticmethod
    def get_daily_summary() -> Dict[str, Any]:
        """Get a summary of all sessions from today."""
        all_stats = llm_monitor.get_stats()
        all_insights = llm_monitor.get_optimization_insights()

        # Calculate daily totals
        daily_summary = {
            "date": datetime.now().date().isoformat(),
            "total_sessions": len(llm_monitor.session_requests),
            "total_requests": all_stats.total_requests,
            "total_cost_usd": round(all_stats.total_cost_estimate, 4),
            "avg_requests_per_session": round(
                all_stats.total_requests / max(len(llm_monitor.session_requests), 1), 1
            ),
            "avg_cost_per_session": round(
                all_stats.total_cost_estimate
                / max(len(llm_monitor.session_requests), 1),
                4,
            ),
            "top_agents": ProductionMonitor._get_top_usage(all_stats.requests_by_agent),
            "top_methods": ProductionMonitor._get_top_usage(
                all_stats.requests_by_method
            ),
            "optimization_alerts": [
                r
                for r in all_insights.get("recommendations", [])
                if r["priority"] in ["high", "medium"]
            ],
        }

        return daily_summary

    @staticmethod
    def _get_top_usage(usage_dict: Dict[str, int], top_n: int = 3) -> list:
        """Get top N items from a usage dictionary."""
        sorted_items = sorted(usage_dict.items(), key=lambda x: x[1], reverse=True)
        return [{"name": name, "count": count} for name, count in sorted_items[:top_n]]

    @staticmethod
    def export_session_data(session_id: str, format: str = "json") -> str:
        """Export session monitoring data in specified format."""
        stats = llm_monitor.get_stats(session_id)
        insights = llm_monitor.get_optimization_insights(session_id)

        data = {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "total_tokens": stats.total_tokens,
                "estimated_cost_usd": stats.total_cost_estimate,
                "avg_duration_ms": stats.avg_duration_ms,
                "retry_count": stats.retry_count,
            },
            "breakdown": {
                "requests_by_agent": dict(stats.requests_by_agent),
                "requests_by_method": dict(stats.requests_by_method),
                "requests_by_type": dict(stats.requests_by_type),
            },
            "recommendations": insights.get("recommendations", []),
        }

        if format.lower() == "json":
            return json.dumps(data, indent=2)
        elif format.lower() == "csv":
            # Convert to CSV format (simplified)
            csv_lines = [
                "metric,value",
                f"total_requests,{stats.total_requests}",
                f"successful_requests,{stats.successful_requests}",
                f"failed_requests,{stats.failed_requests}",
                f"total_tokens,{stats.total_tokens}",
                f"estimated_cost_usd,{stats.total_cost_estimate:.4f}",
                f"avg_duration_ms,{stats.avg_duration_ms:.2f}",
                f"retry_count,{stats.retry_count}",
            ]
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @staticmethod
    def check_cost_threshold(
        session_id: Optional[str] = None, threshold_usd: float = 0.10
    ) -> Dict[str, Any]:
        """Check if LLM usage has exceeded cost threshold."""
        stats = llm_monitor.get_stats(session_id)

        exceeded = stats.total_cost_estimate > threshold_usd

        result = {
            "threshold_exceeded": exceeded,
            "current_cost": stats.total_cost_estimate,
            "threshold": threshold_usd,
            "percentage_of_threshold": (stats.total_cost_estimate / threshold_usd)
            * 100,
            "session_id": session_id,
            "total_requests": stats.total_requests,
        }

        if exceeded:
            print(
                f"⚠️ [COST_ALERT] LLM usage exceeded threshold: ${stats.total_cost_estimate:.4f} > ${threshold_usd:.4f}"
            )

        return result

    @staticmethod
    def get_optimization_report(session_id: Optional[str] = None) -> str:
        """Generate a human-readable optimization report."""
        stats = llm_monitor.get_stats(session_id)
        insights = llm_monitor.get_optimization_insights(session_id)

        scope = f"Session {session_id}" if session_id else "Overall"

        report = f"""
LLM Usage Optimization Report - {scope}
{"=" * 50}

📊 USAGE STATISTICS:
- Total Requests: {stats.total_requests}
- Success Rate: {(stats.successful_requests / max(stats.total_requests, 1)) * 100:.1f}%
- Total Tokens: {stats.total_tokens:,}
- Estimated Cost: ${stats.total_cost_estimate:.4f}
- Average Duration: {stats.avg_duration_ms:.1f}ms

🔧 REQUEST BREAKDOWN:
"""

        for agent, count in stats.requests_by_agent.items():
            report += f"- {agent}: {count} requests\n"

        report += "\n💡 OPTIMIZATION OPPORTUNITIES:\n"

        recommendations = insights.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_icon = {"high": "🚨", "medium": "⚠️", "low": "💡"}.get(
                    rec["priority"], "📝"
                )
                report += f"{i}. {priority_icon} {rec['message']}\n"
        else:
            report += "✅ No optimization issues detected!\n"

        efficiency_score = ProductionMonitor._calculate_efficiency_score(
            stats, insights
        )
        report += f"\n⭐ EFFICIENCY SCORE: {efficiency_score}/100\n"

        if efficiency_score >= 90:
            report += "🎉 Excellent efficiency!\n"
        elif efficiency_score >= 70:
            report += "👍 Good efficiency with room for improvement.\n"
        elif efficiency_score >= 50:
            report += "⚠️ Moderate efficiency - consider optimizations.\n"
        else:
            report += "🚨 Low efficiency - immediate optimization recommended.\n"

        return report


def add_monitoring_to_workflow_response(
    session_id: str, response_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Add monitoring data to workflow response for frontend visibility."""

    # Get monitoring summary
    monitoring_summary = ProductionMonitor.log_session_completion(session_id)

    # Add to response
    response_data["monitoring"] = {
        "llm_usage": {
            "total_requests": monitoring_summary["metrics"]["total_requests"],
            "estimated_cost_usd": monitoring_summary["metrics"]["estimated_cost_usd"],
            "efficiency_score": monitoring_summary["optimization"][
                "cost_efficiency_score"
            ],
            "has_optimization_alerts": monitoring_summary["optimization"][
                "high_priority_issues"
            ]
            > 0,
        }
    }

    # Clean up session data to prevent memory leaks
    llm_monitor.clear_session(session_id)

    return response_data


# Environment variable to control monitoring
def is_monitoring_enabled() -> bool:
    """Check if LLM monitoring is enabled."""
    return llm_monitor.enabled
