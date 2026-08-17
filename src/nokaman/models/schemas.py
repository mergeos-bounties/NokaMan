from pydantic import BaseModel, Field


class Sample(BaseModel):
    id: str
    language: str
    skill: str
    expected_cefr: str | None = None
    text: str

class SkillInfo(BaseModel):
    weight: float = 1.0
    notes: str = ""

class Rubric(BaseModel):
    language: str
    name: str | None = None
    skills: dict[str, SkillInfo] = Field(default_factory=dict)
    bands: list[str] = Field(default_factory=list)

class ListeningItem(BaseModel):
    id: str | None = None
    text: str | None = None
    answer: str | None = None

class ListeningPack(BaseModel):
    id: str
    language: str
    skill: str
    items: list[ListeningItem] = Field(default_factory=list)
    questions: list[ListeningItem] = Field(default_factory=list)
