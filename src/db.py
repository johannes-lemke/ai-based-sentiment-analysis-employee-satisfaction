import os
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Field, SQLModel, create_engine

DATABASE_URL = os.environ["DATABASE_URL"]

# Bei SQLite den Ordner der Datei anlegen, falls er fehlt.
if DATABASE_URL.startswith("sqlite:///"):
    path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Location(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Feedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str
    location_id: int | None = Field(default=None, foreign_key="location.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Aspect(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    feedback_id: int = Field(foreign_key="feedback.id")
    category: str
    score: int


def init_db():
    SQLModel.metadata.create_all(engine)
