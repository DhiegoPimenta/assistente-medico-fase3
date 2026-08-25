variable "project_name" {
  type = string
}

variable "suffix" {
  type        = string
  description = "Sufixo para garantir nome globalmente único."
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "container_app_identity_principal_id" {
  type        = string
  description = "Principal ID da identidade gerenciada do Container App, para poder ler os segredos."
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
