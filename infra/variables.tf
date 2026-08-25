variable "project_name" {
  type        = string
  description = "Prefixo curto do projeto (minúsculo, sem espaços/símbolos)."
  default     = "hvn"
}

variable "environment" {
  type        = string
  description = "Nome do ambiente."
  default     = "dev"
}

variable "location" {
  type        = string
  description = <<-EOT
    Região Azure. A assinatura "Azure for Students" tem uma policy
    (sys.regionrestriction) que restringe o deploy a um conjunto pequeno de
    regiões — nesta conta: southafricanorth, southcentralus, eastus,
    chilecentral, eastus2. Confira a sua com:
      az rest --method get --url "https://management.azure.com/subscriptions/<sub-id>/providers/Microsoft.Authorization/policyAssignments/sys.regionrestriction?api-version=2023-04-01"
  EOT
  default     = "eastus2"
}

variable "budget_amount" {
  type        = number
  description = "Orçamento mensal (USD) — dimensionado para o crédito Azure for Students."
  default     = 20
}

variable "budget_start_date" {
  type        = string
  description = "Primeiro dia do mês corrente, formato RFC3339 (ex.: 2026-08-01T00:00:00Z)."
}

variable "alert_emails" {
  type        = list(string)
  description = "E-mails que recebem o alerta de orçamento."
}

variable "anthropic_api_key" {
  type        = string
  description = "Chave da API Anthropic (console.anthropic.com) — nunca commitar em .tfvars versionado."
  sensitive   = true
}

variable "container_image" {
  type        = string
  description = "Imagem completa do Streamlit (ex.: acrhvnxxxx.azurecr.io/assistente-medico:latest). Deixe em branco na primeira aplicação (usa o placeholder público) — ver infra/DEPLOY.md."
  default     = null
}

variable "tags" {
  type        = map(string)
  description = "Tags aplicadas a todos os recursos."
  default = {
    projeto = "assistente-medico-fase3"
    gerido_por = "terraform"
  }
}
