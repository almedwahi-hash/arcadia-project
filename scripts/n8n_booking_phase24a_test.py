#!/usr/bin/env python3
"""Phase 2.4A — payment gate, CONFIRMED gate, approval handler tests on RU-2026-030.

Usage:
  python3 scripts/n8n_booking_phase24a_test.py import
  python3 scripts/n8n_booking_phase24a_test.py test
  python3 scripts/n8n_booking_phase24a_test.py restore
  python3 scripts/n8n_booking_phase24a_test.py all
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
    strip_for_api,
    trigger_webhook,
    wait_for_new_execution,
)

REPORT_PATH = ROOT / "deliverables" / "arcadia-phase2-4a-test-results.json"
BOOKING_ID = "RU-2026-030"
STAFF_USER = "493831958"
UNAUTHORIZED_USER = "999999001"
DEPOSIT_AMOUNT = 500
TOTAL_AMOUNT = 2390

TASK_HOTEL_MOSCOW = "73a7d126-9e0b-4cf6-855b-081f53ca366f"

WORKFLOWS = [
    "Arcadia - Booking Task Update.json",
    "Arcadia - Booking Payment Record.json",
    "Arcadia - Booking Approval Handler.json",
    "Arcadia - Booking Staff Notify.json",
]


def supabase_request(method: str, path: str, body: dict | None = None) -> list | dict:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY required for DB setup/verify")
    base = os.environ.get("SUPABASE_URL", "https://xfibcjhshpmqkrhlpsoa.supabase.co").rstrip("/")
    url = f"{base}/rest/v1/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else []


def supabase_rpc(fn: str, args: dict) -> dict:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    base = os.environ.get("SUPABASE_URL", "https://xfibcjhshpmqkrhlpsoa.supabase.co").rstrip("/")
    url = f"{base}/rest/v1/rpc/{fn}"
    req = urllib.request.Request(
        url,
        data=json.dumps(args).encode(),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        data = json.loads(raw)
        return data[0] if isinstance(data, list) and data else data


def fetch_booking() -> dict:
    rows = supabase_request(
        "GET",
        f"bookings?booking_id=eq.{BOOKING_ID}&select=booking_id,lifecycle_status,payment_status,paid_amount,total_amount,payment_requirement,required_payment_amount",
    )
    return rows[0] if rows else {}


def count_payments(idem_key: str) -> int:
    rows = supabase_request(
        "GET",
        f"booking_payments?booking_id=eq.{BOOKING_ID}&idempotency_key=eq.{idem_key}&select=payment_id",
    )
    return len(rows)


def count_pending_approvals(action_type: str = "supplier_price_change") -> int:
    rows = supabase_request(
        "GET",
        f"human_approval_queue?booking_id=eq.{BOOKING_ID}&action_type=eq.{action_type}&status=eq.pending&select=approval_id",
    )
    return len(rows)


def count_workflow_failures_since(since_iso: str) -> int:
    rows = supabase_request(
        "GET",
        f"workflow_failures?created_at=gte.{since_iso}&select=failure_id,workflow_name,error_message",
    )
    return len(rows)


def prepare_test_booking() -> None:
    """Reset RU-2026-030 to Phase 2.4A test baseline."""
    supabase_request(
        "PATCH",
        f"bookings?booking_id=eq.{BOOKING_ID}",
        {
            "lifecycle_status": "PENDING_PAYMENT",
            "payment_status": "unpaid",
            "paid_amount": 0,
            "is_paid": False,
            "payment_requirement": "deposit",
            "required_payment_amount": DEPOSIT_AMOUNT,
            "manual_payment_approved_at": None,
            "manual_payment_approved_by": None,
            "modified_by": "phase24a_test_setup",
        },
    )
    # Remove test payments from prior runs (keep ledger append-only in prod; test cleanup only)
    supabase_request("DELETE", f"booking_payments?booking_id=eq.{BOOKING_ID}&idempotency_key=like.phase24a_*")
    supabase_request(
        "DELETE",
        f"human_approval_queue?booking_id=eq.{BOOKING_ID}&idempotency_key=like.phase24a_*",
    )
    supabase_request(
        "PATCH",
        f"booking_tasks?task_id=eq.{TASK_HOTEL_MOSCOW}",
        {"quoted_cost_usd": 100, "status": "awaiting_confirmation", "supplier_cost_usd": None},
    )


def restore_test_booking() -> None:
    supabase_request(
        "PATCH",
        f"bookings?booking_id=eq.{BOOKING_ID}",
        {
            "lifecycle_status": "PENDING_PAYMENT",
            "payment_status": "unpaid",
            "paid_amount": 0,
            "is_paid": False,
            "payment_requirement": None,
            "required_payment_amount": None,
            "manual_payment_approved_at": None,
            "manual_payment_approved_by": None,
            "modified_by": "phase24a_test_restore",
        },
    )
    supabase_request("DELETE", f"booking_payments?booking_id=eq.{BOOKING_ID}&idempotency_key=like.phase24a_*")
    supabase_request(
        "DELETE",
        f"human_approval_queue?booking_id=eq.{BOOKING_ID}&idempotency_key=like.phase24a_*",
    )
    supabase_request(
        "PATCH",
        f"booking_tasks?task_id=eq.{TASK_HOTEL_MOSCOW}",
        {"status": "confirmed", "quoted_cost_usd": None, "supplier_cost_usd": None},
    )
    supabase_rpc("recompute_booking_lifecycle", {"p_booking_id": BOOKING_ID})


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
        client.activate_workflow(wf_id)
        out[name] = wf_id
        print(f"Upserted+activated {name} ({wf_id})")
    return out


def post_webhook(path: str, payload: dict) -> tuple[int, str]:
    api_base = os.environ.get("N8N_API_URL", "").strip()
    secret = os.environ.get("BOOKING_AGENT_START_SECRET") or os.environ.get("BOOKING_AGENT_TEST_SECRET")
    if secret:
        payload = {**payload, "auth_secret": secret}
    return trigger_webhook(api_base, path, payload, test_mode=False)


def run_payment(client: N8nClient, wf_id: str, payload: dict) -> dict:
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    status, body = post_webhook("booking-payment-record", payload)
    ex = wait_for_new_execution(client, wf_id, after, timeout_s=90)
    result = {"http_status": status, "body": body[:2000] if body else ""}
    try:
        result["json"] = json.loads(body) if body else {}
    except json.JSONDecodeError:
        result["json"] = None
    result["execution_id"] = ex.get("id") if ex else None
    result["execution_status"] = ex.get("status") if ex else None
    return result


def run_approval(client: N8nClient, wf_id: str, payload: dict) -> dict:
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    status, body = post_webhook("booking-approval-callback-test", payload)
    ex = wait_for_new_execution(client, wf_id, after, timeout_s=90)
    result = {"http_status": status, "body": body[:2000] if body else ""}
    try:
        result["json"] = json.loads(body) if body else {}
    except json.JSONDecodeError:
        result["json"] = None
    result["execution_id"] = ex.get("id") if ex else None
    result["execution_status"] = ex.get("status") if ex else None
    return result


def run_task_confirm(client: N8nClient, wf_id: str, payload: dict) -> dict:
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    status, body = post_webhook("booking-task-callback-test", payload)
    ex = wait_for_new_execution(client, wf_id, after, timeout_s=90)
    result = {"http_status": status, "body": body[:2000] if body else ""}
    try:
        result["json"] = json.loads(body) if body else {}
    except json.JSONDecodeError:
        result["json"] = None
    result["execution_id"] = ex.get("id") if ex else None
    result["execution_status"] = ex.get("status") if ex else None
    return result


def run_tests(client: N8nClient, ids: dict[str, str]) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    pay_wf = ids["Arcadia - Booking Payment Record"]
    appr_wf = ids["Arcadia - Booking Approval Handler"]
    task_wf = ids["Arcadia - Booking Task Update"]
    report: dict = {"tested_at": started_at, "booking_id": BOOKING_ID, "steps": {}, "pass": True}

    prepare_test_booking()
    time.sleep(1)

    b0 = fetch_booking()
    report["steps"]["0_baseline"] = b0

    # Step 1-3: partial deposit below required
    r_partial = run_payment(
        client,
        pay_wf,
        {
            "simulate": True,
            "telegram_user_id": STAFF_USER,
            "booking_id": BOOKING_ID,
            "amount": 200,
            "currency": "USD",
            "payment_method": "bank_transfer",
            "reference": "PHASE24A-PARTIAL",
            "idempotency_key": "phase24a_pay_partial_001",
        },
    )
    b1 = fetch_booking()
    report["steps"]["1_partial_payment"] = {"result": r_partial, "booking": b1}
    if b1.get("lifecycle_status") != "PENDING_PAYMENT" or float(b1.get("paid_amount") or 0) != 200:
        report["pass"] = False

    time.sleep(1)

    # Step 4: replay same payment
    r_dup = run_payment(
        client,
        pay_wf,
        {
            "simulate": True,
            "telegram_user_id": STAFF_USER,
            "booking_id": BOOKING_ID,
            "amount": 200,
            "currency": "USD",
            "payment_method": "bank_transfer",
            "reference": "PHASE24A-PARTIAL",
            "idempotency_key": "phase24a_pay_partial_001",
        },
    )
    pay_count = count_payments("phase24a_pay_partial_001")
    report["steps"]["2_duplicate_payment"] = {
        "result": r_dup,
        "payment_rows": pay_count,
        "idempotent": r_dup.get("json", {}).get("idempotent"),
    }
    if pay_count != 1 or not r_dup.get("json", {}).get("idempotent"):
        report["pass"] = False

    time.sleep(1)

    # Step 5: remaining deposit
    r_remain = run_payment(
        client,
        pay_wf,
        {
            "simulate": True,
            "telegram_user_id": STAFF_USER,
            "booking_id": BOOKING_ID,
            "amount": 300,
            "currency": "USD",
            "payment_method": "bank_transfer",
            "reference": "PHASE24A-REMAIN",
            "idempotency_key": "phase24a_pay_remain_001",
        },
    )
    b2 = fetch_booking()
    report["steps"]["3_complete_deposit"] = {"result": r_remain, "booking": b2}
    if float(b2.get("paid_amount") or 0) < DEPOSIT_AMOUNT:
        report["pass"] = False

    time.sleep(1)

    # Step 6: should reach CONFIRMED (required tasks done + deposit satisfied)
    lifecycle = supabase_rpc("recompute_booking_lifecycle", {"p_booking_id": BOOKING_ID})
    b3 = fetch_booking()
    report["steps"]["4_confirmed_gate"] = {"lifecycle_rpc": lifecycle, "booking": b3}
    if b3.get("lifecycle_status") != "CONFIRMED":
        report["pass"] = False

    # Reset lifecycle for variance test while keeping payments
    supabase_request(
        "PATCH",
        f"bookings?booking_id=eq.{BOOKING_ID}",
        {"lifecycle_status": "PENDING_PAYMENT", "modified_by": "phase24a_variance_setup"},
    )

    time.sleep(1)

    # Step 7-8: supplier cost variance approval
    r_var = run_task_confirm(
        client,
        task_wf,
        {
            "simulate": True,
            "telegram_user_id": STAFF_USER,
            "callback_data": f"bk:task:{TASK_HOTEL_MOSCOW}:to:confirmed",
            "callback_query_id": "phase24a_var_001",
            "confirm_data": {"supplier_cost_usd": 120, "confirmation_ref": "HOTEL-VAR-001"},
        },
    )
    appr_count_1 = count_pending_approvals()
    report["steps"]["5_supplier_variance"] = {
        "result": r_var,
        "pending_approvals": appr_count_1,
    }
    if appr_count_1 != 1:
        report["pass"] = False

    approval_rows = supabase_request(
        "GET",
        f"human_approval_queue?booking_id=eq.{BOOKING_ID}&action_type=eq.supplier_price_change&status=eq.pending&select=approval_id,idempotency_key&order=created_at.desc&limit=1",
    )
    approval_id = approval_rows[0]["approval_id"] if approval_rows else None

    r_var_dup = run_task_confirm(
        client,
        task_wf,
        {
            "simulate": True,
            "telegram_user_id": STAFF_USER,
            "callback_data": f"bk:task:{TASK_HOTEL_MOSCOW}:to:confirmed",
            "callback_query_id": "phase24a_var_dup_001",
            "confirm_data": {"supplier_cost_usd": 120, "confirmation_ref": "HOTEL-VAR-001"},
        },
    )
    appr_count_2 = count_pending_approvals()
    report["steps"]["6_duplicate_variance"] = {
        "result": r_var_dup,
        "pending_approvals": appr_count_2,
        "approval_id": approval_id,
    }
    if appr_count_2 != 1:
        report["pass"] = False

    time.sleep(1)

    # Step 9: unauthorized approval
    r_unauth = run_approval(
        client,
        appr_wf,
        {
            "simulate": True,
            "telegram_user_id": UNAUTHORIZED_USER,
            "approval_id": approval_id,
            "decision": "approve",
            "callback_query_id": "phase24a_unauth_001",
        },
    )
    report["steps"]["7_unauthorized_approval"] = r_unauth
    if r_unauth.get("json", {}).get("ok") is not False:
        report["pass"] = False

    time.sleep(1)

    # Step 10: authorized deny then audit
    r_deny = run_approval(
        client,
        appr_wf,
        {
            "simulate": True,
            "telegram_user_id": STAFF_USER,
            "approval_id": approval_id,
            "decision": "deny",
            "reason": "phase24a test deny",
            "callback_query_id": "phase24a_deny_001",
        },
    )
    actions = supabase_request(
        "GET",
        f"agent_actions?booking_id=eq.{BOOKING_ID}&action_type=eq.approval_decision&order=created_at.desc&limit=3&select=action_type,status,metadata,output_summary",
    )
    report["steps"]["8_authorized_deny_audit"] = {"result": r_deny, "agent_actions": actions}

    time.sleep(1)

    # Step 11: workflow failures
    wf_failures = count_workflow_failures_since(started_at)
    report["steps"]["9_workflow_failures"] = {"count_since_test_start": wf_failures}
    if wf_failures > 0:
        report["pass"] = False

    restore_test_booking()
    report["restored_state"] = fetch_booking()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    client = load_client()
    if cmd in ("import", "all"):
        ids = upsert_workflows(client)
    else:
        ids = {w["name"]: str(w["id"]) for w in client.list_workflows()}
    if cmd == "restore":
        restore_test_booking()
        print(json.dumps(fetch_booking(), indent=2))
        return
    if cmd in ("test", "all"):
        if cmd == "all":
            time.sleep(2)
        run_tests(client, ids)


if __name__ == "__main__":
    main()
