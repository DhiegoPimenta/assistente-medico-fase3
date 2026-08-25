"""Índice dinâmico (prontuários de pacientes) — STUB.

Ainda não substituído pela ingestão real via Synthea + upload no Streamlit
(seção 2.1 do documento de arquitetura). Esse dicionário em memória permite
testar e demonstrar o fluxo de decisão completo do LangGraph (seção 4.2) sem
depender daquele pipeline, que é uma peça separada do projeto. Trocar
`get_patient` por uma consulta ao índice dinâmico real não muda o resto do
grafo — as duas branches (com/sem exame pendente) continuam as mesmas.
"""

MOCK_PATIENTS = {
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
    return MOCK_PATIENTS.get(patient_id)
