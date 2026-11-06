import re

from bs4 import BeautifulSoup


def _soup(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for junk in soup.select("span.mw-editsection, sup.reference, style, script"):
        junk.decompose()
    return soup


def _is_heading(el) -> bool:
    if not getattr(el, "name", None):
        return False
    if re.fullmatch(r"h[2-4]", el.name):
        return True
    return el.name == "div" and "mw-heading" in (el.get("class") or [])


def _heading_container(soup, title_prefix: str):
    """First heading whose text starts with title_prefix; returns the element to walk siblings from."""
    for h in soup.find_all(re.compile(r"h[2-4]")):
        if h.get_text(" ", strip=True).startswith(title_prefix):
            parent = h.parent
            return parent if "mw-heading" in (parent.get("class") or []) else h
    return None


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def parse_pokedex_entries(html: str, generation: str = "Generation I") -> dict:
    """Return {region, regional_dex_number, entries: [{game, text}]} from the game-data Pokédex table."""
    soup = _soup(html)
    start = _heading_container(soup, "Pokédex entries")  # first match = Game data (anime one comes later)
    result = {"region": None, "regional_dex_number": None, "entries": []}
    if start is None:
        return result

    table = None
    for sib in start.find_next_siblings():
        if _is_heading(sib):
            break
        if sib.name == "table":
            first_th = sib.find("th")
            if first_th and first_th.get_text(" ", strip=True) == generation:
                table = sib
                break
    if table is None:
        return result

    m = re.match(r"(.+?)\s*#(\d+)", table.find_all("th")[1].get_text(" ", strip=True))
    if m:
        result["region"], result["regional_dex_number"] = m.group(1), int(m.group(2))

    last_text = ""
    for tr in table.find_all("tr"):
        th = tr.find("th", recursive=False)
        if th is None:
            continue
        label = _clean(th.get_text())
        if label == generation or "#" in label:
            continue
        if label.startswith("Generation"):  # the next generation's block starts here
            break
        td = tr.find("td", recursive=False)
        if td is not None:  # a rowspan'd entry sits on the first row and covers the rows below it
            for br in td.find_all("br"):
                br.replace_with(" ")
            last_text = _clean(td.get_text())
        if last_text and not last_text.startswith("("):  # skip translation notes
            result["entries"].append({"game": label, "text": last_text})
    return result


def parse_evolution(html: str, own_name: str) -> dict:
    """Return {text, related_names} from the Evolution subsection of Biology."""
    soup = _soup(html)
    start = None
    for h in soup.find_all(re.compile(r"h[2-4]")):
        if h.get_text(" ", strip=True) == "Evolution":
            start = h.parent if "mw-heading" in (h.parent.get("class") or []) else h
            break
    if start is None:
        return {"text": "", "related_names": [own_name]}

    paragraphs, names = [], {own_name}
    for sib in start.find_next_siblings():
        if _is_heading(sib):
            break
        if sib.name == "p":
            paragraphs.append(_clean(sib.get_text()))
            for a in sib.find_all("a", title=re.compile(r"\(Pokémon\)$")):
                names.add(re.sub(r"\s*\(Pokémon\)$", "", a["title"]))
    text = re.sub(r"\(For specifics.*?\)", "", " ".join(paragraphs)).strip()
    return {"text": text, "related_names": sorted(names)}