import argparse
from datetime import datetime

import config
from build_record import build_record, record_path, write_record
from bulbapedia_client import fetch_page, list_pokemon_scope


def main():
    ap = argparse.ArgumentParser(description="Ingest Pokémon pages from Bulbapedia into data/raw/")
    ap.add_argument("--max-dex", type=int, default=config.DEFAULT_MAX_DEX)
    ap.add_argument("--limit", type=int, help="only process the first N Pokémon (for testing)")
    ap.add_argument("--force", action="store_true", help="re-write records that already exist")
    args = ap.parse_args()

    full_scope = list_pokemon_scope(args.max_dex)
    name_to_dex = {e["name"]: e["dex"] for e in full_scope}
    scope = full_scope[: args.limit] if args.limit else full_scope
    print(f"{len(scope)} Pokémon in scope")

    failures = 0
    for i, entry in enumerate(scope, 1):
        if record_path(entry).exists() and not args.force:
            print(f"[{i}/{len(scope)}] skip {entry['name']}")
            continue
        try:
            html, wikitext = fetch_page(entry["title"])
            path = write_record(entry, build_record(entry, html, wikitext, name_to_dex))
            print(f"[{i}/{len(scope)}] wrote {path.name}")
        except Exception as exc:  # keep going; log and retry later
            failures += 1
            config.FAILURES_LOG.parent.mkdir(parents=True, exist_ok=True)
            with config.FAILURES_LOG.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}\t{entry['title']}\t{exc}\n")
            print(f"[{i}/{len(scope)}] FAILED {entry['name']}: {exc}")
    print(f"Done. {failures} failures.")


if __name__ == "__main__":
    main()