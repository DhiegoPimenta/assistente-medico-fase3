import json

from finetuning.data_prep.anonymize import anonymize_file, anonymize_text


def test_anonymize_text_removes_cpf():
    text, counts = anonymize_text("Paciente com CPF 123.456.789-00 foi admitido.")
    assert "123.456.789-00" not in text
    assert "[DADO_REMOVIDO:CPF]" in text
    assert counts["CPF"] == 1


def test_anonymize_text_removes_email():
    text, counts = anonymize_text("Contato: paciente@exemplo.com para retorno.")
    assert "paciente@exemplo.com" not in text
    assert counts["EMAIL"] == 1


def test_anonymize_text_removes_multiple_patterns():
    text, counts = anonymize_text(
        "CPF 111.222.333-44, telefone (11) 91234-5678, e-mail x@y.com"
    )
    assert counts["CPF"] == 1
    assert counts["TELEFONE"] == 1
    assert counts["EMAIL"] == 1


def test_anonymize_text_leaves_clean_text_unchanged():
    text = "Protocolo institucional de manejo de sepse, sem dados pessoais."
    result, counts = anonymize_text(text)
    assert result == text
    assert counts == {}


def test_anonymize_file_scrubs_all_configured_fields(tmp_path):
    path = tmp_path / "faqs.jsonl"
    rows = [
        {"instrucao": "Pergunta sem PII", "resposta": "Resposta sem PII", "fonte": "geral"},
        {
            "instrucao": "Qual o contato do paciente CPF 123.456.789-00?",
            "resposta": "Contato: paciente@exemplo.com",
            "fonte": "geral",
        },
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    counts = anonymize_file(str(path))

    assert counts["CPF"] == 1
    assert counts["EMAIL"] == 1

    saved_rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert "123.456.789-00" not in saved_rows[1]["instrucao"]
    assert "paciente@exemplo.com" not in saved_rows[1]["resposta"]
    assert saved_rows[0] == rows[0]
