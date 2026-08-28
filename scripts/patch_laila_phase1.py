#!/usr/bin/env python3
"""Patch exported Laila V5 production JSON with Phase 1 integration nodes.

Usage:
  python3 scripts/patch_laila_phase1.py \\
    --input "n8n Workflows/production-backup/Arcadia - Laila Telegram V5.2026-08-27.json" \\
    --output "n8n Workflows/Arcadia - Laila Telegram V5 Phase1 Working.json"

Requires production export in production-backup/ first.
Does NOT modify the input file.

Import order in n8n:
  1. Arcadia - Central Error Handler.json
  2. Arcadia - Phase1 Inbound Pipeline.json
  3. Arcadia - Phase1 Outbound Log.json
  4. Arcadia - Phase1 Pricing Action Log.json
  5. Patched Laila Working copy (this script output)
  6. Wire Execute Workflow nodes to imported sub-workflow IDs
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "n8n Workflows" / "production-backup"
DEFAULT_INPUT = BACKUP_DIR / "Arcadia - Laila Telegram V5.2026-08-27.json"
DEFAULT_OUTPUT = ROOT / "n8n Workflows" / "Laila V4 - Final Phase1 Final Candidate.json"
DIFF_OUTPUT = ROOT / "deliverables" / "arcadia-phase1-laila-diff.json"

SUBFLOW_INBOUND = "Arcadia - Phase1 Inbound Pipeline"
SUBFLOW_OUTBOUND = "Arcadia - Phase1 Outbound Log"
SUBFLOW_PRICING = "Arcadia - Phase1 Pricing Action Log"
ERROR_HANDLER = "Arcadia - Central Error Handler"

AI_AGENT_NAMES = {"AI Agent", "Laila Agent", "OpenAI", "Sales Agent", "Laila", "Decision Engine"}
SEND_NODE_NAMES = {
    "Send Message",
    "WhatsApp Send",
    "Send WhatsApp",
    "Telegram Send",
    "Reply to Customer",
    "Send Telegram",
}
PRICING_NODE_NAMES = {
    "get_price",
    "Pricing Engine",
    "TOOL:get_price",
    "Get Price",
    "Supabase Pricing",
    "Quote Options",
    "quote_options",
}


def nid() -> str:
    return str(uuid.uuid4())


def find_nodes_by_type_suffix(wf: dict, suffix: str) -> list[dict]:
    return [n for n in wf.get("nodes", []) if n.get("type", "").endswith(suffix)]


def find_node_by_names(wf: dict, names: set[str]) -> dict | None:
    for n in wf.get("nodes", []):
        if n.get("name") in names:
            return n
    return None


def find_pricing_node(wf: dict) -> dict | None:
    for n in wf.get("nodes", []):
        name = n.get("name", "")
        if name in PRICING_NODE_NAMES:
            return n
        blob = json.dumps(n.get("parameters", {})).lower()
        if "quote_options" in blob or "quote_package" in blob or "get_price" in name.lower():
            return n
    return None


def find_first_after_trigger(wf: dict) -> str | None:
    conns = wf.get("connections", {})
    triggers = (
        find_nodes_by_type_suffix(wf, "webhook")
        + find_nodes_by_type_suffix(wf, "telegramTrigger")
        + find_nodes_by_type_suffix(wf, "whatsAppTrigger")
    )
    if not triggers:
        return None
    tname = triggers[0]["name"]
    outs = conns.get(tname, {}).get("main", [[]])
    if outs and outs[0]:
        return outs[0][0]["node"]
    return None


def pricing_path_report(wf: dict) -> dict:
    report: dict = {
        "nodes": [],
        "urls": [],
        "rpc_calls": [],
        "webhook_wrappers": [],
        "canonical_entry_point": "quote_options",
        "notes": [],
    }
    for n in wf.get("nodes", []):
        name = n.get("name", "")
        params = json.dumps(n.get("parameters", {}))
        blob = (name + " " + params).lower()
        if not any(k in blob for k in ("quote_package", "quote_options", "quote_multi", "get_price", "pricing", "/rpc/")):
            continue
        report["nodes"].append({"name": name, "type": n.get("type")})
        if "quote_package" in blob:
            report["rpc_calls"].append("quote_package")
        if "quote_options" in blob:
            report["rpc_calls"].append("quote_options")
        if "quote_multi" in blob:
            report["rpc_calls"].append("quote_multi")
        if n.get("type", "").endswith("webhook") or ("/webhook" in blob and "pric" in blob):
            report["webhook_wrappers"].append(name)
        if n.get("type", "").endswith("httpRequest") and ("quote" in blob or "rpc" in blob):
            report["urls"].append(name)

    report["rpc_calls"] = sorted(set(report["rpc_calls"]))
    report["webhook_wrappers"] = sorted(set(report["webhook_wrappers"]))
    report["urls"] = sorted(set(report["urls"]))

    if "quote_options" in report["rpc_calls"]:
        report["canonical_entry_point"] = "quote_options"
        report["notes"].append("Keep quote_options as canonical — quote_package has overload ambiguity in Postgres.")
    elif "quote_package" in report["rpc_calls"] and "quote_options" not in report["rpc_calls"]:
        report["canonical_entry_point"] = "quote_options (recommended migration — not applied in Phase 1)"
        report["notes"].append("Production uses quote_package — consider switching to quote_options without changing formulas.")
    elif report["webhook_wrappers"]:
        report["canonical_entry_point"] = f"webhook wrapper: {report['webhook_wrappers'][0]}"
        report["notes"].append("Document wrapper URL; do not change calculation path in Phase 1.")
    else:
        report["notes"].append("Pricing node not detected — wire Phase1 Pricing Action Log manually after get_price.")

    return report


PREPARE_OUTBOUND_JS = """// Phase1 — prepare outbound log AFTER successful send only
function extractOutboundText(val) {
  if (val == null) return null;
  if (typeof val === 'string') { const s = val.trim(); return s || null; }
  if (typeof val === 'object') {
    return val.conversation || val.extendedTextMessage?.text || val.text || null;
  }
  return null;
}
const send = $input.first().json;
const de = $('Decision Engine').first()?.json || {};
const ctx = $('Arcadia - Phase1 Inbound Pipeline').first()?.json
  || $('Phase1 IF Proceed (not duplicate)').first()?.json
  || {};
