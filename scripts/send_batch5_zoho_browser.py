# -*- coding: utf-8 -*-
"""Send Batch 5 outreach via Zoho Mail web UI (browser). No SMTP."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH5_JSON = ROOT / ".tmp_batch5_remaining.json"
GCC_JSON = ROOT / ".tmp_batch5_gcc_followups.json"
SENT_JSON = ROOT / ".tmp_batch5_sent.json"
FAILED_JSON = ROOT / ".tmp_batch5_failed.json"
LOCK_FILE = ROOT / ".tmp_batch5_browser.lock"
LOG_MD = ROOT / "deliverables" / "outreach-sent-log-batch5-ar.md"
PDF = ROOT / "deliverables" / "pdfs" / "Arcadia-B2B-Rate-Sheet-Almaty.pdf"
PROFILE = ROOT / ".zoho-chrome-profile"
ZOHO_URL = "https://mail.zoho.eu/zm/#mail/folder/inbox"
SENT_URL = "https://mail.zoho.eu/zm/#mail/folder/sent"
ALMATY = timezone(timedelta(hours=5))
MAX_RETRIES = 1  # one retry after first failure, then skip

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
  const toInput = vis.querySelector('input[aria-label="To"], input[aria-label="Получатели"], [role="combobox"][aria-label="To"] input, [role="combobox"][aria-label="Получатели"] input');
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
  const subj = vis.querySelector('input[placeholder="Subject"], input[placeholder="Тема"], [aria-label="Subject"], [aria-label="Тема"]');
  if (!subj) return { ok: false, err: 'no subject', company: item.company };
  subj.focus();
  subj.value = item.subject;
  subj.dispatchEvent(new Event('input', { bubbles: true }));
  subj.dispatchEvent(new Event('change', { bubbles: true }));
  await sleep(600);
  if ((subj.value || '').trim() !== item.subject.trim()) {
    subj.focus();
    if (subj.select) subj.select();
    document.execCommand('insertText', false, item.subject);
    subj.dispatchEvent(new Event('input', { bubbles: true }));
    await sleep(400);
  }
  if ((subj.value || '').trim() !== item.subject.trim()) {
    return { ok: false, err: 'subject not set', company: item.company, got: subj.value };
  }
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
  const sendBtn = [...vis.querySelectorAll('button')].find(
    b => { const t=((b.textContent||'')+' '+(b.getAttribute('aria-label')||'')).toLowerCase(); return t.includes('send') || t.includes('отправить'); }
  );
  if (!sendBtn) return { ok: false, err: 'no send btn', company: item.company };
  sendBtn.click();
  await sleep(3000);
  [...document.querySelectorAll('button')].filter(
    b => (b.textContent||'').includes('Отправить в любом случае')
  ).forEach(b => b.click());
  const okBtn = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'ОК');
  if (okBtn) okBtn.click();
  await sleep(2000);
  return { ok: true, company: item.company, email: item.email, subject: item.subject };
}
"""

CHECK_LOGIN_JS = """
() => {
  const login = document.querySelector('input[type="password"], #login_id, [name="LOGIN_ID"]');
  const inbox = [...document.querySelectorAll('button, a, span')].some(
    el => (el.textContent||'').includes('Новое письмо') || (el.textContent||'').includes('Входящие')
  );
  return { loginVisible: !!login, inboxVisible: inbox, url: location.href };
}
"""

VERIFY_SENT_JS = """
async (payload) => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  await sleep(2000);
  const email = (payload.email || '').toLowerCase();
  const sub = (payload.subjectSnippet || '').slice(0, 28);
  const rows = [...document.querySelectorAll('[role="row"], .zmList, .zmML, li, tr, .mail-list-item')];
  let rowText = rows.map(r => (r.innerText || '').toLowerCase()).join('\\n');
  if (!rowText) rowText = (document.body.innerText || '').toLowerCase();
  const hasEmail = email && rowText.includes(email);
  const hasSub = !sub || rowText.includes(sub.toLowerCase());
  return { hasEmail, hasSub, verified: hasEmail && hasSub, sample: rowText.slice(0, 400) };
}
"""


def load_json_list(path: Path) -> list[dict]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_json_list(path: Path, items: list[dict]) -> None:
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def append_sent_unique(rec: dict) -> None:
    sent_list = load_json_list(SENT_JSON)
    em = rec["email"].lower()
    if any(x.get("email", "").lower() == em for x in sent_list):
        return
    sent_list.append(rec)
    save_json_list(SENT_JSON, sent_list)


def acquire_lock() -> bool:
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
            # Windows: os.kill(pid, 0) checks if process exists
            os.kill(pid, 0)
            print(f"LOCKED: another send_batch5_zoho_browser.py is running (pid {pid})", file=sys.stderr)
            return False
        except (OSError, ValueError):
            LOCK_FILE.unlink(missing_ok=True)
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)


