# Arcadia Phase 2.5 — Real Booking Handoff Test Report

**Tested at:** 2026-08-28T21:30:00Z  
**Result:** 9/9 passed ✅  
**STOP:** Phase 2.5 canary complete — no Orchestrator, no supplier auto-booking, no payment automation

---

## Policy enforced

| Rule | Status |
|------|--------|
| Booking Agent creates DRAFT + tasks only | ✅ |
| NO payment / refund / charge automation | ✅ |
| Handoff requires `leads.stage=approved` + exact `approved_quote_ref` | ✅ |
| Never guess customer-approved quote | ✅ |
| Idempotency `booking_request_key = lead_id:quote_ref` | ✅ |
| Staff `/book <lead_id> <quote_ref>` uses same entry path | ✅ |
| Stage watcher cron deployed but **disabled** (`booking_handoff_enabled=false`) | ✅ |
| Phase 2.4A tables remain — not connected to auto execution | ✅ |

---

## Desired flow (implemented)

```
Sales/Laila → quote → staff sets approved + approved_quote_ref
       → Booking Agent Start → DRAFT booking → deterministic tasks
       → Telegram Booking Ops → staff handles supplier reservations manually
```

**No Laila prompt changes.** Ambiguous customer messages do not trigger bookings.

---

## n8n workflows (production)

| Workflow | ID | Webhook / Trigger |
|----------|-----|-------------------|
| Arcadia - Booking Agent Start | `e4oBtEjQsHh3z7at` | `POST /webhook/booking-agent/start` |
| Arcadia - Booking Stage Watcher | `K0tAZa70qaI0HEyK` | Cron 10min (feature-flagged OFF) |
| Arcadia - Booking Staff Commands | `Dk3eENZICWG0E4Li` | Telegram `/book` + test webhook |
| Arcadia - Booking Staff Notify | `xHcju7YOoiUdLH0c` | `POST /webhook/booking-staff-notify` |

---

## Test matrix (canary)

| Case | Result |
|------|--------|
| Approved lead + exact quote → one booking | ✅ `RU-2026-030` (idempotent) |
| Duplicate trigger → no duplicate booking/tasks | ✅ idempotent replay |
| Wrong `quote_ref` → blocked | ✅ `quote_not_found` |
| Quote owned by another lead → blocked | ✅ `quote_belongs_to_another_lead` |
| Non-approved lead → blocked | ✅ `lead_not_approved` |
| Fresh approved lead → DRAFT + tasks + Telegram | ✅ `RU-2026-032`, 16 tasks, Telegram msg_id=39 |
| Staff `/book` override → same entry path | ✅ staff_override idempotent to `RU-2026-030` |
| No payment ledger writes from handoff | ✅ |
| No unexpected `workflow_failures` | ✅ |

---

## Canary fixtures

- **Idempotency:** lead `b6fada92-a0c4-45a9-a5f7-2e60897af3c8` + quote `ARC-367344` → booking `RU-2026-030`
- **Fresh create:** lead `cb874bb1-d10c-4f0f-82c1-166ccbb3c75c` + quote `ARC-884991` → booking `RU-2026-032`

---

## DB changes (Phase 2.5)

- `leads.approved_quote_ref`, `approved_at`, `approved_by`, `booking_handoff_at`
- `lead_quote_links` — explicit quote↔lead mapping (one quote → one lead)
- Config: `booking_handoff_enabled` (OFF), `booking_agent_start_webhook`, `booking_agent_ci_probe` (CI only)

Migration: `Database/supabase_schema_booking_agent_phase2_5.sql`

---

## Next step (not started)

After team review: enable `booking_handoff_enabled` for canary lead IDs only, then decide how Booking Agent can help with supplier correspondence **without payment authority**.

*Arcadia Tourism · Phase 2.5 · 28 Aug 2026*
