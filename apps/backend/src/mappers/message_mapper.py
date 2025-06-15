"""
Message mapper for converting between different message formats.
"""

import uuid
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.models import ChatMessage
from src.models.chat_models import MessageType


class MessageMapper:
    """Mapper class for converting between message formats."""

    @staticmethod
    def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
        """Convert a langchain message to ChatMessage format."""

        if isinstance(message, HumanMessage):
            message_type = MessageType.HUMAN
        elif isinstance(message, (AIMessage, SystemMessage)):
            message_type = MessageType.ASSISTANT
        else:
            message_type = MessageType.ASSISTANT

        message_id = getattr(message, "id", None) or str(uuid.uuid4())

        return ChatMessage(id=message_id, content=message.content, type=message_type)

    @staticmethod
    def convert_messages_from_state(state: dict[str, Any]) -> list[ChatMessage]:
        """Convert messages from workflow state to ChatMessage format."""

        messages = state.get("messages", [])
        chat_messages = []

        for message in messages:
            if hasattr(message, "content") and hasattr(message, "__class__"):
                chat_messages.append(MessageMapper.langchain_to_chat_message(message))

        return chat_messages

    @staticmethod
    def chat_message_to_langchain(chat_message: ChatMessage) -> BaseMessage:
        """Convert ChatMessage to langchain message format."""

        if chat_message.type == MessageType.HUMAN:
            return HumanMessage(content=chat_message.content, id=chat_message.id)
        else:
            return AIMessage(content=chat_message.content, id=chat_message.id)
