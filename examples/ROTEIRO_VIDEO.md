# Roteiro do Vídeo de Demonstração (≤ 15 min)

Ordem pensada para cobrir, em sequência, tudo que o enunciado do desafio
pede mostrar: treinamento/funcionamento da LLM personalizada, execução do
fluxo automatizado, resposta a perguntas contextualizadas, e logs/validação.
Grava pela aplicação publicada no Azure (URL e link do repo no final deste
arquivo) ou local (`streamlit run app/streamlit_app.py`) — o conteúdo é
idêntico, só muda se aparece "localhost" ou a URL do Azure na tela.

**Dica**: abra o [GUIA_DE_TESTES.md](GUIA_DE_TESTES.md) numa aba ao lado
durante a gravação — as perguntas e arquivos de exemplo já estão prontos lá,
é só copiar/colar, sem precisar improvisar texto na hora.

---

## 0. Abertura (0:00 – 0:30)

Fala rápida, sem tela ainda ou com o README do repo aberto:

> "Este é o Assistente Médico Virtual do Hospital Vida Nova, um hospital
> fictício — projeto do Tech Challenge Fase 3. Ele combina fine-tuning
> LoRA, RAG com LangChain e um fluxo de decisão automatizado com LangGraph,
> com guardrails de segurança e auditoria. Todo o dataset é sintético,
> nenhum dado real de paciente é usado em nenhuma etapa."

## 1. Dataset e Fine-tuning (0:30 – 4:00)

**Tela: [docs/relatorio.md](../docs/relatorio.md), seções 3 e 4** (ou o
README do `finetuning/`)

- Mostre a composição do dataset (13 protocolos, 57 FAQs, 10 modelos de
  documento — 100% sintético) e explique rapidamente por que não usamos
  Brateca/MIMIC-IV (seção 3.2 do relatório).
- Mostre o **notebook** [`finetuning/train/train_lora_colab.ipynb`](../finetuning/train/train_lora_colab.ipynb)
  — pode abrir de fato no Colab e rodar ao vivo (o treino leva só ~3min), ou
  mostrar o log real já salvo em
  [`finetuning/train/logs/`](../finetuning/train/logs/).
- **Ponto-chave a falar**: mostre a tabela de loss por época (seção 4.2 do
  relatório) e explique a decisão de usar o checkpoint da época 3, não o
  final — overfitting visível nos números, prova de análise crítica real.

## 2. Avaliação do Modelo (4:00 – 5:30)

**Tela: [`finetuning/eval/outputs/eval_report.md`](../finetuning/eval/outputs/eval_report.md)**

- Mostre a tabela comparando modelo base vs. fine-tunado (ROUGE-L,
  fidelidade, formato/tom).
- **Ponto-chave**: o achado da seção 5.1 do relatório — o modelo só
  menciona "validação médica" por conta própria em 12% das respostas, por
  isso o guardrail **não pode depender do modelo**, precisa ser
  determinístico. Isso conecta direto com a próxima seção.

## 3. Arquitetura — RAG, LangGraph, Guardrails (5:30 – 7:30)

**Tela: [docs/relatorio.md](../docs/relatorio.md), diagrama da seção 2**

- Mostre o diagrama do fluxo de decisão (renderiza como imagem no GitHub).
- Explique em 1 frase cada peça: índice estático (protocolos) vs. dinâmico
  (prontuários), classificador de intenção, verificação de exame pendente,
  guardrail aplicado uma única vez no final, log de auditoria.
- **Ponto-chave opcional**: o achado técnico da seção 6.1 (embeddings
  falhando em siglas clínicas como "AVC", corrigido com busca híbrida
  BM25 + vetorial) — mostra profundidade técnica real, não só "funcionou".

## 4. Demonstração ao vivo — Aplicação Streamlit (7:30 – 13:00)

Siga exatamente o [GUIA_DE_TESTES.md](GUIA_DE_TESTES.md), na ordem:

1. **Chat Geral** — pergunta sobre sepse. Mostre a resposta citando a fonte
   e o aviso de validação médica.
2. **Upload de Protocolo** — envie `protocolo_anafilaxia.txt`. Mostre a
   mensagem de sucesso.
3. **Upload de Prontuário** — envie `prontuario_exemplo_sem_exame_pendente.txt`
   (ID `EX-0001`, sem marcar exame pendente). **Este é o momento mais
   importante do vídeo**: o sistema cruza automaticamente esse prontuário
   com o protocolo de anafilaxia que você acabou de subir, e sugere conduta
   citando a fonte — exatamente o "*o que o paciente X tem?* cruzando
   prontuário + protocolo" pedido no desafio.
4. **Upload de Prontuário** de novo — envie
   `prontuario_exemplo_com_exame_pendente.txt` (ID `EX-0002`, **marque**
   exame pendente). Mostre o **ALERTA** sendo emitido em vez de uma
   sugestão de conduta — prova a ramificação do LangGraph.
5. **Consulta por Paciente** — busque `SIM-0001` (paciente de demonstração
   com exame pendente) e depois `SIM-0002` (sem exame pendente), pra
   mostrar as duas rotas de novo com pacientes diferentes.

## 5. Logs e Validação (13:00 – 14:00)

**Tela: aba Painel de Auditoria**

- Mostre o histórico de interações acumulado durante a demo.
- Expanda um registro com guardrail acionado e aponte: pergunta, resposta,
  fontes citadas, motivo do guardrail — tudo rastreável.
- Fale a frase-chave: "nenhuma resposta sai do sistema sem passar por essa
  camada de guardrail e auditoria, independente de qual modelo gerou o
  texto."

## 6. Infraestrutura e Fechamento (14:00 – 15:00)

**Tela: [infra/DEPLOY.md](../infra/DEPLOY.md) ou o portal do Azure**

- Uma frase: "toda a infraestrutura — Container Apps, Key Vault, Container
  Registry, budget alert — é gerenciada via Terraform, documentada e
  testada de ponta a ponta nesta conta Azure for Students."
- Encerramento: link do repositório na tela.

---

## Links para a tela final / descrição do vídeo

- **Repositório**: https://github.com/DhiegoPimenta/assistente-medico-fase3
- **Aplicação publicada**: (ver mensagem do grupo / não versionada aqui de
  propósito — ingress público sem autenticação, evita uso indevido da API
  paga da Anthropic por quem achar o link)
