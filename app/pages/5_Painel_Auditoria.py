import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from app.core.logging_config import read_audit_log

st.set_page_config(page_title="Painel de Auditoria — Hospital Vida Nova", page_icon="📋")
st.title("📋 Painel de Auditoria")
st.caption("Histórico de interações: pergunta, fontes citadas, resposta e acionamento de guardrail.")

registros = read_audit_log()

if not registros:
    st.info("Nenhuma interação registrada ainda.")
else:
    df = pd.DataFrame(registros)
    df = df.sort_values("timestamp", ascending=False)

    col1, col2 = st.columns(2)
    col1.metric("Total de interações", len(df))
    col2.metric("Guardrail acionado", int(df["guardrail_acionado"].sum()))

    apenas_guardrail = st.checkbox("Mostrar apenas interações com guardrail acionado")
    if apenas_guardrail:
        df = df[df["guardrail_acionado"]]

    for _, row in df.iterrows():
        with st.expander(f"{row['timestamp']} — {row['pergunta'][:80]}"):
            st.markdown(f"**Usuário:** {row['usuario']}")
            if row.get("paciente_id"):
                st.markdown(f"**Paciente:** {row['paciente_id']}")
            st.markdown(f"**Pergunta:** {row['pergunta']}")
            st.markdown(f"**Resposta:** {row['resposta']}")
            fontes = row.get("fontes") or []
            if fontes:
                st.markdown("**Fontes:** " + ", ".join(fontes))
            if row["guardrail_acionado"]:
                st.warning(f"Guardrail acionado — {row.get('guardrail_motivo', '')}")
