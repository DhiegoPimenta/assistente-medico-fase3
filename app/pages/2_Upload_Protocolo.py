import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from app.core.file_utils import extract_text
from app.core.ingestion import add_static_document

st.set_page_config(page_title="Upload de Protocolo — Hospital Vida Nova", page_icon="📄")
st.title("📄 Upload de Protocolo Institucional")
st.caption("Adiciona um novo documento ao índice estático (protocolos, diretrizes).")

with st.form("upload_protocolo"):
    titulo = st.text_input("Título do protocolo")
    especialidade = st.text_input("Especialidade", value="Geral")
    arquivo = st.file_uploader("Arquivo (.txt ou .pdf)", type=["txt", "pdf"])
    texto_manual = st.text_area("Ou cole o texto diretamente", height=200)
    enviado = st.form_submit_button("Adicionar ao índice institucional")

if enviado:
    if not titulo:
        st.error("Informe um título.")
    elif not arquivo and not texto_manual.strip():
        st.error("Envie um arquivo ou cole o texto do protocolo.")
    else:
        texto = extract_text(arquivo) if arquivo else texto_manual
        with st.spinner("Anonimizando e indexando..."):
            source_id = add_static_document(titulo=titulo, texto=texto, especialidade=especialidade)
        st.success(f"Protocolo '{titulo}' adicionado ao índice estático (id: `{source_id}`).")
        st.caption(
            "Já pode ser consultado na aba Chat Geral — o texto passou por uma "
            "checagem de anonimização antes de ser indexado."
        )
