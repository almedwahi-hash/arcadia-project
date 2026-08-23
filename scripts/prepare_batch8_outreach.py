#!/usr/bin/env python3
"""Prepare batch 8 outreach queue and Arabic ready doc (no send)."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIV = ROOT / "deliverables"

COUNTRY_ORDER = {
    "Vietnam": 1,
    "United Kingdom": 2,
    "Philippines": 3,
    "South Korea": 4,
    "Jordan": 5,
}

TIER_ORDER = {"A": 0, "B": 1, "C": 2}


def load_exclude() -> set[str]:
    emails: set[str] = set()
    for line in (DELIV / "exclude_emails.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "@" in line:
            emails.add(line.split("\t")[-1].strip().lower())
    return emails


def assign_tier(row: dict) -> str:
    country = row["country"]
    if country in COUNTRY_ORDER:
        return "A"
    if country in ("Japan", "India", "Turkey", "Hong Kong", "Indonesia", "Malaysia", "Singapore"):
        return "B"
    return "C"


def load_rows(exclude: set[str]) -> list[dict]:
    rows: list[dict] = []
    with open(DELIV / "b2b-database-batch8-new.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = row["email"].strip().lower()
            if email in exclude:
                continue
            row["priority_tier"] = assign_tier(row)
            row["_country_rank"] = COUNTRY_ORDER.get(row["country"], 99)
            rows.append(row)
    rows.sort(
        key=lambda r: (
            r["_country_rank"],
            TIER_ORDER[r["priority_tier"]],
            r["company"].lower(),
        )
    )
    return rows


def write_queue(rows: list[dict]) -> None:
    path = DELIV / "outreach-batch8-queue.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#", "company", "country", "email", "website", "priority_tier"])
        for i, row in enumerate(rows, 1):
            w.writerow(
                [
                    i,
                    row["company"],
                    row["country"],
                    row["email"],
                    row["website"],
                    row["priority_tier"],
                ]
            )


def tier_a_top15(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["priority_tier"] == "A"][:15]


def write_ready_ar(rows: list[dict]) -> None:
    tiers = Counter(r["priority_tier"] for r in rows)
    top15 = tier_a_top15(rows)
    today = date.today().isoformat()

    lines = [
        "# Batch 8 — جاهز للإرسال (بدون إرسال)",
        "",
        f"> **التاريخ:** {today}  ",
        "> **الحالة:** ⏸️ **READY** — في قائمة الانتظار، لم يُرسَل شيء  ",
        "> **المصدر:** `deliverables/b2b-database-batch8-new.csv` (48 موثّقة)  ",
        "> **From:** info@arcadia-tour.com | **PDF:** `deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.pdf`",
        "",
        "---",
        "",
        "## 1. ملخص",
        "",
        "| البند | العدد |",
        "|-------|------:|",
        f"| **إجمالي قائمة الانتظار** | **{len(rows)}** |",
        f"| **Priority A** (فيتنام، UK، الفلبين، كوريا، الأردن) | **{tiers['A']}** |",
        f"| **Priority B** (اليابان، الهند، تركيا، HK، SG/MY/ID) | **{tiers['B']}** |",
        f"| **Priority C** (المغرب، مصر) | **{tiers['C']}** |",
        f"| **مُرسَل** | **0** |",
        "",
        "**ترتيب القائمة:** فيتنام → UK → الفلبين → كوريا → الأردن → باقي الأسواق (B ثم C).",
        "",
        "---",
        "",
        "## 2. الموجة الأولى — Tier A (أفضل 15)",
        "",
        "| # | Company | Country | Email |",
        "|---|---------|---------|-------|",
    ]

    for i, row in enumerate(top15, 1):
        lines.append(
            f"| {i} | {row['company']} | {row['country']} | {row['email']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. تشغيل SMTP (نفس نمط Batch 6/7)",
            "",
            "> **تذكير:** أرفق `Arcadia-B2B-Rate-Sheet-Almaty.pdf` مع كل رسالة.",
            "",
            "```powershell",
            "python scripts/batch8_targets.py",
            "python scripts/send_batch8_outreach.py --build-from-md --dry-run",
            "python scripts/send_batch8_outreach.py --only 1 --delay 0",
            "python scripts/send_batch8_outreach.py --delay 3",
            "```",
            "",
            "| البند | المسار |",
            "|-------|--------|",
            "| قائمة الانتظار | `deliverables/outreach-batch8-queue.csv` |",
            "| JSON المعلّق | `.tmp_batch8_remaining.json` |",
            "| سجل المُرسَل | `.tmp_batch8_sent.json` |",
            "| إصلاح SMTP | `deliverables/email-smtp-fix-ar.md` |",
            "",
            "**Idempotent:** يتخطى أي email موجود في sent log.",
            "",
            "---",
            "",
            "*Batch 8 outreach ready — 48 queued — 0 sent — لا إرسال حتى موافقة صريحة*",
        ]
    )

    (DELIV / "outreach-batch8-ready-ar.md").write_text("\n".join(lines), encoding="utf-8")


def update_master_status(rows: list[dict]) -> None:
    path = DELIV / "outreach-master-status-ar.md"
    text = path.read_text(encoding="utf-8")
    tiers = Counter(r["priority_tier"] for r in rows)

    batch8_section = f"""
---

## Batch 8 (48 — READY)

> **الحالة:** ⏸️ **READY** — 48 في قائمة الانتظار، **0 مُرسَل** (2026-07-09)

| البند | القيمة |
|-------|--------|
| **المصدر** | `b2b-database-batch8-new.csv` |
| **قائمة الانتظار** | `outreach-batch8-queue.csv` |
| **جاهز للإرسال** | `outreach-batch8-ready-ar.md` |
| **Tier A / B / C** | {tiers['A']} / {tiers['B']} / {tiers['C']} |
| **مُرسَل SMTP** | **0/48** |

**الترتيب:** فيتنام (10) → UK (8) → الفلبين (6) → كوريا (3) → الأردن (4) → باقي الأسواق (17).

**Script (عند الموافقة):** `scripts/send_batch8_outreach.py` + `scripts/batch8_targets.py`

"""

    marker = "## Batch 7 FOLLOW-UP"
    if marker in text:
        text = text.replace(marker, batch8_section.strip() + "\n\n" + marker)
    else:
        text = text.rstrip() + "\n" + batch8_section

    # Update executive summary table if present
    old_line = "| **Batch 7** | **45/45 ✅** (موجتان: 19 موثّقة @03:58 + 26 جديدة @04:15) |"
    new_line = (
        "| **Batch 7** | **45/45 ✅** (موجتان: 19 موثّقة @03:58 + 26 جديدة @04:15) |\n"
        f"| **Batch 8** | **0/48 ⏸️ READY** (queued 2026-07-09) |"
    )
    if old_line in text and "**Batch 8**" not in text:
        text = text.replace(old_line, new_line)

    old_update = "> **آخر تحديث:** 2026-07-05 04:16 Almaty (UTC+5)"
    text = text.replace(old_update, "> **آخر تحديث:** 2026-07-09 Almaty (UTC+5)")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    exclude = load_exclude()
    rows = load_rows(exclude)
    if len(rows) != 48:
        raise SystemExit(f"Expected 48 rows, got {len(rows)}")
    write_queue(rows)
    write_ready_ar(rows)
    update_master_status(rows)
    tiers = Counter(r["priority_tier"] for r in rows)
    print(f"Queue: {len(rows)} rows | A={tiers['A']} B={tiers['B']} C={tiers['C']}")


if __name__ == "__main__":
    main()
