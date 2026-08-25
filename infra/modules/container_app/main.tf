# Container Apps Environment + Container App (Streamlit) — seção 6.1.
# Consumption plan, min_replicas=0 (escala a zero quando ocioso — sem
# tráfego, custo ~zero, importante pra conta "Azure for Students").
#
# image_tag tem um default público (quickstart da Microsoft) de propósito:
# o primeiro `terraform apply` precisa funcionar ANTES da imagem real do
# Streamlit existir no ACR (só existe depois do `az acr build`, que por sua
# vez só pode rodar depois do ACR já existir). Ver infra/DEPLOY.md para o
# fluxo de duas etapas.

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${var.project_name}-${var.environment}"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = var.log_analytics_workspace_id

  tags = var.tags
}

resource "azurerm_container_app" "main" {
  name                         = "ca-${var.project_name}-${var.environment}"
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }

  registry {
    server   = var.acr_login_server
    identity = var.identity_id
  }

  secret {
    name                = "anthropic-api-key"
    key_vault_secret_id = var.anthropic_api_key_secret_id
    identity            = var.identity_id
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "streamlit"
      image  = var.image
      cpu    = 1.0
      memory = "2Gi" # 1Gi (default) OOM-matava o container quando a pilha de
      # ML (torch + sentence-transformers + chromadb) carregava — visível como
      # um loop de restart no Log Analytics (Uvicorn reiniciando a cada poucos
      # minutos), não relacionado a scale-to-zero.

      env {
        name        = "ANTHROPIC_API_KEY"
        secret_name = "anthropic-api-key"
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = var.app_insights_connection_string
      }
    }
  }

  ingress {
    external_enabled = true
    target_port       = 8501
    transport         = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags

  lifecycle {
    # depois do primeiro deploy, a imagem real passa a ser atualizada via
    # `az containerapp update` no pipeline de CI/CD (ver infra/DEPLOY.md) —
    # não queremos que um `terraform apply` de rotina reverta pra imagem
    # antiga só porque a variável `image` no tfvars não foi atualizada.
    ignore_changes = [template[0].container[0].image]
  }
}
