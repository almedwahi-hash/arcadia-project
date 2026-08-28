#!/usr/bin/env python3
"""Embed booking agent JS logic files into n8n workflow JSON before import."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOGIC_MAP = {
    "Arcadia - Booking Task Update.json": ("Task Update Logic", "scripts/booking_task_update_logic.js"),
    "Arcadia - Booking Supplier Draft.json": ("Supplier Draft Logic", "scripts/booking_supplier_draft_logic.js"),
    "Arcadia - Booking Task Reminder Watcher.json": ("Reminder Watcher Logic", "scripts/booking_task_reminder_watcher_logic.js"),
}


def embed_logic(workflow_path: Path, node_name: str, logic_path: Path) -> None:
    wf = json.loads(workflow_path.read_text(encoding="utf-8"))
    js = logic_path.read_text(encoding="utf-8")
    for node in wf.get("nodes", []):
        if node.get("name") == node_name:
            node.setdefault("parameters", {})["jsCode"] = js
            node["parameters"]["mode"] = "runOnceForAllItems"
            break
    else:
        raise KeyError(f"Node {node_name!r} not found in {workflow_path.name}")
    workflow_path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def embed_all() -> None:
    for wf_name, (node_name, rel_logic) in LOGIC_MAP.items():
        wf_path = ROOT / "n8n Workflows" / wf_name
        logic_path = ROOT / rel_logic
        if not wf_path.exists():
            print(f"skip missing workflow: {wf_name}")
            continue
        embed_logic(wf_path, node_name, logic_path)
        print(f"embedded {rel_logic} -> {wf_name}")


if __name__ == "__main__":
    embed_all()
