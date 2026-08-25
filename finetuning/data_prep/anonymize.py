"""Camada de segurança: varre texto em busca de padrões de dado pessoal real
(CPF, RG, telefone, e-mail, CEP) e substitui por marcadores.

Os dados deste projeto já nascem sintéticos (Synthea + gerados via LLM), mas
este módulo roda como rede de segurança final antes de qualquer texto entrar
no dataset de treino ou no índice RAG — inclusive sobre documentos que
usuários do hospital venham a enviar pelo Streamlit no futuro.
"""

import re

_PATTERNS = {
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "RG": re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]\b"),
    "TELEFONE": re.compile(r"\b(?:\(\d{2}\)\s?)?\d{4,5}-?\d{4}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "CEP": re.compile(r"\b\d{5}-?\d{3}\b"),
}


def anonymize_text(text: str) -> tuple[str, dict[str, int]]:
    """Substitui padrões de PII pelo marcador [DADO_REMOVIDO:<TIPO>].

    Retorna o texto tratado e um dicionário com a contagem de ocorrências
    por tipo de padrão encontrado (útil para auditoria do dataset).
    """
    counts: dict[str, int] = {}
    for label, pattern in _PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            counts[label] = len(matches)
            text = pattern.sub(f"[DADO_REMOVIDO:{label}]", text)
    return text, counts


def anonymize_file(path: str) -> dict[str, int]:
    """Aplica anonymize_text a um arquivo .jsonl (campo 'texto' ou 'resposta') in-place.

    Retorna contagem total de ocorrências encontradas no arquivo inteiro.
    """
    import json

    total: dict[str, int] = {}
    lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            for field in ("texto", "resposta", "instrucao"):
                if field in obj and isinstance(obj[field], str):
                    obj[field], counts = anonymize_text(obj[field])
                    for k, v in counts.items():
                        total[k] = total.get(k, 0) + v
            lines.append(json.dumps(obj, ensure_ascii=False))

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return total


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python anonymize.py <arquivo.jsonl>")
        sys.exit(1)

    result = anonymize_file(sys.argv[1])
    if result:
        print(f"Padrões de PII encontrados e removidos em {sys.argv[1]}: {result}")
    else:
        print(f"Nenhum padrão de PII encontrado em {sys.argv[1]}.")
