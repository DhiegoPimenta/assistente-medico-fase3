"""Gera respostas do modelo BASE e do modelo FINE-TUNADO para as perguntas de
validação, para comparação posterior em evaluate_model.py.

Roda em GPU (Colab), a partir da raiz do projeto em /content:
    python finetuning/eval/generate_responses.py
"""

import gc
import json
from pathlib import Path

import torch
import yaml
from unsloth import FastLanguageModel

ROOT = Path.cwd()
CONFIG_PATH = ROOT / "finetuning" / "train" / "config.yaml"
VAL_PATH = ROOT / "data" / "processed" / "val.jsonl"
ADAPTER_PATH = ROOT / "finetuning" / "train" / "adapters" / "hospital-vida-nova-lora" / "checkpoint-27"
OUT_PATH = ROOT / "finetuning" / "eval" / "outputs" / "responses.json"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_val() -> list[dict]:
    with open(VAL_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def generate(model, tokenizer, instruction: str, max_new_tokens: int = 400) -> str:
    FastLanguageModel.for_inference(model)
    messages = [{"role": "user", "content": instruction}]
    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    outputs = model.generate(
        input_ids=inputs,
        max_new_tokens=max_new_tokens,
        use_cache=True,
        temperature=0.3,
        do_sample=True,
    )
    text = tokenizer.decode(outputs[0][inputs.shape[1] :], skip_special_tokens=True)
    return text.strip()


def run_pass(model_name: str, cfg: dict, val: list[dict], label: str) -> list[str]:
    print(f"Carregando modelo ({label})...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=cfg["model"]["max_seq_length"],
        load_in_4bit=cfg["model"]["load_in_4bit"],
    )

    responses = []
    for row in val:
        resp = generate(model, tokenizer, row["instruction"])
        responses.append(resp)
        print(f"[{label}] {row['instruction'][:60]}... -> {resp[:80]}...")

    del model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    return responses


def main() -> None:
    cfg = load_config()
    val = load_val()

    base_responses = run_pass(cfg["model"]["name"], cfg, val, "base")
    ft_responses = run_pass(str(ADAPTER_PATH), cfg, val, "fine-tuned")

    results = []
    for row, base_r, ft_r in zip(val, base_responses, ft_responses):
        results.append(
            {
                "instruction": row["instruction"],
                "reference": row["output"],
                "base_response": base_r,
                "finetuned_response": ft_r,
                "source": row.get("source", ""),
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Resultados salvos em {OUT_PATH}")


if __name__ == "__main__":
    main()
