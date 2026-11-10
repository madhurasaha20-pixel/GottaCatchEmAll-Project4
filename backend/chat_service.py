import uuid

from . import memory
from .schemas import AskResponse


def answer(session_id: str | None, question: str, top_k: int) -> AskResponse:
  session_id = session_id or uuid.uuid4().hex

  history = memory.get(session_id)

  text = f"(stub) You asked: {question}. I remember {len(history)} earlier messages."

  memory.append(session_id, "user", question)
  memory.append(session_id, "assistant", text)

  return AskResponse(kind="answer", text=text, sources=[], session_id=session_id)