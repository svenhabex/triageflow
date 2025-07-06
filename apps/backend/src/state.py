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


class IntakeAgentState(MessagesState):
    """
    Local state for the intake agent.
    """

    # Output (what intake agent produces)
    patient_info: Optional[PatientInfo] = None
    intake_conversation_info: Optional[IntakeConversationInfo] = None

    # Internal control
    retry_count: int = 0
    errors: Annotated[list[str], add] = []


class TriageAgentState(MessagesState):
    """
    Local state for the triage agent.
    """

    # Input (what triage agent receives)
    patient_info: Optional[PatientInfo] = None
    intake_conversation_info: Optional[IntakeConversationInfo] = None

    # Output (what triage agent produces)
    triage_info: Optional[TriageInformation] = None

    # Internal control
    retry_count: int = 0
    errors: Annotated[list[str], add] = []


class CoordinatorAgentState(MessagesState):
    """
    Local state for the coordinator agent.
    """

    # Input (what coordinator agent receives)
    patient_info: Optional[PatientInfo] = None
    intake_conversation_info: Optional[IntakeConversationInfo] = None
    triage_info: Optional[TriageInformation] = None

    # Output (what coordinator agent produces)
    available_staff: Optional[list[StaffMember]] = None

    # Internal control
    retry_count: int = 0
    errors: Annotated[list[str], add] = []
