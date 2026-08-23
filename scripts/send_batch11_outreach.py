#!/usr/bin/env python3
"""Batch 11: Dynasty re-engage + NEW RIGHT cold + close-ready FU. SMTP + IMAP Sent append."""
from __future__ import annotations

import argparse
import csv
import imaplib
import json
import ssl
import sys
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import (  # noqa: E402
    FROM_EMAIL,
    PDF_PATH,
    append_sent,
    build_message,
    load_dotenv,
    load_sent_keys,
    normalize_item,
    safe_print,
    sent_key,
    smtp_config,
)

ALMATY = timezone(timedelta(hours=5))
EMAILS_JSON = ROOT / ".tmp_batch11_emails.json"
SENT_LOG_JSON = ROOT / ".tmp_batch11_sent.json"
CSV_PATH = ROOT / "deliverables" / "b2b-database-batch11-close-right.csv"
EXCLUDE = ROOT / "deliverables" / "exclude_emails.txt"

COLD_BODY = """Dear {company} Team,

Arcadia Tourism is a licensed DMC in Almaty. We partner with outbound operators who send groups to Kazakhstan and need reliable local ground handling — hotels, transport, licensed guides, and halal meal coordination — white-label under your brand.

We noticed your Kazakhstan / Almaty programmes and would like to propose net B2B rates for groups of 15–40 pax (Sep 2026–Jun 2027 season). Our indicative Almaty 5D/4N ground rates:

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

DYNASTY_BODY = """Dear John / Dynasty Planners Team,

Following up on our July exchange regarding the integrated Charyn / Kolsai / Kaindy programme and DMC partnership.

We remain ready to lock net rates for your next Almaty group once you share estimated pax and travel dates. Attached again: our B2B Rate Sheet (Almaty).

Reply with pax + dates and we will issue a written net quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
"""

FU_BODY = """Dear {company} Team,

Following up on our July note regarding Almaty / Kazakhstan group ground handling.

We are ready to lock net B2B rates for your next departure. Attached: Arcadia B2B Rate Sheet (Almaty).

Please reply with estimated pax and travel dates — we will send a written net quote within 24 hours.

Best regards,

