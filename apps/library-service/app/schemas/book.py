from datetime import date, datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator

ISBN_PATTERN = r"^[0-9][0-9\-]{8,15}[0-9Xx]$"


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    author: str = Field(min_length=2, max_length=200)
    isbn: str | None = Field(default=None, pattern=ISBN_PATTERN)
    category: str = Field(default="general", min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=3000)
    published_year: int | None = Field(default=None, ge=1000)
    copies: int = Field(default=1, ge=0, le=1000, description="Copies the library owns")
    shelf_location: str | None = Field(default=None, max_length=100)

    @field_validator("title", "author", "category")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("category")
    @classmethod
    def lower_category(cls, value: str) -> str:
        return value.lower()

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, value: str | None) -> str | None:
        return value.replace("-", "").upper() if value else value

    @field_validator("published_year")
    @classmethod
    def check_year(cls, value: int | None) -> int | None:
        if value is not None and value > date.today().year + 1:
            raise ValueError("published_year cannot be in the future")
        return value


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    author: str | None = Field(default=None, min_length=2, max_length=200)
    isbn: str | None = Field(default=None, pattern=ISBN_PATTERN)
    category: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=3000)
    published_year: int | None = Field(default=None, ge=1000)
    copies: int | None = Field(default=None, ge=0, le=1000)
    shelf_location: str | None = Field(default=None, max_length=100)


class BookResponse(BookBase):
    id: PydanticObjectId
    created_by: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
