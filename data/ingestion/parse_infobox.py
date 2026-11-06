import mwparserfromhell


def _clean(value) -> str:
    return mwparserfromhell.parse(str(value)).strip_code().strip()


def _num(value: str):
    try:
        return float(value)
    except ValueError:
        return None


def parse_infobox(wikitext: str) -> dict:
    """
    Pull structured facts out of the {{Pokémon Infobox}} template. Missing keys are skipped.
    """
    code = mwparserfromhell.parse(wikitext)
    box = None
    for t in code.filter_templates():
        if "infobox" in str(t.name).strip().lower():
            box = t
            break
    if box is None:
        return {}

    def get(name):
        return _clean(box.get(name).value) if box.has(name) else ""

    types = [t for t in (get("type1"), get("type2")) if t and t.lower() != "unknown"]
    abilities = [a for a in (get("ability1"), get("ability2")) if a]
    facts = {
        "types": types,
        "category": get("category"),
        "abilities": abilities,
        "hidden_ability": get("abilityd") or None,
        "height_m": _num(get("height-m")),
        "weight_kg": _num(get("weight-kg")),
        "egg_groups": [g for g in (get("egggroup1"), get("egggroup2")) if g],
        "color": get("color") or None,
    }
    return {k: v for k, v in facts.items() if v not in (None, "", [])}