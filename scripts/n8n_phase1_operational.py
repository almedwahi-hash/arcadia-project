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
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "n8n Workflows" / "production-backup"
WF_DIR = ROOT / "n8n Workflows"
REPORT_PATH = ROOT / "deliverables" / "arcadia-phase1-live-test-results.json"
TODAY = date.today().isoformat()

SUPABASE_REST = "https://xfibcjhshpmqkrhlpsoa.supabase.co/rest/v1"


def supabase_service_key() -> str:
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        raise RuntimeError("Set SUPABASE_SERVICE_ROLE_KEY for Supabase HTTP node patching during import.")
    return key

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
    "Arcadia - Phase1 Laila Scenario Test.json",
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

    def activate_workflow(self, wf_id: str) -> dict:
        payload = self._request("POST", f"/workflows/{wf_id}/activate")
        return payload.get("data", payload)

    def deactivate_workflow(self, wf_id: str) -> dict:
        payload = self._request("POST", f"/workflows/{wf_id}/deactivate")
        return payload.get("data", payload)

    def list_executions(self, workflow_id: str | None = None, limit: int = 5) -> list[dict]:
        path = f"/executions?limit={limit}"
        if workflow_id:
            path += f"&workflowId={workflow_id}"
        payload = self._request("GET", path)
        return payload.get("data", payload) if isinstance(payload, dict) else payload

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


def normalize_n8n_api_base(raw_url: str) -> str:
    """Map UI or project URLs to REST base .../api/v1."""
    url = raw_url.strip().rstrip("/")
    if not url:
        return url
    if url.endswith("/api/v1"):
        return url
    idx = url.find("/api/v1")
    if idx != -1:
        return url[: idx + len("/api/v1")]
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/api/v1"
    return url


def n8n_public_base(api_base: str) -> str:
    """https://host/api/v1 -> https://host"""
    parsed = urlparse(api_base)
    return f"{parsed.scheme}://{parsed.netloc}"


def trigger_webhook(api_base: str, path: str, payload: dict, *, test_mode: bool = False) -> tuple[int, str]:
    """POST to n8n webhook (production or test URL). Returns (status_code, body)."""
    base = n8n_public_base(api_base)
    prefix = "webhook-test" if test_mode else "webhook"
    url = f"{base}/{prefix}/{path.lstrip('/')}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def wait_for_new_execution(
    client: N8nClient, workflow_id: str, after_iso: str, timeout_s: int = 90
) -> dict | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for ex in client.list_executions(workflow_id=workflow_id, limit=10):
            started = ex.get("startedAt") or ""
            if started >= after_iso:
                ex_id = str(ex.get("id", ""))
                if ex_id:
                    detail = client.wait_execution(ex_id, timeout_s=max(10, int(deadline - time.time())))
                    detail["id"] = ex_id
                    return detail
        time.sleep(2)
    return None


def load_client() -> N8nClient:
    raw = os.environ.get("N8N_API_URL", "").strip()
    key = os.environ.get("N8N_API_KEY", "").strip()
    if not raw or not key:
        raise SystemExit("Set N8N_API_URL and N8N_API_KEY environment variables.")
    base = normalize_n8n_api_base(raw)
    if base != raw.rstrip("/"):
        print(f"Using n8n REST base: {base}", file=sys.stderr)
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
    backup = BACKUP_DIR
    dated = lambda pat: sorted(backup.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)

    def pick(candidates: list[Path]) -> Path | None:
        for p in candidates:
            n = p.name.lower()
            if any(x in n for x in ("backup", "test", "copy", "work", "_backup")):
                continue
            return p
        return candidates[0] if candidates else None

    # Production reality (Aug 2026): active WA sales = Laila V4 - Final; web chat = Laila
    for pattern in (
        "Laila V4 - Final.*.json",
        "Laila.*.json",
        "*Laila*V5*.json",
        "*Laila*Telegram*.json",
    ):
        cands = [p for p in dated(pattern) if not p.name.endswith(".json.json")]
        found = pick(cands)
        if found:
            return found
    raise SystemExit(f"No Laila production export in {BACKUP_DIR}")


