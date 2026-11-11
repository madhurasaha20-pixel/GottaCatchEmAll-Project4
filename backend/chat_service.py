import uuid

from . import memory, llm
from .schemas import AskResponse
from .pokemon_scope import find_pokemon


def answer(session_id: str | None, question: str, top_k: int) -> AskResponse:
  session_id = session_id or uuid.uuid4().hex

  history = memory.get(session_id)

  pokemon = find_pokemon(question)

  if pokemon and pokemon["dex"] > 151:
      name = pokemon["name"].title()
      text = (
          f"My head... Psy-ay-ay! "
          f"{name} isn't in my Pokédex! "
          f"I only cover the original 151 Pokémon!"
      )
  else:
      text = llm.generate(history, question)

  memory.append(session_id, "user", question)
  memory.append(session_id, "assistant", text)

  return AskResponse(kind="answer", text=text, sources=[], session_id=session_id)