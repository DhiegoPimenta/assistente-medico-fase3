"""Guardrail determinístico contra prescrição/decisão clínica definitiva.

Não depende do modelo "lembrar" de incluir a ressalva de validação médica — é
uma regra aplicada sobre o texto de saída, não uma instrução de prompt. Isso
importa de verdade: no relatório de avaliação
(finetuning/eval/outputs/eval_report.md) o modelo fine-tunado só mencionou
"validação médica" por conta própria em 12% das respostas.
"""

import re
from dataclasses import dataclass

VALIDATION_DISCLAIMER = (
    "\n\n⚠️ Esta é uma sugestão baseada em protocolo institucional e/ou "
    "conhecimento médico geral — não constitui prescrição ou conduta válida. "
    "Exige validação e assinatura de um médico responsável antes de qualquer "
    "execução."
)

# número + unidade farmacológica/posológica comum
_DOSAGE_PATTERN = re.compile(
    r"\b\d+([.,]\d+)?\s*(mg|mcg|µg|ml|mL|g|UI|U|mEq|mmol|gotas?|comprimidos?)\b",
    re.IGNORECASE,
)

# verbos de execução/administração direta
_IMPERATIVE_PATTERN = re.compile(
    r"\b(administr\w+|aplic\w+|prescrev\w+|inject\w+|infundi\w+)\b", re.IGNORECASE
)

_VALIDATION_MENTIONED_PATTERN = re.compile(
    r"valida(ç|c)[aã]o m[ée]dica|m[ée]dico respons[aá]vel|sujeit[ao] a valida",
    re.IGNORECASE,
)


@dataclass
class GuardrailResult:
    text: str
    triggered: bool
    reason: str | None = None


def contains_direct_prescription(text: str) -> bool:
    """True se o texto tiver padrão de dosagem + verbo de administração direta."""
    return bool(_DOSAGE_PATTERN.search(text)) and bool(_IMPERATIVE_PATTERN.search(text))


def mentions_validation(text: str) -> bool:
    return bool(_VALIDATION_MENTIONED_PATTERN.search(text))


def apply_guardrail(text: str) -> GuardrailResult:
    """Garante que toda resposta com sinal de prescrição direta carregue a
    ressalva de validação médica — de forma determinística, não opcional.

    Não reescreve o conteúdo clínico da resposta (isso é responsabilidade da
    RAG chain); apenas garante que a ressalva esteja presente sempre que
    houver padrão de prescrição direta, ou quando o modelo simplesmente não
    a incluiu por conta própria.
    """
    has_prescription = contains_direct_prescription(text)
    already_validated = mentions_validation(text)

    if already_validated:
        return GuardrailResult(text=text, triggered=has_prescription, reason=(
            "padrão de prescrição direta detectado (dosagem + verbo de administração)"
            if has_prescription else None
        ))

    reason = (
        "padrão de prescrição direta sem ressalva de validação médica"
        if has_prescription
        else "resposta clínica sem menção à validação médica"
    )
    return GuardrailResult(
        text=text.rstrip() + VALIDATION_DISCLAIMER,
        triggered=True,
        reason=reason,
    )
