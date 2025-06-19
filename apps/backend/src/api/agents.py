"""
API endpoints for the multi-agent triage system.
"""

import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.mappers import ResultMapper
from src.models import IntakeResponseDTO, WebSocketTriageDTO, WebSocketTriageTypeEnum
from src.services import WorkflowService

router = APIRouter()
active_connections: dict[str, WebSocket] = {}
workflow_service = WorkflowService()


class PatientIntakeRequest(BaseModel):
    """Request model for patient intake."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation: str


async def patient_triage_ws(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time workflow streaming."""

    await websocket.accept()
    active_connections[session_id] = websocket

    print(f"New connection: {session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message_data: WebSocketTriageDTO = json.loads(data)

            if message_data["type"] == WebSocketTriageTypeEnum.START_WORKFLOW:
                await workflow_service.start_workflow_stream(
                    websocket, session_id, message_data["conversation"]
                )
            elif message_data["type"] == WebSocketTriageTypeEnum.HUMAN_APPROVAL:
                await handle_approval(websocket, session_id, message_data)
            elif message_data["type"] == WebSocketTriageTypeEnum.END_WORKFLOW:
                await handle_continue_workflow(websocket, session_id)

    except WebSocketDisconnect:
        active_connections.pop(session_id, None)


async def handle_approval(websocket: WebSocket, session_id: str, data: dict):
    """Handle user approval/rejection (placeholder for future implementation)."""
    try:
        approved = data.get("approved", False)
        feedback = data.get("feedback", "")

        await websocket.send_text(
            json.dumps(
                {
                    "type": "approval_received",
                    "approved": approved,
                    "feedback": feedback,
                    "session_id": session_id,
                    "message": "Approval functionality will be implemented in next phase",
                }
            )
        )

    except Exception as e:
        await websocket.send_text(
            json.dumps({"type": "error", "message": str(e), "session_id": session_id})
        )


async def handle_continue_workflow(websocket: WebSocket, session_id: str):
    """Continue workflow after approval (placeholder for future implementation)."""
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "continue_received",
                    "session_id": session_id,
                    "message": "Continue workflow functionality will be implemented in next phase",
                }
            )
        )

    except Exception as e:
        await websocket.send_text(
            json.dumps({"type": "error", "message": str(e), "session_id": session_id})
        )


@router.post("/patient/intake", response_model=IntakeResponseDTO)
async def start_workflow(request: PatientIntakeRequest) -> IntakeResponseDTO:
    """
    HTTP endpoint for synchronous workflow execution.
    """
    try:
        result = await workflow_service.execute_workflow(request.conversation)
        agent_response = ResultMapper.create_agent_response(result, "completed")

        return agent_response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        ) from None
