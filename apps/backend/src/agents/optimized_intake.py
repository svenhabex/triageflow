"""
Optimized Intake Agent - Reduces LLM requests by combining operations.
"""

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


COMBINED_INTAKE_NODE = "combined_intake"
TOOLS_NODE = "tools"


class OptimizedIntakeAgent:
    """
    Optimized Intake agent - combines conversation parsing and tool coordination
    into a single LLM request to reduce total API calls.

    OPTIMIZATION: Instead of 2 separate LLM calls:
    1. Parse conversation → structured output
    2. Analyze + tool calling

    We now do 1 combined call:
    1. Parse conversation + analyze + tool calling in single request
    """

    def __init__(self, max_iterations: int = 3):  # Reduced max iterations
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
        """Build the optimized intake agent graph."""

        workflow = StateGraph(IntakeAgentState, output=IntakeAgentState)

        workflow.add_node(COMBINED_INTAKE_NODE, self._combined_intake_processing)
        workflow.add_node(TOOLS_NODE, self._execute_tools)

        workflow.set_entry_point(COMBINED_INTAKE_NODE)
        workflow.add_conditional_edges(
            COMBINED_INTAKE_NODE,
            self._should_continue,
        )
        workflow.add_edge(TOOLS_NODE, COMBINED_INTAKE_NODE)

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

        # Check if we already have intake_conversation_info, indicating completion
        if state.get("intake_conversation_info") is not None:
            return END

        return END

    async def _execute_tools(self, state: IntakeAgentState) -> IntakeAgentState:
        """Execute tools and update state with results."""
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

    @track_llm_request(
        "optimized_intake", "_combined_intake_processing", "structured_with_tools"
    )
    async def _combined_intake_processing(
        self, state: IntakeAgentState
    ) -> IntakeAgentState:
        """
        OPTIMIZATION: Single LLM call that both parses conversation AND decides on tool usage.
        This reduces the 2 separate LLM calls in the original intake agent to just 1.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        retry_count = state.get("retry_count", 0) + 1

        # Get the conversation from messages
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

        # If we haven't extracted conversation info yet, do structured extraction first
        if not state.get("intake_conversation_info"):
            try:
                extracted_info = (
                    await self._extract_conversation_with_structured_output(
                        conversation
                    )
                )
                state = {**state, "intake_conversation_info": extracted_info}
            except Exception as e:
                return {
                    **state,
                    "errors": state.get("errors", [])
                    + [f"Error extracting conversation info: {str(e)}"],
                    "retry_count": retry_count,
                }

        # Now handle tool calling for patient information
        system_message = SystemMessage(
            content="""You are a medical intake coordinator with access to the hospital's patient database.

            Your role is to:
            1. Analyze the conversation between nurse and patient
            2. Determine if additional patient information is needed for complete intake
            3. Use available tools when medically appropriate for patient safety

            MEDICAL SAFETY GUIDELINES:
            - Always check patient database when a patient name is mentioned
            - Compare conversation info with existing medical records
            - Look for medication conflicts, allergy discrepancies, or missing critical information
            - Ensure complete intake documentation for patient safety

            AVAILABLE TOOLS:
            - get_patient_medical_record: Access complete patient medical history, medications, and allergies

            Extract patient names from the conversation and retrieve their medical records when mentioned."""
        )

        context_message = HumanMessage(
            content=f"""Please analyze this conversation and determine if additional patient information is needed:
            {conversation}
            
            If a patient name is mentioned, please use the get_patient_medical_record tool to retrieve their complete medical history for safety verification."""
        )

        combined_messages = [system_message, context_message]

        try:
            response = await self.model.ainvoke(combined_messages)

            full_messages = state.get("messages", [])
            updated_messages = full_messages + combined_messages + [response]

            return {
                **state,
                "messages": updated_messages,
                "retry_count": retry_count,
            }

        except Exception as e:
            return {
                **state,
                "errors": state.get("errors", [])
                + [f"Error in combined intake processing: {str(e)}"],
                "retry_count": retry_count,
            }

    async def _extract_conversation_with_structured_output(
        self, conversation: str
    ) -> IntakeConversationInfo:
        """Extract conversation information using structured output."""

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

    async def run(self, state: IntakeAgentState) -> IntakeAgentState:
        """Run the optimized intake agent subgraph."""
        result = await self.app.ainvoke(state)
        return result
