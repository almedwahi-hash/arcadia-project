#!/usr/bin/env python3
"""Send Batch 6 B2B outreach via Zoho SMTP."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import ROOT as _ROOT, load_dotenv, run_outreach_batch  # noqa: E402

EMAILS_JSON = _ROOT / ".tmp_batch6_remaining.json"
SENT_LOG_JSON = _ROOT / ".tmp_batch6_sent.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Batch 6 B2B outreach via Zoho SMTP")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", type=str, default="")
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--build-from-md", action="store_true")
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    if args.build_from_md:
        import batch6_targets  # noqa: WPS433

        n = batch6_targets.write_json()
        print(f"Built {n} batch6 targets from markdown.")

    return run_outreach_batch(
        batch_label="Batch 6 outreach",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only=args.only,
        delay=args.delay,
        force=args.force,
        attach_pdf_flag=not args.no_pdf,
    )


if __name__ == "__main__":
    raise SystemExit(main())