def patch_laila_working_copy() -> Path:
    laila_export = find_laila_export()
    out = WF_DIR / "Laila V4 - Final Phase1 Working.json"
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
    allowed = {"name", "nodes", "connections", "settings", "staticData"}
    return {k: wf[k] for k in allowed if k in wf and wf[k] is not None}


def fix_error_workflow_id(wf: dict, name_to_id: dict[str, str]) -> dict:
    out = json.loads(json.dumps(wf))
    settings = out.setdefault("settings", {})
    eh = settings.get("errorWorkflow")
    if isinstance(eh, str) and eh in name_to_id:
        settings["errorWorkflow"] = name_to_id[eh]
    return out


def fix_supabase_http_nodes(wf: dict) -> dict:
    """Replace missing supabaseApi credentials with header auth (matches production Laila pattern)."""
    out = json.loads(json.dumps(wf))
    for node in out.get("nodes", []):
        if node.get("type") != "n8n-nodes-base.httpRequest":
            continue
        params = node.setdefault("parameters", {})
        blob = json.dumps(params)
        if "supabaseApi" not in blob and "supabase.co" not in blob and "$env.SUPABASE_URL" not in blob:
            continue
        params.pop("authentication", None)
        params.pop("nodeCredentialType", None)
        url = str(params.get("url", ""))
        # Fix corrupted expression URLs from earlier imports
        if "={{ https://" in url or "={{ http://" in url:
            url = re.sub(
                r"=\{\{\s*(https?://[^\s/]+)\s*\}\}(/rest/v1/\S+)?",
                lambda m: (m.group(1) + (m.group(2) or "")),
                url,
            )
        if "$env.SUPABASE_URL" in url:
            url = url.replace("={{ $env.SUPABASE_URL }}", SUPABASE_REST.rsplit("/rest/v1", 1)[0])
            url = url.replace("$env.SUPABASE_URL", "https://xfibcjhshpmqkrhlpsoa.supabase.co")
        if url.startswith("={{") and "$env" not in url and "supabase.co" not in url:
            pass
        elif not url.startswith("http") and not url.startswith("={{"):
            url = SUPABASE_REST + (url if url.startswith("/") else "")
        params["url"] = url
        params["sendHeaders"] = True
        hp = params.setdefault("headerParameters", {"parameters": []})
        names = {p.get("name") for p in hp.get("parameters", [])}
        for name, val in (
            ("apikey", supabase_service_key()),
            ("Authorization", f"Bearer {supabase_service_key()}"),
            ("Content-Type", "application/json"),
        ):
            if name not in names:
                hp["parameters"].append({"name": name, "value": val})
        node.pop("credentials", None)
        node["alwaysOutputData"] = True
    return out


