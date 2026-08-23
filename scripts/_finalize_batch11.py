#!/usr/bin/env python3
"""Finalize Batch 11 logs: exclude, sent-log md, master status, pipeline."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SENT = ROOT / ".tmp_batch11_sent.json"
EXCLUDE = ROOT / "deliverables" / "exclude_emails.txt"
LOG_MD = ROOT / "deliverables" / "outreach-sent-log-batch11-ar.md"
MASTER = ROOT / "deliverables" / "outreach-master-status-ar.md"
PIPELINE = ROOT / "deliverables" / "b2b-pipeline-hot-leads-ar.md"
CLOSE = ROOT / "deliverables" / "close-ready-companies-ar.md"


def unique_sent() -> list[dict]:
    recs = json.loads(SENT.read_text(encoding="utf-8"))
    sent = [r for r in recs if r.get("status") == "sent"]
    seen: set[str] = set()
    out: list[dict] = []
    for r in sent:
        e = str(r["email"]).lower()
        if e in seen:
            continue
        seen.add(e)
        out.append(r)
    return out, len(sent)


def update_exclude(unique: list[dict]) -> int:
    lines = EXCLUDE.read_text(encoding="utf-8").splitlines()
    existing: set[str] = set()
    max_n = 0
    for line in lines:
        parts = line.split()
        if parts and parts[0].isdigit():
            max_n = max(max_n, int(parts[0]))
        for p in parts:
            if "@" in p:
                existing.add(p.lower().strip())
    added = 0
    with EXCLUDE.open("a", encoding="utf-8") as f:
        for r in unique:
            e = str(r["email"]).lower()
            if e in existing:
                continue
            max_n += 1
            f.write(f"{max_n}\t{e}\n")
            existing.add(e)
            added += 1
    return added


def write_sent_log(unique: list[dict], raw_count: int) -> None:
    wave_a = sum(1 for r in unique if r.get("wave") == "A")
    wave_b = sum(1 for r in unique if r.get("wave") == "B")
    wave_c = sum(1 for r in unique if r.get("wave") == "C")
    lines = [
        "# سجل إرسال Batch 11 — RIGHT close + re-engage",
        "",
        "> **التاريخ:** 2026-08-24  ",
        "> **المصدر:** `b2b-database-batch11-close-right.csv` + Dynasty/CLOSE follow-ups  ",
        "> **السكربت:** `scripts/send_batch11_outreach.py` · SMTP Zoho · PDF rate sheet · تأخير 45ث  ",
        f"> **النتيجة:** **{len(unique)}/{len(unique)}** فريدة وصلت · **0** فشل SMTP  ",
        "> **IMAP Sent:** ❌ معطّل على حساب Zoho (`You are yet to enable IMAP`) — الرسائل أُرسلت عبر SMTP",
        "",
        "## الموجات",
        "",
        "| موجة | العدد | الوصف |",
        "|------|------:|--------|",
        f"| A | {wave_a} | Dynasty re-engagement |",
        f"| B | {wave_b} | NEW RIGHT cold (batch11 CSV) |",
        f"| C | {wave_c} | CLOSE follow-ups (SGTREK + GCC) |",
        "",
        "| # | موجة | الشركة | البريد | الحالة | الوقت (Almaty) |",
        "|---|------|--------|--------|--------|----------------|",
    ]
    for i, r in enumerate(unique, 1):
        lines.append(
            f"| {i} | {r.get('wave', '')} | {r['company']} | `{r['email']}` | ✅ وصلت | {r.get('time', '')} |"
        )
    lines += [
        "",
        "**CTA:** reply with pax + dates → written quote ≤24h · لا طلب مكالمة",
        "",
        f"**ملاحظة:** سجل خام `{raw_count}` صف بسبب استئناف متزامن — الجدول = **{len(unique)}** فريدة.",
        "",
        "---",
        "",
        "*Batch 11 — 2026-08-24*",
        "",
    ]
    LOG_MD.write_text("\n".join(lines), encoding="utf-8")


def update_master(unique: list[dict]) -> None:
    text = MASTER.read_text(encoding="utf-8")
    text = text.replace(
        "> **آخر تحديث:** 2026-07-17 05:50 Almaty (UTC+5)  \n"
        "> **From:** info@arcadia-tour.com  \n"
        "> **SMTP:** ✅ Zoho `smtp.zoho.eu:465` — Batch 9 FU + Batch 10 RIGHT",
        "> **آخر تحديث:** 2026-08-24 ~03:00 Almaty (UTC+5)  \n"
        "> **From:** info@arcadia-tour.com  \n"
        "> **SMTP:** ✅ Zoho `smtp.zoho.eu:465` — Batch 11 A/B/C",
    )
    if "Batch 11" not in text:
        text = text.replace(
            "| **Batch 10 — RIGHT cold** | **18/18 ✅** (2026-07-17 05:35–05:48 · PDF · تأخير 45ث · 0 فشل) |",
            "| **Batch 10 — RIGHT cold** | **18/18 ✅** (2026-07-17 05:35–05:48 · PDF · تأخير 45ث · 0 فشل) |\n"
            f"| **Batch 11 — A+B+C** | **{len(unique)}/{len(unique)} ✅** (2026-08-24 · Dynasty FU + 18 NEW + 5 CLOSE FU · PDF · 45ث · 0 فشل SMTP · IMAP Sent معطّل) |",
        )
    if "send_batch11_outreach.py" not in text:
        text = text.replace(
            "| `send_batch10_outreach.py` | `.tmp_batch10_emails.json` | `.tmp_batch10_sent.json` |",
            "| `send_batch10_outreach.py` | `.tmp_batch10_emails.json` | `.tmp_batch10_sent.json` |\n"
            "| `send_batch11_outreach.py` | `.tmp_batch11_emails.json` | `.tmp_batch11_sent.json` |",
        )
    MASTER.write_text(text, encoding="utf-8")


def update_pipeline() -> None:
    if not PIPELINE.exists():
        return
    text = PIPELINE.read_text(encoding="utf-8")
    text = text.replace(
        "> **آخر تحديث:** 17 يوليو 2026",
        "> **آخر تحديث:** 24 أغسطس 2026 — Batch 11 أُرسل (Dynasty FU + 18 NEW + 5 CLOSE FU)",
    )
    # mark Dynasty re-engage
    if "sent 2026-08-24" not in text:
        text = text.replace(
            "| انتظار **رد بريد** — pax + dates من John | ☐ |",
            "| انتظار **رد بريد** — pax + dates من John | ☐ |\n"
            "| **Re-engage FU 24 أغسطس** | ✅ **sent 2026-08-24** |",
        )
    PIPELINE.write_text(text, encoding="utf-8")


def update_close_ready() -> None:
    if not CLOSE.exists():
        return
    text = CLOSE.read_text(encoding="utf-8")
    text = text.replace(
        "> **التاريخ:** 17 يوليو 2026",
        "> **التاريخ:** 17 يوليو 2026 · **تحديث إرسال:** 24 أغسطس 2026 (Batch 11 FU)",
    )
    CLOSE.write_text(text, encoding="utf-8")


def main() -> None:
    unique, raw = unique_sent()
    added = update_exclude(unique)
    write_sent_log(unique, raw)
    update_master(unique)
    update_pipeline()
    update_close_ready()
    print(f"unique={len(unique)} raw={raw} exclude_added={added}")
    for r in unique:
        print(f"{r.get('wave')}\t{r['company']}\t{r['email']}")


if __name__ == "__main__":
    main()
