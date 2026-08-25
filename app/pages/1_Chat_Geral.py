import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from app.core.langgraph_flow import run

st.set_page_config(page_title="Chat Geral — Hospital Vida Nova", page_icon="💬")
st.title("💬 Chat Geral")
st.caption("Perguntas sobre protocolos institucionais e conhecimento médico geral.")

if "chat_geral_historico" not in st.session_state:
    st.session_state.chat_geral_historico = []

for msg in st.session_state.chat_geral_historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("fontes"):
            st.caption("Fontes: " + ", ".join(msg["fontes"]))

pergunta = st.chat_input("Digite sua pergunta...")

if pergunta:
    st.session_state.chat_geral_historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando protocolos institucionais..."):
            resultado = run(pergunta, patient_id=None, usuario="streamlit_chat_geral")
        st.markdown(resultado["answer"])
        fontes = sorted(set(resultado.get("sources", [])))
        if fontes:
            st.caption("Fontes: " + ", ".join(fontes))
        if resultado.get("guardrail_triggered"):
            st.info(f"🛡️ Guardrail acionado: {resultado.get('guardrail_reason')}")

    st.session_state.chat_geral_historico.append(
        {"role": "assistant", "content": resultado["answer"], "fontes": fontes}
    )
