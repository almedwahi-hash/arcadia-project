#!/usr/bin/env python3
"""Build batch7 JSON — 27 NEW verified agencies (deduped against all sent logs)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp_batch7_remaining.json"
WEB = "https://arcadia-tour.com/"

# fmt: off
BATCH7 = [
    # GCC / UAE / BH / QA — Segment A/B
    (1, "Akbar Travels (Gulf DIC)", "dic@akbargulf.com", "A", "UAE", "Russia/KZ holiday packages — DIC desk", "Your Russia tour packages from Dubai can extend to Kazakhstan/Uzbekistan via our Almaty DMC."),
    (2, "Rayna Tours (B2B desk)", "b2b@raynab2b.com", "A", "UAE", "4N/5D Almaty partner channel", "Your Almaty fixed departures and B2B partner channel align with our Arabic-market ground operations."),
    (3, "Energy Travel", "info@energytravels.ae", "A", "UAE", "KZ+UZ packages from Abu Dhabi", "Your Kazakhstan and Uzbekistan packages from Abu Dhabi match our B2B net ground rates in Almaty."),
    (4, "Orient Travel", "info@orienttravels.com", "B", "UAE", "Dubai–Tashkent CIS legacy", "Your CIS portfolio and Dubai–Central Asia routes fit our ground partner model for KZ extensions."),
    (5, "Orient Travel (Support)", "support@orienttravels.com", "B", "UAE", "Holiday operations desk", "We can support your holiday desk with Kazakhstan group ground handling and Arabic coordination."),
    (6, "Gulf Air Holidays", "stopover@gulfair.com", "C", "Bahrain", "Airline stopover packages", "We can provide Kazakhstan ground extensions for Gulf Air Holidays stopover and regional packages."),
    (7, "Aamal Travel (Outbound)", "outbound@aamal-travel.com", "A", "Qatar", "Russia outbound — expand to KZ", "Your Russia outbound programmes can add KZ/UZ segments with our Arabic-speaking Almaty DMC."),
    # India — Segment C
    (8, "Veena World", "travel@veenaworld.com", "C", "India", "9D EUKK 3-Stans groups", "Your Uzbekistan/Kazakhstan/Kyrgyzstan group series is exactly the volume we handle on the ground in Almaty."),
    (9, "Veena World (Inbound)", "inbound@veenaworld.com", "C", "India", "NRI/GCC mixed groups", "We support NRI and GCC mixed groups with English & Arabic guides across the Kazakhstan segment."),
    (10, "SOTC (MICE Plus)", "incentive.travel@sotc.in", "C", "India", "KZ group holidays + MICE", "Your Kazakhstan group holidays and incentive programmes can use our single-contract Almaty ground rates."),
    # Indonesia / Malaysia — Segment B
    (11, "Panorama JTB (Tours)", "tours@panorama-jtb.com", "B", "Indonesia", "Group tour operator Jakarta", "We can white-label Kazakhstan segments for your Indonesian group departures with halal coordination."),
    (12, "Panorama JTB (Contact Center)", "contactcenter@panorama-jtb.com", "B", "Indonesia", "ASITA-scale outbound", "Your group and incentive tours can add Central Asia via our Almaty DMC with B2B net rates."),
    (13, "Aviatour", "aviatour@avia-tour.com", "B", "Indonesia", "Large ASITA outbound", "We propose a new Silk Road group line for your Jakarta outbound portfolio — ground by Arcadia in Almaty."),
    (14, "Namira Tour", "namiratour@yahoo.co.id", "B", "Indonesia", "Halal international tours", "Your halal international programmes can include Uzbekistan+Kazakhstan with our Arabic-friendly ground team."),
    # Singapore — Segment C
    (15, "Silk Road Holiday (SG)", "hello@silkroadholiday.com", "C", "Singapore", "STB-licensed KZ+KG+UZ", "Your Singapore-licensed Central Asia group tours need reliable Almaty ground — we offer B2B net rates and direct hotel blocks."),
    # Vietnam — Segment C
    (16, "Pattours (Thien Duong A Chau)", "thienduongachau@gmail.com", "C", "Vietnam", "Silk Road 16–22D series", "Your Central Asia Silk Road group series (17 years CA/Russia) matches our daily Almaty operations."),
    (17, "Pattours (Operations)", "dieuhanh@thienduongachau.vn", "C", "Vietnam", "Tour operations Hanoi", "We can coordinate the Kazakhstan segment for your scheduled đoàn khách departures from Hanoi/HCMC."),
    # Turkey — Segment C
    (18, "Setur", "info@setur.com.tr", "C", "Turkey", "Orta Asya THY group departures 2026", "Your Central Asia group departures (Apr–Aug 2026) can use our Almaty ground hub with Turkish/Arabic guide options."),
    # Korea — Segment C/D
    (19, "Hana Tour", "15771233@hanatour.com", "C", "Korea", "KZ 7–10D product 2025–26", "Your Kazakhstan 7–10D catalogue for 2025–26 can benefit from our local DMC rates and Almaty hotel blocks."),
    # Additional verified — mixed segments
    (20, "Veena World (Corporate)", "guestconnect@veenaworld.com", "C", "India", "Corporate/MICE Central Asia", "For corporate and MICE Central Asia programmes, we offer end-to-end Kazakhstan ground with English & Arabic support."),
    (21, "Pattours (Alt inbox)", "vietnampattours@gmail.com", "C", "Vietnam", "Paradise Asia JSC groups", "Your Paradise Asia group operations can source Almaty ground through Arcadia at B2B net rates."),
    (22, "Aviatour (Web desk)", "aviaweb@avia-tour.com", "B", "Indonesia", "Avia head office web inquiries", "Following our B2B note — we can supply Kazakhstan ground for your next Indonesian group series."),
    (23, "Ajwa Travel", "info@ajwatravel.net", "B", "Malaysia", "Uzbekistan halal from RM7,690", "Your Uzbekistan halal programmes can extend to Kazakhstan with our Arabic-friendly Almaty DMC."),
    (24, "ViaVacation", "info@viavacation.my", "B", "Malaysia", "UZ+KZ+KG Muslim tours", "Your dedicated UZ/KZ/KG Muslim tour page aligns with our B2B ground rates in Almaty."),
    (25, "Dynasty Travel", "enquiries@dynastytravel.com.sg", "C", "Singapore", "Bespoke groups 10+ pax", "We can support your first Central Asia group departure with end-to-end Almaty ground handling."),
    (26, "Apple Vacations", "enquiry@applevacations.my", "C", "Malaysia", "Largest MY outbound operator", "We propose a new Central Asia group season for Apple Vacations with B2B net Almaty rates."),
    (27, "Jumbo Travel Kuwait", "hello@jumbotravels.com", "B", "Kuwait", "50+ years outbound holidays", "Your international holiday portfolio can add Silk Road group products via Arcadia ground rates."),
    (28, "Citron Tours (Holidays desk)", "holidays@citrontours.ae", "A", "UAE", "6-day Almaty group Dubai", "Your 6-day Almaty group from Dubai is a direct fit for our Arabic-speaking ground operations."),
]
# fmt: on

TEMPLATES = {
    "A": {
        "subject": "B2B Ground Partner — Kazakhstan Group Tours | Arcadia Tourism (Almaty)",
        "body": """Dear {company} Team,

