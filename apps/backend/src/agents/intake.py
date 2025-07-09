import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from src.core.llm_monitor import track_llm_request
from src.models import IntakeConversationInfo, PatientInfo
from src.state import IntakeAgentState

load_dotenv()


def _get_model():
    """Get the ChatGoogleGenerativeAI model, initialized lazily."""

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=1.0,
        max_retries=1,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


EXTRACT_CONVERSATION_INFO_NODE = "extract_conversation_info"
ANALYZE_AND_GATHER_INFO_NODE = "analyze_and_gather_info"
TOOLS_NODE = "tools"


@tool
def get_patient_medical_record(patient_identifier: str = "") -> PatientInfo:
    """
    Retrieves a patient's complete medical record from the hospital database.

    🏥 CRITICAL FOR PATIENT SAFETY: This tool provides access to:
    - Complete medical history and chronic conditions
    - Current medications and dosages
    - Known allergies and adverse reactions
    - Previous treatments and procedures

    The tool can find patients using various identifiers:
    - Full name (e.g., "Tony Stark", "Bruce Wayne")
    - First name only if unique (e.g., "Tony", "Bruce")
    - Patient ID number if known

    Args:
        patient_identifier: Patient name, partial name, or ID mentioned in conversation
    """

    # If no identifier provided, cannot retrieve patient info
    if not patient_identifier or not patient_identifier.strip():
        raise ValueError(
            """Patient identifier is required. 
            Cannot retrieve medical record without patient name or ID."""
        )

    csv_path = Path(__file__).parent.parent.parent / "data" / "patients.csv"

    try:
        df = pd.read_csv(csv_path)

        # If identifier looks like a number, try ID search first
        if patient_identifier.isdigit():
            patient_row = df[df["id"] == int(patient_identifier)]
            if not patient_row.empty:
                return _create_patient_info_from_row(patient_row.iloc[0])

        # Search by name (flexible matching)
        identifier_lower = patient_identifier.lower()

        # Try exact full name match first
        for _, row in df.iterrows():
            full_name = f"{row['firstname']} {row['lastname']}".lower()
            if identifier_lower == full_name:
                return _create_patient_info_from_row(row)

        # Try partial name matching
        for _, row in df.iterrows():
            first_name = row["firstname"].lower()
            last_name = row["lastname"].lower()
            full_name = f"{first_name} {last_name}"

            # Check if identifier matches first name, last name, or in full name
            if (
                identifier_lower == first_name
                or identifier_lower == last_name
                or identifier_lower in full_name
                or any(part in full_name for part in identifier_lower.split())
            ):
                return _create_patient_info_from_row(row)

        raise ValueError(
            f"No patient found matching '{patient_identifier}'. Available patients: {', '.join([f'{row.firstname} {row.lastname}' for _, row in df.iterrows()])}"
        )

    except FileNotFoundError:
        raise ValueError(f"Patient database file not found at {csv_path}")
    except Exception as e:
        raise ValueError(f"Error searching patient database: {str(e)}")


def _create_patient_info_from_row(patient_data) -> PatientInfo:
    """Helper function to create PatientInfo from DataFrame row."""

    medical_history = (
        [
            item.strip()
            for item in patient_data["medical_history"].split(";")
            if item.strip()
        ]
        if pd.notna(patient_data["medical_history"])
        else []
    )

    medications = (
        [item.strip() for item in patient_data["medication"].split(";") if item.strip()]
        if pd.notna(patient_data["medication"]) and patient_data["medication"] != "None"
        else ["None"]
    )

    return PatientInfo(
        patient_id=str(patient_data["id"]),
        first_name=patient_data["firstname"],
        last_name=patient_data["lastname"],
        date_of_birth=patient_data["date_of_birth"],
        medical_history=medical_history,
        medications=medications,
    )


