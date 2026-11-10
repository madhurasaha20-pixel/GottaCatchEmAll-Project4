from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=10)
    session_id: str | None = None


class Source(BaseModel):
    title: str = ""
    section: str = ""
    url: str = ""


class AskResponse(BaseModel):
    kind: Literal["answer", "refusal"] = "answer"
    text: str
    sources: list[Source] = []
    session_id: str
