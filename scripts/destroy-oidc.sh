#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-gh-oidc-app-devops}"

APP_OBJECT_ID="$(az ad app list --display-name "$APP_NAME" --query '[0].id' -o tsv)"
if [[ -z "$APP_OBJECT_ID" ]]; then
  echo "App not found: $APP_NAME"
  exit 0
fi

echo "About to DELETE App Registration: $APP_NAME"
echo "Type DELETE to confirm:"
read -r CONFIRM
if [[ "$CONFIRM" != "DELETE" ]]; then
  echo "Aborted."
  exit 1
fi

az ad app delete --id "$APP_OBJECT_ID"
echo "Deleted."
