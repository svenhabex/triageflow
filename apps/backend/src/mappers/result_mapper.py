from abc import ABC, abstractmethod
from typing import Any

from src.models import AgentNameEnum, IntakeResponseDTO, ResponseAgentMessage


class NodeResultMapper(ABC):
    """Abstract base class for node-specific result mappers."""

    @abstractmethod
    def map_result(self, state: dict[str, Any]) -> Any:
        """Map the workflow state to the appropriate result format."""
        pass


class IntakeNodeMapper(NodeResultMapper):
    """Mapper for intake node results."""

    def map_result(self, state: dict[str, Any]) -> IntakeResponseDTO:
        """Map intake node state to IntakeResult."""

        intake_info = state.get("intake_conversation_info")

        if intake_info is None:
            return IntakeResponseDTO(
                symptoms=[],
                pain_level=0,
                chief_complaint="",
                medications=[],
                allergies=[],
                additional_notes="",
            )

        return IntakeResponseDTO(
            symptoms=intake_info.symptoms,
            pain_level=intake_info.pain_level,
            chief_complaint=intake_info.chief_complaint,
            medications=intake_info.medications,
            allergies=intake_info.allergies,
            additional_notes=intake_info.additional_notes,
        )


class ResultMapper:
    """Main result mapper that delegates to node-specific mappers."""

    _node_mappers: dict[str, NodeResultMapper] = {
        "intake": IntakeNodeMapper(),
        # Add more node mappers here as needed:
        # "triage": TriageNodeMapper(),
    }

    @classmethod
    def register_node_mapper(cls, node_name: str, mapper: NodeResultMapper) -> None:
        """Register a new node mapper for extensibility."""
        cls._node_mappers[node_name] = mapper

    @classmethod
    def _map_node_result(cls, state: dict[str, Any], last_node: str) -> Any:
        """Map the result based on the last_node type."""

        mapper = cls._node_mappers.get(last_node)
        if mapper:
            return mapper.map_result(state)

        return {
            "message": f"No specific mapper found for node type: {last_node}",
            "raw_state": state,
        }

    @classmethod
    def create_agent_response(
        cls, state: dict[str, Any], status: str
    ) -> ResponseAgentMessage:
        """Create a ResponseAgentMessage from workflow state."""

        last_node = state.get("last_node", "unknown")

        result_data = cls._map_node_result(state, last_node)

        agent_name = AgentNameEnum.INTAKE

        return ResponseAgentMessage(name=agent_name, data=result_data)
