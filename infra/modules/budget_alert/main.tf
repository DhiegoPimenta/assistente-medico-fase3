# Orçamento em nível de ASSINATURA — deliberadamente o primeiro recurso a
# subir (ver root main.tf), antes de qualquer coisa que gere custo. Não
# depende do resource group existir.
#
# Importante para conta "Azure for Students": o crédito é limitado (~US$100)
# e sem cartão associado — sem esse alerta, um erro de configuração (ex.:
# esquecer um SKU caro) só seria percebido quando o crédito já tivesse acabado.

data "azurerm_subscription" "current" {}

resource "azurerm_consumption_budget_subscription" "main" {
  name            = "budget-${var.project_name}"
  subscription_id = data.azurerm_subscription.current.id

  amount     = var.budget_amount
  time_grain = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  dynamic "notification" {
    for_each = var.thresholds
    content {
      enabled        = true
      threshold      = notification.value
      operator       = "GreaterThan"
      contact_emails = var.alert_emails
    }
  }
}
