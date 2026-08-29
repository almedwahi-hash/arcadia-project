#!/usr/bin/env python3
"""Embed booking financial logic JS into n8n workflow JSON."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAP = {
    "Arcadia - Booking Payment Record.json": ("Logic", "scripts/booking_payment_record_logic.js"),
    "Arcadia - Booking Approval Handler.json": ("Logic", "scripts/booking_approval_handler_logic.js"),
}


def embed() -> None:
    for wf_name, (node_name, rel_logic) in MAP.items():
        wf_path = ROOT / "n8n Workflows" / wf_name
        logic_path = ROOT / rel_logic
        wf = json.loads(wf_path.read_text(encoding="utf-8"))
        js = logic_path.read_text(encoding="utf-8")
        for node in wf.get("nodes", []):
            if node.get("name") == node_name:
                node.setdefault("parameters", {})["jsCode"] = js
                break
        else:
            raise KeyError(f"{node_name} not in {wf_name}")
        wf_path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"embedded {rel_logic} -> {wf_name}")


if __name__ == "__main__":
    embed()
