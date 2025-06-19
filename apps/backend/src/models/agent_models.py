"""
Agent response models corresponding to TypeScript interfaces.
"""

from enum import Enum
from typing import TypeVar, Union

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class AgentNameEnum(str, Enum):
    """Python equivalent of AgentNameEnum from TypeScript."""

    INTAKE = "INTAKE"
    TRIAGE = "TRIAGE"
    COORDINATOR = "COORDINATOR"


class WebSocketTriageTypeEnum(str, Enum):
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


class IntakeResponseDTO(BaseModel):
    """Python equivalent of IntakeResult from TypeScript."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symptoms: list[str] = []
    pain_level: int = 0
    chief_complaint: str = ""
    medications: list[str] = []
    allergies: list[str] = []
    additional_notes: str = ""


class StartWorkflowMessage(BaseModel):
    """WebSocket message for starting workflow."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.START_WORKFLOW
    conversation: str


class RunningAgentMessage(BaseModel):
    """WebSocket message for agent running status."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.RUNNING_AGENT
    name: AgentNameEnum


class StartAgentMessage(BaseModel):
    """WebSocket message for starting an agent."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.START_AGENT
    name: AgentNameEnum


class ResponseAgentMessage(BaseModel):
    """WebSocket message for agent response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.RESPONSE_AGENT
    name: str = AgentNameEnum.INTAKE
    data: IntakeResponseDTO


class ErrorAgentMessage(BaseModel):
    """WebSocket message for agent error."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.ERROR_AGENT
    error: str


class HumanApprovalMessage(BaseModel):
    """WebSocket message for human approval."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.HUMAN_APPROVAL
    approved: bool


class EndWorkflowMessage(BaseModel):
    """WebSocket message for ending workflow."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    type: str = WebSocketTriageTypeEnum.END_WORKFLOW


# Union type equivalent to WebSocketTriageDTO from TypeScript
WebSocketTriageDTO = Union[
    StartWorkflowMessage,
    RunningAgentMessage,
    StartAgentMessage,
    ResponseAgentMessage,
    ErrorAgentMessage,
    HumanApprovalMessage,
    EndWorkflowMessage,
]
