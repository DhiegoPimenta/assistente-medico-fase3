"""Expande o dataset sintético (protocolos, FAQs, laudos) usando a API da
Anthropic, tomando os exemplos já existentes em data/raw/*.jsonl como guia
de tom e formato.

Uso:
    export ANTHROPIC_API_KEY=sk-ant-...
    python generate_synthetic_data.py --categoria faqs --n 20
    python generate_synthetic_data.py --categoria protocolos --n 5
    python generate_synthetic_data.py --categoria laudos --n 3

Os novos exemplos são anexados ao respectivo arquivo em data/raw/, sempre
passando antes por anonymize.anonymize_text como camada extra de segurança.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anonymize import anonymize_text  # noqa: E402
from hospital_profile import ESPECIALIDADES, HOSPITAL_NOME  # noqa: E402

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

MODEL = "claude-sonnet-5"

PROMPTS = {
    "faqs": """Você gera dados sintéticos de treino para o assistente médico virtual do \
{hospital}, um hospital fictício. Gere {n} novos pares de pergunta e resposta no estilo \
de perguntas frequentes que um médico faria ao assistente, cobrindo temas clínicos gerais \
das especialidades: {especialidades}. As respostas devem ser tecnicamente corretas, \
objetivas, e sempre que envolverem conduta terapêutica devem deixar claro que a sugestão \
depende de validação médica. Não inclua nomes de pacientes reais nem dados de identificação.

Exemplos do estilo esperado:
{exemplos}

Responda APENAS com uma lista JSON de objetos no formato:
[{{"instrucao": "...", "resposta": "...", "fonte": "geral"}}]""",
    "protocolos": """Você gera protocolos clínicos sintéticos para o {hospital}, um hospital \
fictício, no mesmo estilo dos exemplos abaixo (objetivo, critérios, conduta escalonada, \
quando acionar alerta, observação sobre validação médica obrigatória). Gere {n} novos \
protocolos sobre temas clínicos ainda não cobertos, das especialidades: {especialidades}.

Exemplos do estilo esperado:
{exemplos}

Responda APENAS com uma lista JSON de objetos no formato:
[{{"id": "slug_curto", "titulo": "...", "especialidade": "...", "texto": "..."}}]""",
    "laudos": """Você gera modelos (templates) sintéticos de documentos clínicos para o \
{hospital}, um hospital fictício, no mesmo estilo dos exemplos abaixo — apenas a \
ESTRUTURA/FORMATO do documento, com placeholders entre colchetes, nunca dados reais de \
paciente. Gere {n} novos modelos de documentos ainda não cobertos.

Exemplos do estilo esperado:
{exemplos}

Responda APENAS com uma lista JSON de objetos no formato:
[{{"tipo": "slug_curto", "titulo": "...", "texto": "..."}}]""",
}

FILES = {
    "faqs": RAW_DIR / "faqs.jsonl",
    "protocolos": RAW_DIR / "protocolos.jsonl",
    "laudos": RAW_DIR / "laudos_templates.jsonl",
}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _call_claude(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente
    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    if message.stop_reason == "max_tokens":
        raise RuntimeError(
            "Resposta cortada por limite de tokens (max_tokens=8192). "
            "Rode novamente com --n menor para esta categoria."
        )
    for block in message.content:
        if block.type == "text":
            return block.text
    raise RuntimeError("Resposta da API não contém bloco de texto.")


def generate(categoria: str, n: int) -> list[dict]:
    existing = _read_jsonl(FILES[categoria])
    exemplos = json.dumps(existing[:3], ensure_ascii=False, indent=2)

    prompt = PROMPTS[categoria].format(
        hospital=HOSPITAL_NOME,
        especialidades=", ".join(ESPECIALIDADES),
        n=n,
        exemplos=exemplos,
    )

    raw_response = _call_claude(prompt)
    # tolera bloco ```json ... ``` na resposta
    raw_response = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    novos = json.loads(raw_response)

    text_field = "resposta" if categoria == "faqs" else "texto"
    total_pii = {}
    for item in novos:
        item[text_field], counts = anonymize_text(item[text_field])
        for k, v in counts.items():
            total_pii[k] = total_pii.get(k, 0) + v
    if total_pii:
        print(f"[aviso] padrões de PII removidos durante geração: {total_pii}")

    return novos


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", choices=list(FILES), required=True)
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Defina a variável de ambiente ANTHROPIC_API_KEY antes de rodar este script.")

    novos = generate(args.categoria, args.n)

    path = FILES[args.categoria]
    with path.open("a", encoding="utf-8") as f:
        for item in novos:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"{len(novos)} novos exemplos adicionados a {path}")


if __name__ == "__main__":
    main()
