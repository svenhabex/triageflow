"""
Agent response models corresponding to TypeScript interfaces.
"""

from enum import Enum
from typing import Annotated, Literal, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.models.intake_models import IntakeResponseDTO
from src.models.triage_models import TriageResponseDTO

T = TypeVar("T")


class AgentNameEnum(str, Enum):
    """Python equivalent of AgentNameEnum from TypeScript."""

    INTAKE = "INTAKE"
    TRIAGE = "TRIAGE"
    COORDINATOR = "COORDINATOR"


class TriageMessageTypeEnum(str, Enum):
    """Python equivalent of WebSocketTriageTypeEnum from TypeScript."""

    START_WORKFLOW = "START_WORKFLOW"
    RUNNING_AGENT = "RUNNING_AGENT"
    START_AGENT = "START_AGENT"
    RESPONSE_AGENT = "RESPONSE_AGENT"
    ERROR_AGENT = "ERROR_AGENT"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    END_WORKFLOW = "END_WORKFLOW"


class StartIntakeRequest(BaseModel):
    """Python equivalent of StartIntakeRequest from TypeScript."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation: str


class TriageMessage(BaseModel):
    """Base class for all WebSocket messages."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str


class StartWorkflowMessage(TriageMessage):
    """WebSocket message for starting workflow."""

    type: str = TriageMessageTypeEnum.START_WORKFLOW
    conversation: str


class RunningAgentMessage(TriageMessage):
    """WebSocket message for agent running status."""

    type: str = TriageMessageTypeEnum.RUNNING_AGENT
    name: AgentNameEnum


class StartAgentMessage(TriageMessage):
    """WebSocket message for starting an agent."""

    type: str = TriageMessageTypeEnum.START_AGENT
    name: AgentNameEnum


class IntakeResponseAgentMessage(TriageMessage):
    """WebSocket message for intake agent response."""

    type: str = TriageMessageTypeEnum.RESPONSE_AGENT
    name: Literal[AgentNameEnum.INTAKE] = AgentNameEnum.INTAKE
    data: IntakeResponseDTO


class TriageResponseAgentMessage(TriageMessage):
    """WebSocket message for triage agent response."""

    type: str = TriageMessageTypeEnum.RESPONSE_AGENT
    name: Literal[AgentNameEnum.TRIAGE] = AgentNameEnum.TRIAGE
    data: TriageResponseDTO


ResponseAgentMessage = Annotated[
    Union[IntakeResponseAgentMessage, TriageResponseAgentMessage],
    Field(discriminator="name"),
]


class ErrorAgentMessage(TriageMessage):
    """WebSocket message for agent error."""

    type: str = TriageMessageTypeEnum.ERROR_AGENT
    error: str


class HumanApprovalMessage(TriageMessage):
    """WebSocket message for human approval."""

    type: str = TriageMessageTypeEnum.HUMAN_APPROVAL
    approved: bool


class EndWorkflowMessage(TriageMessage):
    """WebSocket message for ending workflow."""

    type: str = TriageMessageTypeEnum.END_WORKFLOW


TriageDTO = Union[
    StartWorkflowMessage,
    RunningAgentMessage,
    StartAgentMessage,
    IntakeResponseAgentMessage,
    TriageResponseAgentMessage,
    ErrorAgentMessage,
    HumanApprovalMessage,
    EndWorkflowMessage,
]
