import json
import re
from datetime import datetime, timezone

import config
from parse_infobox import parse_infobox
from parse_sections import parse_sections


def generation_for(dex: int) -> int | None:
    for gen, last in config.GEN_END:
        if dex <= last:
            return gen
    return None


def build_record(entry: dict, html: str, wikitext: str) -> dict:
    facts = parse_infobox(wikitext)
    facts["generation"] = generation_for(entry["dex"])
    return {
        "dex_number": entry["dex"],
        "name": entry["name"],
        "source_url": "https://bulbapedia.bulbagarden.net/wiki/" + entry["title"].replace(" ", "_"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "facts": facts,
        "sections": parse_sections(html, entry["name"]),
    }


def record_path(entry: dict):
    slug = re.sub(r"[^a-z0-9]+", "-", entry["name"].lower()).strip("-")
    return config.RAW_DIR / f"{entry['dex']:04d}-{slug}.json"


def write_record(entry: dict, record: dict):
    path = record_path(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path