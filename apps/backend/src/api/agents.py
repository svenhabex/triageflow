"""
API endpoints for the multi-agent triage system.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.graphs import triage_workflow

router = APIRouter()


class PatientIntakeRequest(BaseModel):
    """Request model for patient intake."""

    conversation: str


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    status: str
    result: dict[str, Any]


@router.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(request: PatientIntakeRequest) -> WorkflowResponse:
    """
    Start a new triage workflow for a patient.
    """
    try:
        initial_state = {"messages": [HumanMessage(content=request.conversation)]}
        result = await triage_workflow.run(initial_state)

        return WorkflowResponse(status="completed", result=result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/workflow/status/{thread_id}")
async def get_workflow_status(thread_id: str) -> dict[str, Any]:
    """
    Get the current status of a workflow by thread ID.
    """
    try:
        # This would typically query the workflow state from the checkpointer
        # For now, return a placeholder response
        return {
            "thread_id": thread_id,
            "status": "running",
            "current_step": "processing",
            "message": "Workflow status retrieval not fully implemented yet",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get workflow status: {str(e)}"
        )
