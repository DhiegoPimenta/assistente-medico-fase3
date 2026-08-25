# Tech Challenge Fase 3 — Assistente Médico Virtual
## Documento de Arquitetura e Plano de Construção (Azure + Terraform + LLM Fine-tuning + RAG + Streamlit)

> **Objetivo deste documento**: servir de referência completa para retomar a construção em outra sessão, com todas as decisões de arquitetura, peças de infraestrutura e passos técnicos já definidos.

---

## 1. Visão Geral do Projeto

Construir um **assistente virtual médico** para um hospital fictício, que:
- Responde perguntas clínicas gerais (conhecimento médico amplo)
- Responde perguntas sobre **protocolos internos** do hospital (personalização)
- Permite **alimentar a base em tempo real** com novos prontuários de pacientes (RAG dinâmico)
- Responde perguntas do tipo *"o que o paciente X tem?"* cruzando prontuário + protocolo
- Executa um **fluxo automatizado de decisão** (LangGraph): verifica exame pendente → sugere conduta → emite alerta
- Nunca prescreve diretamente — sempre exige validação humana
- Registra logs de auditoria e cita a fonte de cada resposta (explainability)
- É publicado com interface **Streamlit** hospedada no **Azure**, com infraestrutura como código em **Terraform**

### Requisitos do Tech Challenge (checklist de entrega)
- [ ] Fine-tuning de LLM com dados médicos internos (dataset anonimizado/sintético)
- [ ] Pipeline LangChain integrando a LLM customizada
- [ ] Consulta em base estruturada (prontuários)
- [ ] Contextualização com dados atualizados do paciente
- [ ] Guardrails de segurança (sem prescrição direta)
- [ ] Logging detalhado / auditoria
- [ ] Explainability (fonte da informação)
- [ ] Projeto Python modularizado + README
- [ ] Repositório Git com pipeline de fine-tuning + LangChain + LangGraph
- [ ] Dataset anonimizado ou sintético
- [ ] Relatório técnico + diagrama do fluxo
- [ ] Vídeo de até 15 min

---

## 2. Datasets e Base de Conhecimento

### 2.1 Fontes de dados
| Fonte | Uso | Observação |
|---|---|---|
| **Brateca** | Estrutura/vocabulário de notas clínicas em PT-BR | 70k+ internações, 2,5M notas, anonimizado |
| **Synthea** | Geração de prontuários 100% sintéticos | Simulador, zero risco de dado real |
| **MTSamples** | Formato de laudos/receitas por especialidade | Referência de estrutura |
| **MIMIC-IV** | Referência de estrutura de resumo de alta | Seções: queixa principal, HDA, HPP, evolução, exame físico, diagnóstico |
| **PubMedQA** | Conhecimento médico geral (RAG) | https://pubmedqa.github.io/ |
| **MedQuAD** | Perguntas/respostas de saúde (RAG) | https://github.com/abachaa/MedQuAD |
| **Protocolos sintéticos** | Escritos/gerados para o "Hospital Fictício" | Dá identidade e personalização ao projeto |

### 2.2 Dois índices vetoriais separados
1. **Índice estático** — protocolos internos + PubMedQA/MedQuAD (conhecimento geral e institucional)
2. **Índice dinâmico** — prontuários de pacientes, alimentado via upload no Streamlit, cresce em tempo real

---

## 3. Modelo Fundacional e Fine-tuning

### 3.1 Escolha do modelo base
- Modelo aberto compatível com fine-tuning leve: **Llama 3.2 3B/1B** ou **Phi-3-mini** (preferir modelo pequeno — ver risco de GPU abaixo). Llama 3.1 8B / Mistral 7B só se confirmarem GPU disponível.
- Fine-tuning via **LoRA/QLoRA** (barato, roda em GPU única, ideal para escopo acadêmico)
- Alternativa gerenciada no Azure: **Azure AI Foundry** com fine-tuning de modelos (ex.: Phi-3, Llama) direto na plataforma, sem gerenciar GPU manualmente — **mas confirmar antes se o SKU de fine-tuning gerenciado está habilitado para assinatura "Azure for Students"**, nem sempre está.

> ⚠️ **Risco de quota GPU (Azure for Students)**: assinaturas de estudante normalmente vêm com quota 0 para VMs de GPU (família NC/ND) e o pedido de aumento de quota pode ser negado ou demorar dias — inviável para o prazo do challenge. **Plano seguro**: treinar o LoRA fora do Azure (Google Colab free/Colab Pro com T4, ou Kaggle Notebooks com GPU grátis), exportar só o adapter (poucos MB) e usar o Azure exclusivamente para **hospedar a inferência** (Container App servindo o modelo base + adapter, ou Azure AI Foundry se o modelo já estiver disponível no catálogo). Isso ainda conta como "subimos e publicamos no Azure" — só a etapa de treino roda em GPU gratuita externa.

### 3.2 Dados de treino do fine-tuning
- Protocolos médicos do hospital (sintéticos)
- Perguntas frequentes de médicos (sintéticas, geradas em lote via LLM)
- Modelos de laudos/receitas/procedimentos (formato, não conteúdo sensível)
- Formato: pares `(instrução, resposta)` estilo Alpaca/ShareGPT

