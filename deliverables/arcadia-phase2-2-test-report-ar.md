# Phase 2.2 — Test Report
**التاريخ:** 28 أغسطس 2026  
**الحالة:** ✅ **E2E passed** — توقف قبل Phase 2.3

---

## Scope (what was built)

| Item | Status |
|------|--------|
| Webhook `booking-agent-test` only | ✅ |
| Deterministic rules (NO AI/LLM) | ✅ |
| `booking_request_key` idempotency | ✅ |
| DRAFT booking + task generation | ✅ |
| `booking_status_log` INSERT audit | ✅ |
| `agent_actions` logging | ✅ |
| Telegram test notification | ⏸️ skipped (`chat_id` null) |

**NOT in scope (as requested):** stage watcher, Admin /book, Laila wiring, supplier messages, approvals, payments, CONFIRMED.

---

## Workflow

| Field | Value |
|-------|-------|
| Name | `Arcadia - Booking Agent Test` |
| n8n ID | `srMKgn7dtqLLAWcJ` |
| Webhook | `POST https://n8n.arcadia-tour.cloud/webhook/booking-agent-test` |
| Payload | `{ lead_id, quote_ref, requested_by }` |

---

## Test 1 — Create DRAFT + tasks

**Input:**
```json
{
  "lead_id": "b6fada92-a0c4-45a9-a5f7-2e60897af3c8",
  "quote_ref": "ARC-367344",
  "requested_by": "phase2_2_test"
}
```

**Result (execution 59829):**

| Field | Value |
|-------|-------|
| booking_id | `RU-2026-030` |
| lifecycle_status | `DRAFT` |
| payment_status | `unpaid` |
| booking_request_key | `b6fada92-a0c4-45a9-a5f7-2e60897af3c8:ARC-367344` |
| tasks | **13** (deterministic from quote cities + tours_by_city) |

**Task keys generated:**
- `hotel:moscow:1`, `hotel:saint_petersburg:2`, `hotel:moscow:3`
- `airport:moscow:arrival`, `airport:moscow:departure`
- `intercity_transfer:moscow-saint_petersburg:1`, `intercity_transfer:saint_petersburg-moscow:1`
- `tour:moscow:1` … `tour:moscow:4`, `tour:saint_petersburg:1`, `tour:saint_petersburg:2`

---

## Test 2 — Duplicate webhook (idempotency)

**Same payload re-sent (execution 59830):**

| Check | Result |
|-------|--------|
| New booking created? | ❌ No — same `RU-2026-030` |
| Task count | 13 (unchanged) |
| Response | `idempotent: true` |
| agent_actions | Logged replay with `idempotent=true` |

---

## DB verification

| Table | Expected | Actual |
|-------|----------|--------|
| `bookings` (request key) | 1 row | ✅ 1 |
| `booking_tasks` | 13 | ✅ 13 |
| `booking_status_log` | 2 INSERT audit rows | ✅ lifecycle + payment |
| `agent_actions` | 2 (create + replay) | ✅ |

---

## Telegram

`arcadia_system_config.telegram_booking_ops.chat_id` is **null** → notification skipped with reason `chat_id_not_configured`. No test message sent (expected until ops chat configured).

---

## Next step

**Phase 2.3** — not started. Awaiting approval after review of this report.

**Re-run test:**
```bash
python3 scripts/n8n_booking_agent_test.py test
```

---

*Arcadia Tourism · Phase 2.2 Test Report · 28 Aug 2026*