Arcadia Tourism Company is an Almaty-based DMC (10+ years, 7,500+ Arabic/GCC clients):
• Net B2B ground rates for groups (15–40 pax)
• Arabic guides + halal coordination + direct hotel contracts
• KZ/UZ/RU modules with 24/7 WhatsApp tour-leader support

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


def collect_sent_emails() -> set[str]:
    sent: set[str] = set()
    patterns = [
        ROOT / ".tmp_batch4_sent.json",
        ROOT / ".tmp_batch5_sent.json",
        ROOT / ".tmp_batch5_gcc_sent.json",
        ROOT / ".tmp_batch6_sent.json",
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
        for match in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", md.read_text(encoding="utf-8")):
            if match != "info@arcadia-tour.com":
                sent.add(match.lower())
    return sent


def build_items() -> list[dict]:
    sent = collect_sent_emails()
    seen_emails: set[str] = set()
    items: list[dict] = []
    for num, company, email, seg, market, product, angle in BATCH7:
        email = email.lower()
        if email in ("dummy@example.com",) or "removed" in product.lower():
            continue
        if email in seen_emails:
            continue
        if email in sent:
            continue
        seen_emails.add(email)
        tpl = TEMPLATES.get(seg, TEMPLATES["C"])
        body = tpl["body"].format(company=company, angle=angle, web=WEB)
        items.append(
            {
                "num": num,
                "company": company,
                "email": email,
                "segment": seg,
                "market": market,
                "product": product,
                "subject": tpl["subject"],
                "body": body,
            }
        )
    # renumber sequentially
    for i, item in enumerate(items, 1):
        item["num"] = i
    return items


def write_json() -> tuple[int, int]:
    items = build_items()
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(items), len(collect_sent_emails())


if __name__ == "__main__":
    n, deduped = write_json()
    print(f"batch7={n} (deduped against {deduped} sent emails)")
