#!/usr/bin/env python3
"""Assign Central Error Handler to exported n8n workflow JSON files.

Usage:
  python3 scripts/patch_workflow_error_handler.py \\
    "n8n Workflows/production-backup/Arcadia - Follow-up Cron (3h-24h).json"

  python3 scripts/patch_workflow_error_handler.py --all-backups

Does NOT modify pricing formulas, prompts, or follow-up timing — only settings.errorWorkflow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "n8n Workflows" / "production-backup"
ERROR_HANDLER = "Arcadia - Central Error Handler"
SKIP_NAMES = {"Arcadia - Central Error Handler", "Arcadia - Phase1 Error Handler Test"}


def patch_file(path: Path, in_place: bool = True) -> bool:
    wf = json.loads(path.read_text(encoding="utf-8"))
    name = wf.get("name", path.stem)
    if any(skip.lower() in name.lower() for skip in SKIP_NAMES):
        print(f"SKIP (error handler itself): {path.name}")
        return False
    settings = wf.setdefault("settings", {})
    old = settings.get("errorWorkflow")
    settings["errorWorkflow"] = ERROR_HANDLER
    out_path = path if in_place else path.with_suffix(".error-handler.json")
    out_path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PATCHED {path.name}: errorWorkflow {old!r} -> {ERROR_HANDLER!r}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", type=Path, help="Workflow JSON files to patch")
    ap.add_argument("--all-backups", action="store_true", help="Patch all JSON in production-backup/")
    args = ap.parse_args()

    targets: list[Path] = list(args.files)
    if args.all_backups:
        targets.extend(sorted(BACKUP_DIR.glob("*.json")))

    if not targets:
        print("No files. Export production workflows to production-backup/ first.", file=sys.stderr)
        return 1

    patched = 0
    for p in targets:
        if not p.exists():
            print(f"MISSING: {p}", file=sys.stderr)
            continue
        if patch_file(p):
            patched += 1
    print(f"Done. Patched {patched} file(s).")
    return 0 if patched else 1


if __name__ == "__main__":
    raise SystemExit(main())
