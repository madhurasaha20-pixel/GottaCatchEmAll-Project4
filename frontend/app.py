"""Live Streamlit frontend. Run: streamlit run frontend/app.py"""
import os
from pathlib import Path

import streamlit as st

import style as fd
from api_client import APIError, ask_api

st.set_page_config(page_title="Field Dex · GottaCatchEmAll",
                   page_icon=str(Path(__file__).with_name("static") / "favicon.png"),
                   layout="centered")
fd.apply_style()
ss = st.session_state
ss.setdefault("turns", [])
ss.setdefault("pending_question", None)
busy = ss.pending_question is not None

with st.sidebar:
    st.header("Connection settings")
    endpoint = st.text_input("Question API endpoint", value=os.getenv("FIELDDEX_API_URL", "http://localhost:8000/ask"), disabled=busy)
    top_k = st.slider("Maximum source chunks", 1, 10, 4, disabled=busy)
    st.caption("Answers and sources come from the team's FastAPI service.")
    st.download_button("Download conversation", data="\n\n".join(
        f"Question: {turn['question']}\n\n{turn['answer']['text']}" for turn in ss.turns),
        file_name="field-dex-conversation.txt", mime="text/plain", disabled=busy or not ss.turns)

with fd.device():
    fault = bool(ss.turns and ss.turns[-1]["answer"]["kind"] == "fault")
    fd.render_cap("scanning" if busy else "fault" if fault else "ready")
    fd.render_hinge()
    if ss.turns or busy:
        with fd.screen():
            fd.render_screenbar("DEX SEARCH", f"{len(ss.turns)} READOUTS")
            if busy:
                fd.render_query(ss.pending_question)
                fd.render_receiving()
            for index in range(len(ss.turns) - 1, -1, -1):
                old = busy or index != len(ss.turns) - 1
                if index == len(ss.turns) - 2:
                    fd.render_earlier()
                turn = ss.turns[index]
                fd.render_query(turn["question"], old=old)
                fd.render_answer(key=str(index), old=old, **turn["answer"])
    else:
        fd.render_hint("Ask about Pokémon using the records loaded into the Dex.")

    with fd.slot(busy=busy):
        with st.form("fd-ask", clear_on_submit=True, border=False):
            left, right = st.columns([5, 1.3], vertical_alignment="bottom")
            question = left.text_input("Question", placeholder="What are Pikachu's abilities?",
                                       max_chars=2000, disabled=busy, label_visibility="collapsed")
            submitted = right.form_submit_button("Scan", disabled=busy, use_container_width=True)
            if submitted:
                if question.strip():
                    ss.pending_question = question.strip()
                    st.rerun()
                else:
                    st.warning("Enter a question to start a scan.")

    if ss.turns:
        if fault and st.button("Retry last question", disabled=busy):
            ss.pending_question = ss.turns[-1]["question"]
            st.rerun()
        if st.button("New scan", key="fd-reset", disabled=busy):
            ss.turns = []
            st.rerun()

fd.render_footer()

if busy:
    try:
        answer = ask_api(endpoint, ss.pending_question, top_k)
    except APIError as exc:
        answer = {"kind": "fault", "text": str(exc), "sources": []}
    ss.turns.append({"question": ss.pending_question, "answer": answer})
    ss.pending_question = None
    st.rerun()
