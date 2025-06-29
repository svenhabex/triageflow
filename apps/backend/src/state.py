"""
Shared state definitions for the multi-agent workflow system.
"""

from operator import add
from typing import Annotated, Any, Optional

from langgraph.graph import MessagesState

from src.core import config
from src.models import (
    IntakeConversationInfo,
    PatientInfo,
    StaffMember,
    TriageInformation,
)


class WorkflowState(MessagesState):
    """
    Extended state for the multi-agent workflow system.
    Inherits from MessagesState to maintain conversation history.
    """

    # Patient information
    patient_info: Optional[PatientInfo] = None

    # Agent outputs
    intake_conversation_info: Optional[IntakeConversationInfo] = None
    triage_info: Optional[TriageInformation] = None
    available_staff: Optional[list[StaffMember]] = None

    # Workflow control
    last_node: Optional[str] = None

    # Error handling
    errors: Annotated[list[str], add] = []
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
