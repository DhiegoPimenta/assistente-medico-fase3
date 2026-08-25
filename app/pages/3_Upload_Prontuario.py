import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from app.core.file_utils import extract_text
from app.core.langgraph_flow import run
from app.core.patient_index import register_patient

st.set_page_config(page_title="Upload de Prontuário — Hospital Vida Nova", page_icon="🗂️")
st.title("🗂️ Upload de Prontuário de Paciente")
st.caption(
    "Indexa um novo prontuário no índice dinâmico e já dispara o fluxo de "
    "decisão automatizado (verifica exame pendente)."
)

with st.form("upload_prontuario"):
    patient_id = st.text_input("ID do paciente (ex.: SIM-0003)")
    nome = st.text_input("Nome do paciente (sintético)")
    arquivo = st.file_uploader("Arquivo (.txt ou .pdf)", type=["txt", "pdf"])
    texto_manual = st.text_area("Ou cole o texto do prontuário", height=200)
    exame_pendente = st.checkbox("Existe exame pendente para este paciente?")
    exame_pendente_desc = st.text_input(
        "Descrição do exame pendente", disabled=not exame_pendente
    )
    enviado = st.form_submit_button("Indexar prontuário")

if enviado:
    if not patient_id or not nome:
        st.error("Informe o ID e o nome do paciente.")
    elif not arquivo and not texto_manual.strip():
        st.error("Envie um arquivo ou cole o texto do prontuário.")
    else:
        texto = extract_text(arquivo) if arquivo else texto_manual
        with st.spinner("Anonimizando e indexando..."):
            register_patient(
                patient_id=patient_id,
                nome=nome,
                prontuario=texto,
                exame_pendente=exame_pendente,
                exame_pendente_desc=exame_pendente_desc if exame_pendente else None,
            )
        st.success(f"Prontuário de '{nome}' (`{patient_id}`) indexado.")

        st.subheader("Fluxo de decisão acionado automaticamente")
        with st.spinner("Executando LangGraph (verifica exame pendente → alerta ou sugestão)..."):
            resultado = run(
                "O que o paciente tem?", patient_id=patient_id, usuario="streamlit_upload_prontuario"
            )

        if resultado.get("alert"):
            st.error(resultado["alert"])
        st.markdown(resultado["answer"])
        if resultado.get("guardrail_triggered"):
            st.info(f"🛡️ Guardrail acionado: {resultado.get('guardrail_reason')}")
