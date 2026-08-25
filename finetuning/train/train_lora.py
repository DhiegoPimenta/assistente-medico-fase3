"""Fine-tuning LoRA do modelo base sobre o dataset sintético do Hospital Vida Nova.

Roda em GPU única (T4 do Colab gratuito). Configuração em config.yaml na mesma pasta.

Uso (dentro de uma sessão Colab com GPU, a partir da raiz do projeto em /content):
    python finetuning/train/train_lora.py

Caminhos são resolvidos a partir do diretório de trabalho atual (não de __file__),
porque o `colab exec` transmite o código para o kernel remoto e o executa como se
fosse colado numa célula — não existe um arquivo real no disco remoto nesse caso.
"""

from pathlib import Path

import yaml
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer
from unsloth import FastLanguageModel, is_bfloat16_supported

ROOT = Path.cwd()
CONFIG_PATH = ROOT / "finetuning" / "train" / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["model"]["name"],
        max_seq_length=cfg["model"]["max_seq_length"],
        load_in_4bit=cfg["model"]["load_in_4bit"],
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["lora_alpha"],
        lora_dropout=cfg["lora"]["lora_dropout"],
        target_modules=cfg["lora"]["target_modules"],
        bias=cfg["lora"]["bias"],
        use_gradient_checkpointing="unsloth",
        random_state=cfg["training"]["seed"],
    )

    template = cfg["prompt_template"]

    def format_example(example: dict) -> dict:
        text = template.format(instruction=example["instruction"], output=example["output"])
        return {"text": text + tokenizer.eos_token}

    train_ds = load_dataset("json", data_files=str(ROOT / cfg["data"]["train_path"]))["train"]
    val_ds = load_dataset("json", data_files=str(ROOT / cfg["data"]["val_path"]))["train"]
    train_ds = train_ds.map(format_example)
    val_ds = val_ds.map(format_example)

    output_dir = ROOT / cfg["training"]["output_dir"]

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        dataset_text_field="text",
        max_seq_length=cfg["model"]["max_seq_length"],
        args=SFTConfig(
            output_dir=str(output_dir),
            num_train_epochs=cfg["training"]["num_train_epochs"],
            per_device_train_batch_size=cfg["training"]["per_device_train_batch_size"],
            gradient_accumulation_steps=cfg["training"]["gradient_accumulation_steps"],
            learning_rate=cfg["training"]["learning_rate"],
            warmup_ratio=cfg["training"]["warmup_ratio"],
            logging_steps=cfg["training"]["logging_steps"],
            save_strategy=cfg["training"]["save_strategy"],
            eval_strategy=cfg["training"]["eval_strategy"],
            optim=cfg["training"]["optim"],
            seed=cfg["training"]["seed"],
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            load_best_model_at_end=cfg["training"].get("load_best_model_at_end", False),
            metric_for_best_model=cfg["training"].get("metric_for_best_model"),
            greater_is_better=cfg["training"].get("greater_is_better"),
            report_to="none",
        ),
    )

    trainer.train()

    adapter_dir = output_dir / "final"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    print(f"Adapter LoRA salvo em {adapter_dir}")


if __name__ == "__main__":
    main()
