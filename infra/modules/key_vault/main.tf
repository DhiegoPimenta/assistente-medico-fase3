# Key Vault — "todas as credenciais, nunca hardcoded" (seção 7 do documento
# de arquitetura). purge_protection_enabled fica sempre ligado (boa prática
# Azure: nunca desligar), o que significa que o vault não pode ser
# recriado com o mesmo nome por até 90 dias após um "terraform destroy" —
# ver infra/DEPLOY.md para o procedimento de limpeza correto.

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                = "kv-${var.project_name}${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  purge_protection_enabled   = true
  soft_delete_retention_days = 7

  tags = var.tags
}

# Acesso do usuário/CI que roda o Terraform, para poder gravar os segredos
resource "azurerm_key_vault_access_policy" "terraform_caller" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
}

# Acesso da identidade gerenciada do Container App, só leitura (seção
# "Least privilege" das boas práticas Azure) — usado via referência direta
# de secret no Container App (módulo container_app), sem o app precisar
# manipular a chave em código.
resource "azurerm_key_vault_access_policy" "container_app_identity" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = var.container_app_identity_principal_id

  secret_permissions = ["Get"]
}

resource "azurerm_key_vault_secret" "anthropic_api_key" {
  name         = "anthropic-api-key"
  value        = var.anthropic_api_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.terraform_caller]
}
