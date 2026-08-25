import streamlit as st

st.set_page_config(page_title="Assistente Médico Virtual — Hospital Vida Nova", page_icon="🏥")

st.title("🏥 Assistente Médico Virtual")
st.subheader("Hospital Vida Nova (fictício) — Tech Challenge Fase 3")

st.markdown(
    """
Use o menu à esquerda para navegar entre as funcionalidades:

- **Chat Geral** — perguntas sobre protocolos institucionais e conhecimento médico geral
- **Upload de Protocolo** — adiciona um novo documento institucional ao índice estático
- **Upload de Prontuário** — indexa um novo prontuário de paciente e já dispara o fluxo de decisão
- **Consulta por Paciente** — pergunta sobre um paciente específico já indexado
- **Painel de Auditoria** — histórico de interações, fontes citadas e acionamentos de guardrail

---

⚠️ **Aviso**: todo o dataset deste projeto é sintético/anonimizado — nenhum dado
real de paciente é usado em nenhuma etapa. Nenhuma resposta deste assistente
substitui a avaliação e a validação de um médico responsável.
"""
)
