from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TriageInformation(BaseModel):
    """Information about a triage decision"""

    esi_level: int = Field(description="ESI risk level on a 1-5 scale")
    medical_category: str = Field(description="medical category")
    reasoning: str = Field(description="reasoning for the risk level")


class TriageResponseDTO(BaseModel):
    """Triage response data transfer object for API responses."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    esi_level: int = Field(description="ESI risk level on a 1-5 scale")
    medical_category: str = Field(description="medical category")
    reasoning: str = Field(description="reasoning for the risk level")
