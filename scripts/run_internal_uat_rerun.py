#!/usr/bin/env python3
"""Re-run internal UAT after defect-fix patch — Kazakhstan Almaty scenario."""
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

from n8n_phase1_operational import n8n_public_base, normalize_n8n_api_base, trigger_webhook

CI = "arcadia-phase25-ci-probe-2026"
LEAD = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
QUOTE = "ARC-459161"
BOOKING = "KA-2026-118"
HOTEL_TASK = "c621cf83-845a-4b54-bd8c-cfda6a679f0a"
STAFF = "493831958"
UNAUTH = "999999001"
OTHER_LEAD = "b6fada92-a0c4-45a9-a5f7-2e60897af3c8"
REPORT = ROOT / "deliverables" / "arcadia-internal-uat-rerun-results.json"


def base_url() -> str:
    return n8n_public_base(normalize_n8n_api_base(os.environ.get("N8N_API_URL", "")))


def post(path: str, payload: dict) -> tuple[int, dict]:
    url = f"{base_url()}/webhook/{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"raw": raw[:800]}


def cb(data: str, user: str = STAFF, confirm: dict | None = None, cid: str | None = None) -> tuple[int, dict]:
    return post(
        "booking-task-callback-test",
        {
            "simulate": True,
            "telegram_user_id": user,
            "callback_data": data,
            "callback_query_id": cid or f"uat_rerun_{int(time.time() * 1000)}_{hash(data) % 100000}",
            "chat_id": user,
            "confirm_data": confirm or {},
        },
    )


def has_body(body: dict) -> bool:
    return bool(body) and ("ok" in body or "error" in body)


