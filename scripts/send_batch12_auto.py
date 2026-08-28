#!/usr/bin/env python3
"""Auto-send Batch 12: SMTP first, browser fallback. Run after secrets are set."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def has_secret(*names: str) -> bool:
    return any(os.environ.get(n) for n in names)


def main() -> int:
    # Ensure targets JSON exists
    prep = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "send_batch12_outreach.py"), "--dry-run"],
        cwd=ROOT,
    )
    if prep.returncode != 0:
        return prep.returncode

    if has_secret("ZOHO_SMTP_PASS", "SMTP_PASS", "SMTP_PASSWORD", "ZOHO_PASS"):
        print("=== Batch 12: SMTP send ===")
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "send_batch12_outreach.py")], cwd=ROOT).returncode

    if has_secret("ZOHO_MAIL_PASSWORD", "ZOHO_PASSWORD"):
        print("=== Batch 12: browser send (Zoho login) ===")
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "send_batch12_zoho_browser.py")],
            cwd=ROOT,
        ).returncode

    print("BLOCKED: add ZOHO_SMTP_PASS (App Password) — Cursor shows paste field in this chat.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
