"""
Configuration management for the triage workflow system.
"""

import os
from typing import Any

from pydantic_settings import BaseSettings


class WorkflowConfig(BaseSettings):
    """Configuration for the workflow system."""

    # Agent configurations
    max_retries: int = 3
    timeout_seconds: int = 30

    # LLM configurations
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    model_name: str = "gemini-2.5-flash-preview-05-20"
    temperature: float = 1.0
    max_tokens: int = 1000

    # Workflow configurations
    enable_memory: bool = True
    memory_type: str = "in_memory"

    # Agent-specific configurations
    intake_agent_config: dict[str, Any] = {
        "max_questions": 10,
        "required_fields": ["symptoms", "medical_history", "current_medications"],
    }

    triage_agent_config: dict[str, Any] = {
        "priority_levels": [1, 2, 3, 4, 5],
        "reasoning_required": True,
    }

    class Config:
        env_prefix = "TRIAGE_"
        case_sensitive = False


config = WorkflowConfig()
