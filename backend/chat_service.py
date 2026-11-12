import uuid

from vectorization.vectorization import retrieve_chunks

from . import memory, llm
from .schemas import AskResponse, Source
from .pokemon_scope import find_pokemon


# Cosine distance. Measured best-chunk distances: in-scope questions 0.17-0.45,
# off-topic 0.64-0.89, so 0.55 sits in the gap.
MAX_DISTANCE = 0.55

REFUSAL = (
  "That's outside what I can help with. I only answer questions about "
  "Pokémon, using the records loaded into this Dex. Try asking about a "
  "species, an evolution or a Pokémon's biology."
)


def _search_query(question: str, history: list[dict], pokemon: dict | None) -> str:
  """Follow-ups like "what about its moves?" name no Pokémon, so borrow
  the most recent one from earlier in the conversation."""
  if not pokemon:
    for message in reversed(history):
      if message["role"] == "user":
        pokemon = find_pokemon(message["content"])
        if pokemon:
          break
  return f"{pokemon['name']}: {question}" if pokemon else question


def _to_sources(chunks: list[dict]) -> list[Source]:
  seen = set()
  sources = []
  for chunk in chunks:
    meta = chunk["metadata"]
    key = (meta["pokemon"], meta["heading"])
    if key not in seen:
      seen.add(key)
      sources.append(Source(
        title=meta["pokemon"],
        section=meta["heading"],
        url=meta.get("source_url", ""),
      ))
  return sources


def answer(session_id: str | None, question: str, top_k: int) -> AskResponse:
  session_id = session_id or uuid.uuid4().hex

  history = memory.get(session_id)

  pokemon = find_pokemon(question)
  sources = []

  if pokemon and pokemon["dex"] > 151:
      name = pokemon["name"].title()
      text = (
          f"My head... Psy-ay-ay! "
          f"{name} isn't in my Pokédex! "
          f"I only cover the original 151 Pokémon!"
      )
  else:
      chunks = retrieve_chunks(_search_query(question, history, pokemon), top_k)
      chunks = [c for c in chunks if c["distance"] <= MAX_DISTANCE]
      if not chunks:
        return AskResponse(kind="refusal", text=REFUSAL, sources=[], session_id=session_id)
      text = llm.generate(history, question, chunks)
      sources = _to_sources(chunks)

  memory.append(session_id, "user", question)
  memory.append(session_id, "assistant", text)

  return AskResponse(kind="answer", text=text, sources=sources, session_id=session_id)
