import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from app.core.langgraph_flow import run
from app.core.patient_index import DEMO_PATIENTS, get_patient

st.set_page_config(page_title="Consulta por Paciente — Hospital Vida Nova", page_icon="🔎")
st.title("🔎 Consulta por Paciente")
st.caption(
    "Busca por ID de paciente já indexado (upload ou pacientes de demonstração) "
    "e aciona o fluxo LangGraph completo."
)

st.caption("Pacientes de demonstração disponíveis: " + ", ".join(DEMO_PATIENTS.keys()))

patient_id = st.text_input("ID do paciente")
pergunta = st.text_input("Pergunta", value="O que o paciente tem?")
consultar = st.button("Consultar")

if consultar:
    if not patient_id:
        st.error("Informe o ID do paciente.")
    elif get_patient(patient_id) is None:
        st.error(f"Nenhum prontuário encontrado para '{patient_id}'.")
    else:
        with st.spinner("Executando fluxo de decisão..."):
            resultado = run(pergunta, patient_id=patient_id, usuario="streamlit_consulta_paciente")

        if resultado.get("alert"):
            st.error(resultado["alert"])

        st.markdown(resultado["answer"])

        fontes = sorted(set(resultado.get("sources", [])))
        if fontes:
            st.caption("Fontes: " + ", ".join(fontes))
        if resultado.get("guardrail_triggered"):
            st.info(f"🛡️ Guardrail acionado: {resultado.get('guardrail_reason')}")
