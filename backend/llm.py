import ollama

from . import config

SYSTEM_PROMPT = (
    "You are FieldDex, an assistant that answers questions about Pokémon. "
    "Be concise and accurate. If a question is not about Pokémon, politely "
    "decline and say you can only help with Pokémon."
)


class LLMUnavailable(Exception):
    """Raised when the model server can't be reached or fails."""


_client = ollama.Client(host=config.OLLAMA_HOST, timeout=config.LLM_TIMEOUT)


def generate(history: list[dict], question: str) -> str:
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": question}]
    )
    try:
        response = _client.chat(model=config.OLLAMA_MODEL, messages=messages)
    except Exception as exc:  # connection refused, timeout, model not found
        raise LLMUnavailable(str(exc)) from exc
    return response["message"]["content"]