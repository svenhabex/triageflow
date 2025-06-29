from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class StaffMember(BaseModel):
    """Staff member model."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str = Field(description="staff member id")
    first_name: str = Field(description="staff member first name")
    last_name: str = Field(description="staff member last name")
    role: str = Field(description="staff member role")
    speciality: str = Field(description="staff member speciality")
    status: str = Field(description="staff member status")


class CoordinatorResponseDTO(BaseModel):
    """Coordinator response data transfer object for API responses."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    available_staff: list[StaffMember] = Field(description="available staff members")
