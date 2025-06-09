"""
Shared state definitions for the multi-agent workflow system.
"""

from typing import Any, Literal, Optional

from langgraph.graph import MessagesState
from pydantic import BaseModel

from ..core.config import config


class PatientInfo(BaseModel):
    """Patient information model."""

    patient_id: str
    name: str
    age: Optional[int] = None
    medical_history: Optional[list[str]] = None
    current_symptoms: Optional[list[str]] = None
    vital_signs: Optional[dict[str, Any]] = None


class TriageDecision(BaseModel):
    """Triage decision model."""

    priority_level: Literal[1, 2, 3, 4, 5]
    reasoning: str
    recommended_actions: list[str]
    estimated_wait_time: Optional[int] = None


class WorkflowState(MessagesState):
    """
    Extended state for the multi-agent workflow system.
    Inherits from MessagesState to maintain conversation history.
    """

    # Patient information
    patient_info: Optional[PatientInfo] = None

    # Agent outputs
    intake_completed: bool = False
    intake_data: Optional[dict[str, Any]] = None

    triage_completed: bool = False
    triage_decision: Optional[TriageDecision] = None

    # Workflow control
    last_node: Optional[str] = None

    # Error handling
    errors: list[str] = []
    retry_count: int = 0

    # Additional context
    context: dict[str, Any] = {}

    def should_retry(self) -> bool:
        """Check if workflow should retry based on config."""
        return self.retry_count < config.max_retries

    def get_timeout_seconds(self) -> int:
        """Get timeout seconds from config."""
        return config.timeout_seconds

    def get_required_intake_fields(self) -> list[str]:
        """Get required intake fields from config."""
        return config.intake_agent_config["required_fields"]

    def is_reasoning_required(self) -> bool:
        """Check if reasoning is required for triage decisions."""
        return config.triage_agent_config["reasoning_required"]
