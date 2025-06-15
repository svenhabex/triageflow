"""
Agent response models corresponding to TypeScript interfaces.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from .chat_models import ChatMessage

T = TypeVar("T")


class AgentResponse(BaseModel, Generic[T]):
    """Python equivalent of AgentResponse<T> from TypeScript."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str
    messages: list[ChatMessage] = []
    errors: list[str] = []
    last_node: str
    result: T


class StartIntakeResult(BaseModel):
    """Python equivalent of StartIntakeResult from TypeScript."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symptoms: list[str] = []
    pain_level: int = 0
    chief_complaint: str = ""
    additional_notes: str = ""
