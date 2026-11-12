"""Tests of the actual ingestion functions using local input documents.

The HTML/wikitext is test input, not a replaced HTTP service or mocked function.
"""

import pytest

from build_record import generation_for, record_path
from parse_infobox import parse_infobox


@pytest.mark.parametrize(
    ("dex_number", "generation"),
    [
        (1, 1), (151, 1), (152, 2), (251, 2),
        (252, 3), (1025, 9), (1026, None),
    ],
)
def test_generation_for_pokedex_boundary(dex_number, generation):
    assert generation_for(dex_number) == generation


def test_parse_real_infobox_template_fields():
    wikitext = """{{Pokémon Infobox
    |type1=Electric|type2=Unknown|category=Mouse Pokémon
    |ability1=Static|ability2=Lightning Rod|abilityd=Surge Surfer
    |height-m=0.4|weight-kg=6.0|egggroup1=Field|color=Yellow
    }}"""
    details = parse_infobox(wikitext)
    assert details["types"] == ["Electric"]
    assert details["abilities"] == ["Static", "Lightning Rod"]
    assert details["hidden_ability"] == "Surge Surfer"
    assert details["height_m"] == 0.4
    assert details["weight_kg"] == 6.0
    assert details["egg_groups"] == ["Field"]
    assert details["color"] == "Yellow"
    assert details["category"] == "Mouse Pokémon"


def test_parse_infobox_without_template_returns_empty_facts():
    assert parse_infobox("Pikachu is an Electric-type Pokémon.") == {}


def test_record_path_slug_preserves_dex_prefix():
    path = record_path({"name": "Mr. Mime", "dex": 122})
    assert path.name == "0122-mr-mime.json"
    assert path.parent.name == "raw"
