# Log Analytics Workspace (exigido pelo Container Apps Environment) +
# Application Insights (workspace-based) para logging/observabilidade da
# aplicação — seção 4.4 do documento de arquitetura (auditoria/logging).

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30 # mínimo prático para manter custo baixo

  tags = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = var.tags
}
