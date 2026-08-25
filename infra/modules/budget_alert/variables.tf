variable "project_name" {
  type = string
}

variable "budget_amount" {
  type        = number
  description = "Valor mensal do orçamento, na moeda da assinatura (USD para Azure for Students)."
}

variable "budget_start_date" {
  type        = string
  description = "Data de início do período do orçamento, formato RFC3339 (ex.: 2026-08-01T00:00:00Z). Deve ser o primeiro dia de um mês."
}

variable "alert_emails" {
  type        = list(string)
  description = "E-mails que recebem o alerta quando o orçamento atinge um dos thresholds."
}

variable "thresholds" {
  type        = list(number)
  description = "Percentuais do orçamento em que o alerta é disparado."
  default     = [50, 80, 100]
}
