#!/usr/bin/env python3
"""Embed Laila conversation-behavior patch into n8n workflow JSON files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDENDUM = ROOT / "scripts" / "laila_conversation_prompt_addendum.txt"
MARKER = "# 💬 أسلوب واتساب (Human-like"

WHATSAPP_MAP = {
    "Arcadia - Laila V4 Final Phase1 Production.json": [
        ("Parse + CRM", "scripts/laila_parse_crm_logic.js"),
        ("Decision Engine", "scripts/laila_decision_engine_logic.js"),
    ],
}

AI_AGENT_MAP = {
    "Arcadia - Laila AI Agent.json": [
        ("Normalize", "scripts/laila_normalize_logic.js"),
        ("format_reply", "scripts/laila_format_reply_logic.js"),
    ],
}


def embed_js(workflow_path: Path, node_name: str, logic_path: Path) -> None:
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


def patch_agent_prompt(workflow_path: Path) -> bool:
    if not ADDENDUM.exists():
        return False
    addendum = ADDENDUM.read_text(encoding="utf-8").strip()
    wf = json.loads(workflow_path.read_text(encoding="utf-8"))
    changed = False
    for node in wf.get("nodes", []):
        if node.get("name") != "AI Agent":
            continue
        opts = node.setdefault("parameters", {}).setdefault("options", {})
        msg = str(opts.get("systemMessage", ""))
        if MARKER in msg:
            return False
        if msg.startswith("="):
            opts["systemMessage"] = msg + "\n" + addendum
        else:
            opts["systemMessage"] = "=" + msg + "\n" + addendum
        changed = True
        break
    if changed:
        workflow_path.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def embed_all() -> None:
    for wf_name, pairs in {**WHATSAPP_MAP, **AI_AGENT_MAP}.items():
        wf_path = ROOT / "n8n Workflows" / wf_name
        if not wf_path.exists():
            print(f"skip missing workflow: {wf_name}")
            continue
        for node_name, rel_logic in pairs:
            embed_js(wf_path, node_name, ROOT / rel_logic)
            print(f"embedded {rel_logic} -> {wf_name} ({node_name})")
    ai_path = ROOT / "n8n Workflows" / "Arcadia - Laila AI Agent.json"
    if ai_path.exists() and patch_agent_prompt(ai_path):
        print("appended conversation prompt addendum -> Arcadia - Laila AI Agent.json")


if __name__ == "__main__":
    embed_all()
