import json

from finetuning.data_prep import format_dataset


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


def test_build_examples_combines_all_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(format_dataset, "RAW_DIR", tmp_path)

    _write_jsonl(
        tmp_path / "faqs.jsonl",
        [{"instrucao": "Pergunta 1?", "resposta": "Resposta 1", "fonte": "sepse"}],
    )
    _write_jsonl(
        tmp_path / "protocolos.jsonl",
        [{"id": "sepse", "titulo": "Protocolo de Sepse", "especialidade": "Emergência", "texto": "conduta X"}],
    )
    _write_jsonl(
        tmp_path / "laudos_templates.jsonl",
        [{"tipo": "receita", "titulo": "Modelo de Receita", "texto": "formato Y"}],
    )

    examples = format_dataset.build_examples()

    assert len(examples) == 3
    sources = {e["source"] for e in examples}
    assert sources == {"faq:sepse", "protocolo:sepse", "laudo:receita"}

    faq_example = next(e for e in examples if e["source"] == "faq:sepse")
    assert faq_example["instruction"] == "Pergunta 1?"
    assert faq_example["output"] == "Resposta 1"
    assert faq_example["input"] == ""

    protocolo_example = next(e for e in examples if e["source"] == "protocolo:sepse")
    assert "Protocolo de Sepse" in protocolo_example["instruction"]
    assert protocolo_example["output"] == "conduta X"


def test_build_examples_handles_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(format_dataset, "RAW_DIR", tmp_path)
    assert format_dataset.build_examples() == []


def test_main_writes_train_val_split(tmp_path, monkeypatch):
    monkeypatch.setattr(format_dataset, "RAW_DIR", tmp_path)
    out_dir = tmp_path / "processed"
    monkeypatch.setattr(format_dataset, "OUT_DIR", out_dir)

    faqs = [
        {"instrucao": f"Pergunta {i}?", "resposta": f"Resposta {i}", "fonte": "geral"}
        for i in range(10)
    ]
    _write_jsonl(tmp_path / "faqs.jsonl", faqs)

    format_dataset.main()

    train = (out_dir / "train.jsonl").read_text(encoding="utf-8").strip().splitlines()
    val = (out_dir / "val.jsonl").read_text(encoding="utf-8").strip().splitlines()

    assert len(train) + len(val) == 10
    assert len(val) == 1  # VAL_SPLIT=0.1 sobre 10 exemplos
