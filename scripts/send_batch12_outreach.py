#!/usr/bin/env python3
"""Batch 12: NEW GCC cold outreach — 8 verified targets (Aug 2026)."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import load_dotenv, run_outreach_batch, safe_print  # noqa: E402

CSV_PATH = ROOT / "deliverables" / "b2b-database-batch12-gcc-new.csv"
EMAILS_JSON = ROOT / ".tmp_batch12_emails.json"
SENT_LOG_JSON = ROOT / ".tmp_batch12_sent.json"
EXCLUDE = ROOT / "deliverables" / "exclude_emails.txt"

COLD_EN = """Dear {company} Team,

Arcadia Tourism is a licensed DMC in Almaty (+10 years serving Arab travellers — 7,500+ clients). We partner with outbound operators in the GCC who sell Kazakhstan group programmes and need reliable white-label ground handling: hotels, transport, licensed guides, and halal meal coordination.

We noticed your Kazakhstan / Central Asia programmes and would like to propose net B2B rates for groups of 15–40 pax (Sep 2026–Jun 2027 season). Indicative Almaty 5D/4N ground:

| Pax band | Net USD/person |
|----------|----------------|
| 15–19 | $745 |
| 20–29 | $685 |
| 30–40 | $625 |

Attached: Arcadia B2B Rate Sheet (Almaty).

Reply with estimated pax and travel dates — we will send a written net quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
WhatsApp: +77051181845
"""

COLD_AR = """السلام عليكم فريق {company}،

نحن **شركة أركاديا السياحية** — DMC مرخّص في ألماتي (+10 سنوات، +7500 عميل عربي). نتعاون مع مشغّلي المجموعات في الخليج الذين يبيعون برامج كازاخستان ويحتاجون ground handling موثوق: فنادق، نقل، مرشدون، وتنسيق وجبات حلال — white-label تحت علامتكم.

لاحظنا برامجكم السياحية إلى كازاخستان ونودّ اقتراح أسعار B2B صافية لمجموعات 15–40 مسافر (موسم سبتمبر 2026 – يونيو 2027). ألماتي 5 أيام/4 ليالٍ تقريباً:

| عدد المسافرين | السعر الصافي USD/شخص |
|---------------|----------------------|
| 15–19 | 745 |
| 20–29 | 685 |
| 30–40 | 625 |

مرفق: Rate Sheet B2B (\u0623\u0644\u0645\u0627\u062a\u064a).

ردّوا بـ pax + التواريخ — نرسل عرضاً مكتوباً خلال 24 ساعة.

مع التحية،
\u0645\u062d\u0645\u062f \u0639\u0644\u064a — \u0645\u062f\u064a\u0631 \u062a\u0637\u0648\u064a\u0631 \u0627\u0644\u0623\u0639\u0645\u0627\u0644
Arcadia Tourism | Almaty DMC
info@arcadia-tour.com | https://arcadia-tour.com/
واتساب: +77051181845
"""

AR_COMPANIES = {"Almurtahel Travel"}


def load_exclude() -> set[str]:
    out: set[str] = set()
    if not EXCLUDE.exists():
        return out
    for line in EXCLUDE.read_text(encoding="utf-8").splitlines():
        for part in line.split():
            if "@" in part:
                out.add(part.strip().lower())
    return out


def build_targets() -> list[dict]:
    exclude = load_exclude()
    items: list[dict] = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            email = row["email"].strip().lower()
            if email in exclude:
                safe_print(f"[SKIP] {row['company']} -> {email} (exclude)")
                continue
            company = row["company"].strip()
            ar = company in AR_COMPANIES
            body_tpl = COLD_AR if ar else COLD_EN
            subject = (
                f"شراكة B2B — مجموعات كازاخستان | أركاديا × {company}"
                if ar
                else f"B2B partnership — Kazakhstan group ground | Arcadia × {company}"
            )
            items.append(
                {
                    "num": i,
                    "id": f"b12-{i:02d}",
                    "company": company,
                    "email": row["email"].strip(),
                    "subject": subject,
                    "body": body_tpl.format(company=company),
                }
            )
    return items


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", type=str, default="")
    args = parser.parse_args()

    targets = build_targets()
    EMAILS_JSON.write_text(json.dumps(targets, ensure_ascii=False, indent=2), encoding="utf-8")
    safe_print(f"Prepared {len(targets)} targets -> {EMAILS_JSON}")

    return run_outreach_batch(
        batch_label="Batch 12 GCC",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only=args.only,
        delay=45.0,
        force=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())
