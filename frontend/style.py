"""Field Dex look and feel for the Streamlit frontend.

Call apply_style() once at the top of every page, then build the UI from the helpers below.
The rules behind every color, size and animation are in docs/style-guide.md.

Anything that renders HTML escapes its inputs. Model answers are rendered with st.markdown
(no unsafe HTML), so nothing the LLM or the scraped data returns can inject markup.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Iterable, Literal, Sequence, TypedDict

import streamlit as st

_CSS_PATH = Path(__file__).with_name("style.css")

Status = Literal["ready", "scanning", "fault"]
Kind = Literal["answer", "refusal", "fault"]

STATUS_LABEL: dict[str, str] = {"ready": "READY", "scanning": "SCANNING", "fault": "NO SIGNAL"}
KIND_LABEL: dict[str, str] = {"answer": "READOUT", "refusal": "OUT OF RANGE", "fault": "SIGNAL LOST"}

# One color per type. Text color is picked for contrast, see _type_text().
TYPE_COLORS: dict[str, str] = {
    "normal": "#A8A77A", "fire": "#EE8130", "water": "#6390F0", "electric": "#F7D02C",
    "grass": "#7AC74C", "ice": "#96D9D6", "fighting": "#C22E28", "poison": "#A33EA1",
    "ground": "#E2BF65", "flying": "#A98FF3", "psychic": "#F95587", "bug": "#A6B91A",
    "rock": "#B6A136", "ghost": "#735797", "dragon": "#6F35FC", "dark": "#705746",
    "steel": "#B7B7CE", "fairy": "#D685AD",
}


class Source(TypedDict, total=False):
    title: str     # page title, e.g. "Pikachu (Pokémon)"
    section: str   # section the chunk came from, e.g. "Biology"
    url: str


class Entry(TypedDict, total=False):
    number: int            # national dex number
    name: str
    category: str          # e.g. "Mouse Pokémon"
    types: list[str]
    stats: dict[str, str]  # label -> value, e.g. {"HEIGHT": "0.4 m"}
    image_url: str


# ---------- setup ----------

def apply_style() -> None:
    """Inject the stylesheet. Streamlit re-runs the script on every interaction, so call this each run.

    Note: Streamlit sanitizes this through DOMPurify, so style.css must never contain "<" or ">" inside
    comments or strings, or the whole stylesheet is silently dropped.
    """
    st.html(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>")


def device(**container_kwargs):
    """The red device shell. Use as `with device():` and put everything inside it."""
    return st.container(key="fielddex", **container_kwargs)


def screen():
    """The blue screen. Only render it once there is something to show (this is the 'open' state).

    It grows with its content and starts scrolling past min(62vh, 560px), set in style.css.
    """
    return st.container(key="fd-screen")


def slot(busy: bool = False):
    """Wrapper for the question form. busy=True runs the scan sweep across the input."""
    return st.container(key="fd-slot-busy" if busy else "fd-slot")


def stage():
    """Bottom strip of the screen: the speech bubble on the left, the mascot on the right. Sticks to the screen's bottom edge."""
    return st.container(key="fd-stage")


def bubble():
    """The speech bubble beside the mascot. Put the latest response (or a greeting) inside it."""
    return st.container(key="fd-bubble")


def render_mascot(status: Status = "ready") -> None:
    """The lab-coat Psyduck. data-state drives the idle bob (ready) and the fidget (scanning)."""
    st.html(f'<div class="fd-mascot" data-state="{status}" aria-hidden="true">'
            '<img src="app/static/mascot.png" alt="" draggable="false"></div>')


def render_bubble_text(text: str) -> None:
    st.html(f'<div class="fd-bubble__text">{escape(text)}</div>')


# ---------- hardware ----------

def render_cap(status: Status = "ready", serial: str = "GCEA · UNIT 05") -> None:
    """Lens, name plate, status light and speaker grille across the top of the device."""
    st.html(
        f'<div class="fd-cap" data-state="{status}">'
        '<div class="fd-lens" aria-hidden="true"><span class="fd-lens__glass"></span>'
        '<span class="fd-lens__iris"></span><span class="fd-lens__glint"></span></div>'
        f'<div class="fd-plate"><span class="fd-plate__word">FIELD DEX</span>'
        f'<span class="fd-plate__serial">{escape(serial)}</span></div>'
        f'<div class="fd-status" role="status"><span class="fd-status__led"></span>{STATUS_LABEL[status]}</div>'
        '<div class="fd-grille" aria-hidden="true"><i></i><i></i><i></i></div>'
        "</div>"
    )


