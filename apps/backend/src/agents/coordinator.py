import os
from pathlib import Path

import pandas as pd
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph

from src.core.llm_monitor import track_llm_request
from src.models import StaffMember
from src.state import CoordinatorAgentState

COORDINATE_STAFF_ASSIGNMENT_NODE = "coordinate_staff_assignment"
TOOLS_NODE = "tools"

# Tool names
GET_STAFF_MEMBER_TOOL_NAME = "get_staff_member"


def _get_model():
    """Get the ChatGoogleGenerativeAI model, initialized lazily."""

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=1.0,
        max_retries=1,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


def _create_staff_member_from_row(row) -> StaffMember:
    """Create a StaffMember object from a pandas DataFrame row."""
    return StaffMember(
        id=row["ID"],
        first_name=row["firstName"],
        last_name=row["lastName"],
        role=row["role"],
        speciality=row["speciality"],
        status=row["status"],
    )


@tool
def get_staff_member(query: str = "") -> list[StaffMember]:
    """
    Retrieves staff members from the hospital database.

    This tool can be used to find staff members by name, role, speciality, or status.
    If no query is provided, returns all available staff members.
    The results are ordered by speciality match priority (exact speciality matches
    first, then partial speciality matches, then other matches), with available staff
    prioritized within each category.

    Args:
        query: Optional query to search for specific staff members by name, role,
               speciality, or status

    Returns:
        List of StaffMember objects matching the query or all staff if no query provided
    """

    csv_path = Path(__file__).parent.parent.parent / "data" / "staff.csv"

    try:
        data = pd.read_csv(csv_path)

        if data.empty:
            raise ValueError("Staff database is empty")

        if not query or not query.strip():
            data_sorted = data.sort_values(
                by=["status", "role"],
                key=lambda x: x.map({"available": 0, "busy": 1})
                if x.name == "status"
                else x,
            )
            return [
                _create_staff_member_from_row(row) for _, row in data_sorted.iterrows()
            ]

        query_lower = query.lower().strip()
        matched_staff = []

        for _, row in data.iterrows():
            staff_data = {
                "id": str(row["ID"]).lower(),
                "first_name": str(row["firstName"]).lower(),
                "last_name": str(row["lastName"]).lower(),
                "full_name": f"{row['firstName']} {row['lastName']}".lower(),
                "role": str(row["role"]).lower(),
                "speciality": str(row["speciality"]).lower(),
                "status": str(row["status"]).lower(),
            }

            if any(query_lower in value for value in staff_data.values()):
                matched_staff.append((row, staff_data))

        if not matched_staff:
            available_staff = data[data["status"].str.lower() == "available"]
            if not available_staff.empty:
                return [
                    _create_staff_member_from_row(row)
                    for _, row in available_staff.iterrows()
                ]
            else:
                return [
                    _create_staff_member_from_row(row) for _, row in data.iterrows()
                ]

        def get_speciality_priority(staff_info):
            row, staff_data = staff_info

            if query_lower == staff_data["speciality"]:
                speciality_priority = 0
            elif query_lower in staff_data["speciality"]:
                speciality_priority = 1
            else:
                speciality_priority = 2

            availability_priority = 0 if staff_data["status"] == "available" else 1

            return (speciality_priority, availability_priority)

        matched_staff.sort(key=get_speciality_priority)

        return [_create_staff_member_from_row(row) for row, _ in matched_staff]

    except FileNotFoundError as e:
        raise ValueError(f"Staff database file not found at {csv_path}") from e
    except Exception as e:
        raise ValueError(f"Error searching staff database: {str(e)}") from e


