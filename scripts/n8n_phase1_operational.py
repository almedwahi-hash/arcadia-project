#!/usr/bin/env python3
"""Phase 1 n8n operational runner — discover, export, patch, import, test.

Requires:
  N8N_API_URL   e.g. https://your-instance.app.n8n.cloud/api/v1
  N8N_API_KEY   n8n API key

Optional (Supabase verification):
  SUPABASE_URL + service role via direct SQL MCP or env for REST checks

Usage:
  python3 scripts/n8n_phase1_operational.py discover
  python3 scripts/n8n_phase1_operational.py export
  python3 scripts/n8n_phase1_operational.py import-all
  python3 scripts/n8n_phase1_operational.py link-error-handlers
  python3 scripts/n8n_phase1_operational.py test-error-handler
  python3 scripts/n8n_phase1_operational.py test-laila
  python3 scripts/n8n_phase1_operational.py run-all

Does NOT activate Laila Working Copy or deactivate production.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "n8n Workflows" / "production-backup"
WF_DIR = ROOT / "n8n Workflows"
REPORT_PATH = ROOT / "deliverables" / "arcadia-phase1-live-test-results.json"
TODAY = date.today().isoformat()

DISCOVER_TERMS = (
    "arcadia",
    "laila",
    "follow-up",
    "follow up",
    "followup",
    "admin",
    "pricing",
    "cron",
    "error handler",
)

LAILA_NAME_HINTS = ("laila", "telegram v5")
FOLLOWUP_HINTS = ("follow-up", "follow up", "followup", "cron")
ADMIN_HINTS = ("admin commands", "admin")
PRICING_HINTS = ("pricing", "get_price", "quote")

LOCAL_WORKFLOWS = [
    "Arcadia - Central Error Handler.json",
    "Arcadia - Phase1 Inbound Pipeline.json",
    "Arcadia - Phase1 Outbound Log.json",
    "Arcadia - Phase1 Pricing Action Log.json",
    "Arcadia - Phase1 Error Handler Test.json",
]

READONLY_WF_KEYS = {
    "id",
    "createdAt",
    "updatedAt",
    "versionId",
    "meta",
    "shared",
    "homeProject",
    "usedBy",
    "active",
    "tags",
    "isArchived",
    "triggerCount",
    "pinData",
}


class N8nClient:
    def __init__(self, base: str, key: str) -> None:
        self.base = base.rstrip("/")
        self.key = key

    def _request(self, method: str, path: str, body: dict | None = None) -> Any:
        data = None
        headers = {"Accept": "application/json", "X-N8N-API-KEY": self.key}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(f"{self.base}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"n8n API {method} {path} -> {e.code}: {detail}") from e

    def list_workflows(self, limit: int = 250) -> list[dict]:
        payload = self._request("GET", f"/workflows?limit={limit}")
        return payload.get("data", payload) if isinstance(payload, dict) else payload

    def get_workflow(self, wf_id: str) -> dict:
        payload = self._request("GET", f"/workflows/{wf_id}")
        return payload.get("data", payload)

    def create_workflow(self, body: dict) -> dict:
        payload = self._request("POST", "/workflows", body)
        return payload.get("data", payload)

    def update_workflow(self, wf_id: str, body: dict) -> dict:
        payload = self._request("PUT", f"/workflows/{wf_id}", body)
        return payload.get("data", payload)

    def execute_workflow(self, wf_id: str, input_data: dict | None = None) -> dict:
        body = {"inputData": input_data or {}}
        for endpoint in (f"/workflows/{wf_id}/execute", f"/workflows/{wf_id}/run"):
            try:
                payload = self._request("POST", endpoint, body)
                return payload.get("data", payload)
            except RuntimeError as e:
                if "404" in str(e):
                    continue
                raise
        raise RuntimeError(f"Could not execute workflow {wf_id} — no execute/run endpoint")

    def get_execution(self, execution_id: str) -> dict:
        payload = self._request("GET", f"/executions/{execution_id}")
        return payload.get("data", payload)

    def wait_execution(self, execution_id: str, timeout_s: int = 90) -> dict:
        deadline = time.time() + timeout_s
        last = {}
        while time.time() < deadline:
            last = self.get_execution(str(execution_id))
            status = last.get("status") or last.get("finished")
            if status in ("success", "error", "failed", "crashed", True):
                return last
            if last.get("finished") is True or last.get("stoppedAt"):
                return last
            time.sleep(2)
        return last


def load_client() -> N8nClient:
    base = os.environ.get("N8N_API_URL", "").strip()
    key = os.environ.get("N8N_API_KEY", "").strip()
    if not base or not key:
        raise SystemExit("Set N8N_API_URL and N8N_API_KEY environment variables.")
    return N8nClient(base, key)


def name_matches(name: str, terms: tuple[str, ...]) -> bool:
    n = name.lower()
    return any(t in n for t in terms)


def classify_workflow(name: str) -> list[str]:
    n = name.lower()
    roles: list[str] = []
    if any(h in n for h in LAILA_NAME_HINTS):
        roles.append("laila")
    if any(h in n for h in FOLLOWUP_HINTS):
        roles.append("followup")
    if any(h in n for h in ADMIN_HINTS):
        roles.append("admin")
    if any(h in n for h in PRICING_HINTS):
        roles.append("pricing")
    if "error handler" in n:
        roles.append("error_handler")
    if "phase1" in n and "working" in n:
        roles.append("laila_working")
    return roles


def discover(client: N8nClient) -> dict:
    all_wf = client.list_workflows()
    matched = []
    for wf in all_wf:
        name = wf.get("name", "")
        if name_matches(name, DISCOVER_TERMS):
            matched.append(
                {
                    "id": wf.get("id"),
                    "name": name,
                    "active": wf.get("active"),
                    "roles": classify_workflow(name),
                    "updatedAt": wf.get("updatedAt"),
                }
            )
    result = {"discovered_at": datetime.now(timezone.utc).isoformat(), "workflows": matched}
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def export_production(client: N8nClient) -> list[Path]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    exported: list[Path] = []
    for wf in client.list_workflows():
        name = wf.get("name", "")
        if not name_matches(name, DISCOVER_TERMS):
            continue
        detail = client.get_workflow(str(wf["id"]))
        safe = re.sub(r'[<>:"/\\|?*]', "-", name)
        dated = BACKUP_DIR / f"{safe}.{TODAY}.json"
        latest = BACKUP_DIR / f"{safe}.json"
        body = json.dumps(detail, indent=2, ensure_ascii=False) + "\n"
        dated.write_text(body, encoding="utf-8")
        latest.write_text(body, encoding="utf-8")
        exported.append(dated)
        print(f"Exported: {dated.name}")
    if not exported:
        raise SystemExit("No Arcadia/Laila workflows found to export.")
    return exported


def find_laila_export() -> Path:
    candidates = sorted(BACKUP_DIR.glob("*Laila*Telegram*V5*.json"))
    candidates = [p for p in candidates if "Phase1 Working" not in p.name and "Working" not in p.name]
    if not candidates:
        raise SystemExit(f"No Laila V5 export in {BACKUP_DIR}")
    return candidates[0]


def patch_laila_working_copy() -> Path:
    laila_export = find_laila_export()
    out = WF_DIR / "Arcadia - Laila Telegram V5 Phase1 Working.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "patch_laila_phase1.py"),
            "--input",
            str(laila_export),
            "--output",
            str(out),
        ],
        check=True,
    )
    return out


def strip_for_api(wf: dict) -> dict:
    out = {k: v for k, v in wf.items() if k not in READONLY_WF_KEYS}
    out.setdefault("settings", {})
    out.setdefault("connections", {})
    out.setdefault("nodes", [])
    return out


def upsert_local_workflow(client: N8nClient, path: Path, activate: bool = False) -> dict:
    wf = json.loads(path.read_text(encoding="utf-8"))
    name = wf.get("name", path.stem)
    existing = {w["name"]: w for w in client.list_workflows()}
    body = strip_for_api(wf)
    if name in existing:
        wf_id = str(existing[name]["id"])
        updated = client.update_workflow(wf_id, body)
        print(f"Updated workflow: {name} ({wf_id}) active={existing[name].get('active')}")
        return updated
    body["name"] = name
    created = client.create_workflow(body)
    wf_id = str(created.get("id"))
    print(f"Created workflow: {name} ({wf_id}) active=false")
    if activate:
        print(f"WARNING: activate=True requested for {name} — skipped by policy")
    return created


def wire_execute_workflow_ids(wf: dict, name_to_id: dict[str, str]) -> dict:
    out = json.loads(json.dumps(wf))
    for node in out.get("nodes", []):
        if node.get("type") != "n8n-nodes-base.executeWorkflow":
            continue
        cached = node.get("parameters", {}).get("workflowId", {})
        target_name = cached.get("cachedResultName") or node.get("name")
        if target_name in name_to_id:
            node["parameters"]["workflowId"] = {
                "__rl": True,
                "mode": "list",
                "value": name_to_id[target_name],
                "cachedResultName": target_name,
            }
    settings = out.setdefault("settings", {})
    eh_name = "Arcadia - Central Error Handler"
    if eh_name in name_to_id:
        settings["errorWorkflow"] = name_to_id[eh_name]
    return out


def import_all(client: N8nClient) -> dict[str, str]:
    # 1) Export fresh production backups
    export_production(client)

    # 2) Patch Laila working copy from export
    working_path = patch_laila_working_copy()

    # 3) Import base sub-workflows first
    name_to_id: dict[str, str] = {}
    for rel in LOCAL_WORKFLOWS:
        if rel == "Arcadia - Phase1 Error Handler Test.json":
            continue
        wf = upsert_local_workflow(client, WF_DIR / rel, activate=False)
        name_to_id[wf["name"]] = str(wf["id"])

    # 4) Import wired Laila working copy (inactive)
    working = json.loads(working_path.read_text(encoding="utf-8"))
    working = wire_execute_workflow_ids(working, name_to_id)
    working_path.write_text(json.dumps(working, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    laila_wf = upsert_local_workflow(client, working_path, activate=False)
    name_to_id[laila_wf["name"]] = str(laila_wf["id"])

    # 5) Import error handler test wired to central handler id
    test_path = WF_DIR / "Arcadia - Phase1 Error Handler Test.json"
    test_wf_json = json.loads(test_path.read_text(encoding="utf-8"))
    if "Arcadia - Central Error Handler" in name_to_id:
        test_wf_json.setdefault("settings", {})["errorWorkflow"] = name_to_id["Arcadia - Central Error Handler"]
    test_tmp = WF_DIR / ".tmp-error-handler-test-import.json"
    test_tmp.write_text(json.dumps(test_wf_json, indent=2) + "\n", encoding="utf-8")
    test_wf = upsert_local_workflow(client, test_tmp, activate=False)
    name_to_id[test_wf["name"]] = str(test_wf["id"])
    test_tmp.unlink(missing_ok=True)

    mapping_path = ROOT / "deliverables" / "arcadia-phase1-n8n-id-map.json"
    mapping_path.write_text(json.dumps(name_to_id, indent=2) + "\n", encoding="utf-8")
    print(f"ID map: {mapping_path}")
    return name_to_id


def link_error_handlers(client: N8nClient, name_to_id: dict[str, str]) -> None:
    eh_id = name_to_id.get("Arcadia - Central Error Handler")
    if not eh_id:
        for wf in client.list_workflows():
            if "central error handler" in wf.get("name", "").lower():
                eh_id = str(wf["id"])
                break
    if not eh_id:
        raise SystemExit("Central Error Handler workflow id not found")

    for wf in client.list_workflows():
        name = wf.get("name", "")
        n = name.lower()
        if "phase1 working" in n or "phase1 inbound" in n or "phase1 outbound" in n:
            continue
        if "error handler test" in n:
            continue
        roles = classify_workflow(name)
        if not any(r in roles for r in ("laila", "followup", "admin", "pricing")):
            continue
        if "phase1 working" in n:
            continue
        detail = client.get_workflow(str(wf["id"]))
        settings = detail.setdefault("settings", {})
        if settings.get("errorWorkflow") == eh_id:
            print(f"Already linked: {name}")
            continue
        settings["errorWorkflow"] = eh_id
        client.update_workflow(str(wf["id"]), strip_for_api(detail))
        print(f"Linked errorWorkflow on: {name} ({wf['id']})")


def test_error_handler(client: N8nClient, name_to_id: dict[str, str]) -> dict:
    test_name = "Arcadia - Phase1 Error Handler Test"
    test_id = name_to_id.get(test_name)
    if not test_id:
        for wf in client.list_workflows():
            if wf.get("name") == test_name:
                test_id = str(wf["id"])
                break
    if not test_id:
        raise SystemExit("Error Handler Test workflow not imported")

    before = datetime.now(timezone.utc).isoformat()
    exec_info = client.execute_workflow(test_id)
    execution_id = str(exec_info.get("executionId") or exec_info.get("id") or "")
    result = client.wait_execution(execution_id) if execution_id else exec_info
    return {
        "test": "error_handler",
        "workflow_id": test_id,
        "execution_id": execution_id,
        "status": result.get("status"),
        "started_after": before,
        "note": "Verify workflow_failures row + Telegram alert manually in dashboard if API lacks message proof",
    }


def test_laila_scenarios(client: N8nClient, name_to_id: dict[str, str]) -> list[dict]:
    working_name = next((n for n in name_to_id if "phase1 working" in n.lower()), None)
    if not working_name:
        raise SystemExit("Laila Phase1 Working workflow not found")
    working_id = name_to_id[working_name]

    scenarios = [
        ("new_customer", {"body": {"entry": [{"changes": [{"value": {"messages": [{"id": "wa_test_new_001", "from": "971500000001", "type": "text", "text": {"body": "hello new"}}]}}]}]}}),
        ("existing_customer", {"body": {"entry": [{"changes": [{"value": {"messages": [{"id": "wa_test_exist_002", "from": "971500000001", "type": "text", "text": {"body": "second msg"}}]}}]}]}}),
        ("duplicate_whatsapp", {"body": {"entry": [{"changes": [{"value": {"messages": [{"id": "wa_test_exist_002", "from": "971500000001", "type": "text", "text": {"body": "dup"}}]}}]}]}}),
        ("telegram_inbound", {"message": {"message_id": 9001, "chat": {"id": 123456789}, "text": "telegram test"}}),
    ]

    results: list[dict] = []
    for label, payload in scenarios:
        try:
            exec_info = client.execute_workflow(working_id, payload)
            execution_id = str(exec_info.get("executionId") or exec_info.get("id") or "")
            detail = client.wait_execution(execution_id) if execution_id else exec_info
            results.append({"scenario": label, "execution_id": execution_id, "status": detail.get("status"), "ok": True})
        except Exception as e:
            results.append({"scenario": label, "ok": False, "error": str(e)})

    for label in ("pricing_success", "manual_quote", "send_failure", "ai_node_failure"):
        results.append(
            {
                "scenario": label,
                "ok": None,
                "note": "Requires pinned test path or controlled node failure — run after working copy execute baseline succeeds",
            }
        )
    return results


def run_all(client: N8nClient) -> int:
    report: dict[str, Any] = {"started_at": datetime.now(timezone.utc).isoformat(), "steps": {}}
    try:
        report["steps"]["discover"] = discover(client)
        name_to_id = import_all(client)
        report["steps"]["import"] = {"workflow_ids": name_to_id}
        link_error_handlers(client, name_to_id)
        report["steps"]["error_handler_test"] = test_error_handler(client, name_to_id)
        report["steps"]["laila_tests"] = test_laila_scenarios(client, name_to_id)
        report["status"] = "completed"
    except Exception as e:
        report["status"] = "failed"
        report["error"] = str(e)
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        raise
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 1 n8n operational runner")
    ap.add_argument(
        "command",
        choices=["discover", "export", "patch-laila", "import-all", "link-error-handlers", "test-error-handler", "test-laila", "run-all"],
    )
    args = ap.parse_args()
    client = load_client()

    if args.command == "discover":
        discover(client)
        return 0
    if args.command == "export":
        export_production(client)
        return 0
    if args.command == "patch-laila":
        export_production(client)
        patch_laila_working_copy()
        return 0
    if args.command == "import-all":
        import_all(client)
        return 0
    if args.command == "link-error-handlers":
        mapping = json.loads((ROOT / "deliverables" / "arcadia-phase1-n8n-id-map.json").read_text())
        link_error_handlers(client, mapping)
        return 0
    if args.command == "test-error-handler":
        mapping = json.loads((ROOT / "deliverables" / "arcadia-phase1-n8n-id-map.json").read_text())
        print(json.dumps(test_error_handler(client, mapping), indent=2))
        return 0
    if args.command == "test-laila":
        mapping = json.loads((ROOT / "deliverables" / "arcadia-phase1-n8n-id-map.json").read_text())
        print(json.dumps(test_laila_scenarios(client, mapping), indent=2))
        return 0
    return run_all(client)


if __name__ == "__main__":
    raise SystemExit(main())