const messageText = extractOutboundText(send.text)
  || extractOutboundText(send.message)
  || extractOutboundText(send.body?.text)
  || extractOutboundText(send.body)
  || (typeof send.output === 'string' ? send.output.trim() : null)
  || (typeof send.reply === 'string' ? send.reply.trim() : null)
  || (typeof de.response === 'string' ? de.response.trim() : null);
return [{ json: {
  lead_id: ctx.lead_id,
  customer_id: ctx.customer_id,
  conversation_id: ctx.conversation_id,
  channel: ctx.phase1?.channel || ctx.channel,
  message_text: messageText,
  provider_message_id: send.message_id || send.messages?.[0]?.id || send.key?.id || null,
  metadata: { phase1: 'outbound_after_send_success' }
}}];"""

PREPARE_PRICING_OBSERVABILITY_JS = """// Phase1 observability — parse Decision Engine response (no pricing logic change)
const de = $input.first().json;
const ctx = $('Arcadia - Phase1 Inbound Pipeline').first()?.json || {};
const response = String(de.response || '');
const priceUsd = response.match(/\\$[\\d,]+/)?.[0] || response.match(/([\\d,]{3,})\\s*USD/i)?.[0] || null;
const manualPath = /no_hotel|يدوي|human|موظف|فريق/i.test(response);
const hasPrice = !!priceUsd || /\\$[\\d,]{2,}|USD\\s*[\\d,]+|دولار/.test(response);
return [{ json: {
  phone: de.phone,
  remoteJid: de.remoteJid,
  response: de.response,
  isManager: de.isManager,
  followup: de.followup,
  lead_id: ctx.lead_id,
  customer_id: ctx.customer_id,
  channel: ctx.phase1?.channel || 'whatsapp',
  action_type: 'get_price',
  status: manualPath && !hasPrice ? 'failed' : (hasPrice ? 'success' : 'failed'),
  output_summary: (priceUsd || response).slice(0, 500),
  input_summary: String(ctx.phase1?.message_text || '').slice(0, 500),
  metadata: { phase1: 'pricing_observability', source: 'decision_engine_response' }
}}];"""


def patch_save_response_after_pricing_log(save_node: dict) -> None:
    """Pricing Action Log returns {logged:true}; restore Decision Engine fields for Send WhatsApp."""
    js = save_node.get("parameters", {}).get("jsCode", "")
    if "Decision Engine" in js:
        return
    save_node.setdefault("parameters", {})["jsCode"] = js.replace(
        "const prev = $input.first().json;",
        "const de = $('Decision Engine').first()?.json || {};\nconst prev = { ...de, ...($input.first().json || {}) };",
        1,
    )


def wire_decision_engine_pricing_observability(
    out: dict, conns: dict, ai_node: dict, meta: dict
) -> bool:
    """Wire observability-only Pricing Action Log after Decision Engine (Laila V4 path)."""
    if find_node_by_names(out, {"Phase1 Prepare Pricing Action"}):
        return False
    save_node = find_node_by_names(out, {"Save Response"})
    if not save_node:
        return False
    patch_save_response_after_pricing_log(save_node)
    de = ai_node
    prep = {
        "parameters": {"mode": "runOnceForAllItems", "jsCode": PREPARE_PRICING_OBSERVABILITY_JS},
        "id": nid(),
        "name": "Phase1 Prepare Pricing Action",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [de["position"][0] + 100, de["position"][1] + 120],
    }
    pricing_exec = make_execute_workflow_node(
        SUBFLOW_PRICING, de["position"][0] + 220, de["position"][1] + 120
    )
    pricing_exec["continueOnFail"] = True
    pricing_exec["onError"] = "continueRegularOutput"
    out["nodes"].extend([prep, pricing_exec])
    meta["inserted_nodes"].extend([prep["name"], pricing_exec["name"]])
    conns[de["name"]] = {"main": [[{"node": prep["name"], "type": "main", "index": 0}]]}
    conns[prep["name"]] = {"main": [[{"node": SUBFLOW_PRICING, "type": "main", "index": 0}]]}
    conns[SUBFLOW_PRICING] = {"main": [[{"node": save_node["name"], "type": "main", "index": 0}]]}
    meta["rewired"].append(
        f"{de['name']} -> Phase1 Prepare Pricing Action -> Pricing Action Log -> {save_node['name']}"
    )
    return True


def make_execute_workflow_node(name: str, x: int, y: int) -> dict:
    return {
        "parameters": {
            "workflowId": {"__rl": True, "mode": "list", "value": "", "cachedResultName": name},
            "mode": "once",
            "options": {},
        },
        "id": nid(),
        "name": name,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.2,
        "position": [x, y],
        "notes": f"Phase1 — select imported workflow '{name}' after import",
    }


def patch_workflow(wf: dict) -> tuple[dict, dict]:
    out = deepcopy(wf)
    meta: dict = {"patched": True, "warnings": [], "inserted_nodes": [], "rewired": []}

    ai_node = find_node_by_names(out, AI_AGENT_NAMES)
    if not ai_node:
        agents = find_nodes_by_type_suffix(out, "agent")
        ai_node = agents[0] if agents else None
    if not ai_node:
        meta["warnings"].append("AI Agent node not found — wire Phase1 IF Proceed manually to your AI node")

    send_node = find_node_by_names(out, SEND_NODE_NAMES)
    if not send_node:
        meta["warnings"].append("Send node not found — outbound log must be wired on send SUCCESS branch manually")

    conns = out.setdefault("connections", {})

    pricing_node = find_pricing_node(out)
    pricing_wired = False
    if ai_node and ai_node.get("name") == "Decision Engine":
        pricing_wired = wire_decision_engine_pricing_observability(out, conns, ai_node, meta)
    elif pricing_node:
        pricing_wired = True  # handled in RPC/tool block below
    if not pricing_wired and not pricing_node:
        meta["warnings"].append("Pricing node not found — wire Phase1 Pricing Action Log manually after get_price")

    norm_node = {
        "parameters": {
            "mode": "runOnceForAllItems",
            "jsCode": """// Phase1 — normalize inbound (no prompt / stage changes)