### 3.3 Abordagem recomendada: Fine-tuning leve + RAG (não fine-tuning "puro")
- Fine-tuning (LoRA) ensina **tom, formato e jargão** do hospital
- RAG traz o **conteúdo factual atualizado** (protocolos, prontuários)
- Combinação reduz alucinação e facilita explainability (cita a fonte do RAG, não depende de "memória" do modelo fine-tunado)

### 3.4 Pipeline de fine-tuning (peças a construir)
```
/finetuning
  ├── data_prep/
  │   ├── generate_synthetic_data.py     # gera protocolos, FAQs, laudos sintéticos via LLM
  │   ├── anonymize.py                   # anonimização/curadoria
  │   └── format_dataset.py              # formata em JSONL (instrução/resposta)
  ├── train/
  │   ├── train_lora.py                  # QLoRA fine-tuning (PEFT + bitsandbytes)
  │   └── config.yaml
  ├── eval/
  │   └── evaluate_model.py              # métricas (ROUGE, BLEU, avaliação humana/LLM judge)
  └── README.md
```

---

## 4. RAG + LangChain + LangGraph

### 4.1 Componentes LangChain
- **Embeddings**: `text-embedding-3-large` (Azure OpenAI) ou modelo open-source (`bge-large`)
- **Vector store**: Azure AI Search (vector search nativo) — permite dois índices separados
- **Retriever**: `AzureAISearchRetriever` com filtro por `patient_id` para consultas específicas
- **Chain**: RAG conversacional com citação de fonte (retorna `source_documents`)

### 4.2 Fluxo LangGraph (grafo de decisão)
```
[Entrada: pergunta ou upload de prontuário]
        │
        ▼
 [Classificador de intenção] ──► pergunta geral ──► RAG (índice estático)
        │
        ├──► pergunta sobre paciente ──► RAG (índice dinâmico, filtro paciente)
        │                                     │
        │                                     ▼
        │                          [Verifica exame pendente?]
        │                                 │         │
        │                               sim         não
        │                                 │           │
        │                                 ▼           ▼
        │                       [Emite alerta]   [Sugere conduta
        │                       para equipe]      c/ base no protocolo]
        │                                 │           │
        │                                 └─────┬─────┘
        │                                       ▼
        │                          [Guardrail: bloqueia prescrição
        │                           direta, exige validação humana]
        │                                       ▼
        │                          [Resposta final + fonte citada]
        ▼                                       │
   [Log de auditoria] ◄─────────────────────────┘
```

### 4.3 Guardrails
- Regra determinística (não depende só do modelo): se a resposta contiver padrão de prescrição direta (ex.: dosagem + "administrar"), bloqueia e substitui por "sugestão sujeita a validação médica"
- Opcional: `Guardrails AI` ou validação via segundo LLM (LLM-as-judge)

### 4.4 Logging/Auditoria
- Cada interação grava: timestamp, usuário, pergunta, documentos recuperados (fonte), resposta, se guardrail foi acionado
- Estrutura: log JSON estruturado → Azure Application Insights ou Azure Table Storage

---

## 5. Aplicação Streamlit

### 5.1 Estrutura das abas
1. **Chat geral** — perguntas de conhecimento médico amplo (RAG índice estático)
2. **Upload de protocolo** — sobe novo documento institucional (PDF/TXT), indexa no índice estático
3. **Upload de prontuário** — sobe novo prontuário de paciente (texto/PDF), extrai campos, indexa no índice dinâmico, dispara o LangGraph automaticamente (verifica pendências)
4. **Consulta por paciente** — busca por ID/nome, LangGraph decide fluxo, resposta com fontes citadas
5. **Painel de auditoria** (opcional) — visualização dos logs

### 5.2 Estrutura de código sugerida
```
/app
  ├── streamlit_app.py
  ├── pages/
  │   ├── 1_chat_geral.py
  │   ├── 2_upload_protocolo.py
  │   ├── 3_upload_prontuario.py
  │   └── 4_consulta_paciente.py
  ├── core/
  │   ├── rag_chain.py
  │   ├── langgraph_flow.py
  │   ├── guardrails.py
  │   ├── ingestion.py          # parsing + chunking + embeddings
  │   └── logging_config.py
  └── requirements.txt
```

---

## 6. Infraestrutura Azure

