"""Exercise real Pokémon name normalization, without altering the Pokédex."""

import pytest

from backend.pokemon_scope import normalize_name


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("PIKACHU", "pikachu"),
        (" Mr. Mime ", "mr mime"),
        ("Mime   Jr.", "mime jr"),
        ("EeVeE!", "eevee"),
        ("  a--b__c ", "a b c"),
        ("!!!", ""),
        ("Farfetch'd", "farfetch d"),
        ("Nidoran♀", "nidoran"),
    ],
)
def test_normalize_pokemon_names(raw, normalized):
    assert normalize_name(raw) == normalized
