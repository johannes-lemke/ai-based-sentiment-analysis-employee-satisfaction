from datetime import date

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator


class NamedItem(BaseModel):
    id: int | None = None
    name: str

    @field_validator("name")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name darf nicht leer sein")
        return stripped


class CategorySave(BaseModel):
    categories: list[NamedItem]
    since: date


class LocationSave(BaseModel):
    locations: list[NamedItem]


class FeedbackIn(BaseModel):
    text: str = Field(max_length=1000)
    location_id: int | None = None

    @field_validator("text")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text darf nicht leer sein")
        return stripped


def check_unique(items: list[NamedItem], label: str) -> list[str]:
    names = [item.name for item in items]
    if len(set(names)) != len(names):
        raise HTTPException(status_code=422, detail=f"doppelte {label}")
    return names