const j = $input.first().json;
const raw = $('WhatsApp Webhook').first()?.json || $('Telegram Trigger').first()?.json || {};
const body = raw.body || raw;
const data = body.data || body;
const key = data.key || {};
const waMsg = body.entry?.[0]?.changes?.[0]?.value?.messages?.[0];
const tgMsg = raw.message || body.message;
const msg = waMsg || tgMsg || body.messages?.[0] || {};
const phone = String(
  j.phone
  || key.remoteJid?.replace('@s.whatsapp.net', '').replace('@g.us', '')
  || msg.from
  || tgMsg?.chat?.id
  || body.from?.id
  || j.chat_id
  || ''
).trim();
const providerMessageId = key.id ? String(key.id)
  : (waMsg?.id ? String(waMsg.id)
  : (tgMsg?.message_id != null ? String(tgMsg.message_id) : (j.provider_message_id || null)));
const channel = key.remoteJid || waMsg?.id ? 'whatsapp' : (tgMsg ? 'telegram' : (j.channel || 'whatsapp'));
const text = j.textContent || j.text || msg.text?.body || msg.body || tgMsg?.text || '';
const ALLOWED = new Set(['text','image','audio','document','location','video','sticker','unknown']);
const TYPE_MAP = { conversation: 'text', extendedTextMessage: 'text', audioMessage: 'audio', imageMessage: 'image', documentMessage: 'document', videoMessage: 'video', stickerMessage: 'sticker' };
const rawType = data.messageType || msg.type || (tgMsg?.photo ? 'image' : 'text');
const messageType = TYPE_MAP[rawType] || (ALLOWED.has(rawType) ? rawType : 'unknown');
return [{ json: {
  ...j,
  phase1: {
    phone,
    provider_message_id: providerMessageId,
    channel,
    message_text: text,
    message_type: messageType,
    metadata: { raw_channel: channel, normalized_at: new Date().toISOString(), source: 'phase1_normalize' }
  }
}}];""",
        },
        "id": nid(),
        "name": "Phase1 Normalize Inbound",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [200, 300],
    }
    out["nodes"].append(norm_node)
    meta["inserted_nodes"].append(norm_node["name"])

    # Prefer inserting after existing Parse/Normalize node if present
    parse_node = find_node_by_names(out, {"Parse + CRM", "Normalize"})
    insert_after = parse_node["name"] if parse_node else None

    if insert_after and parse_node:
        norm_node["position"] = [parse_node["position"][0] + 180, parse_node["position"][1]]
        inbound_exec = make_execute_workflow_node(SUBFLOW_INBOUND, parse_node["position"][0] + 400, parse_node["position"][1])
        out["nodes"].append(inbound_exec)
        meta["inserted_nodes"].append(inbound_exec["name"])
        if_proceed = {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": "proceed-check",
                            "leftValue": "={{ $json.proceed }}",
                            "rightValue": True,
                            "operator": {"type": "boolean", "operation": "true"},
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
            "id": nid(),
            "name": "Phase1 IF Proceed (not duplicate)",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [parse_node["position"][0] + 620, parse_node["position"][1]],
        }
        out["nodes"].append(if_proceed)
        meta["inserted_nodes"].append(if_proceed["name"])
        old_targets = conns.get(insert_after, {}).get("main", [[]])
        next_node = old_targets[0][0]["node"] if old_targets and old_targets[0] else (ai_node["name"] if ai_node else None)
        conns[insert_after] = {"main": [[{"node": "Phase1 Normalize Inbound", "type": "main", "index": 0}]]}
        conns["Phase1 Normalize Inbound"] = {"main": [[{"node": SUBFLOW_INBOUND, "type": "main", "index": 0}]]}
        conns[SUBFLOW_INBOUND] = {"main": [[{"node": "Phase1 IF Proceed (not duplicate)", "type": "main", "index": 0}]]}
        if next_node:
            conns["Phase1 IF Proceed (not duplicate)"] = {
                "main": [[{"node": next_node, "type": "main", "index": 0}], []]
            }
        meta["rewired"].append(f"{insert_after} -> Normalize -> Inbound Pipeline -> IF Proceed -> {next_node}")
    else:
        inbound_exec = make_execute_workflow_node(SUBFLOW_INBOUND, 420, 300)
        out["nodes"].append(inbound_exec)
        meta["inserted_nodes"].append(inbound_exec["name"])

        if_proceed = {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": "proceed-check",
                            "leftValue": "={{ $json.proceed }}",
                            "rightValue": True,
                            "operator": {"type": "boolean", "operation": "true"},
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
            "id": nid(),
            "name": "Phase1 IF Proceed (not duplicate)",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [640, 300],
        }
        out["nodes"].append(if_proceed)
        meta["inserted_nodes"].append(if_proceed["name"])

        conns.setdefault("Phase1 Normalize Inbound", {"main": [[{"node": SUBFLOW_INBOUND, "type": "main", "index": 0}]]})
        conns[SUBFLOW_INBOUND] = {"main": [[{"node": "Phase1 IF Proceed (not duplicate)", "type": "main", "index": 0}]]}

        if ai_node:
            conns["Phase1 IF Proceed (not duplicate)"] = {
                "main": [[{"node": ai_node["name"], "type": "main", "index": 0}], []]
            }

        triggers = (
            find_nodes_by_type_suffix(out, "webhook")
            + find_nodes_by_type_suffix(out, "telegramTrigger")
            + find_nodes_by_type_suffix(out, "whatsAppTrigger")
            + find_nodes_by_type_suffix(out, "chatTrigger")
        )
        for t in triggers:
            tname = t["name"]
            old_target = conns.get(tname, {}).get("main", [[]])[0][0]["node"] if conns.get(tname, {}).get("main", [[]]) and conns[tname]["main"][0] else None
            conns[tname] = {"main": [[{"node": "Phase1 Normalize Inbound", "type": "main", "index": 0}]]}
            if old_target:
                meta["rewired"].append(f"{tname} -> Phase1 Normalize Inbound (was -> {old_target})")

    if send_node:
        prepare_outbound = {
            "parameters": {
                "mode": "runOnceForAllItems",
                "jsCode": PREPARE_OUTBOUND_JS,
            },
            "id": nid(),
            "name": "Phase1 Prepare Outbound",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [send_node["position"][0] + 180, send_node["position"][1]],
        }
        outbound_exec = make_execute_workflow_node(
            SUBFLOW_OUTBOUND, send_node["position"][0] + 400, send_node["position"][1]
        )
        out["nodes"].extend([prepare_outbound, outbound_exec])
        meta["inserted_nodes"].extend([prepare_outbound["name"], outbound_exec["name"]])

        # Send success -> prepare -> outbound log (failure goes to errorWorkflow, no outbound)
        conns[send_node["name"]] = {"main": [[{"node": "Phase1 Prepare Outbound", "type": "main", "index": 0}]]}
        conns["Phase1 Prepare Outbound"] = {"main": [[{"node": SUBFLOW_OUTBOUND, "type": "main", "index": 0}]]}
        meta["rewired"].append(f"{send_node['name']} success -> Phase1 Prepare Outbound -> Outbound Log")

    if pricing_node and not pricing_wired and pricing_node.get("name") != "Decision Engine":
        prepare_pricing = {
            "parameters": {
                "mode": "runOnceForAllItems",
                "jsCode": """// Phase1 — agent_actions for get_price only (no RPC change)
