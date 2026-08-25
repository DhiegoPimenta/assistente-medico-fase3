# Assistente Médico Virtual — Hospital Vida Nova

Tech Challenge Fase 3 (Pós-Tech IA para Devs) — assistente virtual para um hospital
fictício que combina **fine-tuning LoRA**, **RAG** (LangChain) e um **fluxo de decisão
automatizado** (LangGraph), com guardrails de segurança e auditoria.

> Todo o dataset é sintético/anonimizado desde a origem — nenhum dado real de
> paciente é usado em nenhuma etapa. Veja [docs/arquitetura.md](docs/arquitetura.md)
> para o documento de arquitetura e [docs/relatorio.md](docs/relatorio.md)
> para o relatório técnico (fine-tuning, avaliação, RAG, LangGraph).

## Status

- [x] Dataset sintético (protocolos, FAQs, modelos de documento) — `data/`
- [x] Pipeline de geração/anonimização de dados — `finetuning/data_prep/`
- [x] Fine-tuning LoRA (Llama 3.2 3B + Unsloth, GPU T4 no Colab) — `finetuning/train/`
- [x] Avaliação modelo base vs. fine-tunado — `finetuning/eval/`
- [x] Pipeline RAG + LangChain (índice estático + dinâmico, busca híbrida) — `app/core/`
- [x] Fluxo de decisão LangGraph — `app/core/langgraph_flow.py`
- [x] Guardrails determinísticos + logging/auditoria — `app/core/guardrails.py`, `app/core/logging_config.py`
- [x] Aplicação Streamlit (chat, upload de protocolo/prontuário, consulta por paciente, auditoria) — `app/`
- [x] Suite de testes (38 testes) — `tests/`
- [x] Relatório técnico — [`docs/relatorio.md`](docs/relatorio.md)
- [x] Infraestrutura Azure + Terraform — [`infra/`](infra/), deploy real testado e funcionando
- [ ] Vídeo de demonstração — roteiro pronto em [`examples/ROTEIRO_VIDEO.md`](examples/ROTEIRO_VIDEO.md)

## Estrutura

```
/data           dataset sintético (raw + processado para treino) e índices vetoriais
/finetuning     pipeline de fine-tuning: data_prep, train, eval
/docs           documento de arquitetura e relatório técnico
/app            aplicação Streamlit + RAG (LangChain) + fluxo de decisão (LangGraph)
  /core           ingestão, chain RAG, guardrails, logging, grafo de decisão
  /pages          páginas do Streamlit (chat, uploads, consulta, auditoria)
/tests          testes unitários (guardrails, logging, anonimização, RAG, grafo)
/infra          Terraform (Azure) — Container Apps, ACR, Key Vault, budget alert
```

## Infraestrutura (Azure + Terraform)

Deploy completo testado na assinatura Azure for Students: Container Apps
(Consumption, scale-to-zero), Container Registry, Key Vault (segredo via
managed identity, sem chave hardcoded), Storage Account, budget alert. Passo
a passo reproduzível em [infra/DEPLOY.md](infra/DEPLOY.md).

> ⚠️ O ambiente de deploy fica com ingress público e sem autenticação — a URL
> não é publicada aqui de propósito (evita alguém de fora consumir a API paga
> da Anthropic). Rode `terraform output streamlit_url` com acesso à
> assinatura, ou veja o vídeo de demonstração.

## Aplicação Streamlit

```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

Cinco abas: **Chat Geral** (RAG sobre protocolos institucionais), **Upload de
Protocolo** (cresce o índice estático), **Upload de Prontuário** (cresce o
índice dinâmico e já dispara o fluxo LangGraph — classifica intenção, verifica
exame pendente, emite alerta ou sugere conduta cruzando prontuário + protocolo),
**Consulta por Paciente** e **Painel de Auditoria**.

Roteiro de testes com perguntas e arquivos prontos:
[examples/GUIA_DE_TESTES.md](examples/GUIA_DE_TESTES.md).

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

pip install -r requirements-dev.txt
pytest   # 38 testes, sem precisar de API/GPU
```

O treino (`finetuning/train/train_lora.py`) precisa de GPU — ver instruções em
[finetuning/train/requirements.txt](finetuning/train/requirements.txt).