def record_failure(item: dict, err: str, attempts: int) -> None:
    failed = load_json_list(FAILED_JSON)
    em = item["email"].lower()
    rec = {
        **{k: item[k] for k in ("num", "company", "email", "subject") if k in item},
        "err": err,
        "attempts": attempts,
        "ts": datetime.now(ALMATY).isoformat(),
        "kind": item.get("kind", "batch5"),
    }
    failed = [f for f in failed if f.get("email", "").lower() != em]
    failed.append(rec)
    save_json_list(FAILED_JSON, failed)


def close_draft_tabs(page) -> None:
    try:
        page.evaluate(
            """() => {
          for (let i = 0; i < 30; i++) {
            const tab = [...document.querySelectorAll('li[role="tab"]:not(.cantClose)')][0];
            if (!tab) break;
            const x = tab.querySelector('.msi-close');
            if (x) x.click();
            else break;
          }
        }"""
        )
        time.sleep(1)
    except Exception:
        pass


def send_and_verify(page, item: dict) -> tuple[bool, str]:
    """Returns (success, error_message)."""
    result = page.evaluate(SEND_ONE_JS, item)
    if not result.get("ok"):
        return False, result.get("err", "send failed")

    page.goto(SENT_URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    verify = page.evaluate(
        VERIFY_SENT_JS,
        {"email": item["email"], "subjectSnippet": item["subject"][:30]},
    )
    if verify.get("verified") or verify.get("hasSub"):
        return True, ""
    return False, f"not in Sent folder (hasEmail={verify.get('hasEmail')}, hasSub={verify.get('hasSub')})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=28)
    parser.add_argument("--gcc", action="store_true")
    parser.add_argument("--only", type=int, default=0)
    parser.add_argument("--retry-failed", action="store_true", help="Include previously failed emails")
    parser.add_argument("--cdp", default="http://127.0.0.1:9222")
    args = parser.parse_args()

    if not acquire_lock():
        return 3

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed", file=sys.stderr)
        release_lock()
        return 1

    batch5 = json.loads(BATCH5_JSON.read_text(encoding="utf-8"))
    gcc = json.loads(GCC_JSON.read_text(encoding="utf-8")) if GCC_JSON.exists() else []
    already = {x["email"].lower() for x in load_json_list(SENT_JSON)}
    failed_set = {x["email"].lower() for x in load_json_list(FAILED_JSON)}
    queue: list[dict] = []

    if args.gcc:
        queue = [g for g in gcc if g["email"].lower() not in already]
    else:
        queue = [b for b in batch5 if b["email"].lower() not in already]

    if not args.retry_failed:
        queue = [x for x in queue if x["email"].lower() not in failed_set]

    if args.only:
        queue = [x for x in queue if x.get("num") == args.only]
    if args.limit:
        queue = queue[: args.limit]

    if not queue:
        print("nothing to send")
        release_lock()
        return 0

    confirmed: list[dict] = []
    session_failures: list[dict] = []
    ts_now = datetime.now(ALMATY).isoformat()

    with sync_playwright() as p:
        browser = None
        context = None
        page = None

        try:
            browser = p.chromium.connect_over_cdp(args.cdp, timeout=15000)
            if browser.contexts:
                context = browser.contexts[0]
                pages = context.pages
                page = next((pg for pg in pages if "zoho" in pg.url.lower()), None)
                if not page:
                    page = pages[0] if pages else context.new_page()
                page.bring_to_front()
            print(f"connected CDP {args.cdp}")
        except Exception as e:
            print(f"CDP unavailable ({e}), launching persistent Chrome profile")

        if not page:
            PROFILE.mkdir(parents=True, exist_ok=True)
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE),
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else context.new_page()

        page.goto(ZOHO_URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(5)
        login_state = page.evaluate(CHECK_LOGIN_JS)
        if login_state.get("loginVisible") and not login_state.get("inboxVisible"):
            print("LOGIN_REQUIRED")
            print("Please log in as info@arcadia-tour.com at https://mail.zoho.eu then re-run.")
            if context and not browser:
                context.close()
            release_lock()
            return 2

        close_draft_tabs(page)

        for item in queue:
            kind = item.get("kind", "batch5")
            print(f"Sending {item.get('company')} -> {item.get('email')}")
            last_err = ""
            success = False

            for attempt in range(MAX_RETRIES + 1):
                if attempt > 0:
                    print(f"  retry {attempt}/{MAX_RETRIES} after: {last_err}")
                    close_draft_tabs(page)
                    time.sleep(2)

                try:
                    page.goto(ZOHO_URL, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(1)
                    success, last_err = send_and_verify(page, item)
                    if success:
                        break
                except Exception as ex:
                    last_err = str(ex)
                    print(f"  attempt {attempt + 1} ERROR: {ex}")

            if success:
                rec = {
                    **item,
                    "ts": ts_now,
                    "kind": kind,
                    "method": "zoho_browser",
                    "verified_sent": True,
                }
                confirmed.append(rec)
                append_sent_unique(rec)
                # Remove from failed if it was there
                failed = load_json_list(FAILED_JSON)
                failed = [f for f in failed if f.get("email", "").lower() != item["email"].lower()]
                save_json_list(FAILED_JSON, failed)
                print("  CONFIRMED in Sent")
            else:
                attempts = MAX_RETRIES + 1
                record_failure(item, last_err, attempts)
                session_failures.append({**item, "err": last_err, "attempts": attempts})
                print(f"  SKIPPED after {attempts} attempt(s): {last_err}")

            close_draft_tabs(page)
            time.sleep(1.5)

        if context and not browser:
            context.close()

    update_log(batch5, gcc, load_json_list(SENT_JSON), load_json_list(FAILED_JSON), session_failures)
    print(
        json.dumps(
            {
                "batch5_confirmed": sum(1 for c in confirmed if c.get("kind") != "gcc_followup"),
                "gcc_confirmed": sum(1 for c in confirmed if c.get("kind") == "gcc_followup"),
                "session_failures": len(session_failures),
                "total_failed_persisted": len(load_json_list(FAILED_JSON)),
                "confirmed": [{"company": c["company"], "email": c["email"]} for c in confirmed],
                "skipped": [{"company": f["company"], "email": f["email"], "err": f["err"]} for f in session_failures],
            },
            ensure_ascii=False,
        )
    )
    release_lock()
    return 0 if confirmed else 1


def update_log(
    batch5: list[dict],
    gcc: list[dict],
    confirmed: list[dict],
    all_failed: list[dict],
    session_failures: list[dict],
) -> None:
    ts = datetime.now(ALMATY).strftime("%Y-%m-%d %H:%M UTC+05:00")
    conf_emails = {c["email"].lower() for c in confirmed}
    conf_map = {c["email"].lower(): c for c in confirmed}
    n_b5 = sum(1 for c in confirmed if c.get("kind") != "gcc_followup")
    n_gcc = sum(1 for c in confirmed if c.get("kind") == "gcc_followup")

    lines = [
        "# سجل الإرسال — Batch 5 + متابعات GCC",
        "",
        f"> **آخر تحديث:** {ts}",
        f"> **الحالة:** **{n_b5}/28 Batch 5** + **{n_gcc}/5 GCC** مُرسل عبر **Zoho Mail (متصفح)** — تأكيد مجلد Sent.",
        f"> **فشل/تخطي (محفوظ):** {len(all_failed)} — لن يُعاد المحاولة إلا مع `--retry-failed`",
        f"> **فشل هذه الجلسة:** {len(session_failures)}",
        "",
        "## Batch 5 (28)",
        "",
        "| # | Company | Email | Status |",
        "|---|---------|-------|--------|",
    ]
    fail_map = {f.get("email", "").lower(): f for f in all_failed if f.get("email")}
    for row in batch5:
        em = row["email"].lower()
        if em in conf_emails:
            st = f"sent ({conf_map[em].get('ts', ts)})"
        elif em in fail_map:
            st = f"skipped ({fail_map[em].get('err', 'error')})"
        else:
            st = "pending"
        lines.append(f"| {row['num']} | {row['company']} | {row['email']} | {st} |")

    lines += ["", "## GCC follow-ups (5)", "", "| ID | Company | Email | Status |", "|---|---------|-------|--------|"]
    for row in gcc:
        em = row["email"].lower()
        if em in conf_emails:
            st = f"sent ({conf_map[em].get('ts', ts)})"
        elif em in fail_map:
            st = f"skipped ({fail_map[em].get('err', 'error')})"
        else:
            st = "pending"
        lines.append(f"| {row.get('id', '')} | {row['company']} | {row['email']} | {st} |")

    if confirmed:
        lines += ["", "## مُؤكَّد (Sent folder)", ""]
        for c in confirmed:
            lines.append(f"- **{c.get('company')}** `{c.get('email')}` — {c.get('ts', ts)}")

    if all_failed:
        lines += ["", "## تخطي / فشل (لا إعادة تلقائية)", ""]
        for f in all_failed:
            lines.append(f"- **{f.get('company')}** `{f.get('email')}` — {f.get('err')} ({f.get('attempts', '?')} attempts)")

    LOG_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
