"""Direct tests of production chat helpers with plain input data and no mocks."""

from backend.chat_service import _search_query, _to_sources


def test_sources_deduplicate_same_heading():
    chunks = [
        {"metadata": {"pokemon": "Pikachu", "heading": "Biology"}},
        {"metadata": {"pokemon": "Pikachu", "heading": "Biology"}},
    ]
    assert len(_to_sources(chunks)) == 1


def test_sources_preserve_distinct_headings():
    chunks = [
        {"metadata": {"pokemon": "Pikachu", "heading": "Biology"}},
        {"metadata": {"pokemon": "Pikachu", "heading": "Moves"}},
    ]
    assert [s.section for s in _to_sources(chunks)] == ["Biology", "Moves"]


def test_sources_preserve_http_link():
    chunks = [{"metadata": {
        "pokemon": "Eevee", "heading": "Abilities", "source_url": "https://example.org/eevee"
    }}]
    assert _to_sources(chunks)[0].url == "https://example.org/eevee"


def test_search_query_uses_explicit_pokemon():
    pokemon = {"name": "eevee", "dex": 133}
    assert _search_query("What moves can it learn?", [], pokemon) == "eevee: What moves can it learn?"
