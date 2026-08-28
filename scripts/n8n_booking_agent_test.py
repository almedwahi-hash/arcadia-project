#!/usr/bin/env python3
"""Phase 2.2 — import Booking Agent Test workflow, run E2E + idempotency test.

Requires: N8N_API_URL, N8N_API_KEY
Optional: SUPABASE_SERVICE_ROLE_KEY (patches HTTP nodes on import)

Usage:
  python3 scripts/n8n_booking_agent_test.py import
  python3 scripts/n8n_booking_agent_test.py test
  python3 scripts/n8n_booking_agent_test.py all
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from n8n_phase1_operational import (  # noqa: E402
    N8nClient,
    fix_supabase_http_nodes,
    load_client,
    strip_for_api,
    trigger_webhook,
    wait_for_new_execution,
)

WF_PATH = ROOT / "n8n Workflows" / "Arcadia - Booking Agent Test.json"
REPORT_PATH = ROOT / "deliverables" / "arcadia-phase2-2-test-results.json"

TEST_LEAD_ID = "b6fada92-a0c4-45a9-a5f7-2e60897af3c8"
TEST_QUOTE_REF = "ARC-367344"
TEST_REQUESTED_BY = "phase2_2_test"


def upsert_workflow(client: N8nClient) -> dict:
    wf = json.loads(WF_PATH.read_text(encoding="utf-8"))
    wf = fix_supabase_http_nodes(wf)
    name_to_id = {w["name"]: str(w["id"]) for w in client.list_workflows()}
    from n8n_phase1_operational import fix_error_workflow_id  # noqa: WPS433

    wf = fix_error_workflow_id(wf, name_to_id)
    name = wf["name"]
    existing = {w["name"]: w for w in client.list_workflows()}
    body = strip_for_api(wf)
    if name in existing:
        wf_id = str(existing[name]["id"])
        updated = client.update_workflow(wf_id, body)
        print(f"Updated workflow {name} ({wf_id})")
    else:
        updated = client.create_workflow(body)
        wf_id = str(updated["id"])
        print(f"Created workflow {name} ({wf_id})")
    client.activate_workflow(wf_id)
    print(f"Activated {name}")
    return {"id": wf_id, "name": name}


def find_workflow_id(client: N8nClient) -> str:
    for wf in client.list_workflows():
        if wf.get("name") == "Arcadia - Booking Agent Test":
            return str(wf["id"])
    raise SystemExit("Booking Agent Test workflow not found — run import first")


def run_webhook_test(client: N8nClient, *, duplicate: bool = False) -> dict:
    wf_id = find_workflow_id(client)
    payload = {
        "lead_id": TEST_LEAD_ID,
        "quote_ref": TEST_QUOTE_REF,
        "requested_by": TEST_REQUESTED_BY,
    }
    label = "duplicate" if duplicate else "create"
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    api_base = os.environ.get("N8N_API_URL", "").strip()
    status, body = trigger_webhook(api_base, "booking-agent-test", payload, test_mode=False)
    ex = wait_for_new_execution(client, wf_id, after, timeout_s=120)
    result = {
        "label": label,
        "http_status": status,
        "response_body": body[:2000] if body else "",
        "execution_id": ex.get("id") if ex else None,
        "execution_status": ex.get("status") if ex else None,
    }
    try:
        result["response_json"] = json.loads(body) if body else {}
    except json.JSONDecodeError:
        result["response_json"] = None
    return result


def cmd_import() -> None:
    client = load_client()
    upsert_workflow(client)


def cmd_test() -> dict:
    client = load_client()
    create = run_webhook_test(client, duplicate=False)
    time.sleep(3)
    dup = run_webhook_test(client, duplicate=True)
    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "lead_id": TEST_LEAD_ID,
        "quote_ref": TEST_QUOTE_REF,
        "create_call": create,
        "duplicate_call": dup,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "import":
        cmd_import()
    elif cmd == "test":
        cmd_test()
    elif cmd == "all":
        cmd_import()
        time.sleep(2)
        cmd_test()
    else:
        raise SystemExit(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
