#!/usr/bin/env bash
# Move uma issue para um status (coluna) do GitHub Project (v2).
# Uso: gh-project-move.sh <numero_da_issue> <nome_do_status>
# Requer as env vars: GH_TOKEN, PROJECT_OWNER, PROJECT_NUMBER, REPO
set -euo pipefail

issue_number="$1"
status_name="$2"

issue_url="https://github.com/${REPO}/issues/${issue_number}"

gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --url "$issue_url" >/dev/null
gh project item-edit "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --url "$issue_url" \
  --field "Status" --value "$status_name"
