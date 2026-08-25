variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "log_analytics_workspace_id" {
  type = string
}

variable "acr_login_server" {
  type = string
}

variable "identity_id" {
  type = string
}

variable "anthropic_api_key_secret_id" {
  type = string
}

variable "app_insights_connection_string" {
  type      = string
  sensitive = true
}

variable "image" {
  type        = string
  description = "Imagem do Container App. Default = placeholder público, até a imagem real ser publicada no ACR (ver infra/DEPLOY.md)."
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "tags" {
  type    = map(string)
  default = {}
}
