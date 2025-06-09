"""
Patient-specific workflow that extends the main graph with additional logic.
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from ..main_graph import TriageWorkflow
from ..state import WorkflowState


class PatientSpecificWorkflow(TriageWorkflow):
    """
    Extended workflow for patients with specific conditions or requirements.
    """

    def __init__(self, patient_conditions: list[str] = None):
        self.patient_conditions = patient_conditions or []
        super().__init__()

    def _build_graph(self) -> StateGraph:
        """Build an extended graph with patient-specific nodes."""
        workflow = StateGraph(WorkflowState)

        # Add all standard nodes
        workflow.add_node("intake", self._intake_node)
        workflow.add_node("triage", self._triage_node)
        workflow.add_node("coordinator", self._enhanced_coordinator_node)

        # Add patient-specific nodes
        workflow.add_node("specialist_referral", self._specialist_referral_node)
        workflow.add_node("emergency_protocol", self._emergency_protocol_node)

        # Define enhanced workflow
        workflow.add_edge(START, "coordinator")
        workflow.add_conditional_edges(
            "coordinator",
            self._enhanced_route_next_step,
            {
                "intake": "intake",
                "triage": "triage",
                "specialist_referral": "specialist_referral",
                "emergency_protocol": "emergency_protocol",
                "end": END,
            },
        )

        # Connect all nodes back to coordinator for decision making
        workflow.add_edge("intake", "coordinator")
        workflow.add_edge("triage", "coordinator")
        workflow.add_edge("specialist_referral", "coordinator")
        workflow.add_edge("emergency_protocol", "coordinator")

        return workflow

    async def _enhanced_coordinator_node(self, state: WorkflowState) -> dict[str, Any]:
        """Enhanced coordinator with patient-specific logic."""
        current_step = state.get("workflow_step", "init")
        patient_info = state.get("patient_info")

        # Standard workflow logic
        if current_step == "init":
            return {"next_agent": "intake", "workflow_step": "intake_pending"}
        elif current_step == "intake_complete":
            # Check for emergency conditions
            if self._requires_emergency_protocol(state):
                return {
                    "next_agent": "emergency_protocol",
                    "workflow_step": "emergency_pending",
                }
            return {"next_agent": "triage", "workflow_step": "triage_pending"}
        elif current_step == "triage_complete":
            # Check for specialist referral needs
            if self._requires_specialist_referral(state):
                return {
                    "next_agent": "specialist_referral",
                    "workflow_step": "referral_pending",
                }
            return {"next_agent": "end", "workflow_step": "complete"}
        elif current_step in ["emergency_complete", "referral_complete"]:
            return {"next_agent": "end", "workflow_step": "complete"}
        else:
            return {"next_agent": "end", "workflow_step": "error"}

    def _enhanced_route_next_step(self, state: WorkflowState) -> str:
        """Enhanced routing with additional options."""
        next_agent = state.get("next_agent", "end")
        return next_agent

    async def _specialist_referral_node(self, state: WorkflowState) -> dict[str, Any]:
        """Handle specialist referral logic."""
        triage_decision = state.get("triage_decision", {})
        patient_info = state.get("patient_info", {})

        # Determine appropriate specialist based on conditions
        specialist_type = self._determine_specialist_type(patient_info, triage_decision)

        return {
            "specialist_referral": {
                "specialist_type": specialist_type,
                "urgency": triage_decision.get("priority_level", "routine"),
                "referral_notes": f"Patient requires {specialist_type} consultation",
            },
            "workflow_step": "referral_complete",
        }

    async def _emergency_protocol_node(self, state: WorkflowState) -> dict[str, Any]:
        """Handle emergency protocol activation."""
        patient_info = state.get("patient_info", {})

        return {
            "emergency_protocol_activated": True,
            "emergency_actions": [
                "immediate_medical_attention",
                "alert_emergency_team",
                "prepare_emergency_room",
            ],
            "workflow_step": "emergency_complete",
        }

    def _requires_emergency_protocol(self, state: WorkflowState) -> bool:
        """Check if emergency protocol should be activated."""
        intake_data = state.get("intake_data", {})

        # Example emergency indicators
        emergency_symptoms = ["chest_pain", "difficulty_breathing", "severe_bleeding"]
        symptoms = intake_data.get("symptoms", [])

        return any(symptom in emergency_symptoms for symptom in symptoms)

    def _requires_specialist_referral(self, state: WorkflowState) -> bool:
        """Check if specialist referral is needed."""
        triage_decision = state.get("triage_decision", {})
        patient_conditions = self.patient_conditions

        # Check for conditions requiring specialist care
        specialist_conditions = ["diabetes", "heart_disease", "cancer"]

        return triage_decision.get("priority_level") in ["urgent", "emergency"] or any(
            condition in specialist_conditions for condition in patient_conditions
        )

    def _determine_specialist_type(
        self, patient_info: dict[str, Any], triage_decision: dict[str, Any]
    ) -> str:
        """Determine the appropriate specialist type."""
        conditions = self.patient_conditions

        if "heart_disease" in conditions or "chest_pain" in str(patient_info):
            return "cardiologist"
        elif "diabetes" in conditions:
            return "endocrinologist"
        elif "cancer" in conditions:
            return "oncologist"
        else:
            return "general_specialist"


# Factory function for creating patient-specific workflows
def create_patient_workflow(
    patient_conditions: list[str] = None,
) -> PatientSpecificWorkflow:
    """Create a patient-specific workflow instance."""
    return PatientSpecificWorkflow(patient_conditions)
