"""
Main orchestration graph for the multi-agent triage workflow system.
"""

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents import intake_agent
from src.state import WorkflowState

INTAKE_NODE = "intake"
TRIAGE_NODE = "triage"
SUPERVISOR_NODE = "supervisor"


class TriageWorkflow:
    """Main workflow orchestrator for the triage system."""

    def __init__(self):
        self.graph = self._build_graph()
        self.memory = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.memory)

    def _build_graph(self) -> StateGraph:
        """Build the main orchestration graph."""

        workflow = StateGraph(WorkflowState)

        workflow.add_node(SUPERVISOR_NODE, self._supervisor_node)
        workflow.add_node(INTAKE_NODE, self._intake_node)
        # workflow.add_node(TRIAGE_NODE, self._triage_node)

        workflow.set_entry_point(SUPERVISOR_NODE)
        workflow.add_conditional_edges(SUPERVISOR_NODE, self._route_next_step)
        workflow.add_edge(INTAKE_NODE, SUPERVISOR_NODE)
        # workflow.add_edge(TRIAGE_NODE, SUPERVISOR_NODE)

        return workflow

    async def _supervisor_node(self, state: WorkflowState) -> dict[str, Any]:
        """Coordinate the workflow and decide next steps."""
        # The supervisor just returns the current state
        # Routing decisions are handled by _route_next_step
        return state

    async def _intake_node(self, state: WorkflowState) -> dict[str, Any]:
        """Execute the intake agent."""

        # Run the intake subgraph
        result = await intake_agent.run(state)

        # Update state with results
        updated_state = {
            "last_node": INTAKE_NODE,
            **result,
        }

        print(f"Updated state: {updated_state}")
        return updated_state

    async def _triage_node(self, state: WorkflowState) -> dict[str, Any]:
        """Execute the triage agent."""
        state["last_node"] = TRIAGE_NODE

        # Here you would call your individual triage agent graph
        triage_result = await self._execute_triage_agent(state)

        return {
            "triage_completed": True,
            "triage_decision": triage_result,
        }

    def _route_next_step(self, state: WorkflowState) -> str:
        """Route to the next step based on the current state."""

        # Check for repeated failures to prevent infinite loops
        errors = state.get("errors", [])
        if len(errors) > 3:
            return END

        # Check if we have intake information or if there are critical errors
        if state.get("intake_conversation_info"):
            return END

        # Check if we're stuck in a loop (intake node was just executed)
        if state.get("last_node") == INTAKE_NODE and not state.get(
            "intake_conversation_info"
        ):
            print("Warning: Intake node completed but no conversation info found")
            return END

        return INTAKE_NODE

    # async def _execute_triage_agent(self, state: WorkflowState) -> dict[str, Any]:
    #     """Execute the triage agent graph."""
    #     # This is where you would integrate with your individual triage agent
    #     # For now, return a placeholder result
    #     return {
    #         "priority_level": "urgent",
    #         "reasoning": "Based on symptoms and medical history",
    #         "recommended_actions": ["immediate_assessment", "order_tests"],
    #         "estimated_wait_time": 15,
    #     }

    async def run(
        self, initial_state: dict[str, Any], thread_id: str = "default"
    ) -> dict[str, Any]:
        """Run the complete workflow."""
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.app.ainvoke(initial_state, config=config)

        return result


triage_workflow = TriageWorkflow()
