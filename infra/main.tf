# Assistente Médico Virtual — Hospital Vida Nova
# Infraestrutura Azure via Terraform. Ordem dos módulos é deliberada:
# o budget_alert sobe primeiro (ou junto), antes de qualquer recurso que
# gere custo de fato — ver docs/relatorio.md e docs/arquitetura.md seção 6.

module "resource_group" {
  source = "./modules/resource_group"

  project_name = var.project_name
  environment  = var.environment
  location     = var.location
  tags         = var.tags
}

module "budget_alert" {
  source = "./modules/budget_alert"

  project_name       = var.project_name
  budget_amount      = var.budget_amount
  budget_start_date  = var.budget_start_date
  alert_emails       = var.alert_emails
}

# Sufixo aleatório para os recursos que exigem nome globalmente único
# (Key Vault, Storage Account, Container Registry).
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

module "log_analytics" {
  source = "./modules/log_analytics"

  project_name         = var.project_name
  environment          = var.environment
  resource_group_name  = module.resource_group.name
  location             = module.resource_group.location
  tags                 = var.tags
}

module "identity" {
  source = "./modules/identity"

  project_name         = var.project_name
  environment          = var.environment
  resource_group_name  = module.resource_group.name
  location             = module.resource_group.location
  tags                 = var.tags
}

module "key_vault" {
  source = "./modules/key_vault"

  project_name                         = var.project_name
  suffix                               = random_string.suffix.result
  resource_group_name                  = module.resource_group.name
  location                             = module.resource_group.location
  container_app_identity_principal_id  = module.identity.principal_id
  anthropic_api_key                    = var.anthropic_api_key
  tags                                 = var.tags
}

data "azurerm_client_config" "current" {}

module "storage_account" {
  source = "./modules/storage_account"

  project_name         = var.project_name
  suffix               = random_string.suffix.result
  resource_group_name  = module.resource_group.name
  location             = module.resource_group.location
  tags                 = var.tags
}

# shared_access_key_enabled=false no storage account (boa prática: sem
# autenticação por chave) significa que até o próprio Terraform precisa de
# RBAC pra criar o container via Azure AD — sem isso, a criação do
# azurerm_storage_container falha com 403.
resource "azurerm_role_assignment" "terraform_storage_blob_data_contributor" {
  scope                = module.storage_account.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# atribuições RBAC no Azure levam alguns segundos pra propagar — sem essa
# espera, a criação do container abaixo pode falhar com 403 mesmo depois
# da role assignment "existir".
resource "time_sleep" "wait_for_rbac_propagation" {
  create_duration = "30s"

  depends_on = [azurerm_role_assignment.terraform_storage_blob_data_contributor]
}

resource "azurerm_storage_container" "documentos" {
  name                  = "documentos"
  storage_account_id    = module.storage_account.id
  container_access_type = "private"

  depends_on = [time_sleep.wait_for_rbac_propagation]
}

module "container_registry" {
  source = "./modules/container_registry"

  project_name         = var.project_name
  suffix               = random_string.suffix.result
  resource_group_name  = module.resource_group.name
  location             = module.resource_group.location
  tags                 = var.tags
}

# Identidade gerenciada do Container App precisa poder puxar imagem do ACR
# — sem usuário/senha, só RBAC (boa prática Azure).
resource "azurerm_role_assignment" "acr_pull" {
  scope                = module.container_registry.id
  role_definition_name = "AcrPull"
  principal_id         = module.identity.principal_id
}

module "container_app" {
  source = "./modules/container_app"

  project_name                    = var.project_name
  environment                     = var.environment
  resource_group_name             = module.resource_group.name
  location                        = module.resource_group.location
  log_analytics_workspace_id      = module.log_analytics.workspace_id
  acr_login_server                = module.container_registry.login_server
  identity_id                     = module.identity.id
  anthropic_api_key_secret_id     = module.key_vault.anthropic_api_key_secret_id
  app_insights_connection_string  = module.log_analytics.app_insights_connection_string
  image                           = var.container_image != null ? var.container_image : "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  tags                             = var.tags

  depends_on = [azurerm_role_assignment.acr_pull]
}
