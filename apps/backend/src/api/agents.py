"""
API endpoints for the multi-agent triage system.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..graphs.main_graph import triage_workflow
from ..graphs.state import PatientInfo
from ..graphs.workflows.patient_workflow import create_patient_workflow

router = APIRouter()


class PatientIntakeRequest(BaseModel):
    """Request model for patient intake."""

    patient_info: PatientInfo
    symptoms: list[str]
    medical_history: list[str] = []
    current_medications: list[str] = []


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    status: str
    result: dict[str, Any]
    thread_id: str


@router.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(request: PatientIntakeRequest) -> WorkflowResponse:
    """
    Start a new triage workflow for a patient.
    """
    try:
        # Prepare initial state
        initial_state = {
            "patient_info": request.patient_info.model_dump(),
            "workflow_step": "init",
            "context": {
                "symptoms": request.symptoms,
                "medical_history": request.medical_history,
                "current_medications": request.current_medications,
            },
        }

        # Generate thread ID based on patient ID
        thread_id = f"patient_{request.patient_info.patient_id}"

        # Run the workflow
        result = await triage_workflow.run(initial_state, thread_id)

        return WorkflowResponse(status="completed", result=result, thread_id=thread_id)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/workflow/specialized", response_model=WorkflowResponse)
async def start_specialized_workflow(
    request: PatientIntakeRequest, patient_conditions: list[str] = []
) -> WorkflowResponse:
    """
    Start a specialized workflow for patients with specific conditions.
    """
    try:
        # Create patient-specific workflow
        specialized_workflow = create_patient_workflow(patient_conditions)

        # Prepare initial state
        initial_state = {
            "patient_info": request.patient_info.model_dump(),
            "workflow_step": "init",
            "context": {
                "symptoms": request.symptoms,
                "medical_history": request.medical_history,
                "current_medications": request.current_medications,
                "patient_conditions": patient_conditions,
            },
        }

        # Generate thread ID
        thread_id = f"specialized_{request.patient_info.patient_id}"

        # Run the specialized workflow
        result = await specialized_workflow.run(initial_state, thread_id)

        return WorkflowResponse(status="completed", result=result, thread_id=thread_id)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Specialized workflow execution failed: {str(e)}"
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


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "triage-workflow"}
