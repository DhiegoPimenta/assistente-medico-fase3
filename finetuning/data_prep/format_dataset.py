"""Converte os dados sintéticos brutos (data/raw/*.jsonl) em pares
instrução/resposta no formato Alpaca, prontos para o fine-tuning LoRA.

Fontes:
  - faqs.jsonl            -> já são pares instrução/resposta, usados direto
  - protocolos.jsonl      -> geram pares a partir de templates de pergunta
  - laudos_templates.jsonl -> geram pares a partir de templates de pergunta

Saída: data/processed/train.jsonl e data/processed/val.jsonl
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hospital_profile import HOSPITAL_NOME  # noqa: E402

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

VAL_SPLIT = 0.1
SEED = 42

PROTOCOLO_PERGUNTAS = [
    "Qual o protocolo do {hospital} para {titulo}?",
    "Descreva a conduta institucional do {hospital} sobre {titulo}.",
]

LAUDO_PERGUNTAS = [
    "Qual o modelo de {titulo} usado no {hospital}?",
    "Como é o formato padrão de {titulo} do {hospital}?",
]


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_examples() -> list[dict]:
    examples: list[dict] = []

    for row in _read_jsonl(RAW_DIR / "faqs.jsonl"):
        examples.append(
            {
                "instruction": row["instrucao"],
                "input": "",
                "output": row["resposta"],
                "source": f"faq:{row.get('fonte', 'geral')}",
            }
        )

    for row in _read_jsonl(RAW_DIR / "protocolos.jsonl"):
        template = random.choice(PROTOCOLO_PERGUNTAS)
        examples.append(
            {
                "instruction": template.format(hospital=HOSPITAL_NOME, titulo=row["titulo"]),
                "input": "",
                "output": row["texto"],
                "source": f"protocolo:{row['id']}",
            }
        )

    for row in _read_jsonl(RAW_DIR / "laudos_templates.jsonl"):
        template = random.choice(LAUDO_PERGUNTAS)
        examples.append(
            {
                "instruction": template.format(hospital=HOSPITAL_NOME, titulo=row["titulo"]),
                "input": "",
                "output": row["texto"],
                "source": f"laudo:{row['tipo']}",
            }
        )

    return examples


def main() -> None:
    random.seed(SEED)
    examples = build_examples()
    random.shuffle(examples)

    n_val = max(1, int(len(examples) * VAL_SPLIT))
    val, train = examples[:n_val], examples[n_val:]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train.jsonl", train), ("val.jsonl", val)):
        with (OUT_DIR / name).open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Total de exemplos: {len(examples)}")
    print(f"  train.jsonl: {len(train)} exemplos -> {OUT_DIR / 'train.jsonl'}")
    print(f"  val.jsonl:   {len(val)} exemplos -> {OUT_DIR / 'val.jsonl'}")


if __name__ == "__main__":
    main()
