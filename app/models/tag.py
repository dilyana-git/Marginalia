from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Tag(SQLModel, table=True):
    __tablename__ = "tag"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    color: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
