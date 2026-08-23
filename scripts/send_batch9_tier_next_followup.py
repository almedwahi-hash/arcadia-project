#!/usr/bin/env python3
"""Batch 9 Tier NEXT follow-ups: Siyana, Tailwinds, Villa, Rose, Chan, Rayna, AMI, CTC."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import (  # noqa: E402
    ROOT as _ROOT,
    load_dotenv,
    load_sent_keys,
    run_outreach_batch,
)

EMAILS_JSON = _ROOT / ".tmp_batch9_tier_next_followup.json"
SENT_LOG_JSON = _ROOT / ".tmp_batch9_tier_next_followup_sent.json"
SENT_LOG_MD = _ROOT / "deliverables" / "outreach-sent-log-batch9-ar.md"
ALMATY = timezone(timedelta(hours=5))

GENERIC_BODY = """Hi,

I wanted to follow up briefly on my earlier message about B2B ground handling for Kazakhstan group tours.

Arcadia Tourism is a licensed DMC in Almaty — we provide net rates for groups of 15–40 pax (hotels, transport, licensed guide, halal meals, city and premium day excursions).

If Kazakhstan or Central Asia is on your 2026 product roadmap, please reply by email with:
1. Estimated group size (pax band)
2. Target travel dates or departure window

We will send a written net quote within 24 hours — no obligation.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
"""

TARGETS = [
    {
        "num": 9,
        "id": "next-siyana",
        "company": "Siyana Travel",
        "email": "info@siyanatours.com",
        "subject": "Re: B2B Ground Rates — Almaty & Tashkent Groups | Arcadia Tourism × Siyana",
        "body": GENERIC_BODY,
    },
    {
        "num": 10,
        "id": "next-tailwinds",
        "company": "Tailwinds Travels",
        "email": "info@tailwindstravels.co",
        "subject": "Re: B2B Ground Partner — 12N Central Asia Group Tours | Arcadia Tourism (Almaty)",
        "body": """Hi,

Following up on our B2B proposal for your 12N Silk Road / Central Asia group programmes.

We can provide the Kazakhstan ground segment (Almaty, Charyn, Kolsai) with halal meal coordination as a white-label block for your Singapore groups.

Please reply by email with estimated pax and departure dates — we will send a written net quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
""",
    },
    {
        "num": 11,
        "id": "next-villa",
        "company": "Villa Tours & Travel",
        "email": "villatourstravel@yahoo.co.id",
        "subject": "Re: B2B Ground Partner — 3–5 Stans Halal Groups | Arcadia Tourism (Almaty)",
        "body": """Hi,

Following up on our B2B proposal for your 3–5 Stans / Kazakhstan–Uzbekistan muslim group programmes.

Arcadia can handle the Almaty ground segment with halal meals and licensed guides — net rates for rombongan 15–40 pax.

Please reply by email with pax count and travel dates for a written quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
""",
    },
    {
        "num": 12,
        "id": "next-rose",
        "company": "Rose Travel",
        "email": "info@rosetravel.sa",
        "subject": "Re: B2B Ground Partner — Kazakhstan & Russia Groups | Arcadia Tourism × Rose Travel",
        "body": GENERIC_BODY,
    },
    {
        "num": 13,
        "id": "next-chan",
        "company": "Chan Brothers Travel",
        "email": "inquiry@chanbrothers.com.sg",
        "subject": "Re: B2B Ground Rates — Central Asia Group Series | Arcadia Tourism × Chan Brothers",
        "body": """Hi,

Following up on our B2B ground rates proposal for your Central Asia group series.

We can support Almaty segments across your Singapore departures with net white-label rates (15–40 pax).

Please reply by email with pax band and dates — written quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
""",
    },
    {
        "num": 14,
        "id": "next-rayna",
        "company": "Rayna Tours",
        "email": "partners@raynatours.com",
        "subject": "Re: B2B Ground Rates — Almaty 4N/5D Groups × Rayna | Arcadia Tourism",
        "body": """Hi,

Following up with your B2B / partners desk on our Almaty 4N/5D group ground proposal.

Happy to share updated net rates or a sample white-label itinerary for your partners channel.

Please reply by email with target pax and departure window — we will confirm in writing within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
""",
    },
    {
        "num": 15,
        "id": "next-ami",
        "company": "AMI Travel",
        "email": "info@amitravel.my",
        "subject": "Re: Ground Partner — 12D 3-Stans Halal Groups | Arcadia Tourism",
        "body": """Hi,

Following up on our proposal to support the Kazakhstan segment of your 12D 3-Stans / Almaty muslim series.

