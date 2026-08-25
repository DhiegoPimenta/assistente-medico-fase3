import json

from app.core import logging_config


def test_log_interaction_writes_expected_fields(tmp_path, monkeypatch):
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    record_id = logging_config.log_interaction(
        usuario="dr_teste",
        pergunta="Qual o protocolo de sepse?",
        resposta="Aplicar qSOFA...",
        fontes=["Protocolo de Identificação e Manejo Inicial de Sepse"],
        guardrail_acionado=True,
        guardrail_motivo="padrão de prescrição direta sem ressalva",
    )

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["id"] == record_id
    assert record["usuario"] == "dr_teste"
    assert record["pergunta"] == "Qual o protocolo de sepse?"
    assert record["fontes"] == ["Protocolo de Identificação e Manejo Inicial de Sepse"]
    assert record["guardrail_acionado"] is True
    assert "timestamp" in record
    assert record["paciente_id"] is None


def test_log_interaction_appends_multiple_records(tmp_path, monkeypatch):
    log_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    for i in range(3):
        logging_config.log_interaction(
            usuario="dr_teste",
            pergunta=f"pergunta {i}",
            resposta="resposta",
            fontes=[],
            guardrail_acionado=False,
        )

    records = logging_config.read_audit_log()
    assert len(records) == 3
    assert [r["pergunta"] for r in records] == ["pergunta 0", "pergunta 1", "pergunta 2"]


def test_read_audit_log_returns_empty_list_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "does_not_exist.jsonl")
    assert logging_config.read_audit_log() == []
