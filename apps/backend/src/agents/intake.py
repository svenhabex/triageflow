"""
Intake Agent Subgraph

This agent receives a conversation between a patient and a nurse, along with a patient ID.
It extracts patient information from the conversation and retrieves patient history.

It extracts the following information:
- Patient name
- Patient age
- Patient gender
- Patient symptoms
- Patient medical history
- Patient vital signs
- Patient allergies
- Patient medications
"""

import re
from datetime import datetime
from typing import Any, Dict, List

from langchain_core.tools import tool
from langgraph.graph import END, StateGraph

from ..graphs.state import WorkflowState


# Mock database functions (to be replaced with real database calls later)
@tool
def get_patient_details(patient_id: str) -> Dict[str, Any]:
    """
    Mock function to get patient details from database.
    Later this will be replaced with actual database calls.
    """
    # Mock patient database
    mock_patients = {
        "P001": {
            "name": "John Doe",
            "age": 45,
            "gender": "Male",
            "medical_history": ["Hypertension", "Type 2 Diabetes"],
            "allergies": ["Penicillin", "Nuts"],
            "current_medications": ["Metformin", "Lisinopril"],
            "emergency_contact": "Jane Doe - 555-0123",
        },
        "P002": {
            "name": "Sarah Smith",
            "age": 32,
            "gender": "Female",
            "medical_history": ["Asthma"],
            "allergies": ["Latex"],
            "current_medications": ["Albuterol inhaler"],
            "emergency_contact": "Mike Smith - 555-0456",
        },
        "P003": {
            "name": "Robert Johnson",
            "age": 67,
            "gender": "Male",
            "medical_history": ["Heart Disease", "Arthritis"],
            "allergies": ["Aspirin"],
            "current_medications": ["Metoprolol", "Ibuprofen"],
            "emergency_contact": "Mary Johnson - 555-0789",
        },
    }

    return mock_patients.get(
        patient_id,
        {
            "name": "Unknown Patient",
            "age": None,
            "gender": "Unknown",
            "medical_history": [],
            "allergies": [],
            "current_medications": [],
            "emergency_contact": "Not provided",
        },
    )


