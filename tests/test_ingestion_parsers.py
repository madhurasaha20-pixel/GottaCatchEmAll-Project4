"""Local HTML fixtures exercise ingestion without scraping Bulbapedia."""

from parse_sections import parse_sections
from parse_gamedata import parse_evolution, parse_pokedex_entries


def test_sections_capture_intro():
    sections = parse_sections('<div class="mw-parser-output"><p>First paragraph.</p></div>', 'Pikachu')
    assert sections == [{"heading": "Pikachu", "level": 1, "path": ["Pikachu"], "text": "First paragraph."}]


def test_sections_track_nested_headings():
    html = '<h2>Biology</h2><p>Body.</p><h3>Evolution</h3><p>Thunder Stone.</p>'
    sections = parse_sections(html, 'Pikachu')
    assert [s['path'] for s in sections] == [['Biology'], ['Biology', 'Evolution']]


def test_sections_reset_path_on_new_top_heading():
    html = '<h2>Biology</h2><p>Body</p><h3>Habitat</h3><p>Forest</p><h2>Moves</h2><p>Thunderbolt</p>'
    sections = parse_sections(html, 'Pikachu')
    assert sections[-1]['path'] == ['Moves']


def test_sections_ignore_reference_section():
    html = '<h2>Biology</h2><p>Mouse</p><h2>References</h2><p>Do not include</p>'
    assert [s['heading'] for s in parse_sections(html, 'Pikachu')] == ['Biology']


def test_sections_ignore_subheadings_under_skipped_section():
    html = '<h2>References</h2><p>Links</p><h3>Notes</h3><p>Notes data</p>'
    assert parse_sections(html, 'Pikachu') == []


def test_sections_resume_after_skipped_section():
    html = '<h2>References</h2><p>Ignored</p><h2>Abilities</h2><p>Static</p>'
    assert [s['text'] for s in parse_sections(html, 'Pikachu')] == ['Static']


def test_sections_discard_tables_and_edit_markers():
    html = '<h2>Biology <span class="mw-editsection">[edit]</span></h2><table><tr><td>Junk</td></tr></table><p>Real <sup class="reference">[1]</sup> details.</p>'
    sections = parse_sections(html, 'Pikachu')
    assert sections[0]['heading'] == 'Biology'
    assert sections[0]['text'] == 'Real details.'


def test_sections_support_modern_mediawiki_heading_wrappers():
    html = '<div class="mw-parser-output"><div class="mw-heading mw-heading2"><h2>Biology</h2></div><p>Electric mouse.</p></div>'
    assert parse_sections(html, 'Pikachu')[0]['heading'] == 'Biology'


def test_pokedex_entries_missing_table_returns_defaults():
    assert parse_pokedex_entries('<p>No game data</p>') == {"region": None, "regional_dex_number": None, "entries": []}


def test_pokedex_entries_extract_region_and_game_text():
    html = '<h3>Pokédex entries</h3><table><tr><th>Generation I</th><th>Kanto #025</th></tr><tr><th>Red</th><td>Electric mouse.</td></tr></table>'
    result = parse_pokedex_entries(html)
    assert result['region'] == 'Kanto'
    assert result['regional_dex_number'] == 25
    assert result['entries'] == [{"game": "Red", "text": "Electric mouse."}]


def test_pokedex_entries_reuse_rowspanned_game_text():
    html = '<h3>Pokédex entries</h3><table><tr><th>Generation I</th><th>Kanto #025</th></tr><tr><th>Red</th><td>Shared entry.</td></tr><tr><th>Blue</th></tr></table>'
    assert [e['text'] for e in parse_pokedex_entries(html)['entries']] == ['Shared entry.', 'Shared entry.']


def test_evolution_without_heading_includes_own_name():
    assert parse_evolution('<p>Nothing</p>', 'Eevee') == {'text': '', 'related_names': ['Eevee']}


def test_evolution_stops_at_next_heading_and_collects_links():
    html = ('<h3>Evolution</h3><p>Evolves into <a title="Raichu (Pokémon)">Raichu</a>.</p>'
            '<h3>Moves</h3><p><a title="Mew (Pokémon)">Mew</a>.</p>')
    result = parse_evolution(html, 'Pikachu')
    assert result['related_names'] == ['Pikachu', 'Raichu']
    assert 'Evolves into' in result['text'] and 'Mew' not in result['text']
