#!/usr/bin/env bash
# Verify n8n credentials are injected into the Cloud Agent pod.
set -euo pipefail

missing=0
for var in N8N_API_URL N8N_API_KEY; do
  if [[ -z "${!var:-}" ]]; then
    echo "MISSING: $var"
    missing=1
  else
    val="${!var}"
    echo "OK: $var (${#val} chars, starts with ${val:0:8}...)"
  fi
done

echo "---"
echo "CLOUD_AGENT_ALL_SECRET_NAMES=${CLOUD_AGENT_ALL_SECRET_NAMES:-<unset>}"
echo "CLOUD_AGENT_INJECTED_SECRET_NAMES=${CLOUD_AGENT_INJECTED_SECRET_NAMES:-<unset>}"

if [[ $missing -ne 0 ]]; then
  echo ""
  echo "Fix: Cursor Dashboard → Cloud Agents → Environment → Secrets"
  echo "  N8N_API_URL = https://YOUR-INSTANCE.app.n8n.cloud/api/v1"
  echo "  N8N_API_KEY = (from n8n Settings → API)"
  echo "Then Save environment and start a NEW agent run."
  exit 1
fi

echo "Credentials ready — run: python3 scripts/n8n_phase1_operational.py run-all"
