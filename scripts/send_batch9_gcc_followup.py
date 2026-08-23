#!/usr/bin/env python3
"""Batch 9 GCC follow-ups: Citron, Arabian Sky, Tabeer, Alqaed, Aamal (thread Reply, no PDF)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import (  # noqa: E402
    ROOT as _ROOT,
    load_dotenv,
    run_outreach_batch,
)

EMAILS_JSON = _ROOT / ".tmp_batch9_gcc_followup.json"
SENT_LOG_JSON = _ROOT / ".tmp_batch9_gcc_followup_sent.json"
TEMPLATES_MD = _ROOT / "deliverables" / "email-followup-templates-ar.md"
PIPELINE_MD = _ROOT / "deliverables" / "b2b-pipeline-hot-leads-ar.md"
BATCH9_PLAN_MD = _ROOT / "deliverables" / "batch9-email-first-plan-ar.md"
SENT_LOG_MD = _ROOT / "deliverables" / "outreach-sent-log-batch9-ar.md"
ALMATY = timezone(timedelta(hours=5))

TARGETS = [
    {
        "num": 4,
        "id": "gcc-citron",
        "company": "Citron Tours",
        "email": "holidays@citrontours.ae",
        "subsection": "### 4.1 Citron Tours",
        "pipeline_markers": ("Citron", "holidays@citrontours.ae"),
    },
    {
        "num": 5,
        "id": "gcc-arabian-sky",
        "company": "Arabian Sky Travels",
        "email": "info@arabianskytravels.com",
        "subsection": "### 4.4 Arabian Sky Travels",
        "pipeline_markers": ("Arabian Sky", "info@arabianskytravels.com"),
    },
    {
        "num": 6,
        "id": "gcc-tabeer",
        "company": "Tabeer Tours",
        "email": "inquiries@tabeertours.com",
        "subsection": "### 4.2 Tabeer Tours",
        "pipeline_markers": ("Tabeer", "inquiries@tabeertours.com"),
    },
    {
        "num": 7,
        "id": "gcc-alqaed",
        "company": "Alqaed Travel",
        "email": "info@alqaedtravel.com",
        "subsection": "### 4.3 Alqaed Travel",
        "pipeline_markers": ("Alqaed", "info@alqaedtravel.com"),
    },
    {
        "num": 8,
        "id": "gcc-aamal",
        "company": "Aamal Travel",
        "email": "sales@aamal-travel.com",
        "subsection": "### 4.5 Aamal Travel",
        "pipeline_markers": ("Aamal", "sales@aamal-travel.com"),
    },
]


def parse_subsection(md: str, sub_header: str) -> tuple[str, str]:
    part = md.split(sub_header, 1)[1].split("###", 1)[0]
    subj_m = re.search(r"\*\*Subject:\*\*\s*(.+?)\s*(?:\r?\n|$)", part)
    body_m = re.search(r"```\n(Hi,.+?)\n```", part, re.DOTALL)
    if not subj_m or not body_m:
        raise ValueError(f"Could not parse {sub_header}")
    return subj_m.group(1).strip(), body_m.group(1).strip()


def build_emails_json() -> list[dict]:
    md = TEMPLATES_MD.read_text(encoding="utf-8")
    items: list[dict] = []
    for t in TARGETS:
        subject, body = parse_subsection(md, t["subsection"])
        items.append(
            {
                "num": t["num"],
                "id": t["id"],
                "company": t["company"],
                "email": t["email"],
                "subject": subject,
                "body": body,
            }
        )
    EMAILS_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def mark_sent_line(line: str, mark: str) -> str:
    if "sent 20" in line:
        return line
    if re.search(r"\|\s*☐\s*\|?\s*$", line):
        return re.sub(r"\|\s*☐\s*\|?\s*$", f"| ✅ **{mark}** |", line)
    if re.search(r"\|\s*☐\s*\|", line):
        return re.sub(r"\|\s*☐\s*\|", f"| ✅ **{mark}** |", line, count=1)
    return line


def update_pipeline(sent_records: list[dict]) -> None:
    ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
    mark = f"sent {ts}"
    sent_emails = {r["email"].lower() for r in sent_records if r.get("status") == "sent"}

    for path in (PIPELINE_MD, BATCH9_PLAN_MD):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lines: list[str] = []
        for line in text.splitlines():
            updated = line
            for t in TARGETS:
                if t["email"].lower() not in sent_emails:
                    continue
                if t["pipeline_markers"][1] in line and "|" in line:
                    updated = mark_sent_line(line, mark)
                    break
                if t["pipeline_markers"][0] in line and "|" in line and "☐" in line:
                    updated = mark_sent_line(line, mark)
                    break
            if path == BATCH9_PLAN_MD and sent_emails >= {t["email"].lower() for t in TARGETS}:
                if line.strip() == "- [ ] Citron · Tabeer · Alqaed · Arabian Sky · Aamal — GCC thread Reply (S)":
                    updated = "- [x] Citron · Tabeer · Alqaed · Arabian Sky · Aamal — GCC thread Reply (S)"
            lines.append(updated)
        path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")


def ensure_sent_log_md() -> None:
    if SENT_LOG_MD.is_file():
        return
    hot = _ROOT / ".tmp_batch9_hot_followup_sent.json"
    rows = ["# سجل إرسال Batch 9 — email-first follow-ups", "", "| # | الشركة | البريد | الحالة | الوقت |", "|---|--------|--------|--------|-------|"]
    if hot.is_file():
        try:
            for r in json.loads(hot.read_text(encoding="utf-8")):
                if r.get("status") == "sent":
                    rows.append(
                        f"| {r.get('num','')} | {r.get('company','')} | {r.get('email','')} | ✅ وصلت | {r.get('time','')} |"
                    )
        except json.JSONDecodeError:
            pass
    rows.extend(["", "---", ""])
    SENT_LOG_MD.write_text("\n".join(rows) + "\n", encoding="utf-8")


def append_sent_log_md(sent_records: list[dict]) -> None:
    ensure_sent_log_md()
    text = SENT_LOG_MD.read_text(encoding="utf-8")
    new_rows: list[str] = []
    for r in sent_records:
        if r.get("status") != "sent":
            continue
        email = r["email"].lower()
        num = r.get("num", "")
        row = f"| {num} | {r.get('company','')} | {email} | ✅ GCC thread Reply | {r.get('time','')} |"
        if row in text:
            continue
        new_rows.append(row)
    if not new_rows:
        return
    marker = "\n\n---\n"
    if marker in text:
        head, _ = text.split(marker, 1)
        SENT_LOG_MD.write_text(head.rstrip() + "\n" + "\n".join(new_rows) + marker + "\n*GCC 5 follow-up — Batch 9*\n", encoding="utf-8")
    else:
        SENT_LOG_MD.write_text(text.rstrip() + "\n" + "\n".join(new_rows) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delay", type=float, default=45.0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    load_dotenv()
    build_emails_json()

    rc = run_outreach_batch(
        batch_label="Batch 9 GCC follow-up (5 agencies)",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only="",
        delay=args.delay,
        force=args.force,
        attach_pdf_flag=False,
    )

    if not args.dry_run and SENT_LOG_JSON.is_file():
        try:
            sent_all = json.loads(SENT_LOG_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sent_all = []
        sent_ok = [r for r in sent_all if r.get("status") == "sent"]
        if sent_ok:
            update_pipeline(sent_ok)
            append_sent_log_md(sent_ok)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
