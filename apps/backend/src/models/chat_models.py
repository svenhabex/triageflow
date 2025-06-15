from enum import Enum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class MessageType(str, Enum):
    """Enum for message types, matching the frontend TypeScript interface."""

    HUMAN = "human"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Chat message model matching the frontend TypeScript interface."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    content: str
    type: MessageType
