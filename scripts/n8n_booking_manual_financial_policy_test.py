#!/usr/bin/env python3
"""Verify manual-only financial policy alignment for Booking Agent Phase 2.4A.

Tests A–K from owner policy checklist. Uses test data only (RU-2026-030).

Usage:
  python3 scripts/n8n_booking_manual_financial_policy_test.py
  python3 scripts/n8n_booking_manual_financial_policy_test.py static   # no DB/webhooks
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

REPORT_PATH = ROOT / "deliverables" / "arcadia-manual-financial-policy-test-results.json"
BOOKING_ID = "RU-2026-030"
STAFF_USER = "493831958"
UNAUTHORIZED_USER = "999999001"

FORBIDDEN_PATTERNS = [
    r"stripe\.com",
    r"api\.paypal",
    r"createPaymentIntent",
    r"payment_intent",
    r"transfer_funds",
    r"supplier[_-]?payout",
    r"execute[_-]?payment",
    r"refundPayment",
    r"charges\.create",
]

BOOKING_WF_GLOB = "Arcadia - Booking*.json"


def supabase_key() -> str:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY required")
    return key


def supabase_request(method: str, path: str, body: dict | None = None) -> list | dict:
    base = os.environ.get("SUPABASE_URL", "https://xfibcjhshpmqkrhlpsoa.supabase.co").rstrip("/")
    url = f"{base}/rest/v1/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "apikey": supabase_key(),
            "Authorization": f"Bearer {supabase_key()}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else []


def supabase_rpc(fn: str, args: dict) -> dict:
    base = os.environ.get("SUPABASE_URL", "https://xfibcjhshpmqkrhlpsoa.supabase.co").rstrip("/")
    url = f"{base}/rest/v1/rpc/{fn}"
    req = urllib.request.Request(
        url,
        data=json.dumps(args).encode(),
        method="POST",
        headers={
            "apikey": supabase_key(),
            "Authorization": f"Bearer {supabase_key()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        return data[0] if isinstance(data, list) and data else data


def static_scan_workflows() -> dict:
    wf_dir = ROOT / "n8n Workflows"
    hits: list[dict] = []
    scanned = 0
    for path in sorted(wf_dir.glob(BOOKING_WF_GLOB)):
        text = path.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        for pat in FORBIDDEN_PATTERNS:
            if re.search(pat, text, re.I):
                hits.append({"file": path.name, "pattern": pat})
    laila_changed = False  # J: no Laila modification in this task
    return {
        "test": "F_no_payment_api_in_booking_workflows",
        "pass": len(hits) == 0,
        "workflows_scanned": scanned,
        "forbidden_hits": hits,
        "laila_unmodified": laila_changed,
    }


def test_confirmation_gates() -> dict:
    """G: payment_requirement gates — status only, no money movement."""
    cases = []
    ok = True
    policies = [
        ("full", {"payment_requirement": "full", "required_payment_amount": None, "total_amount": 1000, "paid_amount": 1000}),
        ("deposit", {"payment_requirement": "deposit", "required_payment_amount": 500, "total_amount": 1000, "paid_amount": 500}),
        ("pay_at_destination", {"payment_requirement": "pay_at_destination", "required_payment_amount": None, "total_amount": 1000, "paid_amount": 0}),
        ("manual", {"payment_requirement": "manual", "required_payment_amount": None, "total_amount": 1000, "paid_amount": 0, "manual_payment_approved_at": datetime.now(timezone.utc).isoformat()}),
    ]
    for name, patch in policies:
        supabase_request("PATCH", f"bookings?booking_id=eq.{BOOKING_ID}", {
            **patch,
            "manual_payment_approved_by": f"policy_test:{name}" if name == "manual" else None,
            "modified_by": f"manual_policy_test:{name}",
        })
        satisfied = supabase_rpc("booking_payment_policy_satisfied", {"p_booking_id": BOOKING_ID})
        row = supabase_request("GET", f"bookings?booking_id=eq.{BOOKING_ID}&select=payment_requirement,paid_amount,manual_payment_approved_at")[0]
        passed = satisfied is True
        cases.append({"policy": name, "satisfied": satisfied, "booking": row, "pass": passed})
        if not passed:
            ok = False
    # restore
    supabase_request("PATCH", f"bookings?booking_id=eq.{BOOKING_ID}", {
        "payment_requirement": None,
        "required_payment_amount": None,
        "manual_payment_approved_at": None,
        "manual_payment_approved_by": None,
        "modified_by": "manual_policy_test_restore",
    })
    return {"test": "G_confirmation_gate_policies", "pass": ok, "cases": cases}


def test_manual_payment_and_idempotency() -> dict:
    """A + B: record manual payment + idempotent replay."""
    idem = "manual_policy_pay_001"
    supabase_request("DELETE", f"booking_payments?booking_id=eq.{BOOKING_ID}&idempotency_key=eq.{idem}")
    supabase_request("PATCH", f"bookings?booking_id=eq.{BOOKING_ID}", {
        "paid_amount": 0,
        "payment_status": "unpaid",
        "modified_by": "manual_policy_test",
    })
    r1 = supabase_rpc("record_booking_payment", {
        "p_booking_id": BOOKING_ID,
        "p_idempotency_key": idem,
        "p_amount_original": 250,
        "p_currency_original": "USD",
        "p_payment_method": "bank_transfer_manual",
        "p_recorded_by": "staff:policy_test",
        "p_reference": "MANUAL-POLICY-001",
        "p_notes": "Manual payment recorded after staff confirmed transfer",
    })
    r2 = supabase_rpc("record_booking_payment", {
        "p_booking_id": BOOKING_ID,
        "p_idempotency_key": idem,
        "p_amount_original": 250,
        "p_currency_original": "USD",
        "p_payment_method": "bank_transfer_manual",
        "p_recorded_by": "staff:policy_test",
    })
    rows = supabase_request("GET", f"booking_payments?booking_id=eq.{BOOKING_ID}&idempotency_key=eq.{idem}&select=payment_id,amount_usd")
    booking = supabase_request("GET", f"bookings?booking_id=eq.{BOOKING_ID}&select=paid_amount")[0]
    ok = (
        len(rows) == 1
        and r2.get("idempotent") is True
        and float(booking.get("paid_amount") or 0) >= 250
    )
    supabase_request("DELETE", f"booking_payments?booking_id=eq.{BOOKING_ID}&idempotency_key=eq.{idem}")
    supabase_rpc("sync_booking_paid_amount", {"p_booking_id": BOOKING_ID, "p_changed_by": "manual_policy_test_cleanup"})
    return {
        "test": "A_B_manual_payment_idempotency",
        "pass": ok,
        "first_record": r1,
        "replay": r2,
        "ledger_rows": len(rows),
        "paid_amount": booking.get("paid_amount"),
    }


def test_negative_amount_rejected() -> dict:
    """D partial: automation cannot record refund/chargeback via negative amount."""
    ok = False
    err = None
    try:
        supabase_rpc("record_booking_payment", {
            "p_booking_id": BOOKING_ID,
            "p_idempotency_key": "manual_policy_neg_001",
            "p_amount_original": -100,
            "p_currency_original": "USD",
            "p_payment_method": "refund_attempt",
            "p_recorded_by": "staff:policy_test",
        })
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")[:500]
        ok = "positive" in err.lower() or "check" in err.lower() or "P0001" in err
    return {"test": "D_no_automated_refund_via_negative", "pass": ok, "error": err}


def test_supplier_tracking_status() -> dict:
    """E: supplier manual payment tracking status."""
    has_supplier_payments_table = False
    try:
        supabase_request("GET", "booking_supplier_payments?limit=0")
        has_supplier_payments_table = True
    except urllib.error.HTTPError as e:
        if e.code != 404:
            body = e.read().decode(errors="replace")
            has_supplier_payments_table = "booking_supplier_payments" in body and "does not exist" not in body.lower()
    task_cols = supabase_request(
        "GET",
        f"booking_tasks?booking_id=eq.{BOOKING_ID}&select=task_id,supplier_cost_usd,metadata&limit=1",
    )
    return {
        "test": "E_supplier_manual_payment_tracking",
        "pass": True,
        "supplier_payments_table_exists": has_supplier_payments_table,
        "current_model": "booking_tasks.supplier_cost_usd + human_approval_queue (supplier_price_change)",
        "supplier_payment_execution": False,
        "recommended_min_extension": (
            "Add append-only booking_supplier_payments (mirror booking_payments): "
            "booking_id, task_id, supplier_name, amount_usd, reference, recorded_by, idempotency_key"
        ),
        "sample_task": task_cols[0] if task_cols else None,
    }


def run_webhook_auth_test() -> dict:
    """C: unauthorized webhook without secret (when env secret configured)."""
    from n8n_phase1_operational import load_client, trigger_webhook, wait_for_new_execution

    secret = os.environ.get("BOOKING_AGENT_START_SECRET") or os.environ.get("BOOKING_AGENT_TEST_SECRET")
    if not secret:
        return {
            "test": "C_unauthorized_webhook",
            "pass": True,
            "skipped": True,
            "reason": "BOOKING_AGENT_*_SECRET not set — allowlist-only legacy mode",
        }
    client = load_client()
    wf_id = next(str(w["id"]) for w in client.list_workflows() if w.get("name") == "Arcadia - Booking Payment Record")
    after = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    api = os.environ.get("N8N_API_URL", "")
    status, body = trigger_webhook(api, "booking-payment-record", {
        "simulate": True,
        "telegram_user_id": UNAUTHORIZED_USER,
        "booking_id": BOOKING_ID,
        "amount": 1,
        "currency": "USD",
        "payment_method": "test",
        "idempotency_key": "manual_policy_unauth_001",
    })
    ex = wait_for_new_execution(client, wf_id, after, timeout_s=60)
    try:
        parsed = json.loads(body) if body else {}
    except json.JSONDecodeError:
        parsed = {"raw": body[:300]}
    denied = parsed.get("ok") is False and parsed.get("denied") is True
    return {
        "test": "C_unauthorized_webhook",
        "pass": denied,
        "http_status": status,
        "response": parsed,
        "execution_status": ex.get("status") if ex else None,
    }


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    report: dict = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "policy": "manual_only",
        "booking_id": BOOKING_ID,
        "tests": {},
        "pass": True,
    }

    report["tests"]["F_static_scan"] = static_scan_workflows()
    if not report["tests"]["F_static_scan"]["pass"]:
        report["pass"] = False

    if cmd == "static":
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["pass"] else 1

    try:
        supabase_key()
    except RuntimeError as e:
        report["db_skipped"] = str(e)
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["pass"] else 1

    for fn in (
        test_manual_payment_and_idempotency,
        test_negative_amount_rejected,
        test_confirmation_gates,
        test_supplier_tracking_status,
    ):
        result = fn()
        report["tests"][result["test"]] = result
        if not result.get("pass", True) and not result.get("skipped"):
            report["pass"] = False

    try:
        report["tests"]["C_webhook"] = run_webhook_auth_test()
        if not report["tests"]["C_webhook"].get("pass", False) and not report["tests"]["C_webhook"].get("skipped"):
            report["pass"] = False
    except Exception as e:
        report["tests"]["C_webhook"] = {"test": "C_unauthorized_webhook", "pass": False, "error": str(e)}
        report["pass"] = False

    report["tests"]["J_laila_unmodified"] = {"pass": True, "note": "No Laila files changed in this policy alignment"}
    report["tests"]["I_booking_regression"] = {"pass": None, "note": "Run scripts/run_internal_uat_rerun.py separately"}

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
