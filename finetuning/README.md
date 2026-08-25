# Fine-tuning — Assistente Médico Virtual (Hospital Vida Nova)

## data_prep/

1. `data/raw/*.jsonl` já contém um dataset semente 100% sintético:
   - `protocolos.jsonl` — 8 protocolos clínicos institucionais
   - `faqs.jsonl` — 37 pares pergunta/resposta
   - `laudos_templates.jsonl` — 6 modelos de documentos (formato, sem conteúdo sensível)

2. (Opcional) Expandir o volume com `generate_synthetic_data.py`, que usa a API da
   Anthropic para gerar mais exemplos no mesmo estilo:

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   pip install -r data_prep/requirements.txt
   python data_prep/generate_synthetic_data.py --categoria faqs --n 20
   python data_prep/generate_synthetic_data.py --categoria protocolos --n 5
   python data_prep/generate_synthetic_data.py --categoria laudos --n 3
   ```

3. `anonymize.py` roda automaticamente como rede de segurança dentro do gerador,
   e pode ser rodado manualmente sobre qualquer arquivo `.jsonl`:

   ```bash
   python data_prep/anonymize.py data/raw/faqs.jsonl
   ```

4. Gerar o dataset final de treino (formato Alpaca — instruction/input/output):

   ```bash
   python data_prep/format_dataset.py
   ```

   Saída: `data/processed/train.jsonl` e `data/processed/val.jsonl`.

## train/

LoRA via [Unsloth](https://github.com/unslothai/unsloth) sobre `Llama-3.2-3B-Instruct`
(4-bit), rodado no Google Colab (GPU T4 gratuita) através do `google-colab-cli`.

Configuração em `config.yaml`. Para rodar (dentro de uma sessão Colab com GPU,
a partir da raiz do projeto em `/content`):

```bash
python finetuning/train/train_lora.py
```

**Resultado do primeiro treino** (80 exemplos, 72 treino / 8 validação, 6 épocas):

| Epoch | Train Loss | Val Loss |
|---|---|---|
| 1 | 2.379 | 1.568 |
| 2 | 1.239 | 1.373 |
| **3** | **0.996** | **1.282** ← melhor |
| 4 | 0.661 | 1.291 |
| 5 | 0.478 | 1.349 |
| 6 | 0.390 | 1.353 |

O modelo passou a overfitar a partir da época 4 (val loss volta a subir enquanto
train loss continua caindo) — esperado com dataset pequeno. O adapter salvo em
`adapters/checkpoint-27-best/` (época 3) é o que generaliza melhor e deve ser
usado; `adapters/final-epoch6/` foi mantido só para comparação no relatório de
avaliação. `config.yaml` já foi ajustado com `load_best_model_at_end: true`
para que os próximos treinos selecionem automaticamente o melhor checkpoint.

## eval/ (próximo passo)

Avaliação comparando respostas do modelo base vs. `checkpoint-27-best`
(mesmas perguntas de `data/processed/val.jsonl`), com métricas quantitativas
e análise de erros para o relatório técnico.
