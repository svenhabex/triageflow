"""
Agents package for the multi-agent triage workflow system.
"""

from .coordinator import CoordinatorAgent
from .intake import IntakeAgent
from .triage import TriageAgent

# Create singleton instances
coordinator_agent = CoordinatorAgent()
intake_agent = IntakeAgent()
triage_agent = TriageAgent()

__all__ = [
    "CoordinatorAgent",
    "IntakeAgent",
    "TriageAgent",
    "coordinator_agent",
    "intake_agent",
    "triage_agent",
]
