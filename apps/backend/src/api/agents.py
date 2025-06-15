"""
API endpoints for the multi-agent triage system.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.graphs import triage_workflow
from src.mappers import ResultMapper
from src.models import AgentResponse

router = APIRouter()


class PatientIntakeRequest(BaseModel):
    """Request model for patient intake."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation: str


@router.post("/patient/intake", response_model=AgentResponse)
async def start_workflow(request: PatientIntakeRequest) -> AgentResponse:
    """
    Start a new triage workflow for a patient.
    """
    try:
        initial_state = {"messages": [HumanMessage(content=request.conversation)]}

        result = await triage_workflow.run(initial_state)
        agent_response = ResultMapper.create_agent_response(result, "completed")

        return agent_response

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
