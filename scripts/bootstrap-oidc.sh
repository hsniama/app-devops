# Este script crea:

# App registration + service principal
# roles (Owner/Contributor + AKS + ACR + Storage si se necesita)
# Federated credentials por GitHub Environments (dev y prod)

# Nota: aquí no tocamos el backend storage (eso es del repo infra).
# Este SP solo necesita permisos para ACR + AKS + RG del ambiente.


#!/usr/bin/env bash
set -euo pipefail

GITHUB_OWNER="${GITHUB_OWNER:-hsniama}"
GITHUB_REPO="${GITHUB_REPO:-app-devops}"
APP_NAME="${APP_NAME:-gh-oidc-app-devops}"

SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-$(az account show --query id -o tsv)}"
TENANT_ID="${TENANT_ID:-$(az account show --query tenantId -o tsv)}"

echo "==> Create App Registration: $APP_NAME"
APP_ID="$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)"
az ad sp create --id "$APP_ID" 1>/dev/null

echo "==> Assign Owner at subscription scope (assessment-friendly)"
az role assignment create \
  --assignee "$APP_ID" \
  --role "Owner" \
  --scope "/subscriptions/$SUBSCRIPTION_ID" 1>/dev/null

echo "==> Create federated credentials for GitHub Environments dev/prod"
az ad app federated-credential create --id "$APP_ID" --parameters "{
  \"name\": \"gh-env-dev\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_OWNER}/${GITHUB_REPO}:environment:dev\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" 1>/dev/null

az ad app federated-credential create --id "$APP_ID" --parameters "{
  \"name\": \"gh-env-prod\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_OWNER}/${GITHUB_REPO}:environment:prod\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" 1>/dev/null

echo
echo "Poner estos GitHub Secrets en el repo app-devops:"
echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID"
