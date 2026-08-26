#!/usr/bin/env bash
# Cloud Agent install — Arcadia project (SEO docs + B2B outreach tooling)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[install] Python outreach dependencies"
pip3 install --user -q -r requirements-outreach.txt

echo "[install] Ensure B2B rate sheet PDF exists"
if [[ ! -f deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.pdf ]]; then
  python3 scripts/generate_rate_sheet_pdf.py
fi

echo "[install] Verify outreach dry-run (Batch 12)"
python3 scripts/send_batch12_outreach.py --dry-run >/tmp/cloud-agent-install-dryrun.log 2>&1 || {
  echo "[install] WARN: batch12 dry-run failed — see /tmp/cloud-agent-install-dryrun.log"
}

echo "[install] Done"
