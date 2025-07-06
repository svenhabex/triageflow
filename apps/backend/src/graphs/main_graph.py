"""
Main orchestration graph for the multi-agent triage workflow system.
"""

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents import coordinator_agent, intake_agent, triage_agent
from src.state import (
    CoordinatorAgentState,
    IntakeAgentState,
    TriageAgentState,
    WorkflowState,
)

INTAKE_NODE = "intake"
TRIAGE_NODE = "triage"
COORDINATOR_NODE = "coordinator"
SUPERVISOR_NODE = "supervisor"


class TriageWorkflow:
    """Main workflow orchestrator for the triage system."""

    def __init__(self):
        self.graph = self._build_graph()
        self.memory = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.memory)

    def _build_graph(self) -> StateGraph:
        """Build the main orchestration graph."""

        workflow = StateGraph(WorkflowState, output=WorkflowState)

        workflow.add_node(SUPERVISOR_NODE, self._supervisor_node)
        workflow.add_node(INTAKE_NODE, self._intake_node)
        workflow.add_node(TRIAGE_NODE, self._triage_node)
        workflow.add_node(COORDINATOR_NODE, self._coordinator_node)

        workflow.set_entry_point(SUPERVISOR_NODE)
        workflow.add_conditional_edges(SUPERVISOR_NODE, self._route_next_step)
        workflow.add_edge(INTAKE_NODE, SUPERVISOR_NODE)
        workflow.add_edge(TRIAGE_NODE, SUPERVISOR_NODE)
        workflow.add_edge(COORDINATOR_NODE, SUPERVISOR_NODE)

        return workflow

    async def _supervisor_node(self, state: WorkflowState) -> WorkflowState:
        """Coordinate the workflow and decide next steps."""

        return state

    def _route_next_step(self, state: WorkflowState) -> str:
        """Route to the next step based on the current state."""

        # Early exit for too many errors
        if len(state.get("errors", [])) > 3:
            return END

        # Initial state - start with intake
        if not state.get("last_node"):
            return INTAKE_NODE

        # After intake: check if we got results
        if state.get("last_node") == INTAKE_NODE:
            if state.get("intake_conversation_info") and state.get("patient_info"):
                return TRIAGE_NODE
            else:
                return END

        # After triage: check if we got results
        if state.get("last_node") == TRIAGE_NODE:
            if state.get("triage_info"):
                return COORDINATOR_NODE
            else:
                return END

        # Fallback: if somehow we don't have intake info yet, try intake
        return INTAKE_NODE if not state.get("intake_conversation_info") else END

    async def _intake_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the intake agent with state mapping."""

        intake_input = IntakeAgentState(messages=state.get("messages", []))

        intake_result = await intake_agent.run(intake_input)

        return {
            **state,  # Preserve existing global state
            "last_node": INTAKE_NODE,
            "messages": intake_result.get("messages", []),
            "patient_info": intake_result.get("patient_info"),
            "intake_conversation_info": intake_result.get("intake_conversation_info"),
            "errors": state.get("errors", []) + intake_result.get("errors", []),
        }

    async def _triage_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the triage agent with state mapping."""

        triage_input = TriageAgentState(
            messages=state.get("messages", []),
            patient_info=state.get("patient_info"),
            intake_conversation_info=state.get("intake_conversation_info"),
        )

        triage_result = await triage_agent.run(triage_input)

        return {
            **state,  # Preserve existing global state
            "last_node": TRIAGE_NODE,
            "messages": triage_result.get("messages", []),
            "triage_info": triage_result.get("triage_info"),
            "errors": state.get("errors", []) + triage_result.get("errors", []),
        }

    async def _coordinator_node(self, state: WorkflowState) -> WorkflowState:
        """Execute the coordinator agent with state mapping."""

        coordinator_input = CoordinatorAgentState(
            messages=state.get("messages", []),
            patient_info=state.get("patient_info"),
            intake_conversation_info=state.get("intake_conversation_info"),
            triage_info=state.get("triage_info"),
        )

        coordinator_result = await coordinator_agent.run(coordinator_input)

        return {
            **state,
            "last_node": COORDINATOR_NODE,
            "messages": coordinator_result.get("messages", []),
            "available_staff": coordinator_result.get("available_staff", []),
            "errors": state.get("errors", []) + coordinator_result.get("errors", []),
        }

    async def run(
        self, initial_state: dict[str, Any], thread_id: str = "default"
    ) -> dict[str, Any]:
        """Run the complete workflow."""
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.app.ainvoke(initial_state, config=config)

        return result


triage_workflow = TriageWorkflow()
