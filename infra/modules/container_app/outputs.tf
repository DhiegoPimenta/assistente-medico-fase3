output "fqdn" {
  value = azurerm_container_app.main.latest_revision_fqdn
}

output "name" {
  value = azurerm_container_app.main.name
}
