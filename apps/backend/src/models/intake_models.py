from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class IntakeResponseDTO(BaseModel):
    """Python equivalent of IntakeResult from TypeScript."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symptoms: list[str] = []
    pain_level: int = 0
    chief_complaint: str = ""
    medications: list[str] = []
    allergies: list[str] = []
    additional_notes: str = ""
