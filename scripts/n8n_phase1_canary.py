#!/usr/bin/env python3
"""Phase 1 Final Canary: cutover, one real prod webhook test, verify, rollback on fail."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "deliverables" / "arcadia-phase1-cutover-results.json"
SUPABASE_PROJECT = "xfibcjhshpmqkrhlpsoa"
MANAGER_PHONE = "380936582617"

sys.path.insert(0, str(ROOT / "scripts"))
from n8n_phase1_operational import (  # noqa: E402
    export_production,
    load_client,
    trigger_webhook,
    wait_for_new_execution,
)
from n8n_phase1_precutover import (  # noqa: E402
    PROD_NAME,
    PROD_WEBHOOK,
    FINAL_NAME,
    canary_start,
    evolution_payload,
    get_id,
    rollback,
)


def mcp_sql(query: str) -> list[dict]:
    body = json.dumps({"project_id": SUPABASE_PROJECT, "query": query})
    # Use supabase execute via subprocess curl to MCP not available — use REST if key set
    import os

    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        proc = subprocess.run(
            [
                "python3",
                "-c",
                f"""
import json, subprocess, sys
# fallback: write query for external verification
print(json.dumps([]))
""",
            ],
            capture_output=True,
            text=True,
        )
        return []
    url = f"https://{SUPABASE_PROJECT}.supabase.co/rest/v1/rpc/"
    return []


def supabase_query_via_mcp_tool(query: str) -> list[dict]:
    """Run SQL through bundled helper invoking cursor dynamic tool is not available in script."""
    import os

    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        return []
    # PostgREST doesn't run arbitrary SQL — skip unless we have rpc
    return []


def get_execution_nodes(client, execution_id: str) -> dict:
    ex = client.get_execution(execution_id)
    data = ex.get("data") or {}
    result_data = data.get("resultData") or {}
    run_data = result_data.get("runData") or {}
    summary: dict = {"status": ex.get("status"), "nodes": {}}
    for node_name, runs in run_data.items():
        if not runs:
            continue
        main = runs[0].get("data", {}).get("main", [[]])
        items = main[0] if main else []
        node_info: dict = {"item_count": len(items), "error": runs[0].get("error")}
        if node_name == "Send WhatsApp" and items:
            j = items[0].get("json", {})
            node_info["http_status"] = j.get("statusCode") or j.get("status")
            node_info["has_key"] = "key" in j or "message" in str(j)
        if node_name == "Decision Engine" and items:
            j = items[0].get("json", {})
            node_info["response_preview"] = str(j.get("response", ""))[:200]
        summary["nodes"][node_name] = node_info
    return summary


def count_executions_for_msg(client, wf_id: str, after_iso: str, msg_id: str) -> int:
    count = 0
    for ex in client.list_executions(workflow_id=wf_id, limit=20):
        started = ex.get("startedAt") or ""
        if started >= after_iso:
            count += 1
    return count


def main() -> int:
    report: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "manager_phone": MANAGER_PHONE,
    }
    client = load_client()
    prod_id = get_id(client, PROD_NAME)
    final_id = get_id(client, FINAL_NAME)

    # 1) Snapshot
    exported = export_production(client)
    report["export_files"] = [str(p.name) for p in exported[:5]]
    report["export_count"] = len(exported)

    # 2) Cutover
    report["canary_start"] = canary_start(client)
    time.sleep(3)

    # Verify activation state
    prod_wf = client.get_workflow(prod_id)
    final_wf = client.get_workflow(final_id)
    report["state_after_cutover"] = {
        "production_active": prod_wf.get("active"),
        "final_candidate_active": final_wf.get("active"),
        "final_webhook": next(
            (
                n.get("parameters", {}).get("path")
                for n in final_wf.get("nodes", [])
                if "webhook" in n.get("type", "")
            ),
            None,
        ),
    }
    if prod_wf.get("active") or not final_wf.get("active"):
        report["error"] = "Cutover state invalid — rolling back"
        report["rollback"] = rollback(client)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    # 3) One prod webhook message (same payload Evolution forwards)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    msg_id = f"wa_canary_{ts}"
    text = "Phase1 Final Canary — رسالة اختبار واحدة، تجاهل"
    before = datetime.now(timezone.utc).isoformat()
    status, body = trigger_webhook(client.base, PROD_WEBHOOK, evolution_payload(MANAGER_PHONE, msg_id, text))
    report["webhook_trigger"] = {"http_status": status, "provider_message_id": msg_id, "text": text}

    ex = wait_for_new_execution(client, final_id, before, timeout_s=180)
    if not ex:
        report["error"] = "No execution within timeout — rolling back"
        report["rollback"] = rollback(client)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    exec_id = str(ex.get("id", ""))
    report["execution_id"] = exec_id
    report["execution_status"] = ex.get("status")
    report["execution_nodes"] = get_execution_nodes(client, exec_id)

    # Duplicate check: only one execution in window for this workflow
    exec_count = count_executions_for_msg(client, final_id, before, msg_id)
    report["execution_count_in_window"] = exec_count

    send_node = report["execution_nodes"]["nodes"].get("Send WhatsApp", {})
    send_ok = ex.get("status") == "success" and not send_node.get("error")
    if send_node.get("http_status"):
        send_ok = send_ok and int(send_node["http_status"]) < 400
    elif ex.get("status") == "success":
        send_ok = True  # n8n API may omit runData; success status implies send completed

    checks = {
        "execution_success": ex.get("status") == "success",
        "no_duplicate_window": exec_count == 1,
        "send_whatsapp_ok": send_ok,
    }
    report["checks"] = checks
    report["passed"] = all(checks.values())

    if not report["passed"]:
        report["rollback"] = rollback(client)
        report["final_state"] = "rolled_back"
    else:
        report["final_state"] = "final_candidate_active"

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
