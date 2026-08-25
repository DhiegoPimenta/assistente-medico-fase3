variable "project_name" {
  type        = string
  description = "Prefixo curto do projeto, usado na nomeação de todos os recursos."
}

variable "environment" {
  type        = string
  description = "Nome do ambiente (ex.: dev, prod)."
}

variable "location" {
  type        = string
  description = "Região Azure onde os recursos serão criados."
}

variable "tags" {
  type        = map(string)
  description = "Tags aplicadas a todos os recursos."
  default     = {}
}
