# Arcadia Internal UAT Re-Run Report — Defect-Fix Patch

**UAT tag:** `internal_uat_kz_almaty_20260828_rerun`  
**Tested:** 2026-08-28 UTC  
**Patch:** UAT-DEF-001, UAT-DEF-002  
**Overall result:** **PASS (12/12 acceptance tests)**  
**Customer canary:** Still **NOT approved** — Laila steps 1–4 require manual WhatsApp UAT (UAT-DEF-003)

---

## Fixes Applied

### UAT-DEF-001 — Telegram callback structured JSON
- All test-webhook callback paths now return explicit JSON via `respondJson()` with `simulated: true`.
- Malformed/unsupported callbacks return `{ ok: false, error: "invalid_callback" | "unknown_callback" }` — no silent HTTP 200 `{}`.
- Simulated webhook path skips live Telegram `sendMessage` (production Telegram callbacks unchanged).
- Markdown-safe wrapping for dynamic status/confirmation fields; plain-text fallback on Telegram parse errors.

### UAT-DEF-002 — Confirmation reference protection
- Confirmed task with existing `confirmation_ref` rejects a different ref with `confirmation_ref_conflict`.
- Same ref replay returns idempotent success.
- Authorized override requires `override_confirmation_ref: true` + `override_reason` + staff allowlist.
- DB trigger `booking_tasks_guard_confirmation_ref` blocks direct PATCH overwrites.
- RPC `override_task_confirmation_ref()` provides audited correction path with `booking_task_status_log` entry.

### UAT-DEF-003 — Laila audit (no code change)
- `phase1-laila-scenario-test` → **404** — workflow file `Arcadia - Phase1 Laila Scenario Test.json` **not in repo** (referenced only in `scripts/n8n_phase1_operational.py`).
- Production Laila in repo: `Arcadia - Laila Telegram V5 Phase1 Working.json` (Telegram channel, not WhatsApp harness).
- **Conclusion:** Steps 1–4 require **manual WhatsApp walkthrough** OR lead pre-seeding (used for booking UAT). No permanent unauthenticated test webhook deployed.

---

## Acceptance Tests (12/12 PASS)

| # | Test | Result |
|---|------|--------|
| 1 | `bk:tasks:` structured JSON | **PASS** |
| 1b | `bk:view:` structured JSON | **PASS** |
| 1c | `bk:task:*:open` structured JSON | **PASS** |
| 2 | Malformed callback explicit error | **PASS** |
| 3 | Confirm / same-ref replay | **PASS** |
| 4 | Same ref idempotent | **PASS** |
| 3b | Different ref rejected | **PASS** |
| 5 | Authorized override audited | **PASS** |
| 6 | Unauthorized correction blocked | **PASS** |
| 6b | Override without reason blocked | **PASS** |
| 7 | Booking `/book` idempotent | **PASS** |
| 8 | Draft facts consistent | **PASS** |

**Booking:** `KA-2026-118` · **Hotel task:** `c621cf83-845a-4b54-bd8c-cfda6a679f0a` · **Final confirmation ref:** `UAT-RERUN-HTL-FINAL`

---

## Safety Checks

| Check | Status |
|-------|--------|
| `booking_handoff_enabled` | **false** |
| `auto_send_enabled` | **false** |
| Reminder watcher | **disabled** |
| Supplier auto-sends | **0** |
| Payments / refunds | **0** |
| Workflow failures after patch | **0** (3 pre-patch failures at 22:20 UTC, before deploy) |

---

## Audit Evidence (override path)

`booking_task_status_log` recorded override:
- `UAT-SHOULD-NOT-OVERWRITE` → `UAT-RERUN-HTL-CORRECTED` (reason: UAT staff correction)
- `UAT-RERUN-HTL-CORRECTED` → `UAT-RERUN-HTL-FINAL` (reason: UAT staff correction)

`agent_actions` logged `confirmation_ref_conflict` for rejected overwrite attempts.

---

## Backlog (NOT fixed — per instructions)

- Mildom hotel missing phone/email in directory
- `days_count` naming (stores nights not calendar days)
- `/book` requires lead UUID

---

## Recommendation

**Booking ops UAT (steps 5–20) is now PASS** after defect-fix patch.

**Do not enable customer canary until:**
1. Manual WhatsApp UAT completes Laila steps 1–4 (quote presentation + acceptance flow), OR
2. A temporary isolated Laila UAT harness is deployed (inactive by default, authenticated) — workflow file currently absent from repo.

*Phase 2 closed · No Phase 3 · No customer canary enabled*
