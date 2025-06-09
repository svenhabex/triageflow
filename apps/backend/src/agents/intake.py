import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from src.state import IntakeConversationInfo, WorkflowState


# Mock database functions (to be replaced with real database calls later)
@tool
def get_patient_details(patient_id: str) -> dict[str, Any]:
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


def _get_model():
    """Get the ChatGoogleGenerativeAI model, initialized lazily."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        temperature=1.0,
        max_retries=1,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


EXTRACT_CONVERSATION_INFO_NODE = "extract_conversation_info"
GET_PATIENT_HISTORY_NODE = "get_patient_history"
VALIDATE_AND_COMPILE_NODE = "validate_and_compile"


class IntakeAgent:
    """
    Intake agent, extracts information from a conversation between a nurse and patient.
    The agent is a LangGraph graph.
    """

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        self._model = None

    @property
    def model(self):
        """Lazily initialize the model when first accessed."""
        if self._model is None:
            self._model = _get_model()
        return self._model

    def _build_graph(self) -> StateGraph:
        """Build the intake agent graph."""

        workflow = StateGraph(WorkflowState)

        workflow.add_node(
            EXTRACT_CONVERSATION_INFO_NODE, self._extract_conversation_info
        )

        workflow.set_entry_point(EXTRACT_CONVERSATION_INFO_NODE)
        workflow.add_edge(EXTRACT_CONVERSATION_INFO_NODE, END)

        return workflow

    async def _extract_conversation_info(self, state: WorkflowState) -> WorkflowState:
        """Extract patient information from the conversation using LLM."""

        # Get the last message which should contain the conversation
        messages = state.get("messages", [])
        if not messages:
            return state

        # Get the last message content
        last_message = messages[-1]
        conversation = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        # Extract information using LLM
        try:
            extracted_info = await self._llm_parse_conversation(conversation)
        except Exception as e:
            return {
                **state,
                "errors": [f"Error extracting conversation info: {str(e)}"],
            }

        return {**state, "intake_conversation_info": extracted_info}

    async def _llm_parse_conversation(self, conversation: str) -> dict[str, Any]:
        """Use LLM to parse conversation and extract patient information."""

        system_prompt = """
            You are a medical intake specialist. 
            Extract key patient information from the conversation.
            The conversation is between a nurse and patient.
            
            Guidelines:
            - Extract symptoms mentioned by the patient
            - Look for pain ratings on a 1-10 scale
            - Summarize the conversation into a single sentence as the chief complaint
            - Extract any additional notes from the conversation
            - Be precise and only include information explicitly mentioned
            - Use null for missing information
            """

        human_prompt = f"""Extract patient information from this conversation:
            {conversation}
            """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        structured_model = self._model.with_structured_output(IntakeConversationInfo)

        response = await structured_model.ainvoke(messages)

        return response

    async def _get_patient_history(self, state: WorkflowState) -> dict[str, Any]:
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

    async def run(self, state: WorkflowState) -> dict[str, Any]:
        """Run the intake agent subgraph."""

        result = await self.app.ainvoke(state)

        return result


intake_agent = IntakeAgent()
