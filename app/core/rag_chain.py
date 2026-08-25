"""Chain RAG conversacional sobre o índice estático (protocolos institucionais),
com citação explícita da fonte (explainability).

O modelo gerador aqui é o Claude (via API), como stand-in de desenvolvimento —
na versão final ele é substituído pelo modelo fine-tunado servido localmente
(ver seção 3 do documento de arquitetura). O guardrail de prescrição/decisão
definitiva é aplicado como uma etapa determinística separada, em
app/core/guardrails.py, sobre a resposta gerada por esta chain — nunca dependa
só do prompt para bloquear isso.
"""

from dataclasses import dataclass, field

from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document

from .guardrails import apply_guardrail
from .ingestion import get_static_retriever
from .logging_config import log_interaction

SYSTEM_PROMPT = """Você é o assistente médico virtual do Hospital Vida Nova. \
Responda SOMENTE com base nos trechos de contexto fornecidos abaixo — não use \
conhecimento próprio para inventar condutas institucionais.

Regras:
1. Se o contexto não contiver a informação pedida, diga isso claramente em vez \
de inventar.
2. Sempre indique de qual protocolo/documento a informação foi retirada (cite o \
título exato do documento entre colchetes, ex.: [Protocolo de Manejo de Sepse]).
3. Nunca apresente uma conduta terapêutica como definitiva — deixe explícito que \
está sujeita a validação de um médico responsável antes de qualquer execução.

CONTEXTO:
{context}

PERGUNTA: {question}"""


@dataclass
class RAGResult:
    answer: str
    source_documents: list[Document] = field(default_factory=list)
    guardrail_triggered: bool = False
    guardrail_reason: str | None = None
    log_id: str | None = None


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-5", max_tokens=1024)


def format_context(docs: list[Document]) -> str:
    parts = []
    for doc in docs:
        titulo = doc.metadata.get("titulo", doc.metadata.get("source_id", "documento"))
        parts.append(f"[{titulo}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def extract_text(content) -> str:
    """`ChatAnthropic` retorna `content` como string simples ou, quando o
    modelo usa extended thinking, como lista de blocos (thinking + text) —
    aqui isolamos só o texto final."""
    if isinstance(content, str):
        return content
    parts = [block["text"] for block in content if isinstance(block, dict) and block.get("type") == "text"]
    return "\n".join(parts)


def answer_question(question: str, k: int = 3, usuario: str = "dev") -> RAGResult:
    retriever = get_static_retriever(k=k)
    docs = retriever.invoke(question)

    context = format_context(docs) if docs else "(nenhum documento institucional relevante encontrado)"
    prompt = SYSTEM_PROMPT.format(context=context, question=question)

    llm = get_llm()
    response = llm.invoke(prompt)
    raw_answer = extract_text(response.content)

    guardrail = apply_guardrail(raw_answer)
    fontes = [d.metadata.get("titulo", d.metadata.get("source_id", "?")) for d in docs]

    log_id = log_interaction(
        usuario=usuario,
        pergunta=question,
        resposta=guardrail.text,
        fontes=fontes,
        guardrail_acionado=guardrail.triggered,
        guardrail_motivo=guardrail.reason,
    )

    return RAGResult(
        answer=guardrail.text,
        source_documents=docs,
        guardrail_triggered=guardrail.triggered,
        guardrail_reason=guardrail.reason,
        log_id=log_id,
    )


if __name__ == "__main__":
    for pergunta in [
        "Qual o protocolo do Hospital Vida Nova para sepse?",
        "Quando devo acionar alerta em um paciente com suspeita de AVC?",
        "Qual a capital da França?",
    ]:
        print(f"\n=== {pergunta} ===")
        result = answer_question(pergunta)
        print(result.answer)
        print("Fontes:", [d.metadata.get("titulo") for d in result.source_documents])
