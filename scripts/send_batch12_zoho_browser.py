#!/usr/bin/env python3
"""Send Batch 12 GCC outreach via Zoho Mail web UI (browser). No SMTP secret needed."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMAILS_JSON = ROOT / ".tmp_batch12_emails.json"
SENT_JSON = ROOT / ".tmp_batch12_sent.json"
FAILED_JSON = ROOT / ".tmp_batch12_browser_failed.json"
LOCK_FILE = ROOT / ".tmp_batch12_browser.lock"
LOG_MD = ROOT / "deliverables" / "outreach-sent-log-batch12-ar.md"
PDF = ROOT / "deliverables" / "pdfs" / "Arcadia-B2B-Rate-Sheet-Almaty.pdf"
PROFILE = ROOT / ".zoho-chrome-profile"
ZOHO_URL = "https://mail.zoho.eu/zm/#mail/folder/inbox"
SENT_URL = "https://mail.zoho.eu/zm/#mail/folder/sent"
SIGNIN_URL = (
    "https://accounts.zoho.eu/signin?servicename=VirtualOffice"
    "&serviceurl=https://mail.zoho.eu/zm/"
)
FROM_EMAIL = "info@arcadia-tour.com"
ALMATY = timezone(timedelta(hours=5))
MAX_RETRIES = 1

SEND_ONE_JS = """
async (item) => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const closeDrafts = () => {
    for (let i = 0; i < 30; i++) {
      const tab = [...document.querySelectorAll('li[role="tab"]:not(.cantClose)')][0];
      if (!tab) break;
      const x = tab.querySelector('.msi-close');
      if (x) x.click();
      else break;
    }
  };
  closeDrafts();
  await sleep(800);
  const newBtn = [...document.querySelectorAll('button,a,[role=button]')].find(b => {
    const t = ((b.textContent||'') + ' ' + (b.getAttribute('aria-label')||'')).toLowerCase();
    return t.includes('new mail') || t.includes('compose') || t.includes('новое') || t.includes('написать');
  });
  if (!newBtn) return { ok: false, err: 'no new btn', company: item.company };
  newBtn.click();
  await sleep(2500);
  const vis = [...document.querySelectorAll('.zmCompose')].find(
    c => c.offsetParent !== null && c.offsetHeight > 100 && c.offsetWidth > 100
  );
  if (!vis) return { ok: false, err: 'no compose', company: item.company };
  const toInput = vis.querySelector(
    'input[aria-label="To"], input[aria-label="Получатели"], [role="combobox"][aria-label="To"] input'
  );
  if (!toInput) return { ok: false, err: 'no to input', company: item.company };
  toInput.focus();
  toInput.value = '';
  for (const ch of item.email) {
    toInput.value += ch;
    toInput.dispatchEvent(new Event('input', { bubbles: true }));
    await sleep(15);
  }
  toInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
  toInput.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
  await sleep(900);
  const opt = [...document.querySelectorAll('[role="option"]')].find(o => (o.textContent||'').includes(item.email));
  if (opt) { opt.click(); await sleep(800); }
  const chip = vis.querySelector('.zmCB');
  if (!chip || chip.classList.contains('zmErrBG')) {
    return { ok: false, err: 'to chip not set', company: item.company };
  }
  const subj = vis.querySelector(
    'input[placeholder="Subject"], input[placeholder="Тема"], [aria-label="Subject"], [aria-label="Тема"]'
  );
  if (!subj) return { ok: false, err: 'no subject', company: item.company };
  subj.focus();
  subj.value = item.subject;
  subj.dispatchEvent(new Event('input', { bubbles: true }));
  subj.dispatchEvent(new Event('change', { bubbles: true }));
  await sleep(600);
  const iframe = vis.querySelector('iframe');
  const ed = vis.querySelector('[contenteditable="true"]');
  const html = item.body.split('\\n').map(l => `<div>${l || '<br>'}</div>`).join('');
  if (iframe?.contentDocument?.body) {
    iframe.contentDocument.body.innerHTML = html;
  } else if (ed) {
    ed.focus();
    ed.innerText = item.body;
    ed.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    return { ok: false, err: 'no body editor', company: item.company };
  }
  await sleep(600);
  const sendBtn = [...vis.querySelectorAll('button')].find(b => {
    const t = ((b.textContent||'') + ' ' + (b.getAttribute('aria-label')||'')).toLowerCase();
    return t.includes('send') || t.includes('отправить');
  });
  if (!sendBtn) return { ok: false, err: 'no send btn', company: item.company };
  sendBtn.click();
  await sleep(3000);
  [...document.querySelectorAll('button')].filter(
    b => (b.textContent||'').includes('Send anyway') || (b.textContent||'').includes('Отправить в любом случае')
  ).forEach(b => b.click());
  return { ok: true, company: item.company, email: item.email, subject: item.subject };
}
"""

CHECK_LOGIN_JS = """
() => {
  const login = document.querySelector('#login_id, input[type="password"][name="PASSWORD"], #password');
  const body = (document.body.innerText || '').toLowerCase();
  const inbox = body.includes('new mail') || body.includes('compose') || body.includes('inbox')
    || body.includes('входящие') || body.includes('новое письмо');
  return { loginVisible: !!login, inboxVisible: inbox, url: location.href };
}
"""

VERIFY_SENT_JS = """
async (payload) => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  await sleep(2000);
  const email = (payload.email || '').toLowerCase();
  const sub = (payload.subjectSnippet || '').slice(0, 28).toLowerCase();
  const rowText = (document.body.innerText || '').toLowerCase();
  return {
    hasEmail: email && rowText.includes(email),
    hasSub: !sub || rowText.includes(sub),
    verified: rowText.includes(email) && (!sub || rowText.includes(sub)),
  };
}
"""


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_list(path: Path, items: list[dict]) -> None:
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def acquire_lock() -> bool:
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            print(f"LOCKED: another batch12 browser send running (pid {pid})", file=sys.stderr)
            return False
        except (OSError, ValueError):
            LOCK_FILE.unlink(missing_ok=True)
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)


def zoho_login(page, email: str, password: str) -> bool:
    page.goto(SIGNIN_URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(2)
    login_id = page.locator("#login_id")
    if login_id.is_visible():
        login_id.fill(email)
        page.locator("button:has-text('Next'), #nextbtn").first.click()
        time.sleep(2)
    pwd = page.locator("#password")
    if not pwd.is_visible():
        pwd = page.locator('input[type="password"]').first
    pwd.wait_for(state="visible", timeout=15000)
    pwd.fill(password)
    for sel in ("button:has-text('Sign in')", "button:has-text('Sign In')", "#nextbtn", "button:has-text('Next')"):
        btn = page.locator(sel).first
        if btn.is_visible():
            btn.click()
            break
    time.sleep(8)
    page.goto(ZOHO_URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(5)
    state = page.evaluate(CHECK_LOGIN_JS)
    return bool(state.get("inboxVisible")) and not state.get("loginVisible")


def send_and_verify(page, item: dict) -> tuple[bool, str]:
    result = page.evaluate(SEND_ONE_JS, item)
    if not result.get("ok"):
        return False, result.get("err", "send failed")
    page.goto(SENT_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    verify = page.evaluate(VERIFY_SENT_JS, {"email": item["email"], "subjectSnippet": item["subject"][:30]})
    if verify.get("verified"):
        return True, ""
    return False, f"not in Sent (hasEmail={verify.get('hasEmail')}, hasSub={verify.get('hasSub')})"


def update_deliverables(confirmed: list[dict], failed: list[dict]) -> None:
    ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M %Z")
    exclude_path = ROOT / "deliverables" / "exclude_emails.txt"
    exclude = set()
    if exclude_path.exists():
        for line in exclude_path.read_text(encoding="utf-8").splitlines():
            for part in line.split():
                if "@" in part:
                    exclude.add(part.strip().lower())
    for rec in confirmed:
        exclude.add(rec["email"].lower())
    exclude_path.write_text("\n".join(sorted(exclude)) + "\n", encoding="utf-8")

    lines = [
        "# سجل الإرسال — Batch 12 GCC",
        "",
        f"> **آخر تحديث:** {ts}",
        f"> **الحالة:** **{len(confirmed)}/8** مُرسل عبر Zoho Mail (متصفح)",
        f"> **From:** {FROM_EMAIL}",
        "",
        "| # | Company | Email | Status |",
        "|---|---------|-------|--------|",
    ]
    all_items = load_json_list(EMAILS_JSON)
    conf_map = {c["email"].lower(): c for c in confirmed}
    fail_map = {f["email"].lower(): f for f in failed}
    for item in all_items:
        em = item["email"].lower()
        if em in conf_map:
            st = f"sent ({conf_map[em].get('ts', ts)})"
        elif em in fail_map:
            st = f"failed ({fail_map[em].get('err', '?')})"
        else:
            st = "pending"
        lines.append(f"| {item.get('num')} | {item['company']} | {item['email']} | {st} |")
    LOG_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--only", type=int, default=0)
    parser.add_argument("--cdp", default="http://127.0.0.1:9222")
    args = parser.parse_args()

    if not EMAILS_JSON.exists():
        print(f"Missing {EMAILS_JSON}. Run: python3 scripts/send_batch12_outreach.py --dry-run", file=sys.stderr)
        return 2
    if not acquire_lock():
        return 3

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed", file=sys.stderr)
        release_lock()
        return 1

    queue = load_json_list(EMAILS_JSON)
    sent = {x["email"].lower() for x in load_json_list(SENT_JSON) if x.get("status") == "sent"}
    queue = [x for x in queue if x["email"].lower() not in sent]
    if args.only:
        queue = [x for x in queue if x.get("num") == args.only]
    if args.limit:
        queue = queue[: args.limit]
    if not queue:
        print("nothing to send")
        release_lock()
        return 0

    mail_pass = (
        os.environ.get("ZOHO_MAIL_PASSWORD")
        or os.environ.get("ZOHO_PASSWORD")
        or os.environ.get("ZOHO_SMTP_PASS")
        or ""
    )
    confirmed: list[dict] = []
    session_failed: list[dict] = []
    ts_now = datetime.now(ALMATY).isoformat()

    with sync_playwright() as p:
        browser = None
        context = None
        page = None
        try:
            browser = p.chromium.connect_over_cdp(args.cdp, timeout=5000)
            context = browser.contexts[0] if browser.contexts else None
            if context:
                pages = context.pages
                page = next((pg for pg in pages if "zoho" in pg.url.lower()), None) or (pages[0] if pages else None)
        except Exception:
            pass

        if not page:
            PROFILE.mkdir(parents=True, exist_ok=True)
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE),
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            browser = None

        page.goto(ZOHO_URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(5)
        login_state = page.evaluate(CHECK_LOGIN_JS)
        if login_state.get("loginVisible") and not login_state.get("inboxVisible"):
            if not mail_pass:
                print("LOGIN_REQUIRED: set ZOHO_SMTP_PASS or ZOHO_MAIL_PASSWORD secret")
                if context and not browser:
                    context.close()
                release_lock()
                return 2
            if not zoho_login(page, FROM_EMAIL, mail_pass):
                print("LOGIN_FAILED: check Zoho password / 2FA")
                if context and not browser:
                    context.close()
                release_lock()
                return 2

        for item in queue:
            print(f"Sending {item.get('company')} -> {item.get('email')}")
            success = False
            last_err = ""
            for attempt in range(MAX_RETRIES + 1):
                try:
                    page.goto(ZOHO_URL, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(1)
                    success, last_err = send_and_verify(page, item)
                    if success:
                        break
                except Exception as exc:
                    last_err = str(exc)
                if attempt < MAX_RETRIES:
                    time.sleep(2)
            if success:
                rec = {**item, "ts": ts_now, "status": "sent", "method": "zoho_browser"}
                confirmed.append(rec)
                sent_list = load_json_list(SENT_JSON)
                sent_list.append(rec)
                save_json_list(SENT_JSON, sent_list)
                print("  CONFIRMED in Sent")
            else:
                session_failed.append({**item, "err": last_err})
                print(f"  FAILED: {last_err}")
            time.sleep(2)

        if context and not browser:
            context.close()

    update_deliverables(confirmed, session_failed)
    if session_failed:
        save_json_list(FAILED_JSON, session_failed)
    print(json.dumps({"sent": len(confirmed), "failed": len(session_failed)}, ensure_ascii=False))
    release_lock()
    return 0 if confirmed and not session_failed else (1 if confirmed else 2)


if __name__ == "__main__":
    raise SystemExit(main())