We offer net B2B ground rates for kumpulan 15–40 pax with halal meals and licensed guides in Almaty.

Please reply by email with your 2026 departure dates and expected pax — written quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
""",
    },
    {
        "num": 16,
        "id": "next-ctc",
        "company": "CTC Travel",
        "email": "enquiry@ctc.com.sg",
        "subject": "Re: B2B Ground Partner — Grand Silk Road 2026 Almaty Segment | Arcadia Tourism",
        "body": """Hi,

Following up on our Almaty ground segment offer for your Grand Silk Road 2026 departures (12 scheduled).

We can supply consistent hotels, transport, and guides for each Almaty block — net rates white-label under CTC.

Please reply by email with which departure(s) and pax estimates you want priced first — quote in writing within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
""",
    },
]


def already_followed_today(email: str) -> bool:
    """Skip if this address was logged as sent today in any batch9 log."""
    today = datetime.now(ALMATY).strftime("%Y-%m-%d")
    email = email.lower()
    for path in (
        SENT_LOG_JSON,
        _ROOT / ".tmp_batch9_gcc_followup_sent.json",
        _ROOT / ".tmp_batch9_hot_followup_sent.json",
        _ROOT / ".tmp_batch9_tier_next_followup_sent.json",
    ):
        if not path.is_file():
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for r in rows:
            if r.get("status") != "sent":
                continue
            if str(r.get("email", "")).lower() != email:
                continue
            if str(r.get("time", "")).startswith(today):
                return True
    if SENT_LOG_MD.is_file():
        text = SENT_LOG_MD.read_text(encoding="utf-8")
        for line in text.splitlines():
            if email in line.lower() and today in line and "✅" in line:
                return True
    return False


def build_emails() -> list[dict]:
    items: list[dict] = []
    skipped: list[str] = []
    sent_keys = load_sent_keys(SENT_LOG_JSON)
    for t in TARGETS:
        email = t["email"].lower()
        if already_followed_today(email):
            skipped.append(f"{t['company']} ({email}) — already followed today")
            continue
        key = t.get("id") or email
        if key in sent_keys or email in sent_keys:
            skipped.append(f"{t['company']} ({email}) — already in sent log")
            continue
        items.append(
            {
                "num": t["num"],
                "id": t["id"],
                "company": t["company"],
                "email": email,
                "subject": t["subject"],
                "body": t["body"].strip() + "\n",
            }
        )
    EMAILS_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s in skipped:
        print(f"[SKIP-BUILD] {s}")
    return items


def append_sent_log_md(sent_records: list[dict]) -> None:
    if not SENT_LOG_MD.is_file():
        return
    text = SENT_LOG_MD.read_text(encoding="utf-8")
    new_rows: list[str] = []
    for r in sent_records:
        if r.get("status") != "sent":
            continue
        email = r.get("to") or r.get("email", "")
        row = (
            f"| {r.get('num','')} | {r.get('company','')} | {email} | "
            f"✅ Tier NEXT follow-up | {r.get('time','')} |"
        )
        if row in text or email.lower() in text and "Tier NEXT" in text and str(r.get("time", ""))[:10] in text:
            # avoid exact dup; still append if not present
            if f"| {email} |" in text and "Tier NEXT" in text:
                continue
        if row not in text:
            new_rows.append(row)
    if not new_rows:
        return
    marker = "\n\n---\n"
    note = "\n*Tier NEXT follow-up — Batch 9*\n"
    if marker in text:
        head, rest = text.split(marker, 1)
        SENT_LOG_MD.write_text(
            head.rstrip() + "\n" + "\n".join(new_rows) + marker + rest,
            encoding="utf-8",
        )
    else:
        SENT_LOG_MD.write_text(text.rstrip() + "\n" + "\n".join(new_rows) + note, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Batch 9 Tier NEXT follow-ups")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", type=str, default="")
    parser.add_argument("--delay", type=float, default=45.0)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--no-pdf", action="store_true", default=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--with-pdf", action="store_true", help="Attach rate sheet PDF")
    args = parser.parse_args()

    load_dotenv()
    if args.build or not EMAILS_JSON.exists():
        n = len(build_emails())
        print(f"Built {n} Tier NEXT follow-up targets.")

    code = run_outreach_batch(
        batch_label="Batch 9 Tier NEXT follow-up",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only=args.only,
        delay=args.delay,
        force=args.force,
        attach_pdf_flag=bool(args.with_pdf),
    )

    if not args.dry_run and SENT_LOG_JSON.is_file():
        try:
            append_sent_log_md(json.loads(SENT_LOG_JSON.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
