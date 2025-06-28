from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class IntakeConversationInfo(BaseModel):
    """Information about a conversation"""

    symptoms: list[str] = Field(description="list of symptoms")
    pain_level: int = Field(description="pain level on a 1-10 scale")
    chief_complaint: str = Field(description="main reason for visit")
    medications: list[str] = Field(description="list of medications")
    allergies: list[str] = Field(description="list of allergies")
    additional_notes: str = Field(description="any other relevant information")


class PatientInfo(BaseModel):
    """Patient information model."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    patient_id: str = Field(description="patient id")
    first_name: str = Field(description="patient first name")
    last_name: str = Field(description="patient last name")
    date_of_birth: str = Field(description="patient date of birth")
    medical_history: list[str] = Field(description="patient medical history")
    medications: list[str] = Field(description="patient medications")


class IntakeResponseDTO(BaseModel):
    """Python equivalent of IntakeResult from TypeScript."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symptoms: list[str] = []
    pain_level: int = 0
    chief_complaint: str = ""
    medications: list[str] = []
    allergies: list[str] = []
    additional_notes: str = ""
    patient_info: PatientInfo
