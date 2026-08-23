#!/usr/bin/env python3
"""Batch 10 RIGHT cold outreach — max 20, PDF rate sheet, 45s delay."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import ROOT as _ROOT, load_dotenv, run_outreach_batch  # noqa: E402

EMAILS_JSON = _ROOT / ".tmp_batch10_emails.json"
SENT_LOG_JSON = _ROOT / ".tmp_batch10_sent.json"
CSV_PATH = _ROOT / "deliverables" / "b2b-database-batch10-close-right.csv"

BODY_TMPL = """Dear {company} Team,

Arcadia Tourism is a licensed DMC in Almaty. We partner with outbound operators who send groups to Kazakhstan and need reliable local ground handling — hotels, transport, licensed guides, and halal meal coordination — white-label under your brand.

We noticed your Kazakhstan / Almaty programmes and would like to propose net B2B rates for groups of 15–40 pax (Jun–Oct 2026 season). Our indicative Almaty 5D/4N ground rates:

| Pax band | Net USD/person |
|----------|----------------|
| 15–19 | $745 |
| 20–29 | $685 |
| 30–40 | $625 |

Attached: Arcadia B2B Rate Sheet (Almaty) with premium day add-ons (Charyn, Kolsai, Kaindy).

Please reply by email with your estimated group size (pax) and target travel dates. We will send a written net quote within 24 hours — no obligation.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
"""


def build_emails(limit: int = 20) -> list[dict]:
    import csv

    items: list[dict] = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            if i > limit:
                break
            company = row["company"].strip()
            email = row["email"].strip().lower()
            country = row.get("country", "").strip()
            items.append(
                {
                    "num": i,
                    "id": f"b10-{i}-{email}",
                    "company": company,
                    "email": email,
                    "subject": (
                        f"B2B Partnership — Net Rates for Almaty Groups | "
                        f"Arcadia Tourism × {company}"
                    ),
                    "body": BODY_TMPL.format(company=company),
                    "country": country,
                }
            )
    EMAILS_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Batch 10 RIGHT B2B outreach")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", type=str, default="")
    parser.add_argument("--delay", type=float, default=45.0)
    parser.add_argument("--build", action="store_true", help="Rebuild JSON from CSV")
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    load_dotenv()
    if args.build or not EMAILS_JSON.exists():
        n = len(build_emails(args.limit))
        print(f"Built {n} batch10 targets from CSV.")

    return run_outreach_batch(
        batch_label="Batch 10 RIGHT outreach",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only=args.only,
        delay=args.delay,
        force=args.force,
        attach_pdf_flag=not args.no_pdf,
    )


if __name__ == "__main__":
    raise SystemExit(main())
