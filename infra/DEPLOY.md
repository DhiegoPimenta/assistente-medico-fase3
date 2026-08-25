# Deploy no Azure — passo a passo

Infraestrutura via Terraform (`infra/`), aplicação Streamlit publicada no
Azure Container Apps. Fluxo em **duas etapas** — a primeira sobe a
infraestrutura com uma imagem placeholder pública (o Container Registry
ainda não existe pra receber a imagem real na primeira aplicação); a
segunda publica a imagem real do Streamlit e atualiza o Container App.

## Pré-requisitos

```bash
az login
az account show   # confirme que é a assinatura certa (ex.: "Azure for Students")
```

Terraform >= 1.9 (`winget install Hashicorp.Terraform` no Windows).

## 0. Configurar segredos e variáveis

```bash
cd infra
cp environments/dev.secrets.tfvars.example environments/dev.secrets.tfvars
# edite dev.secrets.tfvars com sua ANTHROPIC_API_KEY real (esse arquivo é gitignored)
```

Confira `environments/dev.tfvars` — em especial `budget_start_date` (deve
ser o primeiro dia do mês corrente) e `alert_emails`.

## 1. Etapa 1 — Infraestrutura (com placeholder)

```bash
terraform init
terraform validate
terraform plan  -var-file=environments/dev.tfvars -var-file=environments/dev.secrets.tfvars
terraform apply -var-file=environments/dev.tfvars -var-file=environments/dev.secrets.tfvars -auto-approve
```

Isso cria: resource group, **budget alert** (sempre um dos primeiros a
existir), Log Analytics + Application Insights, identidade gerenciada, Key
Vault (com a chave da Anthropic), Storage Account, Container Registry, e o
Container App — rodando, por enquanto, a imagem placeholder pública
`mcr.microsoft.com/azuredocs/containerapps-helloworld`.

Anote o output `container_registry_name`.

## 2. Etapa 2 — Build e publicação da imagem real

`az acr build` builda a imagem **na nuvem** (não precisa de Docker
instalado localmente):

```bash
az acr build \
  --registry <container_registry_name do output> \
  --image assistente-medico:latest \
  --file app/Dockerfile \
  .
```

Depois, atualize o Container App para usar essa imagem:

```bash
terraform apply \
  -var-file=environments/dev.tfvars \
  -var-file=environments/dev.secrets.tfvars \
  -var="container_image=<login_server do output>/assistente-medico:latest" \
  -auto-approve
```

> O módulo `container_app` tem `lifecycle { ignore_changes = [image] }` —
> depois dessa primeira atualização, republicações seguintes podem ser
> feitas direto via `az containerapp update --image ...`, sem precisar
> passar `-var="container_image=..."` de novo no Terraform.

## 3. Verificar

```bash
terraform output streamlit_url
```

Abra a URL — deve mostrar a aplicação Streamlit (não mais o placeholder).

## 4. Atualizações seguintes (CI/CD manual)

```bash
az acr build --registry <nome> --image assistente-medico:latest --file app/Dockerfile .
az containerapp update --name <container_app name> --resource-group <rg name> \
  --image <login_server>/assistente-medico:latest
```

## 5. Limpando tudo (importante — conta de crédito limitado)

```bash
terraform destroy -var-file=environments/dev.tfvars -var-file=environments/dev.secrets.tfvars
```

**Atenção Key Vault**: `purge_protection_enabled = true` (boa prática Azure,
propositalmente nunca desligado) significa que o Key Vault fica em estado
"soft-deleted" por até 90 dias após o destroy — ele **não pode ser
recriado com o mesmo nome** nesse período, mas também não é cobrado
enquanto soft-deleted. Se precisar recriar o ambiente do zero antes disso,
mude `project_name` ou o sufixo, ou rode:

```bash
az keyvault purge --name <nome-do-vault> --location brazilsouth
```

(só funciona se você tiver permissão de purge — normal em conta pessoal).

## O que cada SKU custa (dimensionado pro crédito Azure for Students)

| Recurso | SKU | Custo aproximado |
|---|---|---|
| Container Apps | Consumption, min_replicas=0 | ~US$0 quando ocioso (escala a zero) |
| Container Registry | Basic | ~US$0,17/dia |
| Key Vault | Standard | Centavos (por operação) |
| Storage Account | Standard LRS | Centavos (poucos MB de dados) |
| Log Analytics | PerGB2018, retenção 30 dias | Depende do volume de log — baixo pro escopo do projeto |

O budget alert (50/80/100% de US$20/mês, ajustável em `dev.tfvars`) avisa
por e-mail antes de qualquer surpresa.
