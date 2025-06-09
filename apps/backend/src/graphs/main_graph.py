"""
Main orchestration graph for the multi-agent triage workflow system.
"""

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .state import WorkflowState

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

        workflow.add_node(INTAKE_NODE, self._intake_node)
        workflow.add_node(TRIAGE_NODE, self._triage_node)
        workflow.add_node(SUPERVISOR_NODE, self._supervisor_node)

        workflow.set_entry_point(SUPERVISOR_NODE)
        workflow.add_conditional_edges(SUPERVISOR_NODE, self._route_next_step)
        workflow.add_edge(INTAKE_NODE, SUPERVISOR_NODE)
        workflow.add_edge(TRIAGE_NODE, SUPERVISOR_NODE)

        return workflow

    async def _intake_node(self, state: WorkflowState) -> dict[str, Any]:
        """Execute the intake agent."""
        from ..agents.intake import intake_agent

        # Run the intake subgraph
        result = await intake_agent.run(state)

        # Update state with results
        return {
            "last_node": INTAKE_NODE,
            **result,  # This includes intake_completed and intake_data
        }

    async def _triage_node(self, state: WorkflowState) -> dict[str, Any]:
        """Execute the triage agent."""
        state["last_node"] = TRIAGE_NODE

        # Here you would call your individual triage agent graph
        triage_result = await self._execute_triage_agent(state)

        return {
            "triage_completed": True,
            "triage_decision": triage_result,
        }

    async def _supervisor_node(self, state: WorkflowState) -> dict[str, Any]:
        """Coordinate the workflow and decide next steps."""
        # The supervisor just returns the current state
        # Routing decisions are handled by _route_next_step
        return state

    def _route_next_step(self, state: WorkflowState) -> str:
        """Route to the next step based on the current state."""
        # If both intake and triage are completed, we're done
        if state.get("triage_completed"):
            return END

        # If intake is completed, check conditions and route to triage or end
        if state.get("intake_completed"):
            intake_data = state.get("intake_data", {})
            if intake_data.get("emergency_flag"):
                return "emergency_redirect"
            elif intake_data.get("non_medical"):
                return END
            elif intake_data.get("incomplete_info"):
                return "additional_info_required"
            else:
                return TRIAGE_NODE

        # If nothing is completed yet, start with intake
        return INTAKE_NODE

    async def _execute_triage_agent(self, state: WorkflowState) -> dict[str, Any]:
        """Execute the triage agent graph."""
        # This is where you would integrate with your individual triage agent
        # For now, return a placeholder result
        return {
            "priority_level": "urgent",
            "reasoning": "Based on symptoms and medical history",
            "recommended_actions": ["immediate_assessment", "order_tests"],
            "estimated_wait_time": 15,
        }

    async def run(
        self, initial_state: dict[str, Any], thread_id: str = "default"
    ) -> dict[str, Any]:
        """Run the complete workflow."""
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.app.ainvoke(initial_state, config=config)
        return result


triage_workflow = TriageWorkflow()
