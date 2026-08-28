#!/usr/bin/env python3
"""Phase 2.3 — import workflows, run RU-2026-030 staff notify + task update tests.

Usage:
  python3 scripts/n8n_booking_phase23_test.py import
  python3 scripts/n8n_booking_phase23_test.py test
  python3 scripts/n8n_booking_phase23_test.py all
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from n8n_phase1_operational import (  # noqa: E402
    N8nClient,
    fix_error_workflow_id,
    fix_supabase_http_nodes,
    load_client,
    n8n_public_base,
    strip_for_api,
    trigger_webhook,
    wait_for_new_execution,
)

REPORT_PATH = ROOT / "deliverables" / "arcadia-phase2-3-test-results.json"
BOOKING_ID = "RU-2026-030"
STAFF_USER = "493831958"
UNAUTHORIZED_USER = "999999001"
CHAT_ID = 493831958

# Task IDs from Phase 2.2 test booking
TASK_HOTEL_MOSCOW = "73a7d126-9e0b-4cf6-855b-081f53ca366f"
TASK_HOTEL_SPB = "1bc7b88d-ac1e-477f-b855-61b17b5e7c6f"
TASK_AIRPORT_ARR = "9a0187d3-8c16-43b7-9e29-0955229797a3"
TASK_AIRPORT_DEP = "99e24e0a-e897-4994-b8d2-b420cb217b48"
TASK_IC_1 = "99181bc1-ac13-4303-9e68-3c166952f02a"
TASK_IC_2 = "d0aaf657-3b3f-4c47-a193-5069dd4dfd90"
TASK_HOTEL_MOSCOW_3 = "fc6d853c-425a-4ca4-a009-4bdc9614a86e"

WORKFLOWS = [
    "Arcadia - Booking Staff Notify.json",
    "Arcadia - Booking Task Update.json",
    "Arcadia - Booking Agent Test.json",
]


def upsert_workflows(client: N8nClient) -> dict[str, str]:
    name_to_id = {w["name"]: str(w["id"]) for w in client.list_workflows()}
    out: dict[str, str] = {}
    for fname in WORKFLOWS:
        path = ROOT / "n8n Workflows" / fname
        wf = json.loads(path.read_text(encoding="utf-8"))
        wf = fix_supabase_http_nodes(wf)
        wf = fix_error_workflow_id(wf, name_to_id)
        name = wf["name"]
        body = strip_for_api(wf)
        if name in name_to_id:
            wf_id = name_to_id[name]
            client.update_workflow(wf_id, body)
        else:
            created = client.create_workflow(body)
            wf_id = str(created["id"])
            name_to_id[name] = wf_id
        out[name] = wf_id
        print(f"Upserted {name} ({wf_id})")
    return out


def activate_phase23(client: N8nClient, ids: dict[str, str]) -> None:
    for name in ("Arcadia - Booking Staff Notify", "Arcadia - Booking Task Update"):
        client.activate_workflow(ids[name])
        print(f"Activated {name}")


def deactivate_booking_agent_test(client: N8nClient, ids: dict[str, str]) -> None:
    wf_id = ids.get("Arcadia - Booking Agent Test")
    if wf_id:
        client.deactivate_workflow(wf_id)
        print(f"Deactivated Arcadia - Booking Agent Test ({wf_id})")


def reset_test_booking_state() -> None:
    """Reset RU-2026-030 tasks to pending for repeatable canary."""
    # Uses Supabase REST via n8n env not available locally — SQL via note in report if needed.
    pass


def post_webhook(api_base: str, path: str, payload: dict) -> tuple[int, str]:
    return trigger_webhook(api_base, path, payload, test_mode=False)


def sim_callback(
    client: N8nClient,
    wf_id: str,
    *,
    callback_data: str,
    callback_query_id: str,
    user_id: str = STAFF_USER,
    confirm_data: dict | None = None,
) -> dict:
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "simulate": True,
        "telegram_user_id": user_id,
        "callback_data": callback_data,
        "callback_query_id": callback_query_id,
        "chat_id": CHAT_ID,
    }
    if confirm_data:
        payload["confirm_data"] = confirm_data
    api_base = os.environ.get("N8N_API_URL", "").strip()
    status, body = post_webhook(api_base, "booking-task-callback-test", payload)
    ex = wait_for_new_execution(client, wf_id, after, timeout_s=90)
    result = {"http_status": status, "body": body[:1500] if body else ""}
    try:
        result["json"] = json.loads(body) if body else {}
    except json.JSONDecodeError:
        result["json"] = None
    result["execution_id"] = ex.get("id") if ex else None
    result["execution_status"] = ex.get("status") if ex else None
    return result


def run_tests(client: N8nClient, ids: dict[str, str]) -> dict:
    staff_wf = ids["Arcadia - Booking Staff Notify"]
    task_wf = ids["Arcadia - Booking Task Update"]
    api_base = os.environ.get("N8N_API_URL", "").strip()
    report: dict = {"tested_at": datetime.now(timezone.utc).isoformat(), "booking_id": BOOKING_ID, "steps": {}}

    # Step 0: Telegram channel test message (via staff notify dry ping using webhook with test flag)
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    status, body = post_webhook(api_base, "booking-staff-notify", {"booking_id": BOOKING_ID, "notify_type": "phase23_test"})
    ex = wait_for_new_execution(client, staff_wf, after, timeout_s=90)
    report["steps"]["telegram_booking_notification"] = {
        "http_status": status,
        "execution_id": ex.get("id") if ex else None,
        "execution_status": ex.get("status") if ex else None,
        "response": json.loads(body) if body else {},
    }

    time.sleep(2)

    # Step 1: hotel → requested
    cb_id = "phase23_test_req_001"
    r1 = sim_callback(client, task_wf, callback_data=f"bk:task:{TASK_HOTEL_MOSCOW}:to:requested", callback_query_id=cb_id)
    report["steps"]["hotel_to_requested"] = r1

    time.sleep(1)

    # Step 2: duplicate same callback
    r2 = sim_callback(client, task_wf, callback_data=f"bk:task:{TASK_HOTEL_MOSCOW}:to:requested", callback_query_id=cb_id)
    report["steps"]["duplicate_callback"] = r2

    time.sleep(1)

    # Step 3: progress hotel through confirmed + one more required → PARTIALLY_CONFIRMED
    transitions = [
        (TASK_HOTEL_MOSCOW, "awaiting_confirmation", "phase23_ac_001"),
        (TASK_HOTEL_MOSCOW, "confirmed", "phase23_conf_001", {"confirmation_ref": "HOTEL-MOW-001", "supplier_name": "SADU Hotel"}),
        (TASK_HOTEL_SPB, "requested", "phase23_req_002"),
        (TASK_HOTEL_SPB, "awaiting_confirmation", "phase23_ac_002"),
        (TASK_HOTEL_SPB, "confirmed", "phase23_conf_002", {"confirmation_ref": "HOTEL-SPB-001"}),
    ]
    partial_results = []
    for item in transitions:
        tid, status, cid = item[0], item[1], item[2]
        cd = item[3] if len(item) > 3 else None
        partial_results.append(
            sim_callback(client, task_wf, callback_data=f"bk:task:{tid}:to:{status}", callback_query_id=cid, confirm_data=cd)
        )
        time.sleep(0.5)
    report["steps"]["partial_confirmations"] = partial_results
    report["steps"]["partial_lifecycle"] = partial_results[-1].get("json", {}).get("lifecycle_status") if partial_results else None

    time.sleep(1)

    # Step 4: complete remaining required tasks → PENDING_PAYMENT
    finish = [
        (TASK_HOTEL_MOSCOW_3, "requested", "phase23_f_01"),
        (TASK_HOTEL_MOSCOW_3, "awaiting_confirmation", "phase23_f_02"),
        (TASK_HOTEL_MOSCOW_3, "confirmed", "phase23_f_03", {"confirmation_ref": "HOTEL-MOW3-001"}),
        (TASK_AIRPORT_ARR, "requested", "phase23_f_04"),
        (TASK_AIRPORT_ARR, "awaiting_confirmation", "phase23_f_05"),
        (TASK_AIRPORT_ARR, "confirmed", "phase23_f_06", {"confirmation_ref": "APT-ARR-001"}),
        (TASK_AIRPORT_DEP, "requested", "phase23_f_07"),
        (TASK_AIRPORT_DEP, "awaiting_confirmation", "phase23_f_08"),
        (TASK_AIRPORT_DEP, "confirmed", "phase23_f_09", {"confirmation_ref": "APT-DEP-001"}),
        (TASK_IC_1, "requested", "phase23_f_10"),
        (TASK_IC_1, "awaiting_confirmation", "phase23_f_11"),
        (TASK_IC_1, "confirmed", "phase23_f_12", {"confirmation_ref": "IC-MSQ-001"}),
        (TASK_IC_2, "requested", "phase23_f_13"),
        (TASK_IC_2, "awaiting_confirmation", "phase23_f_14"),
        (TASK_IC_2, "confirmed", "phase23_f_15", {"confirmation_ref": "IC-MSK-001"}),
    ]
    finish_results = []
    for item in finish:
        tid, status, cid = item[0], item[1], item[2]
        cd = item[3] if len(item) > 3 else None
        finish_results.append(
            sim_callback(client, task_wf, callback_data=f"bk:task:{tid}:to:{status}", callback_query_id=cid, confirm_data=cd)
        )
        time.sleep(0.3)
    report["steps"]["complete_required_tasks"] = finish_results[-3:]
    report["steps"]["final_lifecycle"] = finish_results[-1].get("json", {}).get("lifecycle_status") if finish_results else None

    time.sleep(1)

    # Step 5: unauthorized user
    r_denied = sim_callback(
        client,
        task_wf,
        callback_data=f"bk:task:{TASK_HOTEL_MOSCOW}:to:failed",
        callback_query_id="phase23_unauth_001",
        user_id=UNAUTHORIZED_USER,
    )
    report["steps"]["unauthorized_blocked"] = r_denied

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    client = load_client()
    if cmd in ("import", "all"):
        ids = upsert_workflows(client)
        activate_phase23(client, ids)
        deactivate_booking_agent_test(client, ids)
    else:
        ids = {w["name"]: str(w["id"]) for w in client.list_workflows()}
    if cmd in ("test", "all"):
        if cmd == "all":
            time.sleep(2)
        run_tests(client, ids)


if __name__ == "__main__":
    main()
