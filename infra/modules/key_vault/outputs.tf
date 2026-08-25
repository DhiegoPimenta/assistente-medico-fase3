output "id" {
  value = azurerm_key_vault.main.id
}

output "anthropic_api_key_secret_id" {
  value = azurerm_key_vault_secret.anthropic_api_key.versionless_id
}
