"""API endpoints for the triage system."""

from .agents import patient_triage_ws, router

__all__ = ["router", "patient_triage_ws"]