Mohammad Ali
Business Development Manager
Arcadia Tourism Company | Licensed DMC, Almaty
info@arcadia-tour.com | https://arcadia-tour.com/
"""

WAVE_A = [
    {
        "num": 1,
        "id": "b11-wa-dynasty",
        "wave": "A",
        "company": "Dynasty Travel",
        "email": "planners@dynastytravel.com.sg",
        "subject": "Following up — July Almaty quote ready to lock | Arcadia × Dynasty",
        "body": DYNASTY_BODY,
    }
]

WAVE_C = [
    {
        "num": 101,
        "id": "b11-wc-sgtrek",
        "wave": "C",
        "company": "SGTREK",
        "email": "contact@sgtrek.com",
        "subject": "Following up — Almaty segment ready to lock | Arcadia × SGTREK",
        "body": FU_BODY.format(company="SGTREK"),
    },
    {
        "num": 102,
        "id": "b11-wc-citron",
        "wave": "C",
        "company": "Citron Tours",
        "email": "holidays@citrontours.ae",
        "subject": "Following up — July Almaty rates ready to lock | Arcadia × Citron",
        "body": FU_BODY.format(company="Citron Tours"),
    },
    {
        "num": 103,
        "id": "b11-wc-arabian-sky",
        "wave": "C",
        "company": "Arabian Sky Travels",
        "email": "info@arabianskytravels.com",
        "subject": "Following up — July Almaty rates ready to lock | Arcadia × Arabian Sky",
        "body": FU_BODY.format(company="Arabian Sky Travels"),
    },
    {
        "num": 104,
        "id": "b11-wc-tabeer",
        "wave": "C",
        "company": "Tabeer Tours",
        "email": "inquiries@tabeertours.com",
        "subject": "Following up — July Almaty rates ready to lock | Arcadia × Tabeer",
        "body": FU_BODY.format(company="Tabeer Tours"),
    },
    {
        "num": 105,
        "id": "b11-wc-alqaed",
        "wave": "C",
        "company": "Alqaed Travel",
        "email": "info@alqaedtravel.com",
        "subject": "Following up — July Almaty rates ready to lock | Arcadia × Alqaed",
        "body": FU_BODY.format(company="Alqaed Travel"),
    },
]


def load_exclude() -> set[str]:
    out: set[str] = set()
    if not EXCLUDE.exists():
        return out
    for line in EXCLUDE.read_text(encoding="utf-8").splitlines():
        for part in line.split():
            if "@" in part:
                out.add(part.strip().lower())
    return out


def build_wave_b(limit: int = 18) -> list[dict]:
    exclude = load_exclude()
    items: list[dict] = []
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            if len(items) >= limit:
                break
            email = row["email"].strip().lower()
            if email in exclude:
                safe_print(f"[SKIP-CSV] {row['company']} -> {email} (exclude)")
                continue
            company = row["company"].strip()
            items.append(
                {
                    "num": 10 + i,
                    "id": f"b11-wb-{i}-{email}",
                    "wave": "B",
                    "company": company,
                    "email": email,
                    "subject": (
                        f"B2B Partnership — Net Rates for Almaty Groups | "
                        f"Arcadia Tourism × {company}"
                    ),
                    "body": COLD_BODY.format(company=company),
                    "country": row.get("country", "").strip(),
                }
            )
    return items


def build_all(wave_b_limit: int = 18) -> list[dict]:
    items = list(WAVE_A) + build_wave_b(wave_b_limit) + list(WAVE_C)
    EMAILS_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def try_imap_append_sent(msg: MIMEMultipart, raw: bytes) -> tuple[bool, str]:
    """Best-effort: copy sent message into Zoho Sent so it appears in UI."""
    cfg = smtp_config()
    user = str(cfg["user"])
    password = str(cfg["password"])
    last_err = ""
    for host in ("imap.zoho.eu", "imappro.zoho.eu"):
        try:
            M = imaplib.IMAP4_SSL(host, 993, timeout=40)
            M.login(user, password)
            # Zoho folder names vary
            for folder in ("Sent", "INBOX.Sent", '"Sent"', "Sent Items"):
                try:
                    typ, _ = M.append(folder, "\\Seen", None, raw)
                    if typ == "OK":
                        M.logout()
                        return True, f"{host}/{folder}"
                except Exception as exc:  # noqa: BLE001
                    last_err = f"{host}/{folder}: {exc}"
            M.logout()
        except Exception as exc:  # noqa: BLE001
            last_err = f"{host}: {exc}"
    return False, last_err or "IMAP append failed"


def send_batch(
    pending: list[dict],
    *,
    delay: float,
    dry_run: bool,
    attach_pdf_flag: bool,
) -> list[dict]:
    cfg = smtp_config()
    results: list[dict] = []
    if dry_run:
        for item in pending:
            safe_print(f"[DRY-RUN] wave={item.get('wave')} #{item['num']} {item['company']} -> {item['email']}")
            results.append({**item, "status": "dry_run"})
        return results

    if not cfg["password"]:
        safe_print("ERROR: SMTP password not found")
        return [{"status": "failed", "error": "no password"}]

    ctx = ssl.create_default_context()
    with __import__("smtplib").SMTP_SSL(str(cfg["host"]), int(cfg["port"]), context=ctx, timeout=60) as server:
        server.login(str(cfg["user"]), str(cfg["password"]))
        safe_print(f"SMTP OK: {cfg['user']} @ {cfg['host']}:{cfg['port']}\n")
        for i, item in enumerate(pending):
            company = item["company"]
            to_email = item["email"]
            num = item["num"]
            try:
                msg = build_message(
                    to_email,
                    item["subject"],
                    item["body"],
                    from_addr=str(cfg["user"]),
                    attach_rate_sheet=attach_pdf_flag,
                )
                raw = msg.as_bytes() if hasattr(msg, "as_bytes") else msg.as_string().encode("utf-8")
                server.sendmail(str(cfg["user"]), [to_email], msg.as_string())
                ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
                imap_ok, imap_detail = try_imap_append_sent(msg, raw)
                safe_print(
                    f"[SENT] wave={item.get('wave')} #{num} {company} -> {to_email} @ {ts}"
                    f" | IMAP_Sent={'OK '+imap_detail if imap_ok else 'FAIL '+imap_detail}"
                )
                rec = {
                    "num": num,
                    "id": item.get("id"),
                    "wave": item.get("wave"),
                    "company": company,
                    "email": to_email,
                    "status": "sent",
                    "time": ts,
                    "method": "zoho_smtp",
                    "imap_sent": imap_ok,
                    "imap_detail": imap_detail,
                }
                append_sent(SENT_LOG_JSON, rec)
                results.append(rec)
            except Exception as exc:  # noqa: BLE001
                safe_print(f"[FAIL] wave={item.get('wave')} #{num} {company} -> {to_email}: {exc}")
                rec = {
                    "num": num,
                    "id": item.get("id"),
                    "wave": item.get("wave"),
                    "company": company,
                    "email": to_email,
                    "status": "failed",
                    "error": str(exc),
                }
                append_sent(SENT_LOG_JSON, rec)
                results.append(rec)
            if i < len(pending) - 1:
                time.sleep(delay)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Send Batch 11 outreach waves A/B/C")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--delay", type=float, default=45.0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--waves", type=str, default="A,B,C", help="Comma list: A,B,C")
    ap.add_argument("--limit-b", type=int, default=18)
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()

    load_dotenv()
    if not PDF_PATH.is_file() and not args.no_pdf:
        safe_print(f"ERROR: Missing PDF {PDF_PATH}")
        return 2

    if args.build or not EMAILS_JSON.exists():
        items = build_all(args.limit_b)
        safe_print(f"Built {len(items)} targets (A+B+C)")
    else:
        items = [normalize_item(x, i) for i, x in enumerate(json.loads(EMAILS_JSON.read_text(encoding="utf-8")))]

    wanted_waves = {w.strip().upper() for w in args.waves.split(",") if w.strip()}
    items = [x for x in items if str(x.get("wave", "B")).upper() in wanted_waves]

    sent_keys = set() if args.force else load_sent_keys(SENT_LOG_JSON)
    pending: list[dict] = []
    for item in items:
        item = normalize_item(item, item.get("num", 0))
        key = sent_key(item)
        if key in sent_keys or item["email"] in sent_keys:
            safe_print(f"[SKIP] #{item['num']} {item['company']} -> {item['email']} (already sent)")
            continue
        pending.append(item)

    safe_print(f"Batch 11 waves={sorted(wanted_waves)} — {len(pending)} pending — from {FROM_EMAIL}")
    safe_print(f"PDF attach: {not args.no_pdf} | delay={args.delay}s\n")

    if not pending:
        safe_print("Nothing to send.")
        return 0

    results = send_batch(
        pending,
        delay=args.delay,
        dry_run=args.dry_run,
        attach_pdf_flag=not args.no_pdf,
    )
    sent_n = sum(1 for r in results if r.get("status") == "sent")
    fail_n = sum(1 for r in results if r.get("status") == "failed")
    imap_ok = sum(1 for r in results if r.get("imap_sent"))
    safe_print(f"\nDone: {sent_n} sent, {fail_n} failed, IMAP_Sent OK={imap_ok}/{sent_n}")
    return 1 if fail_n else 0


if __name__ == "__main__":
    raise SystemExit(main())