def upsert_local_workflow(
    client: N8nClient, path: Path, activate: bool = False, name_to_id: dict[str, str] | None = None
) -> dict:
    wf = json.loads(path.read_text(encoding="utf-8"))
    wf = fix_supabase_http_nodes(wf)
    if name_to_id:
        wf = fix_error_workflow_id(wf, name_to_id)
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

    # 3) Import base sub-workflows first (Central Error Handler before others for errorWorkflow ids)
    name_to_id: dict[str, str] = {}
    import_order = [
        "Arcadia - Central Error Handler.json",
        "Arcadia - Phase1 Inbound Pipeline.json",
        "Arcadia - Phase1 Outbound Log.json",
        "Arcadia - Phase1 Pricing Action Log.json",
    ]
    for rel in import_order:
        wf = upsert_local_workflow(client, WF_DIR / rel, activate=False, name_to_id=name_to_id)
        name_to_id[wf["name"]] = str(wf["id"])
    for rel in LOCAL_WORKFLOWS:
        if rel in import_order or rel in (
            "Arcadia - Phase1 Error Handler Test.json",
            "Arcadia - Phase1 Laila Scenario Test.json",
        ):
            continue
        wf = upsert_local_workflow(client, WF_DIR / rel, activate=False, name_to_id=name_to_id)
        name_to_id[wf["name"]] = str(wf["id"])

    # 4) Import wired Laila working copy (inactive)
    working = json.loads(working_path.read_text(encoding="utf-8"))
    working = wire_execute_workflow_ids(working, name_to_id)
    working = fix_error_workflow_id(working, name_to_id)
    working_path.write_text(json.dumps(working, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    laila_wf = upsert_local_workflow(client, working_path, activate=False, name_to_id=name_to_id)
    name_to_id[laila_wf["name"]] = str(laila_wf["id"])

    # 5) Import error handler test wired to central handler id
    test_path = WF_DIR / "Arcadia - Phase1 Error Handler Test.json"
    test_wf_json = json.loads(test_path.read_text(encoding="utf-8"))
    if "Arcadia - Central Error Handler" in name_to_id:
        test_wf_json.setdefault("settings", {})["errorWorkflow"] = name_to_id["Arcadia - Central Error Handler"]
    test_tmp = WF_DIR / ".tmp-error-handler-test-import.json"
    test_tmp.write_text(json.dumps(test_wf_json, indent=2) + "\n", encoding="utf-8")
    test_wf = upsert_local_workflow(client, test_tmp, activate=False, name_to_id=name_to_id)
    name_to_id[test_wf["name"]] = str(test_wf["id"])
    test_tmp.unlink(missing_ok=True)

    # 6) Import Laila scenario test runner (inactive)
    scenario_path = WF_DIR / "Arcadia - Phase1 Laila Scenario Test.json"
    scenario_json = json.loads(scenario_path.read_text(encoding="utf-8"))
    scenario_json = wire_execute_workflow_ids(scenario_json, name_to_id)
    scenario_tmp = WF_DIR / ".tmp-laila-scenario-test-import.json"
    scenario_tmp.write_text(json.dumps(scenario_json, indent=2) + "\n", encoding="utf-8")
    scenario_wf = upsert_local_workflow(client, scenario_tmp, activate=False, name_to_id=name_to_id)
    name_to_id[scenario_wf["name"]] = str(scenario_wf["id"])
    scenario_tmp.unlink(missing_ok=True)

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
        if "error handler test" in n or "laila scenario test" in n:
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
    eh_name = "Arcadia - Central Error Handler"
    test_id = name_to_id.get(test_name)
    eh_id = name_to_id.get(eh_name)
    if not test_id or not eh_id:
        for wf in client.list_workflows():
            if wf.get("name") == test_name:
                test_id = str(wf["id"])
            if wf.get("name") == eh_name:
                eh_id = str(wf["id"])
    if not test_id:
        raise SystemExit("Error Handler Test workflow not imported")

    # Central Error Handler must be active to receive errorWorkflow callbacks
    client.activate_workflow(eh_id)
    was_active = False
    try:
        detail = client.get_workflow(test_id)
        was_active = bool(detail.get("active"))
        if not was_active:
            client.activate_workflow(test_id)

        before = datetime.now(timezone.utc).isoformat()
        status_code, body = trigger_webhook(client.base, "phase1-error-handler-test", {"test": True})
        result = wait_for_new_execution(client, test_id, before, timeout_s=60)
        execution_id = str(result.get("id", "")) if result else ""

        # Error handler workflow should also have run
        eh_result = wait_for_new_execution(client, eh_id, before, timeout_s=30)

        return {
            "test": "error_handler",
            "workflow_id": test_id,
            "error_handler_id": eh_id,
            "webhook_status": status_code,
            "webhook_body_preview": body[:200],
            "test_execution_id": execution_id,
            "test_execution_status": result.get("status") if result else None,
            "error_handler_execution_id": str(eh_result.get("id", "")) if eh_result else None,
            "error_handler_execution_status": eh_result.get("status") if eh_result else None,
            "started_after": before,
            "note": "Verify workflow_failures row + Telegram alert in Supabase/dashboard",
        }
    finally:
        if not was_active:
            try:
                client.deactivate_workflow(test_id)
            except RuntimeError:
                pass


def test_laila_scenarios(client: N8nClient, name_to_id: dict[str, str]) -> list[dict]:
    scenario_name = "Arcadia - Phase1 Laila Scenario Test"
    scenario_id = name_to_id.get(scenario_name)
    if not scenario_id:
        for wf in client.list_workflows():
            if wf.get("name") == scenario_name:
                scenario_id = str(wf["id"])
                break
    if not scenario_id:
        raise SystemExit("Laila Scenario Test workflow not imported")

    test_phone = "971509999001"
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    scenarios = [
        (
            "new_customer",
            {
                "scenario": "new_customer",
                "phone": test_phone,
                "provider_message_id": f"wa_phase1_test_new_{ts}",
                "text": "hello new customer phase1 test",
                "channel": "whatsapp",
            },
        ),
        (
            "existing_customer",
            {
                "scenario": "existing_customer",
                "phone": test_phone,
                "provider_message_id": f"wa_phase1_test_exist_{ts}",
                "text": "second message same customer",
                "channel": "whatsapp",
            },
        ),
        (
            "duplicate_whatsapp",
            {
                "scenario": "duplicate_whatsapp",
                "phone": test_phone,
                "provider_message_id": f"wa_phase1_test_exist_{ts}",
                "text": "duplicate should stop",
                "channel": "whatsapp",
            },
        ),
        (
            "missing_provider_id",
            {
                "scenario": "missing_provider_id",
                "phone": test_phone,
                "text": "no provider id — skip dedupe path",
                "channel": "whatsapp",
            },
        ),
    ]

    was_active = bool(client.get_workflow(scenario_id).get("active"))
    if not was_active:
        client.activate_workflow(scenario_id)

    results: list[dict] = []
    try:
        for label, payload in scenarios:
            before = datetime.now(timezone.utc).isoformat()
            try:
                status_code, body = trigger_webhook(client.base, "phase1-laila-scenario-test", payload)
                ex = wait_for_new_execution(client, scenario_id, before, timeout_s=90)
                parsed_body = None
                try:
                    parsed_body = json.loads(body) if body.strip().startswith("{") else body[:300]
                except json.JSONDecodeError:
                    parsed_body = body[:300]
                proceed = isinstance(parsed_body, dict) and parsed_body.get("proceed")
                stop_reason = isinstance(parsed_body, dict) and parsed_body.get("stop_reason")
                ok = (
                    ex is not None
                    and ex.get("status") == "success"
                    and (
                        status_code in (200, 201)
                        or (label == "duplicate_whatsapp" and proceed is False and stop_reason == "duplicate_provider_message_id")
                        or (label != "duplicate_whatsapp" and proceed is True)
                    )
                )
                results.append(
                    {
                        "scenario": label,
                        "webhook_status": status_code,
                        "execution_id": str(ex.get("id", "")) if ex else None,
                        "execution_status": ex.get("status") if ex else None,
                        "response_preview": parsed_body,
                        "ok": ok,
                    }
                )
            except Exception as e:
                results.append({"scenario": label, "ok": False, "error": str(e)})
    finally:
        if not was_active:
            try:
                client.deactivate_workflow(scenario_id)
            except RuntimeError:
                pass

    for label in ("pricing_success", "manual_quote", "send_failure", "ai_node_failure"):
        results.append(
            {
                "scenario": label,
                "ok": None,
                "note": "Requires full Laila Working Copy activation — deferred until user approval",
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
