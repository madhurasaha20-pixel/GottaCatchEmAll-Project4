import re

from bs4 import BeautifulSoup

import config

_JUNK = "style, script, sup.reference, span.mw-editsection, table, .toc, .navbox, .thumb"


def _heading_of(el):
    """
    Return (level, text) if el is a heading (old or new MediaWiki markup), else None.
    """
    if el.name and re.fullmatch(r"h[2-4]", el.name):
        h = el
    elif el.name == "div" and "mw-heading" in (el.get("class") or []):
        h = el.find(re.compile(r"h[2-4]"))
        if h is None:
            return None
    else:
        return None
    return int(h.name[1]), h.get_text(" ", strip=True).replace("[edit]", "").strip()


def parse_sections(html: str, page_name: str) -> list[dict]:
    """
    Split a rendered page into [{heading, level, path, text}] using its own headers.
    """
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("div.mw-parser-output") or soup
    for junk in root.select(_JUNK):
        junk.decompose()

    sections: list[dict] = []
    stack: list[tuple[int, str]] = []
    current = {"heading": page_name, "level": 1, "path": [page_name], "parts": []}
    skipping = False
    skip_level = None

    def flush():
        text = "\n".join(p for p in current["parts"] if p).strip()
        if text and not skipping:
            sections.append({"heading": current["heading"], "level": current["level"],
                             "path": current["path"], "text": text})

    for el in root.find_all(recursive=False):
        head = _heading_of(el)
        if head:
            flush()
            level, title = head
            stack[:] = [(l, t) for l, t in stack if l < level] + [(level, title)]

            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None and title.lower() in config.SKIP_SECTIONS:
                skip_level = level
            skipping = skip_level is not None
            
            current = {"heading": title, "level": level,
                       "path": [t for _, t in stack], "parts": []}
        elif el.name in ("p", "ul", "ol", "dl"):
            text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
            text = re.sub(r"\s+([,.;:!?])", r"\1", text)
            current["parts"].append(text)
    flush()
    return sections