class CoordinatorAgent:
    """
    Coordinator agent that selects appropriate staff members based on
    triage and intake information.
    """

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.tools = [get_staff_member]
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        self._model = None

    @property
    def model(self):
        """Lazily initialize the model when first accessed."""
        if self._model is None:
            model = _get_model()
            self._model = model.bind_tools(self.tools)
        return self._model

    def _build_graph(self) -> StateGraph:
        """Build the coordinator agent graph with local state."""

        workflow = StateGraph(CoordinatorAgentState, output=CoordinatorAgentState)

        workflow.add_node(
            COORDINATE_STAFF_ASSIGNMENT_NODE, self._coordinate_staff_assignment
        )
        workflow.add_node(TOOLS_NODE, self._execute_tools)

        workflow.set_entry_point(COORDINATE_STAFF_ASSIGNMENT_NODE)
        workflow.add_conditional_edges(
            COORDINATE_STAFF_ASSIGNMENT_NODE,
            self._should_continue,
        )
        workflow.add_edge(TOOLS_NODE, COORDINATE_STAFF_ASSIGNMENT_NODE)

        return workflow

    def _should_continue(self, state: CoordinatorAgentState) -> str:
        """Determine whether to continue with tool calling or end."""
        from langgraph.graph import END

        messages = state.get("messages", [])

        if not messages:
            return END

        last_message = messages[-1]

        # Check for tool calls
        has_tool_calls = hasattr(last_message, "tool_calls") and last_message.tool_calls
        if has_tool_calls:
            return TOOLS_NODE

        # Check max iterations only after tool execution is complete
        retry_count = state.get("retry_count", 0)
        coordination_count = len(
            [
                msg
                for msg in messages
                if hasattr(msg, "content") and "get_staff_member" in str(msg)
            ]
        )

        # If we've made multiple coordination attempts without tool calls, increment retry count
        if coordination_count >= self.max_iterations:
            # Update state to increment retry count for future checks
            state["retry_count"] = retry_count + 1
            return END

        if retry_count >= self.max_iterations:
            return END

        return END

    async def _execute_tools(
        self, state: CoordinatorAgentState
    ) -> CoordinatorAgentState:
        """Execute tools and update state with results."""
        from langchain_core.messages import ToolMessage

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

                if tool_name == GET_STAFF_MEMBER_TOOL_NAME and isinstance(result, list):
                    # Accumulate and prioritize available staff
                    current_staff = updated_state.get("available_staff", [])

                    # Add new staff to the list, avoiding duplicates
                    all_staff = current_staff.copy()
                    added_count = 0
                    for new_staff in result:
                        # Check if staff member already exists (by ID)
                        if not any(
                            existing.id == new_staff.id for existing in all_staff
                        ):
                            all_staff.append(new_staff)
                            added_count += 1

                    # Sort by availability first, then by specialty match
                    def staff_priority(staff):
                        availability_score = 0 if staff.status == "available" else 1
                        return availability_score

                    all_staff.sort(key=staff_priority)
                    updated_state["available_staff"] = all_staff

                    available_count = len(
                        [s for s in all_staff if s.status == "available"]
                    )

                    # Create a readable tool message for the LLM
                    if result:
                        available_count = len(
                            [s for s in result if s.status == "available"]
                        )
                        tool_response = f"Found {len(result)} staff member(s) ({available_count} available):\n"
                        for i, staff in enumerate(result[:5], 1):  # Show first 5
                            status_indicator = (
                                "✅" if staff.status == "available" else "❌"
                            )
                            tool_response += (
                                f"{i}. {status_indicator} {staff.first_name} {staff.last_name} "
                                f"({staff.role}, {staff.speciality}) - {staff.status}\n"
                            )
                        if len(result) > 5:
                            tool_response += f"... and {len(result) - 5} more"

                        # Add summary of cumulative results
                        total_available = len(
                            [s for s in all_staff if s.status == "available"]
                        )
                        tool_response += f"\nTotal staff in database: {len(all_staff)} ({total_available} available)"
                    else:
                        tool_response = "No staff members found matching the criteria"
                else:
                    tool_response = str(result)

                tool_message = ToolMessage(
                    content=tool_response, tool_call_id=tool_id, name=tool_name
                )
                tool_messages.append(tool_message)

            except Exception as e:
                error_message = ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_id,
                    name=tool_name,
                )
                tool_messages.append(error_message)

        # Update messages with tool responses
        updated_state["messages"] = messages + tool_messages

        return updated_state

    @track_llm_request("coordinator", "_coordinate_staff_assignment", "tool_calling")
    async def _coordinate_staff_assignment(
        self, state: CoordinatorAgentState
    ) -> CoordinatorAgentState:
        """
        Coordinate staff assignment based on triage and intake information.
        Uses structured JSON context instead of full message history.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        from .utils import build_context_from_state, format_context_as_json

        # Define what context this agent needs
        required_context = [
            "patient_info",
            "intake_conversation_info",
            "triage_info",
        ]
        context_data = build_context_from_state(state, required_context)

        system_message = SystemMessage(
            content=f"""You are a medical staff coordinator with access to the hospital's staff database.

            CRITICAL: You MUST use the {GET_STAFF_MEMBER_TOOL_NAME} tool to find appropriate staff for this patient.

            Your role is to:
            1. Analyze the provided patient data (JSON format) including triage urgency and medical category
            2. Determine the appropriate medical speciality needed for the patient  
            3. ALWAYS call {GET_STAFF_MEMBER_TOOL_NAME} to search for staff with the required medical specialty
            4. If the primary specialty staff are busy, search for alternative specialties:
               - For Neurology cases: also search "Emergency Medicine", "Trauma", "available"
               - For Cardiology cases: also search "Emergency Medicine", "Internal Medicine", "available"
               - For any case: search "available" to find all available staff

            MANDATORY TOOL USAGE:
            - First: Search for staff matching the exact medical category from triage
            - Then: Search for "available" staff if no available specialists found
            - Always use the {GET_STAFF_MEMBER_TOOL_NAME} tool - never return without searching

            The patient data will be provided in JSON format. You must find appropriate medical staff for this patient."""
        )

        context_message = HumanMessage(
            content=f"""URGENT: Find medical staff for this patient immediately using the get_staff_member tool.

Patient data:
{format_context_as_json(context_data)}

REQUIRED ACTIONS:
1. Use get_staff_member tool to search for "{context_data.get("triage_info", {}).get("medical_category", "General")}" specialists
2. If no available specialists found, search for "available" staff
3. Continue searching until you find appropriate available medical staff

Start by calling the get_staff_member tool now."""
        )

        coordinator_messages = [system_message, context_message]

        try:
            response = await self.model.ainvoke(coordinator_messages)

            full_messages = state.get("messages", [])
            updated_messages = full_messages + coordinator_messages + [response]

            final_output = {
                **state,
                "messages": updated_messages,
                "available_staff": state.get("available_staff", []),
            }

            return final_output

        except Exception as e:
            # Only increment retry_count on actual errors
            error_output = {
                **state,
                "errors": state.get("errors", [])
                + [f"Error in coordination: {str(e)}"],
                "retry_count": state.get("retry_count", 0) + 1,
                "available_staff": state.get("available_staff", []),
            }

            return error_output

    async def run(self, state: CoordinatorAgentState) -> CoordinatorAgentState:
        """Run the coordinator agent."""
        result = await self.app.ainvoke(state)

        return result
