#!/usr/bin/env python3
"""Pre-cutover verification: import Final Candidate, smoke tests, optional canary.

Usage:
  python3 scripts/n8n_phase1_precutover.py import-final
  python3 scripts/n8n_phase1_precutover.py smoke
  python3 scripts/n8n_phase1_precutover.py real-send --phone 9715...
  python3 scripts/n8n_phase1_precutover.py canary-start
  python3 scripts/n8n_phase1_precutover.py canary-verify
  python3 scripts/n8n_phase1_precutover.py rollback
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_CANDIDATE = ROOT / "n8n Workflows" / "Laila V4 - Final Phase1 Final Candidate.json"
REPORT_PATH = ROOT / "deliverables" / "arcadia-phase1-precutover-results.json"
ID_MAP_PATH = ROOT / "deliverables" / "arcadia-phase1-n8n-id-map.json"

sys.path.insert(0, str(ROOT / "scripts"))
from n8n_phase1_operational import (  # noqa: E402
    export_production,
    fix_error_workflow_id,
    load_client,
    strip_for_api,
    trigger_webhook,
    wait_for_new_execution,
    wire_execute_workflow_ids,
)

SMOKE_WEBHOOK = "laila-v4-phase1-smoke"
PROD_WEBHOOK = "laila-v4"
FINAL_NAME = "Laila V4 - Final Phase1 Final Candidate"
PROD_NAME = "Laila V4 - Final"
EH_NAME = "Arcadia - Central Error Handler"
TEST_PHONE = "971509998002"
AI_FAIL_JS = "throw new Error('phase1_smoke_ai_failure');"


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


def set_webhook_path(wf: dict, path: str) -> None:
    for n in wf.get("nodes", []):
        if n.get("type", "").endswith("webhook"):
            n.setdefault("parameters", {})["path"] = path


def get_id(client, name: str) -> str:
    for wf in client.list_workflows():
        if wf.get("name") == name:
            return str(wf["id"])
    raise SystemExit(f"Workflow not found: {name}")


def load_name_to_id() -> dict[str, str]:
    if ID_MAP_PATH.exists():
        return json.loads(ID_MAP_PATH.read_text())
    return {}


def import_final(client) -> dict[str, str]:
    export_production(client)
    name_to_id = load_name_to_id()
    for wf in client.list_workflows():
        name_to_id[wf["name"]] = str(wf["id"])

    candidate = json.loads(FINAL_CANDIDATE.read_text(encoding="utf-8"))
    candidate = wire_execute_workflow_ids(candidate, name_to_id)
    candidate = fix_error_workflow_id(candidate, name_to_id)
    existing = {w["name"]: w for w in client.list_workflows()}
    body = strip_for_api(candidate)
    if FINAL_NAME in existing:
        wf_id = str(existing[FINAL_NAME]["id"])
        updated = client.update_workflow(wf_id, body)
    else:
        body["name"] = FINAL_NAME
        updated = client.create_workflow(body)
        wf_id = str(updated["id"])
    name_to_id[FINAL_NAME] = wf_id
    ID_MAP_PATH.write_text(json.dumps(name_to_id, indent=2) + "\n")
    print(f"Imported Final Candidate: {wf_id}")
    return name_to_id


def activate_smoke(client, final_id: str) -> None:
    client.activate_workflow(get_id(client, EH_NAME))
    wf = client.get_workflow(final_id)
    set_webhook_path(wf, SMOKE_WEBHOOK)
    client.update_workflow(final_id, strip_for_api(wf))
    client.activate_workflow(final_id)
    time.sleep(2)


def deactivate_smoke(client, final_id: str) -> None:
    try:
        client.deactivate_workflow(final_id)
    except Exception:
        pass
    wf = client.get_workflow(final_id)
    set_webhook_path(wf, PROD_WEBHOOK)
    client.update_workflow(final_id, strip_for_api(wf))


def run_smoke(client, final_id: str) -> list[dict]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    scenarios = []

    activate_smoke(client, final_id)
    try:
        # new customer
        pid = f"wa_smoke_new_{ts}"
        before = datetime.now(timezone.utc).isoformat()
        trigger_webhook(client.base, SMOKE_WEBHOOK, evolution_payload(TEST_PHONE, pid, "phase1 smoke new customer"))
        ex = wait_for_new_execution(client, final_id, before, timeout_s=90)
        scenarios.append({"scenario": "new_customer", "execution_id": str(ex.get("id", "")), "status": ex.get("status"), "provider_message_id": pid})

        # duplicate
        before = datetime.now(timezone.utc).isoformat()
        trigger_webhook(client.base, SMOKE_WEBHOOK, evolution_payload(TEST_PHONE, pid, "duplicate smoke"))
        ex = wait_for_new_execution(client, final_id, before, timeout_s=60)
        scenarios.append({"scenario": "duplicate", "execution_id": str(ex.get("id", "")), "status": ex.get("status")})

        # pricing
        d0 = (date.today() + timedelta(days=30)).isoformat()
        d1 = (date.today() + timedelta(days=34)).isoformat()
        ppid = f"wa_smoke_price_{ts}"
        before = datetime.now(timezone.utc).isoformat()
        text = f"مرحبا Almaty لشخصين 4 ليالي من {d0} إلى {d1} smoke pricing"
        trigger_webhook(client.base, SMOKE_WEBHOOK, evolution_payload(TEST_PHONE, ppid, text))
        ex = wait_for_new_execution(client, final_id, before, timeout_s=180)
        scenarios.append({"scenario": "pricing_success", "execution_id": str(ex.get("id", "")), "status": ex.get("status"), "expected_usd": 781})

        # manual quote
        mpid = f"wa_smoke_manual_{ts}"
        before = datetime.now(timezone.utc).isoformat()
        trigger_webhook(client.base, SMOKE_WEBHOOK, evolution_payload(TEST_PHONE, mpid, "NonexistentCityXYZ 2 adults 4 nights smoke"))
        ex = wait_for_new_execution(client, final_id, before, timeout_s=180)
        scenarios.append({"scenario": "manual_quote", "execution_id": str(ex.get("id", "")), "status": ex.get("status")})

        # AI failure
        wf = client.get_workflow(final_id)
        de_backup = None
        for n in wf["nodes"]:
            if n.get("name") == "Decision Engine":
                de_backup = deepcopy(n)
                n["parameters"]["jsCode"] = AI_FAIL_JS
        client.update_workflow(final_id, strip_for_api(wf))
        time.sleep(2)
        apid = f"wa_smoke_aifail_{ts}"
        before = datetime.now(timezone.utc).isoformat()
        eh_id = get_id(client, EH_NAME)
        trigger_webhook(client.base, SMOKE_WEBHOOK, evolution_payload(TEST_PHONE, apid, "smoke ai fail"))
        ex = wait_for_new_execution(client, final_id, before, timeout_s=90)
        eh_ex = wait_for_new_execution(client, eh_id, before, timeout_s=45)
        scenarios.append({
            "scenario": "ai_node_failure",
            "execution_id": str(ex.get("id", "")),
            "status": ex.get("status"),
            "error_handler_execution_id": str(eh_ex.get("id", "")) if eh_ex else None,
        })
        if de_backup:
            wf = client.get_workflow(final_id)
            for n in wf["nodes"]:
                if n.get("name") == "Decision Engine":
                    n.clear()
                    n.update(de_backup)
            client.update_workflow(final_id, strip_for_api(wf))
    finally:
        deactivate_smoke(client, final_id)

    return scenarios


def real_send_test(client, final_id: str, phone: str) -> dict:
    activate_smoke(client, final_id)
    try:
        ts = datetime.now(timezone.utc).strftime("%H%M%S")
        pid = f"wa_real_send_{ts}"
        before = datetime.now(timezone.utc).isoformat()
        trigger_webhook(
            client.base,
            SMOKE_WEBHOOK,
            evolution_payload(phone, pid, "Phase1 pre-cutover real WhatsApp send verification — ignore"),
        )
        ex = wait_for_new_execution(client, final_id, before, timeout_s=120)
        return {
            "phone": phone,
            "provider_message_id": pid,
            "execution_id": str(ex.get("id", "")),
            "execution_status": ex.get("status"),
            "webhook": SMOKE_WEBHOOK,
        }
    finally:
        deactivate_smoke(client, final_id)


def canary_start(client) -> dict:
    export_production(client)
    prod_id = get_id(client, PROD_NAME)
    final_id = get_id(client, FINAL_NAME)
    client.deactivate_workflow(prod_id)
    time.sleep(2)
    wf = client.get_workflow(final_id)
    set_webhook_path(wf, PROD_WEBHOOK)
    client.update_workflow(final_id, strip_for_api(wf))
    client.activate_workflow(final_id)
    client.activate_workflow(get_id(client, EH_NAME))
    time.sleep(2)
    return {
        "production_id": prod_id,
        "production_deactivated": True,
        "final_candidate_id": final_id,
        "final_candidate_active": True,
        "webhook": PROD_WEBHOOK,
    }


def rollback(client) -> dict:
    prod_id = get_id(client, PROD_NAME)
    final_id = get_id(client, FINAL_NAME)
    try:
        client.deactivate_workflow(final_id)
    except Exception:
        pass
    client.activate_workflow(prod_id)
    return {"production_reactivated": prod_id, "final_deactivated": final_id}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["import-final", "smoke", "real-send", "canary-start", "rollback"])
    ap.add_argument("--phone", default=TEST_PHONE)
    args = ap.parse_args()
    client = load_client()
    report: dict = {"started_at": datetime.now(timezone.utc).isoformat()}

    if args.command == "import-final":
        report["import"] = import_final(client)
    elif args.command == "smoke":
        final_id = get_id(client, FINAL_NAME)
        report["smoke"] = run_smoke(client, final_id)
    elif args.command == "real-send":
        final_id = get_id(client, FINAL_NAME)
        report["real_send"] = real_send_test(client, final_id, args.phone)
    elif args.command == "canary-start":
        report["canary"] = canary_start(client)
    elif args.command == "rollback":
        report["rollback"] = rollback(client)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
