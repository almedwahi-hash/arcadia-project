#!/usr/bin/env python3
"""Batch 7 FOLLOW-UP sender (rates inline, no PDF) via Zoho SMTP.

Targets:  .tmp_batch7_followup_remaining.json
Sent log: .tmp_batch7_followup_sent.json (idempotent)
Replied:  .tmp_batch7_replied.json -> [{"email": "..."}] skipped automatically

Usage:
  python scripts/send_batch7_followup.py --dry-run
  python scripts/send_batch7_followup.py --only 1 --delay 0
  python scripts/send_batch7_followup.py --delay 3
"""
from __future__ import annotations
import argparse, json, os, smtplib, ssl, sys, time
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMAILS_JSON = ROOT / ".tmp_batch7_followup_remaining.json"
SENT_LOG = ROOT / ".tmp_batch7_followup_sent.json"
REPLIED = ROOT / ".tmp_batch7_replied.json"
LOG_MD = ROOT / "deliverables" / "outreach-sent-log-batch7-ar.md"
FROM_EMAIL = "info@arcadia-tour.com"
FROM_NAME = "Mohammad Ali - Arcadia Tourism"  # ASCII hyphen only
ALMATY = timezone(timedelta(hours=5))


def load_dotenv():
    p = ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cfg():
    host = os.environ.get("SMTP_HOST") or "smtp.zoho.eu"
    if "smtppro" in host:
        host = "smtp.zoho.eu"  # never smtppro - relay 553
    return {
        "host": host,
        "port": int(os.environ.get("SMTP_PORT") or "465"),
        "user": os.environ.get("SMTP_USER") or FROM_EMAIL,
        "password": os.environ.get("SMTP_PASS") or os.environ.get("SMTP_PASSWORD") or "",
    }


def read_json(path):
    if not Path(path).exists():
        return []
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def append_sent(rec):
    recs = read_json(SENT_LOG)
    recs.append(rec)
    SENT_LOG.write_text(json.dumps(recs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(to_email, subject, body):
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((str(Header(FROM_NAME, "utf-8")), FROM_EMAIL))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = FROM_EMAIL
    msg.attach(MIMEText(body, "plain", "utf-8"))
    esc = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = esc.replace("\n\n", "</p><p>").replace("\n", "<br>\n")
    msg.attach(MIMEText(
        f'<html><body style="font-family:Arial,sans-serif;font-size:14px;color:#222;"><p>{html}</p></body></html>',
        "html", "utf-8"))
    return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", type=str, default="")
    ap.add_argument("--delay", type=float, default=3.0)
    a = ap.parse_args()
    load_dotenv()
    c = cfg()

    all_items = read_json(EMAILS_JSON)
    items = list(all_items)
    if a.only:
        want = {int(x) for x in a.only.split(",") if x.strip()}
        items = [e for e in items if e["num"] in want]

    sent = {r["email"].lower() for r in read_json(SENT_LOG) if r.get("status") == "sent"}
    replied = {str(r.get("email", "")).lower() for r in read_json(REPLIED)}
    pending = []
    for e in items:
        em = e["email"].lower()
        if em in sent:
            print(f"[SKIP sent] #{e['num']} {e['company']}")
        elif em in replied:
            print(f"[SKIP replied] #{e['num']} {e['company']}")
        else:
            pending.append(e)

    print(f"Follow-up batch7: {len(pending)} pending / {len(all_items)} total")
    if a.dry_run:
        for e in pending:
            print(f"[DRY] #{e['num']} {e['company']} -> {e['email']} | {e['subject'][:70]}")
        return 0
    if not pending:
        print("Nothing to send.")
        return 0
    if not c["password"]:
        print("ERROR: SMTP_PASS missing", file=sys.stderr)
        return 2

    ctx = ssl.create_default_context()
    remaining = list(all_items)
    fails = 0
    with smtplib.SMTP_SSL(c["host"], c["port"], context=ctx) as s:
        s.login(c["user"], c["password"])
        print(f"SMTP OK: {c['user']} @ {c['host']}:{c['port']}\n")
        for i, e in enumerate(pending):
            try:
                s.sendmail(c["user"], [e["email"]], build(e["email"], e["subject"], e["body"]).as_string())
                ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
                print(f"[SENT] #{e['num']} {e['company']} -> {e['email']} @ {ts}")
                append_sent({"num": e["num"], "company": e["company"], "email": e["email"],
                             "status": "sent", "time": ts, "method": "zoho_smtp_followup"})
                remaining = [x for x in remaining if x["email"].lower() != e["email"].lower()]
            except Exception as exc:
                fails += 1
                print(f"[FAIL] #{e['num']} {e['company']}: {exc}", file=sys.stderr)
            if i < len(pending) - 1:
                time.sleep(a.delay)
    EMAILS_JSON.write_text(json.dumps(remaining, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nDone: {len(pending)-fails} sent, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
