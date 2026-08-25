# Assistente Médico Virtual — Hospital Vida Nova

Tech Challenge Fase 3 (Pós-Tech IA para Devs) — assistente virtual para um hospital
fictício que combina **fine-tuning LoRA**, **RAG** (LangChain) e um **fluxo de decisão
automatizado** (LangGraph), com guardrails de segurança e auditoria.

> Todo o dataset é sintético/anonimizado desde a origem — nenhum dado real de
> paciente é usado em nenhuma etapa. Veja [docs/arquitetura.md](docs/arquitetura.md)
> para o documento completo de arquitetura e decisões de projeto.

## Status

- [x] Dataset sintético (protocolos, FAQs, modelos de documento) — `data/`
- [x] Pipeline de geração/anonimização de dados — `finetuning/data_prep/`
- [x] Fine-tuning LoRA (Llama 3.2 3B + Unsloth, GPU T4 no Colab) — `finetuning/train/`
- [x] Avaliação modelo base vs. fine-tunado — `finetuning/eval/`
- [ ] Pipeline RAG + LangChain
- [ ] Fluxo de decisão LangGraph
- [ ] Guardrails determinísticos + logging/auditoria
- [ ] Aplicação Streamlit
- [ ] Infraestrutura Azure + Terraform
- [ ] Relatório técnico + vídeo de demonstração

## Estrutura

```
/data           dataset sintético (raw + processado para treino)
/finetuning     pipeline de fine-tuning: data_prep, train, eval
/docs           documento de arquitetura e relatório técnico
/app            (em construção) aplicação Streamlit + RAG + LangGraph
/infra          (em construção) Terraform (Azure)
```

## Fine-tuning — resumo

Modelo `Llama-3.2-3B-Instruct` (4-bit) + LoRA via [Unsloth](https://github.com/unslothai/unsloth),
treinado em GPU T4 gratuita do Google Colab. Detalhes, resultados de avaliação e
decisões (ex.: escolha do checkpoint por overfitting) em
[finetuning/README.md](finetuning/README.md) e
[finetuning/eval/outputs/eval_report.md](finetuning/eval/outputs/eval_report.md).

## Rodando localmente

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r finetuning/data_prep/requirements.txt
pip install -r finetuning/eval/requirements.txt

python finetuning/data_prep/format_dataset.py   # gera data/processed/*.jsonl
```

O treino (`finetuning/train/train_lora.py`) precisa de GPU — ver instruções em
[finetuning/train/requirements.txt](finetuning/train/requirements.txt).
