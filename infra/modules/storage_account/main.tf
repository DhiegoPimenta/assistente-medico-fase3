# Storage Account (Blob) — armazenamento dos documentos brutos (protocolos,
# prontuários sintéticos), seção 6.1 do documento de arquitetura.
#
# shared_access_key_enabled=true aqui é uma escolha pragmática, não um
# descuido: a boa prática Azure pede AzureAD-only (chave desabilitada), mas
# o provider azurerm atual tenta ler "queue properties" via a API de dados
# em QUALQUER refresh/plan, e esse endpoint específico ainda exige
# autenticação por chave mesmo com AAD-only habilitado — com a chave
# desabilitada, até um `terraform plan` de rotina falha com 403. O acesso
# continua protegido por rede pública controlada + RBAC (role assignment
# no root main.tf); a chave em si nunca é lida nem exposta em nenhum lugar
# do código.
resource "azurerm_storage_account" "main" {
  name                = "st${var.project_name}${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location

  account_tier             = "Standard"
  account_replication_type = "LRS" # mais barato; suficiente para escopo acadêmico

  shared_access_key_enabled       = true
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = false

  tags = var.tags
}

# O container "documentos" é criado no root main.tf, não aqui — precisa
# esperar a role assignment de RBAC (Storage Blob Data Contributor) do
# Terraform sobre a conta, que só pode ser criada depois que a conta existe.
