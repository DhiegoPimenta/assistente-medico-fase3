project_name = "hvn"
environment  = "dev"
location     = "eastus2"

budget_amount     = 20
budget_start_date = "2026-08-01T00:00:00Z"

alert_emails = [
  "dhiegopimenta@gmail.com",
]

# anthropic_api_key NÃO fica aqui (é sensível). Crie um arquivo separado
# infra/environments/dev.secrets.tfvars (gitignored) com:
#   anthropic_api_key = "sk-ant-..."
# Veja infra/environments/dev.secrets.tfvars.example
