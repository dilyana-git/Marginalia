from datetime import datetime

from pydantic import BaseModel, field_validator


class TagCreate(BaseModel):
    name: str
    color: str | None = None

    @field_validator("name")
    @classmethod
    def lowercase(cls, v: str) -> str:
        return v.strip().lower()


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None

    @field_validator("name")
    @classmethod
    def lowercase(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else v


class TagRead(BaseModel):
    id: int
    name: str
    color: str | None
    created_at: datetime
