output "resource_group_name" {
  value = module.resource_group.name
}

output "streamlit_url" {
  value       = "https://${module.container_app.fqdn}"
  description = "URL pública do Streamlit. Só serve a aplicação real depois do `az acr build` + segunda `terraform apply` — ver infra/DEPLOY.md."
}

output "container_registry_login_server" {
  value = module.container_registry.login_server
}

output "container_registry_name" {
  value = module.container_registry.name
}

output "key_vault_id" {
  value = module.key_vault.id
}

output "storage_account_name" {
  value = module.storage_account.name
}

output "azure_portal_resource_group_url" {
  value = "https://portal.azure.com/#@/resource${module.resource_group.id}"
}
