import hashlib
import json
import re
import time

import requests
from bs4 import BeautifulSoup

import config

_session = requests.Session()
_session.headers["User-Agent"] = config.USER_AGENT
_last_request = 0.0

def _cached_get(params:dict) -> dict:
    """
    GET the MediaWiki API, caching each response on disk and rate-limiting live calls.
    """
    global _last_request
    key = hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()
    path = config.CACHE_DIR / "bulbapedia" / f"{key}.json"

    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    wait = config.REQUEST_DELAY_SECONDS - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = _session.get(config.BASE_URL, params={**params, "format": "json"}, timeout=30)
    _last_request = time.time()
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data

def list_pokemon_scope(max_dex: int) -> list[dict]:
    """
    Return [{dex, name, title}] for dex numbers 1..max_dex from the national dex list page.
    """
    data = _cached_get({
        "action": "parse",
        "page": config.LIST_PAGE,
        "prop": "text"
    })
    soup = BeautifulSoup(data["parse"]["text"]["*"], "html.parser")

    found: dict[int, dict] = {}
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        m = re.fullmatch(r"#(\d{3,4})", cells[0].get_text(strip=True))
        if not m:
            continue
        dex = int(m.group(1))
        if dex > max_dex or dex in found:
            continue
        link = row.find("a", title=re.compile(r"\(pokemon\)$"))
        if link:
            found[dex] = {"dex": dex, "name": link.get_text(strip=True), "title": link["title"]}
    return [found[d] for d in sorted(found)]

def fetch_page(title: str) -> tuple[str, str]:
    """
    Return (rendered HTML, raw wikitext) for a page title.
    """
    html = _cached_get({"action": "parse", "page": title, "prop": "text", "redirects": 1})
    wikitext = _cached_get({"action": "parse", "page": title, "prop": "wikitext", "redirects": 1})
    return html["parse"]["text"]["*"], wikitext["parse"]["wikitext"]["*"]