def render_hinge() -> None:
    st.html('<div class="fd-hinge" aria-hidden="true"></div>')


def render_screenbar(left: str, right: str = "") -> None:
    """Small label strip at the top of the screen, e.g. ('DEX SEARCH', 'BULBAPEDIA · GEN I')."""
    st.html(f'<div class="fd-screenbar"><span><b>{escape(left)}</b></span><span>{escape(right)}</span></div>')


# ---------- readouts ----------

def _type_text(hex_color: str) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#16181D" if lum > 0.55 else "#FFFFFF"


def type_badges(types: Iterable[str]) -> str:
    badges = []
    for t in types:
        color = TYPE_COLORS.get(t.lower(), "#68707C")
        badges.append(
            f'<span class="fd-type" style="background:{color};color:{_type_text(color)}">{escape(t)}</span>'
        )
    return f'<div class="fd-types">{"".join(badges)}</div>'


def render_query(text: str, old: bool = False) -> None:
    cls = "fd-query fd-query--old" if old else "fd-query"
    st.html(f'<div class="{cls}"><span class="fd-query__tag">QUERY</span>'
            f'<span class="fd-query__text">{escape(text)}</span></div>')


def render_entry(entry: Entry) -> None:
    """Dex-style header: number, name, category, types, and a row of stat readouts."""
    number = f"No. {entry['number']:04d}" if entry.get("number") else ""
    parts = [
        '<div class="fd-entry">',
        f'<div class="fd-entry__no">{escape(number)}</div>',
        f'<div class="fd-entry__name">{escape(entry.get("name", ""))}</div>',
        type_badges(entry.get("types", [])),
        f'<div class="fd-entry__cat">{escape(entry.get("category", ""))}</div>',
        "</div>",
    ]
    stats = entry.get("stats") or {}
    if stats:
        cells = "".join(f'<div class="fd-stat"><span>{escape(k)}</span><b>{escape(v)}</b></div>'
                        for k, v in stats.items())
        parts.append(f'<div class="fd-stats">{cells}</div>')
    st.html("".join(parts))


def render_frame(image_url: str | None, caption: str = "") -> None:
    """Grid-backed image frame. With no image it shows an empty slot label instead."""
    inner = (f'<img src="{escape(image_url, quote=True)}" alt="{escape(caption, quote=True)}">'
             if image_url else '<span class="fd-frame__empty">NO IMAGE ON FILE</span>')
    cap = f"<figcaption>{escape(caption)}</figcaption>" if caption and image_url else ""
    st.html(f'<figure class="fd-frame">{inner}{cap}</figure>')


def render_sources(sources: Sequence[Source], open_: bool = False) -> None:
    """Provenance list: which ingested sections the answer was built from."""
    if not sources:
        return
    rows = []
    for s in sources:
        title = escape(s.get("title", "Source"))
        link = (f'<a href="{escape(s["url"], quote=True)}" target="_blank" rel="noopener">{title}</a>'
                if s.get("url") else title)
        rows.append(f"<li>{link}<span>{escape(s.get('section', ''))}</span></li>")
    st.html(f'<details class="fd-src"{" open" if open_ else ""}><summary>SOURCES · {len(sources)}</summary>'
            f'<ol>{"".join(rows)}</ol></details>')


def render_answer(key: str, text: str, kind: Kind = "answer", entry: Entry | None = None,
                  sources: Sequence[Source] = (), show_frame: bool = False, old: bool = False,
                  label: str | None = None) -> None:
    """One answer panel. `key` must be unique per answer (e.g. the message index)."""
    with st.container(key=f"fd-ans-{'old-' if old else ''}{key}"):
        st.html(f'<div class="fd-kind" data-kind="{kind}">{escape(label or KIND_LABEL[kind])}</div>')
        if entry:
            render_entry(entry)
            if show_frame:
                render_frame(entry.get("image_url"), entry.get("name", ""))
        st.markdown(text)
        render_sources(sources)


def render_receiving(label: str = "RECEIVING READOUT") -> None:
    st.html(f'<div class="fd-receiving" role="status">{escape(label)}</div>')


def render_earlier() -> None:
    st.html('<div class="fd-earlier">EARLIER</div>')


def render_hint(text: str) -> None:
    st.html(f'<div class="fd-hint">{escape(text)}</div>')


def render_footer() -> None:
    st.html(
        '<div class="fd-foot">Pokémon data from '
        '<a href="https://bulbapedia.bulbagarden.net" target="_blank" rel="noopener">Bulbapedia</a> '
        '(CC BY-NC-SA). A student project, not affiliated with Nintendo, Game Freak or The Pokémon Company.</div>'
    )
