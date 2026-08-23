#!/usr/bin/env python3
"""Build batch8 JSON from deliverables/outreach-batch8-queue.csv (+ notes lookup)."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE_CSV = ROOT / "deliverables" / "outreach-batch8-queue.csv"
NOTES_CSV = ROOT / "deliverables" / "b2b-database-batch8-new.csv"
OUT = ROOT / ".tmp_batch8_remaining.json"
WEB = "https://arcadia-tour.com/"

RATES_BLOCK = """Net B2B rates (4N Almaty, ground only):
• 15–19 pax: $745/pp
• 20–29 pax: $685/pp
• 30–40 pax: $625/pp
(Charyn / Kolsai / Kaindy = optional add-ons)"""

TEMPLATES = {
    "A": {
        "subject": "B2B Ground Partner — Kazakhstan Group Tours | Arcadia Tourism (Almaty)",
        "body": """Dear {company} Team,

Arcadia Tourism Company is an Almaty-based DMC (10+ years, 7,500+ Arabic/GCC clients):
• Net B2B ground rates for groups (15–40 pax)
• Arabic guides + halal coordination + direct hotel contracts
• KZ/UZ/RU modules with 24/7 WhatsApp tour-leader support

{RATES}

{angle}

Would you be open to a 15-minute call to share our B2B rate sheet?

WhatsApp: +77051181845
info@arcadia-tour.com
{web}

Best regards,
Mohammad Ali
Business Development Manager
Arcadia Tourism Company
Almaty, Kazakhstan""",
    },
    "B": {
        "subject": "B2B DMC Partner — Kazakhstan Segment | Halal/Group Tours | Arcadia Tourism",
        "body": """Dear {company} Team,

Your group and halal outbound programmes align with our daily ground operations in Almaty and across Kazakhstan.

Arcadia Tourism Company — Almaty DMC (10+ years, 7,500+ Muslim/Arabic clients):
• Net B2B rates for groups (15–40 pax)
• Arabic-speaking guides for mixed groups
• Halal meals, prayer times, female guide options
• Single ground partner for KZ + KG + UZ segments

{RATES}

{angle}

Shall we share our B2B rate sheet and a 5-day Almaty sample for your next departure?

WhatsApp: +77051181845
info@arcadia-tour.com
{web}

Best regards,
Mohammad Ali
Arcadia Tourism Company""",
    },
    "C": {
        "subject": "B2B Ground Partner — Kazakhstan Segment | Silk Road Groups 2026 | Arcadia Tourism (Almaty)",
        "body": """Dear {company} Team,

{angle}

Arcadia Tourism Company is an Almaty-based DMC (10+ years, 7,500+ clients):
• End-to-end ground for the Kazakhstan segment (Almaty, Charyn, Kolsai, Shymbulak)
• B2B net rates for groups (15–30 pax)
• English & Russian guides (Arabic coordinator on request)
• Direct hotel blocks — better margins vs. multi-supplier setup

{RATES}

Shall we share our B2B rate sheet and discuss your 2026 Almaty segment dates?

WhatsApp: +77051181845
info@arcadia-tour.com
{web}

Best regards,
Mohammad Ali
Arcadia Tourism Company
Almaty, Kazakhstan""",
    },
}

MENA_COUNTRIES = {"Jordan", "Morocco", "Egypt"}
SILK_ROAD_COUNTRIES = {"Vietnam", "United Kingdom", "South Korea", "Philippines"}


def load_notes_by_email() -> dict[str, str]:
    notes: dict[str, str] = {}
    if not NOTES_CSV.exists():
        return notes
    with open(NOTES_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = row.get("email", "").strip().lower()
            note = row.get("notes", "").strip()
            if email and note:
                notes[email] = note
    return notes


def note_to_angle(notes: str, country: str) -> str:
    if not notes:
        return "Your Central Asia group programmes would benefit from our B2B net ground rates in Almaty."
    lead = notes.split(";")[0].strip()
    if country in MENA_COUNTRIES:
        return (
            f"Your {lead} fits our Arabic-speaking Almaty DMC model "
            "for Kazakhstan ground extensions and MENA outbound groups."
        )
    if country in SILK_ROAD_COUNTRIES:
        return f"Your {lead} matches our daily Almaty ground operations and B2B net rates for group series."
    return f"Your {lead} aligns with our Kazakhstan ground partner programme and B2B net Almaty rates."


def template_key(tier: str, country: str) -> str:
    if country in MENA_COUNTRIES:
        return "A"
    if country in SILK_ROAD_COUNTRIES:
        return "C"
    if tier in TEMPLATES:
        return tier
    return "B"


def collect_sent_emails() -> set[str]:
    sent: set[str] = set()
    patterns = [
        ROOT / ".tmp_batch4_sent.json",
        ROOT / ".tmp_batch5_sent.json",
        ROOT / ".tmp_batch5_gcc_sent.json",
        ROOT / ".tmp_batch6_sent.json",
        ROOT / ".tmp_batch7_sent.json",
        ROOT / ".tmp_batch8_sent.json",
    ]
    for path in patterns:
        if not path.exists():
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for row in rows:
            em = str(row.get("email", "")).strip().lower()
            if em:
                sent.add(em)
    for md in ROOT.glob("deliverables/outreach-sent-log-*.md"):
        for match in re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            md.read_text(encoding="utf-8"),
        ):
            if match != "info@arcadia-tour.com":
                sent.add(match.lower())
    exclude_path = ROOT / "deliverables" / "exclude_emails.txt"
    if exclude_path.exists():
        for line in exclude_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "@" in line:
                sent.add(line.split("\t")[-1].strip().lower())
    return sent


def load_queue_rows() -> list[dict]:
    if not QUEUE_CSV.exists():
        raise FileNotFoundError(f"Missing queue: {QUEUE_CSV}")
    rows: list[dict] = []
    with open(QUEUE_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            num_raw = row.get("#", row.get("num", "")).strip()
            if not num_raw.isdigit():
                continue
            rows.append(
                {
                    "num": int(num_raw),
                    "company": row["company"].strip(),
                    "country": row["country"].strip(),
                    "email": row["email"].strip().lower(),
                    "website": row.get("website", "").strip(),
                    "priority_tier": row.get("priority_tier", "B").strip().upper(),
                }
            )
    rows.sort(key=lambda r: r["num"])
    return rows


def build_items() -> list[dict]:
    sent = collect_sent_emails()
    notes_map = load_notes_by_email()
    seen_emails: set[str] = set()
    items: list[dict] = []

    for row in load_queue_rows():
        email = row["email"]
        if email in seen_emails or email in sent:
            continue
        seen_emails.add(email)

        tier = row["priority_tier"]
        seg = template_key(tier, row["country"])
        tpl = TEMPLATES[seg]
        angle = note_to_angle(notes_map.get(email, ""), row["country"])
        body = tpl["body"].format(
            company=row["company"],
            angle=angle,
            web=WEB,
            RATES=RATES_BLOCK,
        )
        items.append(
            {
                "num": row["num"],
                "company": row["company"],
                "email": email,
                "segment": seg,
                "market": row["country"],
                "priority_tier": tier,
                "subject": tpl["subject"],
                "body": body,
            }
        )

    return items


def write_json() -> tuple[int, int]:
    items = build_items()
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items), len(collect_sent_emails())


if __name__ == "__main__":
    n, deduped = write_json()
    print(f"batch8={n} (deduped against {deduped} sent/excluded emails)")
