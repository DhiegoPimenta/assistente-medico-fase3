"""Fluxo de decisão automatizado (LangGraph) — seção 4.2 do documento de
arquitetura.

    [pergunta] -> [classificador de intenção]
                        |
          +-------------+-------------+
     pergunta geral            pergunta sobre paciente
          |                             |
    [RAG estático]        [RAG dinâmico + verifica exame pendente]
          |                             |
          |                  +----------+----------+
          |                sim                    não
          |                  |                      |
          |           [emite alerta]      [sugere conduta c/ protocolo]
          |                  +----------+-----------+
          +-----------------------------+
                                   [guardrail]
                                         |
                                  [log de auditoria]
                                         |
                                   [resposta final]

O índice dinâmico já é real (Chroma, alimentado via upload no Streamlit — ver
app/core/ingestion.py), com fallback para pacientes de demonstração fixos em
app/core/patient_index.py enquanto a ingestão via Synthea não existe.
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .guardrails import apply_guardrail
from .logging_config import log_interaction
from .patient_index import get_patient
from .rag_chain import generate_raw_answer


class AssistantState(TypedDict, total=False):
    question: str
    patient_id: str | None
    usuario: str
    intent: str
    patient_summary: str | None
    exame_pendente: bool
    exame_pendente_desc: str | None
    answer: str
    sources: list[str]
    alert: str | None
    guardrail_triggered: bool
    guardrail_reason: str | None
    log_id: str | None


def classify_intent(state: AssistantState) -> dict:
    """'geral' ou 'paciente'. Regra determinística primeiro (patient_id
    explícito — é assim que a aba "Consulta por paciente" do Streamlit chama
    o grafo); fallback por palavra-chave para perguntas soltas."""
    if state.get("patient_id"):
        return {"intent": "paciente"}

    question_lower = state["question"].lower()
    if any(kw in question_lower for kw in ("o paciente", "esse paciente", "prontuário do")):
        return {"intent": "paciente"}

    return {"intent": "geral"}


def route_after_classify(state: AssistantState) -> Literal["static_rag", "dynamic_rag"]:
    return "dynamic_rag" if state["intent"] == "paciente" else "static_rag"


def static_rag_node(state: AssistantState) -> dict:
    answer, docs = generate_raw_answer(state["question"])
    return {
        "answer": answer,
        "sources": [d.metadata.get("titulo", "?") for d in docs],
    }


def dynamic_rag_node(state: AssistantState) -> dict:
    patient = get_patient(state["patient_id"])
    if patient is None:
        return {
            "patient_summary": None,
            "exame_pendente": False,
            "answer": f"Nenhum prontuário encontrado para o paciente '{state['patient_id']}'.",
            "sources": [],
        }
    return {
        "patient_summary": patient["prontuario"],
        "exame_pendente": patient["exame_pendente"],
        "exame_pendente_desc": patient.get("exame_pendente_desc"),
        "sources": [f"Prontuário do paciente {state['patient_id']}"],
    }


def route_after_dynamic_rag(state: AssistantState) -> Literal["emit_alert", "suggest_conduct", "guardrail"]:
    if state.get("patient_summary") is None:
        return "guardrail"  # paciente não encontrado — vai direto pro fechamento
    return "emit_alert" if state.get("exame_pendente") else "suggest_conduct"


def emit_alert_node(state: AssistantState) -> dict:
    alert = (
        f"ALERTA: paciente {state['patient_id']} possui exame pendente "
        f"({state.get('exame_pendente_desc') or 'sem descrição'}) — notificar "
        "equipe assistente antes de qualquer conduta."
    )
    answer = (
        f"{alert}\n\nResumo do prontuário: {state['patient_summary']}\n\n"
        "Aguardando resultado do exame pendente antes de sugerir conduta."
    )
    return {"alert": alert, "answer": answer}


def suggest_conduct_node(state: AssistantState) -> dict:
    question = (
        f'Com base neste resumo de prontuário: "{state["patient_summary"]}", '
        f"qual a conduta institucional recomendada? Pergunta original: {state['question']}"
    )
    answer, docs = generate_raw_answer(question)
    return {
        "answer": answer,
        "sources": state.get("sources", []) + [d.metadata.get("titulo", "?") for d in docs],
    }


def guardrail_node(state: AssistantState) -> dict:
    result = apply_guardrail(state["answer"])
    return {
        "answer": result.text,
        "guardrail_triggered": result.triggered,
        "guardrail_reason": result.reason,
    }


def log_node(state: AssistantState) -> dict:
    log_id = log_interaction(
        usuario=state.get("usuario", "dev"),
        pergunta=state["question"],
        resposta=state["answer"],
        fontes=state.get("sources", []),
        guardrail_acionado=state.get("guardrail_triggered", False),
        guardrail_motivo=state.get("guardrail_reason"),
        paciente_id=state.get("patient_id"),
    )
    return {"log_id": log_id}


def build_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("static_rag", static_rag_node)
    graph.add_node("dynamic_rag", dynamic_rag_node)
    graph.add_node("emit_alert", emit_alert_node)
    graph.add_node("suggest_conduct", suggest_conduct_node)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("log", log_node)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges("classify_intent", route_after_classify)
    graph.add_edge("static_rag", "guardrail")
    graph.add_conditional_edges("dynamic_rag", route_after_dynamic_rag)
    graph.add_edge("emit_alert", "guardrail")
    graph.add_edge("suggest_conduct", "guardrail")
    graph.add_edge("guardrail", "log")
    graph.add_edge("log", END)

    return graph.compile()


_GRAPH = None


def run(question: str, patient_id: str | None = None, usuario: str = "dev") -> AssistantState:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH.invoke({"question": question, "patient_id": patient_id, "usuario": usuario})


if __name__ == "__main__":
    print("=== Pergunta geral ===")
    r1 = run("Qual o protocolo do Hospital Vida Nova para sepse?")
    print(r1["answer"][:300], "\nFontes:", r1["sources"], "\nGuardrail:", r1["guardrail_triggered"])

    print("\n=== Paciente com exame pendente ===")
    r2 = run("O que o paciente tem?", patient_id="SIM-0001")
    print(r2["answer"], "\nAlerta:", r2.get("alert"))

    print("\n=== Paciente sem exame pendente ===")
    r3 = run("O que o paciente tem?", patient_id="SIM-0002")
    print(r3["answer"][:400], "\nFontes:", r3["sources"])

    print("\n=== Paciente inexistente ===")
    r4 = run("O que o paciente tem?", patient_id="SIM-9999")
    print(r4["answer"])
