# Phase 2.0 + 2.1 — Implementation Report
**التاريخ:** 28 أغسطس 2026 ~20:31 UTC  
**الحالة:** ✅ **COMPLETE** — توقف قبل Phase 2.2 n8n  
**ملف قابل للنسخ:** `deliverables/arcadia-phase2-0-1-report-ar.md`

---

## ملخص

| Phase | Scope | Status |
|-------|-------|--------|
| **2.0** | Fix outbound `[object Object]` logging | ✅ deployed n8n |
| **2.1** | SQL schema + audited backfill + triggers | ✅ applied Supabase |
| **2.2** | Booking Agent n8n workflows | ⏸️ **NOT started** (per instruction) |

---

## Phase 2.0 — Outbound Logging Fix

### Problem
Evolution API returns `message: { conversation: "..." }` object — old code passed object to `message_text` → `[object Object]` in `lead_interactions`.

### Fix
`extractOutboundText()` in:
- `scripts/patch_laila_phase1.py` → `Phase1 Prepare Outbound`
- `n8n Workflows/Arcadia - Phase1 Outbound Log.json` → defense in depth

### Deployed to n8n
| Workflow | ID |
|----------|-----|
| Laila V4 Final Phase1 Final Candidate | `RSVg9pYlWWa5yege` |
| Arcadia - Phase1 Outbound Log | `QbQ3kJtWOnnq3b2A` |

**Live verification:** pending next production outbound message (no production webhook disruption for test).

---

## Phase 2.1 — Database Migration

### Migrations applied
1. `booking_agent_phase2_1` — schema, tables, functions, counters seed
2. `booking_agent_phase2_1b_sync_backfill` — trigger, RLS, audited backfill

### Files in repo
| File | Purpose |
|------|---------|
| `Database/supabase_schema_booking_agent_phase2.sql` | Full migration source |
| `Database/rollback_booking_agent_phase2.sql` | Rollback |

### New / extended objects

| Object | Notes |
|--------|-------|
| `arcadia_system_config` | `supplier_price_change_threshold_pct` (default 5, configurable JSON) · `telegram_booking_ops` (existing bot + nullable chat_id) |
| `booking_id_counters` + `generate_booking_id()` | Atomic DB-side IDs — **never MAX+1** |
| `bookings.*` new columns | `lifecycle_status`, `payment_status`, audit timestamps, `booking_source` — **nullable, no wrong defaults** |
| `booking_tasks` | `task_key` + `UNIQUE(booking_id, task_key)` |
| `booking_status_log` | All status/payment changes |
| `human_approval_queue.idempotency_key` | Unique pending index |
| `leads.stage` | **`approved`** added formally |
| Trigger `bookings_before_update_sync_trg` | Ops `status` ↔ lifecycle sync + payment guard + logging |

### Design corrections applied

| Requirement | Implementation |
|-------------|----------------|
| No incorrect defaults on legacy rows | Columns nullable; explicit backfill only |
| Reuse `notes` | No `operational_notes` column; `booking_tasks.notes` for task-level |
| defer `quote_offer_id` | Not added |
| `task_key` idempotency | `UNIQUE(booking_id, task_key)` + documented key rules in SQL |
| Safe `booking_id` | `generate_booking_id(destination)` via counter table |
| Payment trusted only | Trigger blocks unless `modified_by IN (admin,staff,system,ops_app)` or session flag |
| Ops app on `status` | Dual-write via trigger; legacy column unchanged for ops app |
| RLS new tables | ON + `REVOKE` anon/authenticated |
| Approval idempotency | Partial unique index on pending rows |
| Configurable threshold | `arcadia_system_config` not hardcoded |

---

## Backfill Verification (150 bookings)

| Check | Result |
|-------|--------|
| `lifecycle_status` populated | **150/150** ✅ |
| `payment_status` populated | **150/150** ✅ |
| `lifecycle_status` NULL | **0** ✅ |
| `booking_status_log` lifecycle rows | **150** (`changed_by=phase2_backfill`) |
| `booking_status_log` payment rows | **150** (`changed_by=phase2_backfill`) |
| `booking_source` | `legacy_ops` on all legacy rows |

### lifecycle_status distribution
| Status | Count |
|--------|-------|
| CONFIRMED | 136 |
| PENDING_SUPPLIER | 10 |
| IN_PROGRESS | 2 |
| CANCELLED | 2 |

### payment_status distribution
| Status | Count |
|--------|-------|
| unpaid | 115 |
| partial | 33 |
| paid | 2 |

---

## Runtime Verification Tests

| Test | Result |
|------|--------|
| `generate_booking_id('kazakhstan')` | `KA-2026-117` (counter was 116 → next new booking **KA-2026-118**) |
| Payment change with `modified_by=booking_agent` (no trust) | **BLOCKED** ✅ |
| Ops `status` → `in_hotel` with `modified_by=admin` | lifecycle → `IN_PROGRESS` + logged ✅ |
| Test row `RU-2026-001` | **reverted** after sync test |

---

## booking_tasks — Deterministic task_key Rules (for Phase 2.2)

Documented in migration SQL — generator must produce:

| Service | task_key pattern |
|---------|------------------|
| hotel | `hotel:{city_slug}:{segment_index}` |
| airport | `airport:{city_slug\|arrival}:transfer` |
| tour | `tour:{city_slug}:{tour_index}` |
| train | `train:{from_slug}-{to_slug}` |
| intercity | `intercity_transfer:{from_slug}-{to_slug}` |
| guide | `guide:{city_slug}:guide` |
| other | `other:{slug}:misc` |

---

## Quote Selection Rule (Phase 2.2 — not implemented yet)

**Explicit only — never phone-only:**
1. Required: `quote_ref` in trigger payload, OR
2. `lead_id` + `quotes.id` (bigint), OR
3. `lead_id` + latest `quotes.created_at` **only if** exactly one quote exists for that lead

---

## Stopped Here

**Phase 2.2 n8n Booking Agent workflows NOT built.**

Next after your approval:
- `Arcadia - Booking Agent` sub-workflows
- Webhook `booking-agent/start`
- Staff Telegram notify (chat_id from `arcadia_system_config`)

---

## Rollback

```bash
# n8n: revert Outbound Log + Final Candidate from git previous commit
# SQL: Database/rollback_booking_agent_phase2.sql (manual apply via Supabase)
```

---

*Arcadia Tourism · Phase 2.0 + 2.1 · 28 Aug 2026*
