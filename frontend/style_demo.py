"""Style preview for the Field Dex UI, with canned answers and no backend.

Run from the repo root:
    streamlit run frontend/style_demo.py

It walks through every state in docs/style-guide.md: closed, scanning, open, follow-up,
refusal, and the data port. Swap fake_answer() for the real FastAPI call in the actual app.
"""
from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

import style as fd

st.set_page_config(
    page_title="Field Dex · GottaCatchEmAll",
    page_icon=str(Path(__file__).with_name("static") / "favicon.png"),
    layout="centered",
)
fd.apply_style()

MODES = ["Chat", "Dex", "Data"]
PLACEHOLDER = {"Chat": "Say hello, or ask a general question", "Dex": "Ask about a Pokémon, move or ability"}
TRIES = [
    "What does Pikachu keep in its cheeks?",
    "Tell me about the Unova Grass starter",
    "Can you do my math homework?",
]
DEMO_STATS = {"DOCUMENTS": "151", "CHUNKS": "2,903", "EMBEDDINGS": "MiniLM-L6", "LAST SYNC": "Today"}

ENTRIES = {
    "pikachu": {
        "entry": {"number": 25, "name": "Pikachu", "category": "Mouse Pokémon", "types": ["Electric"],
                  "stats": {"HEIGHT": "0.4 m", "WEIGHT": "6.0 kg", "GEN": "I"}},
        "text": ("Pikachu stores electricity in the pouches on its cheeks and lets it out in bursts when it "
                 "feels threatened. A group of Pikachu can build up enough charge between them to set off "
                 "small lightning storms."),
        "sources": [
            {"title": "Pikachu (Pokémon)", "section": "Biology",
             "url": "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Pok%C3%A9mon)#Biology"},
            {"title": "Pikachu (Pokémon)", "section": "Pokédex entries",
             "url": "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Pok%C3%A9mon)#Pok%C3%A9dex_entries"},
        ],
        "frame": False,
    },
    "snivy": {
        "entry": {"number": 495, "name": "Snivy", "category": "Grass Snake Pokémon", "types": ["Grass"],
                  "stats": {"HEIGHT": "0.6 m", "WEIGHT": "8.1 kg", "GEN": "V"}},
        "text": ("Snivy is the Grass-type starter of the Unova region. It soaks up sunlight through its tail "
                 "to photosynthesize, so a drooping tail is a sign that it's running low on energy."),
        "sources": [
            {"title": "Snivy (Pokémon)", "section": "Biology",
             "url": "https://bulbapedia.bulbagarden.net/wiki/Snivy_(Pok%C3%A9mon)#Biology"},
            {"title": "Starter Pokémon", "section": "Generation V",
             "url": "https://bulbapedia.bulbagarden.net/wiki/Starter_Pok%C3%A9mon#Generation_V"},
        ],
        "frame": True,
    },
}


def fake_answer(question: str, mode: str) -> dict:
    """Stand-in for the FastAPI call. Returns the same shape the UI expects from the real backend."""
    time.sleep(1.6)
    q = question.lower()
    if any(w in q for w in ("homework", "math", "weather", "stock", "essay")):
        return {"kind": "refusal",
                "text": "That's outside what I can help with. I only answer questions about Pokémon, "
                        "using the records loaded into this Dex. Try asking about a species, a move or an ability."}
    if mode == "Chat":
        return {"kind": "answer",
                "text": "Hey, Trainer! I can chat about Pokémon in general here. Switch to **Dex** mode when you "
                        "want answers pulled straight from the Bulbapedia records, with sources."}
    for name, data in ENTRIES.items():
        if name in q or (name == "snivy" and "unova" in q and "grass" in q):
            return {"kind": "answer", **data}
    return {"kind": "refusal", "label": "NO RECORD",
            "text": "I couldn't find that in the records I have, so I'd rather not guess. "
                    "Try a Pokémon from the ingested pages, or ask it a different way."}


# ---------- state ----------
ss = st.session_state
ss.setdefault("log", [])        # newest last: {"q": str, "a": dict}
ss.setdefault("pending", None)  # question being answered right now


def ask(question: str) -> None:
    question = question.strip()
    if question and not ss.pending:
        ss.pending = question


def reset() -> None:
    ss.log = []
    ss.pending = None


# ---------- page ----------
busy = ss.pending is not None
with fd.device():
    fd.render_cap("scanning" if busy else "ready")
    mode = st.segmented_control("Mode", MODES, default="Dex", key="fd-mode", label_visibility="collapsed") or "Dex"
    fd.render_hinge()

    if mode == "Data":
        with fd.screen():
            fd.render_screenbar("DATA PORT", "DEMO VALUES")
            st.markdown("Drop cleaned pages here to add them to the Dex. Accepted formats: `.json`, `.md`, `.txt`.")
            st.file_uploader("Upload documents", type=["json", "md", "txt"], accept_multiple_files=True,
                             label_visibility="collapsed")
            cells = "".join(f'<div class="fd-stat"><span>{k}</span><b>{v}</b></div>' for k, v in DEMO_STATS.items())
            st.html(f'<div class="fd-stats">{cells}</div>')
    else:
        if ss.log:  # open once there is a readout to show
            with fd.screen():
                fd.render_screenbar("DEX SEARCH" if mode == "Dex" else "GENERAL CHAT",
                                    f"{len(ss.log)} READOUT{'S' if len(ss.log) != 1 else ''}")
                if busy:
                    fd.render_query(ss.pending)
                    fd.render_receiving()
                    fd.render_earlier()
                for i, turn in enumerate(reversed(ss.log)):
                    old = busy or i > 0
                    if i == 1 and not busy:
                        fd.render_earlier()
                    fd.render_query(turn["q"], old=old)
                    a = turn["a"]
                    fd.render_answer(key=str(len(ss.log) - i), text=a["text"], kind=a["kind"],
                                     entry=a.get("entry"), sources=a.get("sources", ()),
                                     show_frame=a.get("frame", False), old=old, label=a.get("label"))

        with fd.slot(busy=busy):
            with st.form("fd-ask", clear_on_submit=True, border=False):
                left, right = st.columns([5, 1.3], vertical_alignment="bottom")
                question = left.text_input("Question", placeholder=ss.pending if busy else PLACEHOLDER[mode],
                                           label_visibility="collapsed", disabled=busy)
                if right.form_submit_button("Scan", disabled=busy, use_container_width=True):
                    ask(question)
                    st.rerun()

        if not ss.log:
            with st.container(key="fd-tries", horizontal=True):
                for n, text in enumerate(TRIES):
                    if st.button(text, key=f"fd-try-{n}", disabled=busy):
                        ask(text)
                        st.rerun()
        elif ss.log:
            hint, action = st.columns([3, 1], vertical_alignment="center")
            with hint:
                fd.render_hint("ENTER TO SCAN · NEWEST READOUT ON TOP")
            with action:
                st.button("New scan", key="fd-reset", on_click=reset, disabled=busy, use_container_width=True)

fd.render_footer()

# Answer the pending question after the page has drawn its scanning state.
if busy:
    ss.log.append({"q": ss.pending, "a": fake_answer(ss.pending, mode)})
    ss.pending = None
    st.rerun()