class IntakeAgent:
    """Intake agent implemented as a LangGraph subgraph."""

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        """Build the intake agent subgraph."""

        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("extract_conversation_info", self._extract_conversation_info)
        workflow.add_node("get_patient_history", self._get_patient_history)
        workflow.add_node("validate_and_compile", self._validate_and_compile)

        # Set entry point and edges
        workflow.set_entry_point("extract_conversation_info")
        workflow.add_edge("extract_conversation_info", "get_patient_history")
        workflow.add_edge("get_patient_history", "validate_and_compile")
        workflow.add_edge("validate_and_compile", END)

        return workflow

    async def _extract_conversation_info(self, state: WorkflowState) -> Dict[str, Any]:
        """Extract patient information from the conversation."""

        # Get the last message which should contain the conversation
        messages = state.get("messages", [])
        if not messages:
            return {
                "errors": state.get("errors", [])
                + ["No conversation found in messages"],
                "extracted_info": {},
            }

        # Get the last message content
        last_message = messages[-1]
        conversation = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        # Extract information using pattern matching (simplified approach)
        extracted_info = self._parse_conversation(conversation)

        return {"extracted_info": extracted_info, "conversation_analyzed": True}

    async def _get_patient_history(self, state: WorkflowState) -> Dict[str, Any]:
        """Retrieve patient history from the database."""

        patient_id = None

        # Try to get patient_id from state
        if state.get("patient_info") and hasattr(state["patient_info"], "patient_id"):
            patient_id = state["patient_info"].patient_id
        elif isinstance(state.get("patient_info"), dict):
            patient_id = state["patient_info"].get("patient_id")
        elif state.get("context", {}).get("patient_id"):
            patient_id = state["context"]["patient_id"]

        if not patient_id:
            return {
                "errors": state.get("errors", []) + ["No patient ID found in state"],
                "patient_details": {},
            }

        # Get patient details using mock function
        patient_details = get_patient_details(patient_id)

        return {"patient_details": patient_details, "patient_history_retrieved": True}

    async def _validate_and_compile(self, state: WorkflowState) -> Dict[str, Any]:
        """Validate extracted information and compile final intake data."""

        extracted_info = state.get("extracted_info", {})
        patient_details = state.get("patient_details", {})

        # Merge extracted info with patient details
        compiled_data = {
            "patient_id": patient_details.get("patient_id", "unknown"),
            "name": extracted_info.get("name")
            or patient_details.get("name", "Unknown"),
            "age": extracted_info.get("age") or patient_details.get("age"),
            "gender": extracted_info.get("gender") or patient_details.get("gender"),
            "current_symptoms": extracted_info.get("symptoms", []),
            "reported_pain_level": extracted_info.get("pain_level"),
            "chief_complaint": extracted_info.get("chief_complaint"),
            "medical_history": patient_details.get("medical_history", []),
            "allergies": patient_details.get("allergies", []),
            "current_medications": patient_details.get("current_medications", []),
            "vital_signs": extracted_info.get("vital_signs", {}),
            "emergency_contact": patient_details.get("emergency_contact"),
            "timestamp": datetime.now().isoformat(),
        }

        # Check for emergency flags
        emergency_keywords = [
            "chest pain",
            "difficulty breathing",
            "severe pain",
            "unconscious",
            "bleeding heavily",
        ]
        emergency_flag = any(
            keyword in str(extracted_info.get("symptoms", [])).lower()
            for keyword in emergency_keywords
        )

        # Check if information is incomplete
        required_fields = ["current_symptoms", "chief_complaint"]
        incomplete_info = any(not compiled_data.get(field) for field in required_fields)

        return {
            "intake_completed": True,
            "intake_data": {
                **compiled_data,
                "emergency_flag": emergency_flag,
                "incomplete_info": incomplete_info,
                "confidence_score": self._calculate_confidence_score(compiled_data),
                "next_steps": self._determine_next_steps(
                    compiled_data, emergency_flag, incomplete_info
                ),
            },
        }

    def _parse_conversation(self, conversation: str) -> Dict[str, Any]:
        """Parse conversation text to extract patient information."""

        extracted_info = {}
        conversation_lower = conversation.lower()

        # Extract symptoms
        symptoms = []
        symptom_keywords = [
            "pain",
            "headache",
            "fever",
            "nausea",
            "dizziness",
            "cough",
            "fatigue",
        ]
        for keyword in symptom_keywords:
            if keyword in conversation_lower:
                symptoms.append(keyword)

        # Extract pain level (1-10 scale)
        pain_match = re.search(
            r"pain.*?(\d+)(?:\s*(?:out of|/)\s*10)?", conversation_lower
        )
        pain_level = int(pain_match.group(1)) if pain_match else None

        # Extract age
        age_match = re.search(
            r"(?:age|years old|year old).*?(\d+)|(\d+).*?(?:years old|year old)",
            conversation_lower,
        )
        age = int(age_match.group(1) or age_match.group(2)) if age_match else None

        # Extract name (simple pattern)
        name_match = re.search(
            r"(?:my name is|i am|i\'m)\s+([a-zA-Z\s]+)", conversation_lower
        )
        name = name_match.group(1).strip().title() if name_match else None

        # Extract chief complaint (first sentence often contains it)
        sentences = conversation.split(".")
        chief_complaint = sentences[0].strip() if sentences else None

        # Extract vital signs if mentioned
        vital_signs = {}
        bp_match = re.search(r"blood pressure.*?(\d+)/(\d+)", conversation_lower)
        if bp_match:
            vital_signs["blood_pressure"] = f"{bp_match.group(1)}/{bp_match.group(2)}"

        temp_match = re.search(r"temperature.*?(\d+\.?\d*)", conversation_lower)
        if temp_match:
            vital_signs["temperature"] = float(temp_match.group(1))

        extracted_info.update(
            {
                "symptoms": symptoms,
                "pain_level": pain_level,
                "age": age,
                "name": name,
                "chief_complaint": chief_complaint,
                "vital_signs": vital_signs,
            }
        )

        return extracted_info

    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on completeness of data."""

        required_fields = ["current_symptoms", "chief_complaint"]
        optional_fields = ["name", "age", "pain_level", "vital_signs"]

        required_score = sum(1 for field in required_fields if data.get(field))
        optional_score = sum(0.5 for field in optional_fields if data.get(field))

        max_score = len(required_fields) + len(optional_fields) * 0.5
        total_score = required_score + optional_score

        return min(total_score / max_score, 1.0)

    def _determine_next_steps(
        self, data: Dict[str, Any], emergency_flag: bool, incomplete_info: bool
    ) -> List[str]:
        """Determine recommended next steps based on intake data."""

        next_steps = []

        if emergency_flag:
            next_steps.append("immediate_medical_attention")
            next_steps.append("notify_emergency_team")
        elif incomplete_info:
            next_steps.append("collect_additional_information")
        else:
            next_steps.append("proceed_to_triage")

        if data.get("vital_signs"):
            next_steps.append("review_vital_signs")

        if data.get("current_medications"):
            next_steps.append("check_medication_interactions")

        return next_steps

    async def run(self, state: WorkflowState) -> Dict[str, Any]:
        """Run the intake agent subgraph."""

        result = await self.app.ainvoke(state)
        return result


# Create singleton instance
intake_agent = IntakeAgent()
