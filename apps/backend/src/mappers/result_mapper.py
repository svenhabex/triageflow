"""
Result mapper for converting workflow state to appropriate response models based on last_node.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from src.models import AgentResponse, StartIntakeResult

from .message_mapper import MessageMapper


class NodeResultMapper(ABC):
    """Abstract base class for node-specific result mappers."""

    @abstractmethod
    def map_result(self, state: Dict[str, Any]) -> Any:
        """Map the workflow state to the appropriate result format."""
        pass


class IntakeNodeMapper(NodeResultMapper):
    """Mapper for intake node results."""

    def map_result(self, state: Dict[str, Any]) -> StartIntakeResult:
        """Map intake node state to StartIntakeResult."""

        # Extract intake-specific data from the state
        # This assumes the intake node stores its results in specific keys
        intake_data = state.get("intake_data", {})

        return StartIntakeResult(
            symptoms=intake_data.get("symptoms", []),
            pain_level=intake_data.get("pain_level", 0),
            chief_complaint=intake_data.get("chief_complaint", ""),
            additional_notes=intake_data.get("additional_notes", ""),
        )


# Example of how to extend for future node types:
#
# class DiagnosisNodeMapper(NodeResultMapper):
#     """Mapper for diagnosis node results."""
#
#     def map_result(self, state: Dict[str, Any]) -> DiagnosisResult:
#         diagnosis_data = state.get("diagnosis_data", {})
#         return DiagnosisResult(
#             primary_diagnosis=diagnosis_data.get("primary_diagnosis", ""),
#             confidence_level=diagnosis_data.get("confidence_level", 0.0),
#             recommendations=diagnosis_data.get("recommendations", [])
#         )


class ResultMapper:
    """Main result mapper that delegates to node-specific mappers."""

    # Registry of node mappers - easily extensible for new node types
    _node_mappers: Dict[str, NodeResultMapper] = {
        "intake": IntakeNodeMapper(),
        # Add more node mappers here as needed:
        # "diagnosis": DiagnosisNodeMapper(),
        # "treatment": TreatmentNodeMapper(),
    }

    @classmethod
    def register_node_mapper(cls, node_name: str, mapper: NodeResultMapper) -> None:
        """Register a new node mapper for extensibility."""
        cls._node_mappers[node_name] = mapper

    @classmethod
    def create_agent_response(
        cls, state: Dict[str, Any], status: str = "completed"
    ) -> AgentResponse:
        """
        Create an AgentResponse from workflow state based on last_node.

        Args:
            state: The workflow state dictionary
            status: The status of the workflow execution

        Returns:
            AgentResponse with appropriate result type based on last_node
        """

        # Extract common fields
        last_node = state.get("last_node", "unknown")
        messages = MessageMapper.convert_messages_from_state(state)
        errors = state.get("errors", [])

        # Map the result based on the last_node
        result = cls._map_node_result(state, last_node)

        return AgentResponse(
            status=status,
            messages=messages,
            errors=errors,
            last_node=last_node,
            result=result,
        )

    @classmethod
    def _map_node_result(cls, state: Dict[str, Any], last_node: str) -> Any:
        """Map the result based on the last_node type."""

        mapper = cls._node_mappers.get(last_node)
        if mapper:
            return mapper.map_result(state)

        # Default fallback for unknown node types
        return {
            "message": f"No specific mapper found for node type: {last_node}",
            "raw_state": state,
        }
