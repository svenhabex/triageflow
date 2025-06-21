"""
Workflow service for handling workflow execution and streaming.
"""

import json
import traceback
from collections.abc import AsyncGenerator
from typing import Any, Optional

from fastapi import WebSocket
from langchain_core.messages import HumanMessage

from src.graphs import triage_workflow
from src.mappers import ResultMapper
from src.models.agent_models import AgentNameEnum, WebSocketTriageTypeEnum


class WorkflowService:
    """Service for managing workflow execution and WebSocket streaming."""

    def __init__(self):
        self.workflow = triage_workflow

    async def start_workflow_stream(
        self, websocket: WebSocket, session_id: str, conversation: str
    ) -> None:
        """Start workflow and stream results to WebSocket."""

        try:
            # Send initial acknowledgment
            await self._send_workflow_started(websocket, session_id)

            # Execute workflow with streaming
            async for message in self._execute_workflow_stream(
                session_id, conversation
            ):
                await websocket.send_text(json.dumps(message))

            # Send completion
            await self._send_workflow_completed(websocket, session_id)

        except Exception as e:
            # Print full stack trace to console for debugging
            print(f"=== WebSocket Error for session {session_id} ===")
            traceback.print_exc()
            print("=== End Error ===")

            await self._send_error(websocket, session_id, str(e))

    async def _execute_workflow_stream(
        self, session_id: str, conversation: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute workflow and yield formatted messages."""

        initial_state = {
            "messages": [HumanMessage(content=conversation)],
            "session_id": session_id,
        }

        config = {"configurable": {"thread_id": session_id}}

        async for chunk in self.workflow.app.astream(initial_state, config=config):
            for node_name, node_output in chunk.items():
                # Yield agent running status
                yield self._create_running_agent_update(node_name, session_id)

                # Yield formatted results for specific nodes
                async for formatted_message in self._handle_node_completion(
                    node_name, node_output, session_id
                ):
                    yield formatted_message

    async def _handle_node_completion(
        self, node_name: str, node_output: dict[str, Any], session_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Handle completion of specific nodes and yield appropriate messages."""

        if node_name == "intake" and node_output.get("intake_conversation_info"):
            yield await self._create_intake_result(node_output, session_id)

        elif node_name == "supervisor":
            supervisor_message = self._create_supervisor_update(node_output, session_id)
            if supervisor_message:
                yield supervisor_message

    async def _create_intake_result(
        self, node_output: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Create formatted intake result message."""

        try:
            agent_response = ResultMapper.create_agent_response(
                node_output, "completed"
            )

            return {
                "type": WebSocketTriageTypeEnum.RESPONSE_AGENT,
                "name": AgentNameEnum.INTAKE,
                "data": agent_response.data.model_dump(by_alias=True),
                "session_id": session_id,
                "status": "completed",
                "last_node": node_output.get("last_node", "intake"),
                "messages": [
                    msg.content if hasattr(msg, "content") else str(msg)
                    for msg in node_output.get("messages", [])
                ],
                "errors": node_output.get("errors", []),
                "message": "Intake completed successfully",
            }
        except Exception as e:
            return {
                "type": WebSocketTriageTypeEnum.ERROR_AGENT,
                "error": f"Failed to format intake result: {str(e)}",
                "session_id": session_id,
            }

    def _create_supervisor_update(
        self, node_output: dict[str, Any], session_id: str
    ) -> Optional[dict[str, Any]]:
        """Create supervisor status update message."""

        last_node = node_output.get("last_node")
        intake_info = node_output.get("intake_conversation_info")

        if last_node == "intake":
            if intake_info:
                return {
                    "type": WebSocketTriageTypeEnum.START_AGENT,
                    "name": AgentNameEnum.TRIAGE,
                    "message": "Patient intake completed successfully",
                    "session_id": session_id,
                }
            else:
                return {
                    "type": WebSocketTriageTypeEnum.ERROR_AGENT,
                    "error": "Intake completed but no information extracted",
                    "session_id": session_id,
                }

        return None

    def _create_running_agent_update(
        self, node_name: str, session_id: str
    ) -> dict[str, Any]:
        """Create running agent update message."""

        # Map node names to agent names
        agent_name_map = {
            "intake": AgentNameEnum.INTAKE,
            "triage": AgentNameEnum.TRIAGE,
            "supervisor": AgentNameEnum.COORDINATOR,
        }

        agent_name = agent_name_map.get(node_name, AgentNameEnum.COORDINATOR)

        return {
            "type": WebSocketTriageTypeEnum.RUNNING_AGENT,
            "name": agent_name,
            "session_id": session_id,
        }

    async def _send_workflow_started(
        self, websocket: WebSocket, session_id: str
    ) -> None:
        """Send workflow started message."""

        message = {
            "type": WebSocketTriageTypeEnum.START_WORKFLOW,
            "session_id": session_id,
            "message": "Triage workflow initiated",
        }
        await websocket.send_text(json.dumps(message))

    async def _send_workflow_completed(
        self, websocket: WebSocket, session_id: str
    ) -> None:
        """Send workflow completed message."""

        message = {
            "type": WebSocketTriageTypeEnum.END_WORKFLOW,
            "session_id": session_id,
            "message": "Triage workflow completed",
        }
        await websocket.send_text(json.dumps(message))

    async def _send_error(
        self, websocket: WebSocket, session_id: str, error: str
    ) -> None:
        """Send error message."""

        message = {
            "type": WebSocketTriageTypeEnum.ERROR_AGENT,
            "error": error,
            "session_id": session_id,
        }
        await websocket.send_text(json.dumps(message))

    def _make_serializable(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format."""
        if hasattr(obj, "content"):  # LangChain message objects
            return {"content": obj.content, "type": obj.__class__.__name__}
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, "model_dump"):  # Pydantic models
            return obj.model_dump()
        elif hasattr(obj, "__dict__"):  # Other objects with attributes
            return {k: self._make_serializable(v) for k, v in obj.__dict__.items()}
        else:
            return obj

    async def execute_workflow(
        self, conversation: str, thread_id: str = "default"
    ) -> dict[str, Any]:
        """Execute workflow synchronously (for HTTP endpoints)."""

        initial_state = {"messages": [HumanMessage(content=conversation)]}
        return await self.workflow.run(initial_state, thread_id)
