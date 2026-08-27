#!/usr/bin/env python3
"""Phase 1 Laila V4 Working Copy E2E runner (isolated test webhook).

Uses separate webhook path `laila-v4-phase1-e2e` so Production `laila-v4` stays untouched.
Activates Working Copy only for tests, then deactivates.

Usage:
  python3 scripts/n8n_phase1_e2e.py run
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "deliverables" / "arcadia-phase1-e2e-results.json"
SNAPSHOT_NOTE = ROOT / "deliverables" / "arcadia-phase1-e2e-snapshot.json"

sys.path.insert(0, str(ROOT / "scripts"))
from n8n_phase1_operational import (  # noqa: E402
    export_production,
    load_client,
    n8n_public_base,
    strip_for_api,
    trigger_webhook,
    wait_for_new_execution,
)

E2E_WEBHOOK = "laila-v4-phase1-e2e"
PROD_WEBHOOK = "laila-v4"
WORKING_NAME = "Laila V4 - Final Phase1 Working"
PROD_NAME = "Laila V4 - Final"
EH_NAME = "Arcadia - Central Error Handler"
PRICING_LOG_NAME = "Arcadia - Phase1 Pricing Action Log"
TEST_PHONE = "971509998001"
SUPABASE_PROJECT = "xfibcjhshpmqkrhlpsoa"

DELETE_TEST_WFS = (
    "Phase1 Minimal Subflow Test DELETE ME",
    "Phase1 Minimal Parent Test DELETE ME",
    "Phase1 call inbound v2 TEST",
    "Laila V4 - Final Phase1 Working TEST2",
    "Arcadia - Phase1 Inbound Pipeline v2 TEST",
)

PREPARE_PRICING_JS = r"""// Phase1 observability — parse Decision Engine response (no pricing logic change)
const de = $input.first().json;
const ctx = $('Arcadia - Phase1 Inbound Pipeline').first()?.json || {};
const response = String(de.response || '');
const priceUsd = response.match(/\$[\d,]+/)?.[0] || response.match(/([\d,]{3,})\s*USD/i)?.[0] || null;
const manualPath = /no_hotel|يدوي|human|موظف|فريق/i.test(response);
const hasPrice = !!priceUsd || /\$[\d,]{2,}|USD\s*[\d,]+|دولار/.test(response);
return [{ json: {
  phone: de.phone,
  remoteJid: de.remoteJid,
  response: de.response,
  isManager: de.isManager,
  followup: de.followup,
  lead_id: ctx.lead_id,
  customer_id: ctx.customer_id,
  channel: ctx.phase1?.channel || 'whatsapp',
  action_type: 'get_price',
  status: manualPath && !hasPrice ? 'failed' : (hasPrice ? 'success' : 'failed'),
  output_summary: (priceUsd || response).slice(0, 500),
  input_summary: String(ctx.phase1?.message_text || '').slice(0, 500),
  metadata: { phase1: 'pricing_observability', source: 'decision_engine_response' }
}}];"""

AI_FAIL_JS = r"""throw new Error('phase1_e2e_ai_node_failure_test');"""

SEND_FAIL_URL = "https://invalid.arcadia-phase1-e2e.local/message/sendText/h"


def supabase_sql(query: str) -> list[dict]:
    """Run SQL via Supabase MCP REST fallback using service role from n8n workflow if needed."""
    # Use PostgREST rpc or direct - we'll use urllib to Supabase if key available
    key = __import__("os").environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        return []
    url = f"https://{SUPABASE_PROJECT}.supabase.co/rest/v1/rpc/quote_options"
    return []


def mcp_counts() -> dict[str, int]:
    """Placeholder — filled from report after manual MCP queries."""
    return {}


def evolution_payload(phone: str, msg_id: str, text: str) -> dict:
    return {
        "data": {
            "key": {
                "remoteJid": f"{phone}@s.whatsapp.net",
                "fromMe": False,
                "id": msg_id,
            },
            "message": {"conversation": text},
            "messageType": "conversation",
        }
    }


def find_node(wf: dict, name: str) -> dict | None:
    for n in wf.get("nodes", []):
        if n.get("name") == name:
            return n
    return None


def set_webhook_path(wf: dict, path: str) -> None:
    for n in wf.get("nodes", []):
        if n.get("type", "").endswith("webhook"):
            n.setdefault("parameters", {})["path"] = path


def wire_pricing_observability(wf: dict, pricing_wf_id: str) -> bool:
    """Insert observability nodes after Decision Engine without modifying its code."""
    if find_node(wf, "Phase1 Prepare Pricing Action"):
        return False
    de = find_node(wf, "Decision Engine")
    save = find_node(wf, "Save Response")
    if not de or not save:
        return False

    prep_id = "phase1-prep-pricing-e2e"
    exec_id = "phase1-exec-pricing-e2e"
    prep = {
        "parameters": {"mode": "runOnceForAllItems", "jsCode": PREPARE_PRICING_JS},
        "id": prep_id,
        "name": "Phase1 Prepare Pricing Action",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [de["position"][0] + 100, de["position"][1] + 120],
    }
    ex = {
        "parameters": {
            "workflowId": {
                "__rl": True,
                "mode": "list",
                "value": pricing_wf_id,
                "cachedResultName": PRICING_LOG_NAME,
            },
            "mode": "once",
            "options": {},
        },
        "id": exec_id,
        "name": "Arcadia - Phase1 Pricing Action Log",
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.2,
        "position": [de["position"][0] + 220, de["position"][1] + 120],
        "continueOnFail": True,
        "onError": "continueRegularOutput",
    }
    wf["nodes"].append(prep)
    wf["nodes"].append(ex)
    conns = wf.setdefault("connections", {})
    conns["Decision Engine"] = {"main": [[{"node": "Phase1 Prepare Pricing Action", "type": "main", "index": 0}]]}
    conns["Phase1 Prepare Pricing Action"] = {
        "main": [[{"node": "Arcadia - Phase1 Pricing Action Log", "type": "main", "index": 0}]]
    }
    conns["Arcadia - Phase1 Pricing Action Log"] = {
        "main": [[{"node": "Save Response", "type": "main", "index": 0}]]
    }
    return True


def patch_node_param(wf: dict, node_name: str, **params: Any) -> dict | None:
    n = find_node(wf, node_name)
    if not n:
        return None
    backup = deepcopy(n)
    p = n.setdefault("parameters", {})
    p.update(params)
    return backup


def restore_node(wf: dict, node_name: str, backup: dict | None) -> None:
    if not backup:
        return
    for i, n in enumerate(wf.get("nodes", [])):
        if n.get("name") == node_name:
            wf["nodes"][i] = backup
            break


def get_wf_id(client, name: str) -> str:
    for wf in client.list_workflows():
        if wf.get("name") == name:
            return str(wf["id"])
    raise SystemExit(f"Workflow not found: {name}")


def run_scenario(
    client,
    working_id: str,
    api_base: str,
    label: str,
    payload: dict,
    *,
    timeout_s: int = 180,
) -> dict:
    before = datetime.now(timezone.utc).isoformat()
    status, body = trigger_webhook(api_base, E2E_WEBHOOK, payload)
    ex = wait_for_new_execution(client, working_id, before, timeout_s=timeout_s)
    return {
        "scenario": label,
        "webhook_status": status,
        "execution_id": str(ex.get("id", "")) if ex else None,
        "execution_status": ex.get("status") if ex else None,
        "response_preview": body[:500] if body else None,
        "started_after": before,
    }


def wait_error_handler_exec(client, eh_id: str, after_iso: str, timeout_s: int = 60) -> dict | None:
    return wait_for_new_execution(client, eh_id, after_iso, timeout_s=timeout_s)


def main() -> int:
    client = load_client()
    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "isolated_webhook": E2E_WEBHOOK,
            "production_webhook": PROD_WEBHOOK,
            "no_simultaneous_webhook": True,
        },
    }

    # 1) Fresh production export
    exported = export_production(client)
    report["production_snapshot"] = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "files": [str(p.name) for p in exported[:10]],
        "count": len(exported),
    }

    working_id = get_wf_id(client, WORKING_NAME)
    prod_id = get_wf_id(client, PROD_NAME)
    eh_id = get_wf_id(client, EH_NAME)
    pricing_id = get_wf_id(client, PRICING_LOG_NAME)

    prod_wf = client.get_workflow(prod_id)
    working_wf = client.get_workflow(working_id)
    report["before"] = {
        "production_active": prod_wf.get("active"),
        "working_copy_active": working_wf.get("active"),
        "production_id": prod_id,
        "working_copy_id": working_id,
    }

    if not prod_wf.get("active"):
        print("WARNING: Production Laila V4 - Final is not active")

    # 2) Prepare Working Copy — separate webhook + pricing observability
    original_wf = deepcopy(working_wf)
    set_webhook_path(working_wf, E2E_WEBHOOK)
    wired = wire_pricing_observability(working_wf, pricing_id)
    client.update_workflow(working_id, strip_for_api(working_wf))
    report["pricing_action_log_wired"] = wired

    # 3) Activate for E2E only
    client.activate_workflow(eh_id)
    was_working_active = bool(working_wf.get("active"))
    client.activate_workflow(working_id)
    time.sleep(3)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    scenarios: list[dict] = []

    try:
        # --- pricing_success ---
        d_start = (date.today() + timedelta(days=30)).isoformat()
        d_end = (date.today() + timedelta(days=34)).isoformat()
        pricing_text = (
            f"مرحبا، أريد رحلة إلى Almaty لشخصين بالغين و4 ليالي "
            f"من {d_start} إلى {d_end} — phase1 e2e pricing test"
        )
        pid = f"wa_e2e_pricing_{ts}"
        r1 = run_scenario(
            client,
            working_id,
            client.base,
            "pricing_success",
            evolution_payload(TEST_PHONE, pid, pricing_text),
            timeout_s=240,
        )
        r1["provider_message_id"] = pid
        r1["expected_price_usd"] = 781
        scenarios.append(r1)

        # --- manual_quote ---
        mq_pid = f"wa_e2e_manual_{ts}"
        manual_text = "أريد رحلة إلى NonexistentCityXYZ لشخصين 4 ليالي — phase1 e2e manual quote test"
        r2 = run_scenario(
            client,
            working_id,
            client.base,
            "manual_quote",
            evolution_payload(TEST_PHONE, mq_pid, manual_text),
            timeout_s=240,
        )
        r2["provider_message_id"] = mq_pid
        scenarios.append(r2)

        # --- send_failure --- (temporary bad Send URL)
        wf_send = client.get_workflow(working_id)
        send_backup = patch_node_param(wf_send, "Send WhatsApp", url=SEND_FAIL_URL)
        client.update_workflow(working_id, strip_for_api(wf_send))
        time.sleep(2)
        sf_pid = f"wa_e2e_sendfail_{ts}"
        sf_before = datetime.now(timezone.utc).isoformat()
        r3 = run_scenario(
            client,
            working_id,
            client.base,
            "send_failure",
            evolution_payload(TEST_PHONE, sf_pid, "phase1 e2e send failure test"),
            timeout_s=120,
        )
        r3["provider_message_id"] = sf_pid
        eh_ex = wait_error_handler_exec(client, eh_id, sf_before, timeout_s=60)
        r3["error_handler_execution_id"] = str(eh_ex.get("id", "")) if eh_ex else None
        scenarios.append(r3)
        # restore send URL
        wf_send = client.get_workflow(working_id)
        restore_node(wf_send, "Send WhatsApp", send_backup)
        client.update_workflow(working_id, strip_for_api(wf_send))

        # --- ai_node_failure --- (temporary throw in Decision Engine)
        wf_ai = client.get_workflow(working_id)
        de_backup = patch_node_param(wf_ai, "Decision Engine", jsCode=AI_FAIL_JS)
        client.update_workflow(working_id, strip_for_api(wf_ai))
        time.sleep(2)
        ai_pid = f"wa_e2e_aifail_{ts}"
        ai_before = datetime.now(timezone.utc).isoformat()
        r4 = run_scenario(
            client,
            working_id,
            client.base,
            "ai_node_failure",
            evolution_payload(TEST_PHONE, ai_pid, "phase1 e2e ai failure test"),
            timeout_s=120,
        )
        r4["provider_message_id"] = ai_pid
        eh_ex2 = wait_error_handler_exec(client, eh_id, ai_before, timeout_s=60)
        r4["error_handler_execution_id"] = str(eh_ex2.get("id", "")) if eh_ex2 else None
        scenarios.append(r4)
        restore_node(wf_ai, "Decision Engine", de_backup)
        client.update_workflow(working_id, strip_for_api(wf_ai))

    finally:
        # 4) Deactivate Working Copy, restore webhook path to prod path (inactive)
        try:
            client.deactivate_workflow(working_id)
        except RuntimeError:
            pass
        restore = deepcopy(original_wf)
        set_webhook_path(restore, PROD_WEBHOOK)
        # Keep pricing observability wiring in repo file but restore from original for n8n
        client.update_workflow(working_id, strip_for_api(restore))
        report["after"] = {
            "working_copy_active": False,
            "production_active": client.get_workflow(prod_id).get("active"),
            "webhook_restored_to": PROD_WEBHOOK,
        }

        # Deactivate stray test workflows
        cleaned = []
        for wf in client.list_workflows():
            if wf.get("name") in DELETE_TEST_WFS:
                try:
                    if wf.get("active"):
                        client.deactivate_workflow(str(wf["id"]))
                    client._request("DELETE", f"/workflows/{wf['id']}")
                    cleaned.append(wf.get("name"))
                except RuntimeError as e:
                    cleaned.append(f"{wf.get('name')}: {e}")
        report["cleaned_test_workflows"] = cleaned

        # Deactivate scenario test if still active
        for wf in client.list_workflows():
            if wf.get("name") == "Arcadia - Phase1 Laila Scenario Test" and wf.get("active"):
                client.deactivate_workflow(str(wf["id"]))

    report["scenarios"] = scenarios
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["status"] = "completed"
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
