#!/usr/bin/env python3
"""Deploy Laila conversation-behavior patch to n8n production workflows.

Usage:
  python3 scripts/embed_laila_conversation_patch.py
  python3 scripts/n8n_laila_conversation_patch.py import
  python3 scripts/n8n_laila_conversation_patch.py deploy
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from n8n_phase1_operational import load_client, strip_for_api  # noqa: E402

WHATSAPP_WF_ID = "RSVg9pYlWWa5yege"
AI_AGENT_WF_ID = "TuoZdJ08EHQMk1RO"

WORKFLOWS = [
    "Arcadia - Laila V4 Final Phase1 Production.json",
    "Arcadia - Laila AI Agent.json",
]


def embed() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "embed_laila_conversation_patch.py")], check=True)


def import_workflows() -> dict[str, str]:
    embed()
    client = load_client()
    ids: dict[str, str] = {}
    for wf_name in WORKFLOWS:
        path = ROOT / "n8n Workflows" / wf_name
        if not path.exists():
            raise FileNotFoundError(path)
        wf = json.loads(path.read_text(encoding="utf-8"))
        target_id = WHATSAPP_WF_ID if "V4" in wf_name else AI_AGENT_WF_ID
        body = strip_for_api(wf)
        client.update_workflow(target_id, body)
        ids[wf_name] = target_id
        print(f"updated {wf_name} -> {target_id}")
    return ids


def deploy() -> None:
    ids = import_workflows()
    client = load_client()
    for wf_id in ids.values():
        detail = client.get_workflow(wf_id)
        if not detail.get("active"):
            client.activate_workflow(wf_id)
            print(f"activated {wf_id}")
        else:
            print(f"already active {wf_id}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    if cmd == "import":
        import_workflows()
    elif cmd == "deploy":
        deploy()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
