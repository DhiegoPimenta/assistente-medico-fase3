# Identidade gerenciada (user-assigned) do Container App. Usada para: (1)
# puxar a imagem do Container Registry sem credenciais (role AcrPull,
# atribuída no root main.tf) e (2) ler o segredo do Key Vault (access
# policy no módulo key_vault) — nunca autenticação por chave/senha.

resource "azurerm_user_assigned_identity" "container_app" {
  name                = "id-${var.project_name}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.tags
}
