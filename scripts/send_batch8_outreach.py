#!/usr/bin/env python3
"""Send Batch 8 B2B outreach via Zoho SMTP."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from outreach_smtp_common import ROOT as _ROOT, load_dotenv, run_outreach_batch  # noqa: E402

EMAILS_JSON = _ROOT / ".tmp_batch8_remaining.json"
SENT_LOG_JSON = _ROOT / ".tmp_batch8_sent.json"
WAVE1_ONLY = ",".join(str(i) for i in range(1, 16))
DEFAULT_DELAY = 50.0  # 45–60s recommended between bulk sends


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Batch 8 B2B outreach via Zoho SMTP")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", type=str, default="")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument(
        "--build-from-md",
        action="store_true",
        help="Rebuild JSON from outreach-batch8-queue.csv via batch8_targets.py",
    )
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--wave1", action="store_true", help="Send wave 1 only (#1–#15)")
    parser.add_argument("--all", action="store_true", help="Send all queued targets (48)")
    args = parser.parse_args()

    load_dotenv()
    if args.build_from_md:
        import batch8_targets  # noqa: WPS433

        n, _ = batch8_targets.write_json()
        print(f"Built {n} batch8 targets from queue CSV.")

    only = args.only
    if args.wave1 and not only:
        only = WAVE1_ONLY
    elif args.all:
        only = ""

    return run_outreach_batch(
        batch_label="Batch 8 outreach",
        emails_json=EMAILS_JSON,
        sent_log_json=SENT_LOG_JSON,
        dry_run=args.dry_run,
        only=only,
        delay=args.delay,
        force=args.force,
        attach_pdf_flag=not args.no_pdf,
    )


if __name__ == "__main__":
    raise SystemExit(main())
