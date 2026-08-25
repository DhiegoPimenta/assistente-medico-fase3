"""Logging estruturado de auditoria — cada interação do assistente é
registrada para rastreabilidade e explainability (seção 4.4 do documento de
arquitetura).

Formato local (JSONL) por padrão, sem dependência de nuvem — troque por Azure
Application Insights / Table Storage na versão publicada, mantendo a mesma
assinatura de `log_interaction`.
"""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "logs" / "audit.jsonl"


def log_interaction(
    *,
    usuario: str,
    pergunta: str,
    resposta: str,
    fontes: list[str],
    guardrail_acionado: bool,
    guardrail_motivo: str | None = None,
    paciente_id: str | None = None,
) -> str:
    """Grava uma interação no log de auditoria. Retorna o id do registro."""
    record_id = str(uuid.uuid4())
    record = {
        "id": record_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "usuario": usuario,
        "paciente_id": paciente_id,
        "pergunta": pergunta,
        "resposta": resposta,
        "fontes": fontes,
        "guardrail_acionado": guardrail_acionado,
        "guardrail_motivo": guardrail_motivo,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record_id


def read_audit_log() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
