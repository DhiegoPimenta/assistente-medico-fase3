import json

from app.core import ingestion


def test_add_static_document_appends_to_raw_file_and_returns_slug(tmp_path, monkeypatch):
    raw_path = tmp_path / "protocolos.jsonl"
    raw_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(ingestion, "PROTOCOLOS_PATH", raw_path)
    monkeypatch.setattr(ingestion, "STATIC_STORE_DIR", tmp_path / "static")

    source_id = ingestion.add_static_document(
        titulo="Protocolo de Teste Automatizado",
        texto="Conduta institucional de teste.",
        especialidade="Clínica Médica",
    )

    assert source_id == "protocolo_de_teste_automatizado"

    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["titulo"] == "Protocolo de Teste Automatizado"
    assert rows[0]["texto"] == "Conduta institucional de teste."


def test_add_static_document_anonymizes_before_saving(tmp_path, monkeypatch):
    raw_path = tmp_path / "protocolos.jsonl"
    raw_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(ingestion, "PROTOCOLOS_PATH", raw_path)
    monkeypatch.setattr(ingestion, "STATIC_STORE_DIR", tmp_path / "static")

    ingestion.add_static_document(
        titulo="Protocolo com CPF acidental",
        texto="Contato do responsável: CPF 111.222.333-44.",
    )

    saved = json.loads(raw_path.read_text(encoding="utf-8").strip())
    assert "111.222.333-44" not in saved["texto"]
    assert "[DADO_REMOVIDO:CPF]" in saved["texto"]