class IntakeAgent:
    """
    Intake agent, extracts information from a conversation between a nurse and patient.
    The agent is a LangGraph graph with tool calling capabilities.
    """

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.tools = [get_patient_medical_record]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
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
        """Build the intake agent graph with local state."""

        workflow = StateGraph(IntakeAgentState, output=IntakeAgentState)

        workflow.add_node(
            EXTRACT_CONVERSATION_INFO_NODE, self._extract_conversation_info
        )
        workflow.add_node(ANALYZE_AND_GATHER_INFO_NODE, self._analyze_and_gather_info)
        workflow.add_node(TOOLS_NODE, self._execute_tools)

        workflow.set_entry_point(EXTRACT_CONVERSATION_INFO_NODE)
        workflow.add_edge(EXTRACT_CONVERSATION_INFO_NODE, ANALYZE_AND_GATHER_INFO_NODE)
        workflow.add_conditional_edges(
            ANALYZE_AND_GATHER_INFO_NODE,
            self._should_continue,
        )
        workflow.add_edge(TOOLS_NODE, ANALYZE_AND_GATHER_INFO_NODE)

        return workflow

    def _should_continue(self, state: IntakeAgentState) -> str:
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

    async def _execute_tools(self, state: IntakeAgentState) -> IntakeAgentState:
        """
        Enhanced tool execution node that:
        1. Executes the tools
        2. Updates the state with structured data (PatientInfo)
        3. Adds tool responses to messages
        4. Handles cases where patient lookup fails
        """
        messages = state.get("messages", [])

        if not messages:
            return state

        last_message = messages[-1]

        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state

        tool_messages = []
        updated_state = dict(state)

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            try:
                tool_func = self.tools_by_name.get(tool_name)
                if not tool_func:
                    raise ValueError(f"Tool {tool_name} not found")

                result = tool_func.invoke(tool_args)

                if tool_name == "get_patient_medical_record" and isinstance(
                    result, PatientInfo
                ):
                    # Update state with structured PatientInfo
                    updated_state["patient_info"] = result

                    # Create a readable tool message
                    tool_response = f"Retrieved patient record for {result.first_name} {result.last_name} (ID: {result.patient_id})\n"
                    tool_response += f"DOB: {result.date_of_birth}\n"
                    tool_response += f"Medical History: {', '.join(result.medical_history) if result.medical_history else 'None'}\n"
                    tool_response += f"Current Medications: {', '.join(result.medications) if result.medications else 'None'}"
                else:
                    tool_response = str(result)

                tool_message = ToolMessage(
                    content=tool_response, tool_call_id=tool_id, name=tool_name
                )
                tool_messages.append(tool_message)

            except Exception as e:
                # Handle tool execution failures
                if tool_name == "get_patient_medical_record":
                    # Ensure patient_info is explicitly set to None when patient lookup fails
                    updated_state["patient_info"] = None

                # Add error message for failed tool calls
                error_message = ToolMessage(
                    content=f"Unable to retrieve patient record: {str(e)}",
                    tool_call_id=tool_id,
                    name=tool_name,
                )
                tool_messages.append(error_message)

        # Update messages with tool responses
        updated_state["messages"] = messages + tool_messages

        return updated_state

    async def _extract_conversation_info(
        self, state: IntakeAgentState
    ) -> IntakeAgentState:
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
                "errors": state.get("errors", [])
                + [f"Error extracting conversation info: {str(e)}"],
            }

        return {**state, "intake_conversation_info": extracted_info}

    @track_llm_request("intake", "_llm_parse_conversation", "structured")
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

    @track_llm_request("intake", "_analyze_and_gather_info", "tool_calling")
    async def _analyze_and_gather_info(
        self, state: IntakeAgentState
    ) -> IntakeAgentState:
        """
        Analyzes intake conversation and coordinates gathering of additional
        patient information using available tools as needed.
        Uses the original conversation text to find patient names for medical record lookup.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        retry_count = state.get("retry_count", 0) + 1

        messages = state.get("messages", [])
        if not messages:
            return {
                **state,
                "errors": state.get("errors", [])
                + ["No conversation found in messages"],
                "retry_count": retry_count,
            }

        conversation = None
        for message in messages:
            if (
                hasattr(message, "content")
                and hasattr(message, "__class__")
                and "HumanMessage" in str(type(message))
            ):
                conversation = message.content
                break

        if not conversation:
            return {
                **state,
                "errors": state.get("errors", []) + ["No conversation content found"],
                "retry_count": retry_count,
            }

        system_message = SystemMessage(
            content="""You are a medical intake information coordinator with access to the hospital's patient database.

            Your role is to:
            1. Analyze the conversation between nurse and patient
            2. Determine if you need additional patient information for a complete intake
            3. Use available tools when medically appropriate for patient safety

            MEDICAL SAFETY GUIDELINES:
            - Always check patient database records when a patient name is mentioned
            - Compare conversation information with existing medical records  
            - Look for medication conflicts, allergy discrepancies, or missing critical information
            - Ensure complete and accurate intake documentation

            AVAILABLE TOOLS:
            - get_patient_medical_record: Access complete patient medical history, medications, and allergies

            Use your medical judgment to determine when database access is necessary for safe patient care.
            Extract the patient's name from the conversation and search their medical record if mentioned."""
        )

        context_message = HumanMessage(
            content=f"""Please analyze the following conversation between nurse and patient and determine if additional patient information is needed:
            {conversation}
            If a patient name is mentioned in the conversation, please use the get_patient_medical_record tool to retrieve their complete medical history."""
        )

        intake_messages = [system_message, context_message]

        try:
            response = await self.model.ainvoke(intake_messages)

            full_messages = state.get("messages", [])
            updated_messages = full_messages + intake_messages + [response]

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

    async def run(self, state: IntakeAgentState) -> IntakeAgentState:
        """Run the intake agent subgraph."""

        result = await self.app.ainvoke(state)

        return result