### 6.1 Recursos necessários
| Recurso | Finalidade | SKU recomendado (Azure for Students) |
|---|---|---|
| **Azure AI Foundry (ou Azure ML)** | Hospedagem/inferência do modelo customizado (treino roda fora, ver 3.1) | Serverless/consumo, sem VM dedicada |
| **Azure AI Search** | Vector store (dois índices: estático e dinâmico) | **Free tier** (50MB/3 índices — suficiente pro escopo do challenge) |
| **Azure OpenAI Service** | Embeddings + modelo auxiliar (classificador de intenção, guardrail) | ⚠️ **serviço com gate de aprovação** — solicitar acesso cedo; se negado, usar fallback abaixo |
| **Azure Container Apps** | Hospedagem do Streamlit | Consumption plan (scale-to-zero, paga só quando alguém acessa) |
| **Azure Container Registry** | Imagem Docker do Streamlit | Basic |
| **Azure Storage Account (Blob)** | Armazenar documentos brutos (protocolos, prontuários sintéticos) | Standard LRS |
| **Azure Key Vault** | Segredos (API keys, connection strings) | Standard (custo desprezível) |
| **Azure Application Insights** | Logging e observabilidade | Pay-as-you-go com cap de ingestão diária |
| **Azure Resource Group** | Agrupamento lógico de todos os recursos | — |
| **Azure Cost Management — Budget** | Alerta automático de gasto (ex.: 50%/80%/100% dos ~US$100 do crédito) | Criar **antes** de subir qualquer outro recurso |

> ⚠️ **Fallback se Azure OpenAI não for aprovado a tempo**: usar embeddings open-source (`bge-large` ou `e5-large`) via **Azure AI Foundry model catalog** (endpoint serverless, sem OpenAI) para os embeddings e para o classificador de intenção/guardrail auxiliar. Evita depender de um serviço com aprovação manual que pode não vir a tempo do prazo de entrega.

### 6.2 Estrutura Terraform (módulos)
```
/infra
  ├── main.tf
  ├── variables.tf
  ├── outputs.tf
  ├── providers.tf
  ├── modules/
  │   ├── resource_group/
  │   ├── budget_alert/
  │   ├── ai_search/
  │   ├── openai/
  │   ├── container_app/
  │   ├── container_registry/
  │   ├── storage_account/
  │   ├── key_vault/
  │   └── app_insights/
  └── environments/
      ├── dev.tfvars
      └── prod.tfvars
```

### 6.3 Objetivo do Terraform
- Permitir que **qualquer pessoa do grupo** rode `terraform init && terraform apply` e suba o ambiente completo (Search + OpenAI + Container App + Storage) sem configuração manual no portal
- Variáveis parametrizadas: região, nome do projeto, SKU dos serviços (para controlar custo em ambiente de estudo)
- `outputs.tf` deve expor: URL do Streamlit, endpoint do AI Search, endpoint do OpenAI
- **Budget alert (`azurerm_consumption_budget_subscription`) criado no primeiro `apply`**, com notificação de e-mail em 50%/80%/100% do crédito Azure for Students disponível — é o primeiro módulo a subir, antes de qualquer recurso que gere custo
- Todos os SKUs "caros por padrão" (AI Search, Container Apps) devem vir parametrizados com o tier **mais barato como default** no `.tfvars`, para que ninguém do grupo suba sem querer um tier de produção
- **Checklist de "desligar depois de validar"**: documentar no README quais recursos custam mesmo parados/ociosos (ex.: AI Search Basic+, endpoints dedicados) vs. os que já escalam a zero (Container Apps consumption) — para o grupo saber o que rodar `terraform destroy` depois de gravar o vídeo

### 6.4 Pipeline de deploy sugerido (CI/CD simples)
```
GitHub Actions:
  1. build da imagem Docker do Streamlit → push no ACR
  2. terraform plan/apply (infra)
  3. update do Container App com a nova imagem
```

---

## 7. Segurança e Anonimização

- Dados sintéticos desde a origem (Synthea) → risco mínimo
- Se usar Brateca/MIMIC como referência de estrutura, **nunca** subir os dados reais para o repositório — usar só como inspiração de formato
- Anonimização adicional (regex/NER) em qualquer texto gerado que simule nomes/documentos reais
- Key Vault para todas as credenciais — nunca hardcoded

---

## 8. Roadmap de construção (ordem sugerida)

1. Gerar dataset sintético (protocolos, FAQs, laudos) do hospital fictício
2. Escrever Terraform básico (Resource Group + Storage + AI Search + OpenAI)
3. Subir os dados no índice estático (ingestão inicial)
4. Construir a RAG chain simples (sem LangGraph ainda) + testar no Jupyter/CLI
5. Fazer o fine-tuning LoRA do modelo base com os dados sintéticos
6. Integrar modelo fine-tunado na chain
7. Construir o LangGraph (fluxo de decisão)
8. Adicionar guardrails + logging
9. Construir o Streamlit (chat + uploads)
10. Dockerizar o Streamlit + Terraform do Container App
11. Deploy completo no Azure via Terraform
12. Gravar vídeo de demonstração + escrever relatório técnico

---

## 9. Entregáveis finais (mapeamento para a nota)

| Entregável do PDF | Onde fica no projeto |
|---|---|
| Pipeline de fine-tuning | `/finetuning` |
| Integração LangChain | `/app/core/rag_chain.py` |
| Fluxos LangGraph | `/app/core/langgraph_flow.py` |
| Dataset anonimizado/sintético | `/data` (gerado por Synthea + scripts próprios) |
| Relatório técnico | `/docs/relatorio.md` (ou docx) |
| Diagrama do fluxo | Seção 4.2 deste documento, refinado |
| Vídeo (15 min) | Demonstração: upload de prontuário → pergunta → resposta com fonte → alerta |
| README | Instruções completas de setup (local + Terraform) |
