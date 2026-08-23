#!/usr/bin/env python3
"""Shared Zoho SMTP helpers for B2B outreach scripts."""
from __future__ import annotations

import json
import os
import smtplib
import ssl
import time
from datetime import datetime, timedelta, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "deliverables" / "pdfs" / "Arcadia-B2B-Rate-Sheet-Almaty.pdf"
FROM_EMAIL = "info@arcadia-tour.com"
FROM_NAME = "Mohammad Ali - Arcadia Tourism"
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


def body_to_html(text: str) -> str:
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_body = escaped.replace("\n\n", "</p><p>").replace("\n", "<br>\n")
    return (
        '<!DOCTYPE html>\n<html><body style="font-family:Arial,sans-serif;'
        f'font-size:14px;color:#222;"><p>{html_body}</p></body></html>'
    )


def attach_pdf(msg: MIMEMultipart, pdf_path: Path = PDF_PATH) -> None:
    if not pdf_path.is_file():
        return
    part = MIMEBase("application", "pdf")
    part.set_payload(pdf_path.read_bytes())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{pdf_path.name}"')
    msg.attach(part)


def build_message(
    to_email: str,
    subject: str,
    body: str,
    *,
    from_addr: str = FROM_EMAIL,
    attach_rate_sheet: bool = True,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((FROM_NAME, from_addr))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = from_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(body_to_html(body), "html", "utf-8"))
    if attach_rate_sheet:
        attach_pdf(msg)
    return msg


def load_sent_keys(sent_log: Path) -> set[str]:
    if not sent_log.exists():
        return set()
    try:
        records = json.loads(sent_log.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    keys: set[str] = set()
    for row in records:
        if row.get("status") != "sent":
            continue
        email = str(row.get("email", "")).strip().lower()
        num = row.get("num")
        rid = row.get("id")
        if rid:
            keys.add(str(rid))
        if email and num is not None:
            keys.add(f"{num}:{email}")
        elif email:
            keys.add(email)
    return keys


def append_sent(sent_log: Path, record: dict) -> None:
    records: list[dict] = []
    if sent_log.exists():
        try:
            records = json.loads(sent_log.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []
    records.append(record)
    sent_log.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sent_key(item: dict) -> str:
    if item.get("id"):
        return str(item["id"])
    return f"{item['num']}:{item['email']}"


def normalize_item(item: dict, index: int, default_num: int = 1) -> dict:
    missing = [k for k in REQUIRED_KEYS if k not in item or not str(item[k]).strip()]
    if missing:
        raise ValueError(f"Item #{index + 1} missing fields: {', '.join(missing)}")
    num = item.get("num")
    if num is None:
        num = default_num + index
    return {**item, "num": int(num), "email": str(item["email"]).strip().lower()}


def send_one(
    server: smtplib.SMTP_SSL | None,
    user: str,
    item: dict,
    sent_log: Path,
    *,
    dry_run: bool = False,
    attach_pdf_flag: bool = True,
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

    msg = build_message(to_email, subject, body, from_addr=user, attach_rate_sheet=attach_pdf_flag)
    server.sendmail(user, [to_email], msg.as_string())
    ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
    safe_print(f"[SENT] #{num} {company} -> {to_email} @ {ts}")
    append_sent(
        sent_log,
        {
            "num": num,
            "company": company,
            "email": to_email,
            "status": "sent",
            "time": ts,
            "method": "zoho_smtp",
        },
    )
    return {"num": num, "company": company, "to": to_email, "status": "sent", "time": ts}


def run_outreach_batch(
    *,
    batch_label: str,
    emails_json: Path,
    sent_log_json: Path,
    dry_run: bool,
    only: str,
    delay: float,
    force: bool,
    attach_pdf_flag: bool = True,
) -> int:
    cfg = smtp_config()
    if not cfg["password"] and not dry_run:
        safe_print("ERROR: SMTP password not found in .env")
        return 2

    if not emails_json.exists():
        safe_print(f"ERROR: Missing {emails_json}")
        return 2

    raw = json.loads(emails_json.read_text(encoding="utf-8"))
    emails = [normalize_item(item, i) for i, item in enumerate(raw)]

    if only:
        wanted = {int(x.strip()) for x in only.split(",") if x.strip()}
        emails = [e for e in emails if e["num"] in wanted]

    sent_keys = set() if force else load_sent_keys(sent_log_json)
    pending: list[dict] = []
    skipped = 0
    for item in emails:
        key = sent_key(item)
        if key in sent_keys or item["email"] in sent_keys:
            skipped += 1
            safe_print(f"[SKIP] #{item['num']} {item['company']} -> {item['email']} (already sent)")
            continue
        pending.append(item)

    safe_print(f"{batch_label} — {len(pending)} pending, {skipped} skipped — from {FROM_EMAIL}")
    safe_print(f"Source: {emails_json.name} | log: {sent_log_json.name}\n")

    if not pending:
        safe_print("All targets already sent.")
        return 0

    if dry_run:
        safe_print("Mode: DRY-RUN (no SMTP connection)\n")
        for item in pending:
            send_one(None, str(cfg["user"]), item, sent_log_json, dry_run=True)
        return 0

    ctx = ssl.create_default_context()
    results: list[dict] = []
    remaining = list(emails)
    try:
        with smtplib.SMTP_SSL(str(cfg["host"]), int(cfg["port"]), context=ctx) as server:
            server.login(str(cfg["user"]), str(cfg["password"]))
            safe_print(f"SMTP OK: {cfg['user']} @ {cfg['host']}:{cfg['port']}\n")
            for i, item in enumerate(pending):
                try:
                    results.append(
                        send_one(
                            server,
                            str(cfg["user"]),
                            item,
                            sent_log_json,
                            attach_pdf_flag=attach_pdf_flag,
                        )
                    )
                    remaining = [e for e in remaining if sent_key(e) != sent_key(item)]
                except Exception as exc:
                    num = item["num"]
                    safe_print(f"[FAIL] #{num} {item['company']} -> {item['email']}: {exc}")
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
                    time.sleep(delay)
    except smtplib.SMTPAuthenticationError:
        safe_print("ERROR: SMTP authentication failed — check Zoho app password")
        return 3
    except OSError as exc:
        safe_print(f"ERROR: SMTP connection failed: {exc}")
        return 4

    emails_json.write_text(json.dumps(remaining, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sent = sum(1 for r in results if r["status"] == "sent")
    failed = sum(1 for r in results if r["status"] == "failed")
    safe_print(f"\nDone: {sent} sent, {failed} failed, {skipped} skipped (this run)")
    return 1 if failed else 0
