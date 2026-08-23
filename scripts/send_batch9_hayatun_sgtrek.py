#!/usr/bin/env python3
"""Batch 9 hot follow-ups: Hayatun + SGTREK (email-first, PDF, no call CTA)."""
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

EMAILS_JSON = _ROOT / ".tmp_batch9_hot_followup.json"
SENT_LOG_JSON = _ROOT / ".tmp_batch9_hot_followup_sent.json"
TEMPLATES_MD = _ROOT / "deliverables" / "email-followup-templates-ar.md"
PIPELINE_MD = _ROOT / "deliverables" / "b2b-pipeline-hot-leads-ar.md"
BATCH9_PLAN_MD = _ROOT / "deliverables" / "batch9-email-first-plan-ar.md"
ALMATY = timezone(timedelta(hours=5))

TARGETS = [
    {
        "num": 2,
        "id": "hayatun",
        "company": "Hayatun Tour",
        "email": "hayatuntour@gmail.com",
        "section": "## 2. Hayatun Tour (Indonesia)",
        "pipeline_markers": ("Hayatun", "hayatuntour@gmail.com"),
    },
    {
        "num": 3,
        "id": "sgtrek",
        "company": "SGTREK",
        "email": "contact@sgtrek.com",
        "section": "## 3. SGTREK (Singapore)",
        "pipeline_markers": ("SGTREK", "contact@sgtrek.com"),
    },
]


def parse_section(md: str, section_header: str) -> tuple[str, str]:
    part = md.split(section_header, 1)[1].split("\n---", 1)[0]
    subj_m = re.search(r"\*\*Subject:\*\*\s*(.+?)\s*(?:\r?\n|$)", part)
    body_m = re.search(r"```\n(Dear .+?)\n```", part, re.DOTALL)
    if not subj_m or not body_m:
        raise ValueError(f"Could not parse {section_header}")
    return subj_m.group(1).strip(), body_m.group(1).strip()


def build_emails_json() -> list[dict]:
    md = TEMPLATES_MD.read_text(encoding="utf-8")
    items: list[dict] = []
    for t in TARGETS:
        subject, body = parse_section(md, t["section"])
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


def update_pipeline(sent_records: list[dict]) -> None:
    ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
    for rec in sent_records:
        if rec.get("status") != "sent":
            continue
        email = rec["email"].lower()
        target = next((t for t in TARGETS if t["email"].lower() == email), None)
        if not target:
            continue
        mark = f"sent {ts}"
        for path in (PIPELINE_MD, BATCH9_PLAN_MD):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines()
            new_lines: list[str] = []
            for line in lines:
                if target["pipeline_markers"][1] in line and "|" in line:
                    if "sent 20" in line:
                        new_lines.append(line)
                        continue
                    if line.rstrip().endswith("| ☐ |"):
                        line = line.replace("| ☐ |", f"| ✅ **{mark}** |")
                    elif "| ☐" in line:
                        line = re.sub(r"\|\s*☐\s*\|", f"| ✅ **{mark}** |", line, count=1)
                new_lines.append(line)
            path.write_text("\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delay", type=float, default=30.0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    load_dotenv()
    build_emails_json()

    rc = run_outreach_batch(
        batch_label="Batch 9 hot follow-up (Hayatun + SGTREK)",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only="",
        delay=args.delay,
        force=args.force,
        attach_pdf_flag=True,
    )

    if not args.dry_run and rc == 0 and SENT_LOG_JSON.is_file():
        try:
            sent_all = json.loads(SENT_LOG_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sent_all = []
        update_pipeline([r for r in sent_all if r.get("status") == "sent"])

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
