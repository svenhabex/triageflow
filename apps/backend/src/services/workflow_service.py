"""
Workflow service for handling workflow execution and streaming.
"""

import traceback
from collections.abc import AsyncGenerator
from typing import Any, Optional, Union

from fastapi import WebSocket
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.graphs import triage_workflow
from src.mappers import ResultMapper
from src.models import (
    AgentNameEnum,
    ErrorAgentMessage,
    IntakeResponseAgentMessage,
    RunningAgentMessage,
    StartWorkflowMessage,
    TriageMessageTypeEnum,
    TriageResponseAgentMessage,
)
from src.models.agent_models import EndWorkflowMessage


class WorkflowService:
    """Service for managing workflow execution and WebSocket streaming."""

    def __init__(self):
        self.workflow = triage_workflow

    async def start_workflow_stream(
        self, websocket: WebSocket, session_id: str, conversation: str
    ) -> None:
        """Start workflow and stream results to WebSocket."""

        try:
            await self._send_workflow_started(websocket, session_id, conversation)

            # Execute workflow with streaming
            async for message in self._execute_workflow_stream(
                session_id, conversation
            ):
                await websocket.send_text(message)

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
    ) -> AsyncGenerator[str, None]:
        """Execute workflow and yield formatted messages as JSON strings."""

        initial_state = {
            "messages": [HumanMessage(content=conversation)],
            "session_id": session_id,
        }

        config = {"configurable": {"thread_id": session_id}}

        async for event in self.workflow.app.astream_events(
            initial_state, config=config
        ):
            # Send running message when a node starts
            if event["event"] == "on_chain_start" and event["name"] in [
                "supervisor",
                "intake",
                "triage",
            ]:
                node_name = event["name"]
                running_message = self._create_running_agent_update(
                    node_name, session_id
                )
                yield running_message.model_dump_json(by_alias=True)

            # Handle node completion events for result processing
            elif event["event"] == "on_chain_end" and event["name"] in [
                "supervisor",
                "intake",
                "triage",
            ]:
                node_name = event["name"]
                node_output = event["data"]["output"]

                # Yield formatted results for specific nodes
                async for formatted_message in self._handle_node_completion(
                    node_name, node_output, session_id
                ):
                    import json

                    # Convert Pydantic models to dict before JSON serialization
                    if hasattr(formatted_message, "model_dump"):
                        yield json.dumps(formatted_message.model_dump(by_alias=True))
                    else:
                        yield json.dumps(formatted_message)

    async def _handle_node_completion(
        self, node_name: str, node_output: dict[str, Any], session_id: str
    ) -> AsyncGenerator[Union[dict[str, Any], BaseModel], None]:
        """Handle completion of specific nodes and yield appropriate messages."""

        if node_name == "intake" and node_output.get("intake_conversation_info"):
            yield await self._create_intake_result(node_output, session_id)

        elif node_name == "triage" and node_output.get("triage_info"):
            yield await self._create_triage_result(node_output, session_id)

        elif node_name == "supervisor":
            supervisor_message = self._create_supervisor_update(node_output, session_id)
            if supervisor_message:
                yield supervisor_message

    async def _create_intake_result(
        self, node_output: dict[str, Any], session_id: str
    ) -> Union[IntakeResponseAgentMessage, ErrorAgentMessage]:
        """Create formatted intake result message."""

        try:
            intake_response = ResultMapper.map_node_result(node_output, "intake")

            return IntakeResponseAgentMessage(
                data=intake_response,
                session_id=session_id,
            )
        except Exception as e:
            return ErrorAgentMessage(
                type=TriageMessageTypeEnum.ERROR_AGENT,
                error=f"Failed to format intake result: {str(e)}",
                session_id=session_id,
            )

    async def _create_triage_result(
        self, node_output: dict[str, Any], session_id: str
    ) -> Union[TriageResponseAgentMessage, ErrorAgentMessage]:
        """Create formatted triage result message."""

        try:
            triage_response = ResultMapper.map_node_result(node_output, "triage")

            return TriageResponseAgentMessage(
                data=triage_response,
                session_id=session_id,
            )
        except Exception as e:
            return ErrorAgentMessage(
                type=TriageMessageTypeEnum.ERROR_AGENT,
                error=f"Failed to format triage result: {str(e)}",
                session_id=session_id,
            )

    def _create_supervisor_update(
        self, node_output: dict[str, Any], session_id: str
    ) -> Optional[dict[str, Any]]:
        """Create supervisor status update message."""

        last_node = node_output.get("last_node")
        intake_info = node_output.get("intake_conversation_info")
        triage_info = node_output.get("triage_info")

        if last_node == "intake":
            if intake_info:
                return {
                    "type": TriageMessageTypeEnum.START_AGENT,
                    "name": AgentNameEnum.TRIAGE,
                    "message": "Patient intake completed successfully",
                    "session_id": session_id,
                }
            else:
                return {
                    "type": TriageMessageTypeEnum.ERROR_AGENT,
                    "error": "Intake completed but no information extracted",
                    "session_id": session_id,
                }

        elif last_node == "triage":
            if triage_info:
                return {
                    "type": TriageMessageTypeEnum.START_AGENT,
                    "name": AgentNameEnum.TRIAGE,
                    "message": "Triage completed successfully",
                    "session_id": session_id,
                }
            else:
                return {
                    "type": TriageMessageTypeEnum.ERROR_AGENT,
                    "error": "Triage completed but no information extracted",
                    "session_id": session_id,
                }

        return None

    def _create_running_agent_update(
        self, node_name: str, session_id: str
    ) -> RunningAgentMessage:
        """Create running agent update message."""

        # Map node names to agent names
        agent_name_map = {
            "intake": AgentNameEnum.INTAKE,
            "triage": AgentNameEnum.TRIAGE,
            "coordinator": AgentNameEnum.COORDINATOR,
        }

        agent_name = agent_name_map.get(node_name, AgentNameEnum.COORDINATOR)

        return RunningAgentMessage(
            type=TriageMessageTypeEnum.RUNNING_AGENT,
            name=agent_name,
            session_id=session_id,
        )

    async def _send_workflow_started(
        self, websocket: WebSocket, session_id: str, conversation: str
    ) -> None:
        """Send workflow started message."""

        message = StartWorkflowMessage(
            type=TriageMessageTypeEnum.START_WORKFLOW,
            conversation=conversation,
            session_id=session_id,
        )
        await websocket.send_text(message.model_dump_json(by_alias=True))

    async def _send_workflow_completed(
        self, websocket: WebSocket, session_id: str
    ) -> None:
        """Send workflow completed message."""

        message = EndWorkflowMessage(
            type=TriageMessageTypeEnum.END_WORKFLOW,
            session_id=session_id,
        )
        await websocket.send_text(message.model_dump_json(by_alias=True))

    async def _send_error(
        self, websocket: WebSocket, session_id: str, error: str
    ) -> None:
        """Send error message."""

        message = ErrorAgentMessage(
            type=TriageMessageTypeEnum.ERROR_AGENT,
            error=error,
            session_id=session_id,
        )
        await websocket.send_text(message.model_dump_json(by_alias=True))

    async def execute_workflow(
        self, conversation: str, thread_id: str = "default"
    ) -> dict[str, Any]:
        """Execute workflow synchronously (for HTTP endpoints)."""

        initial_state = {"messages": [HumanMessage(content=conversation)]}
        return await self.workflow.run(initial_state, thread_id)
