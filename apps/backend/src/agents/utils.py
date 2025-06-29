"""
Utility functions for agents in the triage workflow system.
"""

import json
from typing import Any

from src.state import WorkflowState


def build_context_from_state(
    state: WorkflowState, include_fields: list[str]
) -> dict[str, Any]:
    """
    Build context dictionary from workflow state for LLM consumption.

    This helper extracts specified fields from the workflow state and converts
    Pydantic models to dictionaries for JSON serialization.

    Args:
        state: The workflow state containing agent outputs and data
        include_fields: List of state field names to include in context

    Returns:
        Dictionary with relevant context data ready for JSON serialization

    Example:
        context = build_context_from_state(
            state,
            ["patient_info", "intake_conversation_info", "triage_info"]
        )
    """
    context_data = {}

    for field in include_fields:
        if value := state.get(field):
            # Handle Pydantic models by converting to dict
            if hasattr(value, "model_dump"):
                context_data[field] = value.model_dump()
            # Handle lists of Pydantic models
            elif isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                context_data[field] = [item.model_dump() for item in value]
            else:
                context_data[field] = value

    return context_data


def format_context_as_json(context_data: dict[str, Any]) -> str:
    """
    Format context data as pretty-printed JSON string.

    Args:
        context_data: Dictionary to format as JSON

    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(context_data, indent=2, default=str)
