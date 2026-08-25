"""Consulta unificada de paciente: primeiro nos pacientes de demonstração
(fixos, usados nos testes e no vídeo/demo), depois no índice dinâmico real
(prontuários indexados via upload no Streamlit — ver app/core/ingestion.py).

Os pacientes de demonstração existem porque ainda não há ingestão via Synthea
(seção 2.1 do documento de arquitetura) — servem pra testar e demonstrar o
fluxo de decisão do LangGraph (alerta vs. sugestão de conduta) sem depender
daquele pipeline, que é uma peça separada do projeto.
"""

from .ingestion import add_patient_document, get_patient_record

DEMO_PATIENTS = {
    "SIM-0001": {
        "nome": "Paciente Simulado 1",
        "prontuario": (
            "Paciente admitido com queixa de febre e taquicardia. Suspeita de "
            "infecção de foco urinário. FR 24irpm, PAS 95mmHg, Glasgow 15."
        ),
        "exame_pendente": True,
        "exame_pendente_desc": "Hemocultura coletada, resultado ainda em processamento.",
    },
    "SIM-0002": {
        "nome": "Paciente Simulado 2",
        "prontuario": (
            "Paciente internado para controle de diabetes tipo 2 descompensada. "
            "Glicemias capilares entre 220 e 260mg/dL nas últimas 24h."
        ),
        "exame_pendente": False,
        "exame_pendente_desc": None,
    },
}


def get_patient(patient_id: str) -> dict | None:
    if patient_id in DEMO_PATIENTS:
        return DEMO_PATIENTS[patient_id]
    return get_patient_record(patient_id)


def register_patient(
    patient_id: str,
    nome: str,
    prontuario: str,
    exame_pendente: bool,
    exame_pendente_desc: str | None = None,
) -> None:
    """Usado pela aba de upload de prontuário no Streamlit."""
    add_patient_document(patient_id, nome, prontuario, exame_pendente, exame_pendente_desc)
