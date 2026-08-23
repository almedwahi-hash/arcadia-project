#!/usr/bin/env python3
"""Build batch6 JSON from sales-outreach-batch6-targets-ar.md."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "deliverables" / "sales-outreach-batch6-targets-ar.md"
OUT = ROOT / ".tmp_batch6_remaining.json"
WEB = "https://arcadia-tour.com/"

TEMPLATES = {
    "A": {
        "subject": "B2B Ground Partner — Kazakhstan Group Tours | Arcadia Tourism (Almaty)",
        "body": """Dear {company} Team,

We are reaching out from Arcadia Tourism Company — an Almaty-based DMC specializing in Arabic-speaking travelers (10+ years, 7,500+ GCC clients).

We offer:
• Net B2B ground rates for groups (15–40 pax)
• Arabic guides + halal coordination + direct hotel contracts in Almaty
• 5-day Almaty modules and Silk Road extensions (KZ/UZ/RU)
• 24/7 WhatsApp support during departures

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
        "subject": "B2B Ground Partnership — Central Asia Groups | Arcadia Tourism",
        "body": """Dear {company} Team,

Arcadia Tourism Company is a Kazakhstan-based DMC with daily ground operations across Almaty and Central Asia — ideal for your outbound group programmes.

• B2B net rates for groups (15–40 pax)
• English, Arabic, and Russian-speaking guides
• Single ground partner for KZ + UZ + RU segments
• Halal meal coordination on request

{angle}

Shall we share our rate sheet and sample 5–6 day Almaty itinerary?

WhatsApp: +77051181845
info@arcadia-tour.com
{web}

Best regards,
Mohammad Ali
Arcadia Tourism Company""",
    },
    "C": {
        "subject": "B2B Ground Partner — Central Asia Add-on | Arcadia Tourism (Almaty)",
        "body": """Dear {company} Team,

We support airline-led and regional holiday programmes with dedicated Kazakhstan ground handling from our Almaty HQ.

Arcadia Tourism Company (10+ years):
• B2B net ground rates for group stopovers and extensions
• English & Arabic coordinators
• Direct hotel blocks in Almaty
• 24/7 WhatsApp line for tour leaders

{angle}

Can we schedule a brief call to discuss ground support for your Central Asia segments?

WhatsApp: +77051181845
info@arcadia-tour.com
{web}

Best regards,
Mohammad Ali
Arcadia Tourism Company""",
    },
}

ANGLES = {
    1: "Your KZ+Russia holiday packages from Dubai align with our Arabic-market ground expertise.",
    2: "Your Almaty + Tashkent group packages are a direct match for our B2B net rates.",
    3: "Your Kazakhstan marketing from Dubai fits our visa-friendly group ground support.",
    4: "Your Kazakhstan and Moscow holiday lines are ideal for a dedicated Almaty DMC partner.",
    5: "Your Russia tour packages from the Gulf can extend to KZ/UZ via our inbound ground team.",
    6: "Your 4N/5D Almaty fixed itinerary and Partner page make you an ideal B2B ground supplier match.",
    7: "Your Central Asia expedition groups from Dubai can benefit from our Almaty operations hub.",
    8: "Following our note in June — we would value a B2B ground partnership for your leisure groups.",
    9: "Your KZ/UZ/RU catalogue and Saudi client base match our Arabic-speaking DMC services.",
    10: "Your Kanoo GCC network can add Central Asia group holidays via our Almaty ground rates.",
    11: "Your Russia/Kazakhstan selector programmes fit our Moscow + Almaty B2B coordination.",
    12: "Your international holiday portfolio can add Silk Road group products through Arcadia ground rates.",
    13: "Your Manama outbound centre can source CIS ground through our Kazakhstan DMC team.",
    14: "Your Gulf Air Holidays stopover products may benefit from Kazakhstan ground extensions via Arcadia.",
    15: "Your Qatar holiday catalog can include KZ/UZ group modules with our Almaty ground partner rates.",
    16: "Your Russia outbound desk can expand to KZ/UZ with Arabic guide support from our Almaty team.",
    17: "Your Kuwait holidays division can add Central Asia group products with our B2B net rates.",
    18: "Your Kuwait outbound programmes can include halal-friendly Central Asia via our Almaty DMC.",
}


def parse_rows() -> list[dict]:
    text = MD.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|") or "@" not in line:
            continue
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        rows.append(
            {
                "num": int(cells[0]),
                "company": cells[1],
                "email": cells[2].lower(),
                "segment": cells[3].upper(),
            }
        )
    return rows


def build() -> list[dict]:
    items = []
    for row in parse_rows():
        seg = row["segment"] if row["segment"] in TEMPLATES else "B"
        tpl = TEMPLATES[seg]
        angle = ANGLES.get(row["num"], "We would welcome a B2B ground partnership discussion.")
        body = tpl["body"].format(company=row["company"], angle=angle, web=WEB)
        items.append(
            {
                "num": row["num"],
                "company": row["company"],
                "email": row["email"],
                "segment": seg,
                "subject": tpl["subject"],
                "body": body,
            }
        )
    return items


def write_json() -> int:
    items = build()
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items)


if __name__ == "__main__":
    print(f"batch6={write_json()}")
