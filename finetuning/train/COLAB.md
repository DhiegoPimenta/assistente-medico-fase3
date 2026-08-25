# Rodando o fine-tuning no Google Colab (GPU T4 gratuita)

Usamos a [Colab CLI oficial](https://github.com/googlecolab/google-colab-cli)
(`google-colab-cli`) para provisionar a GPU e rodar o treino direto do terminal,
sem depender do notebook do navegador. **Só roda em Linux/macOS** — no Windows,
use WSL2.

## 1. Instalar a CLI

```bash
# instala o uv (gerenciador de pacotes Python, sem sudo)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env

# instala o colab-cli
# nota: a versão 0.6.0 tem uma dependência quebrada (jupyter-kernel-client 1.0.0
# renomeou a classe KernelClient) — fixamos a última versão compatível
uv tool install google-colab-cli --with jupyter-kernel-client==0.15.0
```

## 2. Autenticar e provisionar a sessão

```bash
colab new -s train --gpu T4   # abre o fluxo OAuth na primeira vez (visite a URL, cole o código)
```

## 3. Instalar as dependências de treino

`colab install -r` tem timeout fixo de 30s — pouco pra instalar o Unsloth (que
compila/baixa bastante coisa). Em vez disso, suba o requirements.txt e instale
via `colab exec` com timeout maior:

```bash
colab upload finetuning/train/requirements.txt /content/requirements.txt -s train
echo '%pip install -q -r /content/requirements.txt' | colab exec -s train --timeout 900
```

## 4. Subir os dados e a config

```bash
# os diretórios remotos precisam existir antes do upload
echo 'import os; os.makedirs("/content/data/processed", exist_ok=True); os.makedirs("/content/finetuning/train", exist_ok=True)' | colab exec -s train --timeout 30

colab upload data/processed/train.jsonl /content/data/processed/train.jsonl -s train
colab upload data/processed/val.jsonl /content/data/processed/val.jsonl -s train
colab upload finetuning/train/config.yaml /content/finetuning/train/config.yaml -s train
```

## 5. Rodar o treino

```bash
colab exec -s train -f finetuning/train/train_lora.py --timeout 900
```

Leva ~3min pros 80 exemplos do dataset atual. O adapter LoRA fica salvo em
`/content/finetuning/train/adapters/hospital-vida-nova-lora/` (um checkpoint por
época, mais uma pasta `final/`).

## 6. Baixar o resultado

`colab download` falha (HTTP 400) em arquivos grandes (o `adapter_model.safetensors`
tem ~97MB). Duas opções:

- **Arquivos pequenos** (`adapter_config.json`, `tokenizer.json`, etc.): `colab download`
  funciona normalmente.
- **Adapter completo**: zipe no VM antes de baixar, ou simplesmente rode a próxima
  etapa (avaliação) **na mesma sessão**, sem precisar mover o adapter pra fora do Colab
  (é o que `finetuning/eval/generate_responses.py` espera — mesma sessão que treinou).

```bash
echo 'import shutil; shutil.make_archive("/content/adapter", "zip", "finetuning/train/adapters/hospital-vida-nova-lora/checkpoint-27")' | colab exec -s train --timeout 60
colab download /content/adapter.zip finetuning/train/adapters/adapter.zip -s train
```

## 7. Parar a sessão

**Sempre pare a sessão depois de terminar** — é o que evita gastar crédito à toa:

```bash
colab stop -s train
```

## Notas / pegadinhas encontradas

- **`bf16`/`fp16`**: uma atualização recente do `trl`/`transformers` passou a exigir
  precisão mista explícita — T4 (arquitetura Turing) não suporta `bf16`. O
  `train_lora.py` já resolve isso com `unsloth.is_bfloat16_supported()`.
- **`colab exec` sem `__file__` real**: o código é transmitido e executado como se
  fosse colado numa célula — não existe um arquivo real no disco remoto. Por isso
  os scripts resolvem caminhos a partir de `Path.cwd()` (que o CLI já configura como
  `/content`), nunca de `Path(__file__)`.
- **Escolha do checkpoint**: o treino sofre overfitting a partir da época 4 com esse
  dataset pequeno — sempre conferir a validation loss por época e usar
  `load_best_model_at_end` (já configurado em `config.yaml`) em vez do checkpoint final.
