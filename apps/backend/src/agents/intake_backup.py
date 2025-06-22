import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.state import IntakeConversationInfo, PatientInfo, WorkflowState

load_dotenv()


def _get_model():
    """Get the ChatGoogleGenerativeAI model, initialized lazily."""

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        temperature=1.0,
        max_retries=1,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


EXTRACT_CONVERSATION_INFO_NODE = "extract_conversation_info"
ANALYZE_AND_GATHER_INFO_NODE = "analyze_and_gather_info"
TOOLS_NODE = "tools"


@tool
def get_patient_info(patient_id: str = "1") -> PatientInfo:
    """
    Retrieve patient information from the CSV database.
    Including first name, last name, date of birth, medical history,
    and medications.

    Args:
        patient_id: The ID of the patient to retrieve information for
    """

    # Get the path to the CSV file
    csv_path = Path(__file__).parent.parent.parent / "data" / "patients.csv"

    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)

        # Find the patient by ID
        patient_row = df[df["id"] == int(patient_id)]

        if patient_row.empty:
            raise ValueError(f"Patient with ID {patient_id} not found")

        # get the first row
        patient_data = patient_row.iloc[0]

        medical_history = (
            [patient_data["medical_history"]]
            if pd.notna(patient_data["medical_history"])
            else []
        )

        medications = (
            [patient_data["medication"]]
            if pd.notna(patient_data["medication"])
            and patient_data["medication"] != "None"
            else ["None"]
        )

        patient_info = PatientInfo(
            patient_id=str(patient_data["id"]),
            first_name=patient_data["firstname"],
            last_name=patient_data["lastname"],
            date_of_birth=patient_data["date_of_birth"],
            medical_history=medical_history,
            medications=medications,
        )

        return patient_info

    except FileNotFoundError:
        raise ValueError(f"Patient database file not found at {csv_path}")
    except Exception as e:
        raise ValueError(f"Error retrieving patient information: {str(e)}")


class IntakeAgent:
    """
    Intake agent, extracts information from a conversation between a nurse and patient.
    The agent is a LangGraph graph with tool calling capabilities.
    """

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.tools = [get_patient_info]
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        self._model = None

    @property
    def model(self):
        """Lazily initialize the model when first accessed."""
        if self._model is None:
            model = _get_model()
            # Bind tools to the model for tool calling
            self._model = model.bind_tools(self.tools)
        return self._model

    def _build_graph(self) -> StateGraph:
        """Build the intake agent graph with tool calling capabilities."""

        workflow = StateGraph(WorkflowState)

        workflow.add_node(
            EXTRACT_CONVERSATION_INFO_NODE, self._extract_conversation_info
        )
        workflow.add_node(ANALYZE_AND_GATHER_INFO_NODE, self._analyze_and_gather_info)

        tool_node = ToolNode(self.tools)
        workflow.add_node(TOOLS_NODE, tool_node)

        workflow.set_entry_point(EXTRACT_CONVERSATION_INFO_NODE)
        workflow.add_edge(EXTRACT_CONVERSATION_INFO_NODE, ANALYZE_AND_GATHER_INFO_NODE)
        workflow.add_conditional_edges(
            ANALYZE_AND_GATHER_INFO_NODE,
            self._should_continue,
        )
        workflow.add_edge(TOOLS_NODE, ANALYZE_AND_GATHER_INFO_NODE)

        return workflow

    def _should_continue(self, state: WorkflowState) -> str:
        """Determine whether to continue with tool calling or end."""
        messages = state.get("messages", [])

        if not messages:
            return END

        last_message = messages[-1]

        retry_count = state.get("retry_count", 0)
        if retry_count >= self.max_iterations:
            return END

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return TOOLS_NODE

        return END

    async def _extract_conversation_info(self, state: WorkflowState) -> WorkflowState:
        """Extract patient information from the conversation using LLM."""

        # Get the last message which should contain the conversation
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1]
        conversation = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        try:
            extracted_info = await self._llm_parse_conversation(conversation)
        except Exception as e:
            return {
                **state,
                "errors": [f"Error extracting conversation info: {str(e)}"],
            }

        return {**state, "intake_conversation_info": extracted_info}

    async def _llm_parse_conversation(
        self, conversation: str
    ) -> IntakeConversationInfo:
        """Use LLM to parse conversation and extract patient information."""

        system_prompt = """
            You are a medical intake specialist. 
            Extract key patient information from the conversation.
            The conversation is between a nurse and patient.
            
            Guidelines:
            - Extract symptoms mentioned by the patient
            - Look for pain ratings on a 1-10 scale
            - Look for medications mentioned by the patient
            - Look for allergies mentioned by the patient
            - Summarize the conversation as the chief complaint
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

        base_model = _get_model()
        structured_model = base_model.with_structured_output(IntakeConversationInfo)

        response = await structured_model.ainvoke(messages)

        return response

    async def _analyze_and_gather_info(self, state: WorkflowState) -> WorkflowState:
        """
        Analyzes intake conversation and coordinates gathering of additional
        patient information using available tools as needed.
        """
        messages = state.get("messages", [])
        retry_count = state.get("retry_count", 0)

        # Increment retry count
        retry_count += 1

        # Create a system message to guide the LLM's analysis and information gathering
        system_message = SystemMessage(
            content="""You are a medical intake information coordinator. 

            IMPORTANT: For every patient intake, you MUST retrieve the patient's complete medical record from the database using the get_patient_info tool.

            Your workflow:
            1. ALWAYS call get_patient_info tool first to retrieve the patient's medical record
            2. Compare the conversation information with the patient's existing medical history
            3. Identify any discrepancies or new information
            4. Provide a comprehensive intake summary that includes both:
               - Information from the conversation 
               - Patient's existing medical history from the database

            The patient database contains critical information like:
            - Complete medical history
            - Current medications
            - Known allergies
            - Previous treatments

            You MUST call get_patient_info to ensure a complete and safe medical intake."""
        )

        # Add system message if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [system_message] + messages

        try:
            response = await self.model.ainvoke(messages)

            # Update messages and state
            updated_messages = messages + [response]

            return {
                **state,
                "messages": updated_messages,
                "retry_count": retry_count,
            }

        except Exception as e:
            return {
                **state,
                "errors": state.get("errors", [])
                + [f"Error in tool calling: {str(e)}"],
                "retry_count": retry_count,
            }

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Run the intake agent subgraph."""

        result = await self.app.ainvoke(state)

        return result


intake_agent = IntakeAgent()