const r = $input.first().json;
const ctx = $('Arcadia - Phase1 Inbound Pipeline').first()?.json || {};
const failed = !!(r.manual_quote || r.error || r.status === 'failed');
const price = r.final_price_usd ?? r.price ?? r[0]?.final_price_usd;
return [{ json: {
  lead_id: ctx.lead_id,
  customer_id: ctx.customer_id,
  source_channel: ctx.phase1?.channel,
  status: failed ? 'failed' : 'success',
  output_summary: failed ? (r.reason || r.error || 'manual_quote') : (price != null ? `final_price_usd=${price}` : JSON.stringify(r).slice(0,200)),
  input_summary: ctx.phase1?.message_text || null,
  action_type: 'get_price'
}}];""",
            },
            "id": nid(),
            "name": "Phase1 Prepare Pricing Action",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [pricing_node["position"][0] + 180, pricing_node["position"][1] + 120],
        }
        pricing_exec = make_execute_workflow_node(
            SUBFLOW_PRICING, pricing_node["position"][0] + 400, pricing_node["position"][1] + 120
        )
        out["nodes"].extend([prepare_pricing, pricing_exec])
        meta["inserted_nodes"].extend([prepare_pricing["name"], pricing_exec["name"]])

        old_pricing_targets = conns.get(pricing_node["name"], {}).get("main", [[]])
        conns[pricing_node["name"]] = {"main": [[{"node": "Phase1 Prepare Pricing Action", "type": "main", "index": 0}]]}
        conns["Phase1 Prepare Pricing Action"] = {"main": [[{"node": SUBFLOW_PRICING, "type": "main", "index": 0}]]}
        if old_pricing_targets and old_pricing_targets[0]:
            next_node = old_pricing_targets[0][0]["node"]
            conns[SUBFLOW_PRICING] = {"main": [[{"node": next_node, "type": "main", "index": 0}]]}
            meta["rewired"].append(f"{pricing_node['name']} -> Pricing Action Log -> {next_node}")
        else:
            meta["warnings"].append(f"Pricing node {pricing_node['name']} had no downstream — wire manually after Pricing Action Log")

    settings = out.setdefault("settings", {})
    settings["errorWorkflow"] = ERROR_HANDLER
    settings["executionOrder"] = settings.get("executionOrder", "v1")

    base_name = out.get("name") or "Laila Production"
    out["name"] = "Laila V4 - Final Phase1 Final Candidate"

    meta["pricing_path"] = pricing_path_report(out)
    meta["source_nodes"] = {
        "ai_agent": ai_node["name"] if ai_node else None,
        "send_node": send_node["name"] if send_node else None,
        "pricing_node": pricing_node["name"] if pricing_node else None,
        "first_after_trigger_before_patch": find_first_after_trigger(wf),
    }
    return out, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    if not args.input.exists():
        print(f"ERROR: Production export not found: {args.input}", file=sys.stderr)
        print("Export from n8n UI to n8n Workflows/production-backup/ first.", file=sys.stderr)
        print("Or test with fixture:", file=sys.stderr)
        print("  python3 scripts/patch_laila_phase1.py --input 'n8n Workflows/fixtures/laila-v5-minimal.fixture.json'", file=sys.stderr)
        return 1

    wf = json.loads(args.input.read_text(encoding="utf-8"))
    patched, meta = patch_workflow(wf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(patched, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DIFF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DIFF_OUTPUT.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote working copy: {args.output}")
    print(f"Patch meta/diff: {DIFF_OUTPUT}")
    if meta["warnings"]:
        print("Warnings:", "; ".join(meta["warnings"]))
    print("Pricing path:", json.dumps(meta["pricing_path"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
