# Container Registry — imagem Docker do Streamlit (seção 6.1). SKU Basic
# (mais barato) e SEM acesso anônimo (boa prática Azure) — autenticação só
# via identidade gerenciada (role AcrPull, atribuída no root main.tf).

resource "azurerm_container_registry" "main" {
  name                = "acr${var.project_name}${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"

  admin_enabled                = false
  anonymous_pull_enabled       = false
  public_network_access_enabled = true

  tags = var.tags
}
