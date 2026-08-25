# Guia de Testes — Assistente Médico Virtual

Roteiro manual pra validar as 5 abas do Streamlit de ponta a ponta, com
perguntas e arquivos prontos. Pode ser rodado local (`streamlit run
app/streamlit_app.py`) ou na aplicação publicada no Azure.

Arquivos de exemplo nesta pasta:
- `protocolo_anafilaxia.txt` — novo protocolo institucional (pra Upload de Protocolo)
- `prontuario_exemplo_sem_exame_pendente.txt` — paciente sintético (pra Upload de Prontuário, testa a rota "sugere conduta")
- `prontuario_exemplo_com_exame_pendente.txt` — paciente sintético (pra Upload de Prontuário, testa a rota "emite alerta")

---

## 1. Chat Geral

| Pergunta | Resultado esperado |
|---|---|
| "Qual o protocolo do Hospital Vida Nova para sepse?" | Cita `[Protocolo de Identificação e Manejo Inicial de Sepse]`, traz qSOFA e conduta, reforça validação médica |
| "Quando devo acionar alerta em um paciente com suspeita de AVC?" | Cita `[Protocolo de Atendimento ao AVC Agudo]`, menciona NIHSS >= 4 |
| "Qual a capital da França?" | Recusa educadamente — fora do escopo institucional (mostra que o assistente não "alucina" fora do domínio) |

## 2. Upload de Protocolo

1. Abra a aba **Upload de Protocolo**.
2. Título: `Protocolo de Manejo de Anafilaxia`. Especialidade: `Emergência`.
3. Envie o arquivo `protocolo_anafilaxia.txt` (ou cole o conteúdo).
4. Clique em "Adicionar ao índice institucional".

**Esperado**: mensagem de sucesso com o `source_id` gerado
(`protocolo_de_manejo_de_anafilaxia`). Volte na aba **Chat Geral** e pergunte
*"Qual a conduta para anafilaxia no Hospital Vida Nova?"* — a resposta deve
citar esse protocolo recém-adicionado (prova de que o índice estático cresce
em tempo real).

## 3. Upload de Prontuário

### 3a. Rota "sugere conduta" (sem exame pendente)

1. Aba **Upload de Prontuário**. ID: `EX-0001`. Nome: `Paciente Exemplo 1`.
2. Envie `prontuario_exemplo_sem_exame_pendente.txt`.
3. **Não** marque "Existe exame pendente".
4. Clique em "Indexar prontuário".

**Esperado**: o fluxo LangGraph dispara automaticamente e retorna uma
sugestão de conduta citando o protocolo de anafilaxia (se você já fez o
passo 2) ou uma resposta admitindo não ter protocolo específico (se ainda
não subiu o protocolo) — mas sempre recusando dar diagnóstico definitivo e
reforçando a validação médica.

### 3b. Rota "emite alerta" (com exame pendente)

1. Mesma aba. ID: `EX-0002`. Nome: `Paciente Exemplo 2`.
2. Envie `prontuario_exemplo_com_exame_pendente.txt`.
3. Marque "Existe exame pendente" e preencha a descrição, ex.: *"Hemocultura e urocultura em processamento"*.
4. Clique em "Indexar prontuário".

**Esperado**: resposta começa com `ALERTA: paciente EX-0002 possui exame
pendente...` — a conduta NÃO é sugerida, só o alerta (prova da ramificação
correta do grafo de decisão).

## 4. Consulta por Paciente

| ID | Pergunta | Resultado esperado |
|---|---|---|
| `SIM-0001` (demo, exame pendente) | "O que o paciente tem?" | Emite alerta |
| `SIM-0002` (demo, sem exame pendente) | "O que o paciente tem?" | Sugere conduta citando protocolo de diabetes |
| `EX-0001` (se voce fez o passo 3a) | "O que o paciente tem?" | Sugere conduta |
| `ID-INEXISTENTE` | qualquer | "Nenhum prontuário encontrado" |

## 5. Painel de Auditoria

Depois de rodar os passos acima, abra **Painel de Auditoria**:

- O contador "Total de interações" deve ter aumentado a cada consulta feita.
- Marque "Mostrar apenas interações com guardrail acionado" — deve sobrar a
  maioria das interações (reflete o achado da seção 5.1 do
  [relatório técnico](../docs/relatorio.md): o guardrail é acionado com
  frequência, exatamente por ser determinístico e não depender do modelo).
- Expanda um registro qualquer e confira: pergunta, resposta, fontes citadas
  e motivo do guardrail (quando acionado) — tudo deve bater com o que
  apareceu na tela durante o teste.