def main() -> int:
    report: dict = {
        "uat_tag": "internal_uat_kz_almaty_20260828_rerun",
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "patch": "uat-def-fix-001-002",
        "booking_id": BOOKING,
        "acceptance": [],
        "steps": [],
        "negatives": [],
        "laila_audit": {},
        "safety": {},
    }

    def acc(name: str, passed: bool, detail: dict) -> None:
        report["acceptance"].append({"name": name, "passed": passed, **detail})
        print(f"[{'PASS' if passed else 'FAIL'}] ACC:{name}")

    # --- Acceptance 1-3: callback structured JSON ---
    st, tasks = cb(f"bk:tasks:{BOOKING}", cid=f"uat_tasks_rerun_{int(time.time())}")
    acc(
        "1_tasks_callback_structured",
        st == 200 and tasks.get("ok") is True and tasks.get("action") == "tasks" and tasks.get("listed", 0) > 0,
        {"http_status": st, "response": tasks},
    )

    st, view = cb(f"bk:view:{BOOKING}", cid=f"uat_view_rerun_{int(time.time())}")
    acc(
        "1b_view_callback_structured",
        st == 200 and view.get("ok") is True and view.get("action") == "view",
        {"http_status": st, "response": view},
    )

    st, opened = cb(f"bk:task:{HOTEL_TASK}:open", cid=f"uat_open_rerun_{int(time.time())}")
    acc(
        "1c_open_callback_structured",
        st == 200 and opened.get("ok") is True and opened.get("action") == "open",
        {"http_status": st, "response": opened},
    )

    st, bad = cb("bk:invalid", cid=f"uat_bad_rerun_{int(time.time())}")
    acc(
        "2_malformed_callback_error",
        has_body(bad) and bad.get("ok") is False and bad.get("error") in ("unknown_callback", "invalid_callback"),
        {"http_status": st, "response": bad},
    )

    # --- Acceptance 3-6: confirmation ref protection ---
    CONF_REF = opened.get("confirmation_ref") or "UAT-RERUN-HTL-FINAL"

    st, conf1 = cb(
        f"bk:task:{HOTEL_TASK}:resp:confirmed",
        confirm={"confirmation_ref": CONF_REF, "idempotency_key": f"uat_rerun_conf1_{int(time.time())}"},
        cid=f"uat_conf1_{int(time.time())}",
    )
    acc(
        "3_first_or_replay_confirm",
        conf1.get("ok") is True,
        {"http_status": st, "response": conf1},
    )

    st, replay = cb(
        f"bk:task:{HOTEL_TASK}:resp:confirmed",
        confirm={"confirmation_ref": CONF_REF, "idempotency_key": f"uat_rerun_replay_{int(time.time())}"},
        cid=f"uat_replay_{int(time.time())}",
    )
    acc(
        "4_same_ref_replay_idempotent",
        replay.get("ok") is True and (replay.get("idempotent") is True or replay.get("confirmation_ref") == CONF_REF),
        {"http_status": st, "response": replay},
    )

    st, conflict = cb(
        f"bk:task:{HOTEL_TASK}:resp:confirmed",
        confirm={"confirmation_ref": "UAT-RERUN-HTL-WRONG", "idempotency_key": f"uat_rerun_conflict_{int(time.time())}"},
        cid=f"uat_conflict_{int(time.time())}",
    )
    acc(
        "3b_different_ref_rejected",
        conflict.get("ok") is False and conflict.get("error") == "confirmation_ref_conflict",
        {"http_status": st, "response": conflict},
    )

    st, override_unauth = cb(
        f"bk:task:{HOTEL_TASK}:resp:confirmed",
        user=UNAUTH,
        confirm={"confirmation_ref": "UAT-RERUN-HTL-OVERRIDE", "idempotency_key": f"uat_unauth_ov_{int(time.time())}"},
        cid=f"uat_unauth_ov_{int(time.time())}",
    )
    acc(
        "6_unauthorized_correction_blocked",
        override_unauth.get("ok") is False and override_unauth.get("error") == "unauthorized",
        {"http_status": st, "response": override_unauth},
    )

    st, override_no_reason = cb(
        f"bk:task:{HOTEL_TASK}:resp:confirmed",
        confirm={
            "confirmation_ref": "UAT-RERUN-HTL-NOREASON-ATTEMPT",
            "override_confirmation_ref": True,
            "idempotency_key": f"uat_ov_noreason_{int(time.time())}",
        },
        cid=f"uat_ov_noreason_{int(time.time())}",
    )
    acc(
        "6b_override_without_reason_blocked",
        override_no_reason.get("ok") is False and override_no_reason.get("error") == "confirmation_ref_conflict",
        {"http_status": st, "response": override_no_reason},
    )

    st, override_ok = cb(
        f"bk:task:{HOTEL_TASK}:resp:confirmed",
        confirm={
            "confirmation_ref": "UAT-RERUN-HTL-FINAL",
            "override_confirmation_ref": True,
            "override_reason": "UAT staff correction of typo in supplier ref",
            "idempotency_key": f"uat_ov_ok_{int(time.time())}",
        },
        cid=f"uat_ov_ok_{int(time.time())}",
    )
    acc(
        "5_authorized_override_audited",
        override_ok.get("ok") is True
        and override_ok.get("action") in ("confirmation_ref_override", "supplier_response"),
        {"http_status": st, "response": override_ok},
    )

    # --- Acceptance 7-8: booking idempotent + draft ---
    st, book = post(
        "booking-staff-book-test",
        {"simulate": True, "telegram_user_id": STAFF, "command_text": f"/book {LEAD} {QUOTE}", "chat_id": STAFF},
    )
    acc(
        "7_booking_idempotent",
        book.get("ok") is True and book.get("booking_id") == BOOKING and book.get("idempotent") is True,
        {"http_status": st, "response": book},
    )

    st, draft = post(
        "booking-supplier-draft",
        {"task_id": HOTEL_TASK, "requested_by": "uat_rerun", "regenerate": False},
    )
    acc(
        "8_draft_consistency",
        draft.get("ok") is True
        and draft.get("facts", {}).get("booking_id") == BOOKING
        and draft.get("facts", {}).get("guest_count") == 2
        and draft.get("auto_send") is False,
        {"http_status": st, "draft_id": draft.get("draft_id"), "facts": draft.get("facts")},
    )

    # --- Negatives ---
    _, wrong = post(
        "booking-staff-book-test",
        {"simulate": True, "telegram_user_id": STAFF, "command_text": f"/book {LEAD} ARC-000000", "chat_id": STAFF},
    )
    report["negatives"].append({"name": "wrong_quote", "passed": wrong.get("ok") is False, "response": wrong})

    _, other = post(
        "booking-staff-book-test",
        {"simulate": True, "telegram_user_id": STAFF, "command_text": f"/book {OTHER_LEAD} {QUOTE}", "chat_id": STAFF},
    )
    report["negatives"].append(
        {
            "name": "quote_other_lead",
            "passed": other.get("ok") is False,
            "response": other,
        }
    )

    # --- Laila audit (DEF-003) ---
    try:
        st_l, body_l = trigger_webhook(os.environ.get("N8N_API_URL", ""), "phase1-laila-scenario-test", {"scenario": "new_customer"}, test_mode=False)
        laila_status = {"webhook": "phase1-laila-scenario-test", "http_status": st_l, "body_preview": (body_l or "")[:300]}
    except Exception as e:
        laila_status = {"webhook": "phase1-laila-scenario-test", "error": str(e)}

    report["laila_audit"] = {
        "phase1_laila_scenario_test": laila_status,
        "workflow_file_in_repo": False,
        "referenced_in": "scripts/n8n_phase1_operational.py",
        "production_laila_workflow_in_repo": "Arcadia - Laila Telegram V5 Phase1 Working.json (Telegram, not WhatsApp harness)",
        "steps_1_4_conclusion": "require_manual_whatsapp_uat",
        "note": "No permanent unauthenticated test webhook deployed; lead pre-seeding used for booking UAT",
    }

    report["safety"] = {
        "auto_send_on_draft": draft.get("auto_send") is False,
        "note": "Verify booking_handoff_enabled, auto_send_enabled, reminder policy via Supabase separately",
    }

    passed = sum(1 for a in report["acceptance"] if a["passed"])
    total = len(report["acceptance"])
    report["summary"] = {
        "acceptance_passed": passed,
        "acceptance_total": total,
        "overall": "PASS" if passed == total else "FAIL",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
