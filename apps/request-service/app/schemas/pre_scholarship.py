from datetime import date

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import RequestMeta
from app.utils.enums import Gender, ScholarshipType


class PreScholarshipBase(BaseModel):  # also the body for "send request"
    scholarship_type: ScholarshipType
    academic_year: str = Field(pattern=r"^\d{4}-\d{4}$", examples=["2026-2027"])
    full_name: str = Field(min_length=2, max_length=100)
    date_of_birth: date
    gender: Gender
    phone: str = Field(pattern=r"^\+?[0-9\s-]{8,15}$")
    address: str = Field(min_length=5, max_length=300)
    school_name: str = Field(min_length=2, max_length=150)
    grade_level: str = Field(min_length=1, max_length=30)
    guardian_name: str = Field(min_length=2, max_length=100)
    guardian_phone: str = Field(pattern=r"^\+?[0-9\s-]{8,15}$")
    guardian_relationship: str = Field(min_length=2, max_length=50)
    monthly_family_income: float | None = Field(default=None, ge=0)  # need_based
    number_of_dependents: int = Field(default=0, ge=0)
    academic_average: float | None = Field(default=None, ge=0, le=100)  # merit
    achievements: list[str] = []
    statement: str = Field(min_length=20, max_length=1500)
    document_urls: list[str] = []

    @model_validator(mode="after")
    def check_type_requirements(self):
        if (
            self.scholarship_type == ScholarshipType.NEED_BASED
            and self.monthly_family_income is None
        ):
            raise ValueError(
                "monthly_family_income is required for need_based scholarships"
            )
        if (
            self.scholarship_type == ScholarshipType.MERIT
            and self.academic_average is None
        ):
            raise ValueError(
                "academic_average is required for merit scholarships"
            )
        return self


class PreScholarshipUpdate(BaseModel):
    scholarship_type: ScholarshipType | None = None
    academic_year: str | None = Field(default=None, pattern=r"^\d{4}-\d{4}$")
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9\s-]{8,15}$")
    address: str | None = Field(default=None, min_length=5, max_length=300)
    school_name: str | None = Field(default=None, min_length=2, max_length=150)
    grade_level: str | None = Field(default=None, min_length=1, max_length=30)
    guardian_name: str | None = Field(default=None, min_length=2, max_length=100)
    guardian_phone: str | None = Field(
        default=None, pattern=r"^\+?[0-9\s-]{8,15}$"
    )
    guardian_relationship: str | None = Field(
        default=None, min_length=2, max_length=50
    )
    monthly_family_income: float | None = Field(default=None, ge=0)
    number_of_dependents: int | None = Field(default=None, ge=0)
    academic_average: float | None = Field(default=None, ge=0, le=100)
    achievements: list[str] | None = None
    statement: str | None = Field(default=None, min_length=20, max_length=1500)
    document_urls: list[str] | None = None


class PreScholarshipResponse(PreScholarshipBase, RequestMeta):
    id: PydanticObjectId
    model_config = ConfigDict(from_attributes=True)