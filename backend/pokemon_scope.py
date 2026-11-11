import re
import sys
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INGESTION_DIR = BASE_DIR / "data" / "ingestion"

sys.path.insert(0, str(INGESTION_DIR))

from bulbapedia_client import list_pokemon_scope


def normalize_name(name: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        name.lower()
    ).strip()


@lru_cache(maxsize=1)
def get_pokemon_lookup() -> dict:
    pokemon_list = list_pokemon_scope(1025)

    return {
        normalize_name(pokemon["name"]): pokemon["dex"]
        for pokemon in pokemon_list
    }


def find_pokemon(question: str):
    lookup = get_pokemon_lookup()
    normalized_question = normalize_name(question)

    for name in sorted(
        lookup,
        key=len,
        reverse=True
    ):
        pattern = rf"\b{re.escape(name)}\b"

        if re.search(pattern, normalized_question):
            return {
                "name": name,
                "dex": lookup[name]
            }

    return None
