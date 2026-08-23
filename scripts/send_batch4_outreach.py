#!/usr/bin/env python3
"""Send Batch 4 B2B outreach emails (#5–16) via Zoho SMTP.

Recipients are loaded ONLY from `.tmp_batch4_remaining.json` at repo root.
Already-sent targets are skipped using `.tmp_batch4_sent.json` (idempotent).

Requires .env (never commit):
  SMTP_HOST=smtp.zoho.eu
  SMTP_PORT=465
  SMTP_USER=info@arcadia-tour.com
  SMTP_PASS=<Zoho app-specific password>

Usage:
  python scripts/send_batch4_outreach.py           # send pending only
  python scripts/send_batch4_outreach.py --dry-run # preview only
  python scripts/send_batch4_outreach.py --only 5,6
  python scripts/send_batch4_outreach.py --force   # ignore sent log (avoid)
"""
from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
import sys
import time
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMAILS_JSON = ROOT / ".tmp_batch4_remaining.json"
SENT_LOG_JSON = ROOT / ".tmp_batch4_sent.json"
FROM_EMAIL = "info@arcadia-tour.com"
FROM_NAME = "Mohammad Ali — Arcadia Tourism"
ALMATY = timezone(timedelta(hours=5))
REQUIRED_KEYS = ("company", "email", "subject", "body")


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def smtp_config() -> dict[str, str | int]:
    host = (
        os.environ.get("SMTP_HOST")
        or os.environ.get("ZOHO_SMTP_HOST")
        or "smtp.zoho.eu"
    )
    port = int(os.environ.get("SMTP_PORT") or os.environ.get("ZOHO_SMTP_PORT") or "465")
    user = (
        os.environ.get("SMTP_USER")
        or os.environ.get("ZOHO_SMTP_USER")
        or os.environ.get("ZOHO_USER")
        or FROM_EMAIL
    )
    password = (
        os.environ.get("SMTP_PASS")
        or os.environ.get("SMTP_PASSWORD")
        or os.environ.get("ZOHO_SMTP_PASS")
        or os.environ.get("ZOHO_PASS")
        or ""
    )
    return {"host": host, "port": port, "user": user, "password": password}


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def load_sent_keys() -> set[str]:
    if not SENT_LOG_JSON.exists():
        return set()
    try:
        records = json.loads(SENT_LOG_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    keys: set[str] = set()
    for row in records:
        if row.get("status") != "sent":
            continue
        email = str(row.get("email", "")).strip().lower()
        num = row.get("num")
        if email and num is not None:
            keys.add(f"{num}:{email}")
        elif email:
            keys.add(email)
    return keys


def append_sent(record: dict) -> None:
    records: list[dict] = []
    if SENT_LOG_JSON.exists():
        try:
            records = json.loads(SENT_LOG_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []
    records.append(record)
    SENT_LOG_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_remaining(items: list[dict]) -> None:
    EMAILS_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_item(item: dict, index: int) -> dict:
    missing = [k for k in REQUIRED_KEYS if k not in item or not str(item[k]).strip()]
    if missing:
        raise ValueError(f"Item #{index + 1} missing fields: {', '.join(missing)}")
    num = item.get("num")
    if num is None:
        num = index + 5
    return {**item, "num": int(num), "email": str(item["email"]).strip().lower()}


def load_emails() -> list[dict]:
    if not EMAILS_JSON.exists():
        raise FileNotFoundError(f"Missing {EMAILS_JSON}")
    raw = json.loads(EMAILS_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{EMAILS_JSON} must be a JSON array")
    return [normalize_item(item, i) for i, item in enumerate(raw)]


def body_to_html(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    html_body = escaped.replace("\n\n", "</p><p>").replace("\n", "<br>\n")
    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;font-size:14px;color:#222;">
<p>{html_body}</p>
</body></html>"""


def build_message(to_email: str, subject: str, body: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = FROM_EMAIL
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(body_to_html(body), "html", "utf-8"))
    return msg


def sent_key(item: dict) -> str:
    return f"{item['num']}:{item['email']}"


def send_one(
    server: smtplib.SMTP_SSL | None,
    user: str,
    item: dict,
    dry_run: bool,
) -> dict:
    company = item["company"]
    to_email = item["email"]
    subject = item["subject"]
    body = item["body"]
    num = item["num"]

    if dry_run:
        safe_print(f"[DRY-RUN] #{num} {company} -> {to_email}")
        safe_print(f"          Subject: {subject[:80]}")
        return {"num": num, "company": company, "to": to_email, "status": "dry_run"}

    msg = build_message(to_email, subject, body)
    server.sendmail(user, [to_email], msg.as_string())
    ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
    safe_print(f"[SENT] #{num} {company} -> {to_email} @ {ts}")
    append_sent(
        {
            "num": num,
            "company": company,
            "email": to_email,
            "status": "sent",
            "time": ts,
            "method": "zoho_smtp",
        }
    )
    return {"num": num, "company": company, "to": to_email, "status": "sent", "time": ts}


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Batch 4 B2B outreach via Zoho SMTP")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--only", type=str, default="", help="Comma-separated batch numbers, e.g. 5,6,7")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between sends")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Send even if already in .tmp_batch4_sent.json (not recommended)",
    )
    args = parser.parse_args()

    load_dotenv()
    cfg = smtp_config()

    if not cfg["password"] and not args.dry_run:
        print("ERROR: SMTP password not found in .env", file=sys.stderr)
        print("Add one of: SMTP_PASS, ZOHO_SMTP_PASS, ZOHO_PASS", file=sys.stderr)
        print("Zoho EU: smtp.zoho.eu:465, user info@arcadia-tour.com", file=sys.stderr)
        return 2

    emails = load_emails()
    if not emails:
        print("Nothing to send — .tmp_batch4_remaining.json is empty.")
        sent_total = len(load_sent_keys())
        if sent_total:
            print(f"Idempotent log has {sent_total} sent key(s) in {SENT_LOG_JSON.name}.")
        return 0

    if args.only:
        wanted = {int(x.strip()) for x in args.only.split(",") if x.strip()}
        emails = [e for e in emails if e["num"] in wanted]

    sent_keys = set() if args.force else load_sent_keys()
    pending: list[dict] = []
    skipped = 0
    for item in emails:
        key = sent_key(item)
        if key in sent_keys or item["email"] in sent_keys:
            skipped += 1
            safe_print(f"[SKIP] #{item['num']} {item['company']} -> {item['email']} (already sent)")
            continue
        pending.append(item)

    print(f"Batch 4 outreach — {len(pending)} pending, {skipped} skipped — from {FROM_EMAIL}")
    print(f"Source: {EMAILS_JSON.name} only\n")

    if not pending:
        print("All targets already sent. Re-run blocked by idempotent sent log.")
        return 0

    if args.dry_run:
        print("Mode: DRY-RUN (no SMTP connection)\n")
        for item in pending:
            send_one(None, str(cfg["user"]), item, dry_run=True)
        return 0

    ctx = ssl.create_default_context()
    results: list[dict] = []
    remaining = list(emails)
    try:
        with smtplib.SMTP_SSL(str(cfg["host"]), int(cfg["port"]), context=ctx) as server:
            server.login(str(cfg["user"]), str(cfg["password"]))
            print(f"SMTP OK: {cfg['user']} @ {cfg['host']}:{cfg['port']}\n")
            for i, item in enumerate(pending):
                try:
                    results.append(send_one(server, str(cfg["user"]), item, dry_run=False))
                    remaining = [e for e in remaining if sent_key(e) != sent_key(item)]
                except Exception as exc:
                    num = item["num"]
                    print(f"[FAIL] #{num} {item['company']} -> {item['email']}: {exc}", file=sys.stderr)
                    results.append(
                        {
                            "num": num,
                            "company": item["company"],
                            "to": item["email"],
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
                if i < len(pending) - 1:
                    time.sleep(args.delay)
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP authentication failed — check Zoho app password", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"ERROR: SMTP connection failed: {exc}", file=sys.stderr)
        return 4

    save_remaining(remaining)

    sent = sum(1 for r in results if r["status"] == "sent")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"\nDone: {sent} sent, {failed} failed, {skipped} skipped (this run)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
