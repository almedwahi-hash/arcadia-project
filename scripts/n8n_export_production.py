#!/usr/bin/env python3
"""Export Arcadia production workflows from n8n REST API into production-backup/.

Requires environment variables:
  N8N_API_URL   e.g. https://your-instance.app.n8n.cloud/api/v1
  N8N_API_KEY   n8n API key (Settings -> API)

Usage:
  export N8N_API_URL='https://...'
  export N8N_API_KEY='...'
  python3 scripts/n8n_export_production.py

Exports workflows whose names contain 'Arcadia' or 'Laila'.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "n8n Workflows" / "production-backup"
TODAY = date.today().isoformat()

MATCH_TERMS = ("arcadia", "laila")


def api_get(base: str, key: str, path: str) -> dict | list:
    req = urllib.request.Request(
        f"{base.rstrip('/')}{path}",
        headers={"Accept": "application/json", "X-N8N-API-KEY": key},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    base = os.environ.get("N8N_API_URL", "").strip()
    key = os.environ.get("N8N_API_KEY", "").strip()
    if not base or not key:
        print("Set N8N_API_URL and N8N_API_KEY environment variables.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        payload = api_get(base, key, "/workflows?limit=250")
    except urllib.error.HTTPError as e:
        print(f"API error: {e.code} {e.reason}", file=sys.stderr)
        return 1

    workflows = payload.get("data", payload) if isinstance(payload, dict) else payload
    exported = 0
    for wf in workflows:
        name = wf.get("name", "")
        if not any(t in name.lower() for t in MATCH_TERMS):
            continue
        wf_id = wf.get("id")
        detail = api_get(base, key, f"/workflows/{wf_id}")
        data = detail.get("data", detail)
        safe = name.replace("/", "-")
        dated = OUT_DIR / f"{safe}.{TODAY}.json"
        latest = OUT_DIR / f"{safe}.json"
        body = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        dated.write_text(body, encoding="utf-8")
        latest.write_text(body, encoding="utf-8")
        print(f"Exported: {dated.name}")
        exported += 1

    if exported == 0:
        print("No matching workflows found.", file=sys.stderr)
        return 1
    print(f"Done — {exported} workflow(s) in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
