# Phase 2.1c — Verification / Patch Report
**التاريخ:** 28 أغسطس 2026  
**الحالة:** ✅ **Applied + verified**

---

## 1. Booking-level idempotency

| Item | Status |
|------|--------|
| `bookings.booking_request_key` | ✅ `text NULL` |
| Partial unique index | ✅ `bookings_booking_request_key_uidx WHERE NOT NULL` |
| Phase 2.2 key format | `{lead_id}:{quote_ref}` |

**Migration:** `booking_agent_phase2_1c`  
**SQL:** `Database/supabase_schema_booking_agent_phase2_1c.sql`

---

## 2. task_key patterns (pre-generator)

Updated documented rules on `booking_tasks`:

| Service | Pattern |
|---------|---------|
| hotel | `hotel:{city_slug}:{segment_index}` |
| airport arrival | `airport:{city_slug}:arrival` |
| airport departure | `airport:{city_slug}:departure` |
| tour | `tour:{city_slug}:{tour_index}` |
| train | `train:{from_slug}-{to_slug}:{segment_index}` |
| intercity | `intercity_transfer:{from_slug}-{to_slug}:{segment_index}` |
| guide | `guide:{city_slug}:{segment_index}` |
| other | `other:{slug}:{index}` |

---

## 3. INSERT audit trigger

| Trigger | Event |
|---------|-------|
| `bookings_after_insert_audit_trg` | AFTER INSERT |

Logs initial `lifecycle_status` + `payment_status` to `booking_status_log` with `reason=initial_insert`.

**Verified on Phase 2.2 test booking `RU-2026-030`:**
- lifecycle_status: NULL → DRAFT (`changed_by=phase2_2_test`)
- payment_status: NULL → unpaid

---

## 4. Payment backfill anomaly audit (no value changes)

**8 rows** with `is_paid=true`:

| booking_id | total | paid_amount | derived | payment_status | Notes |
|------------|-------|-------------|---------|----------------|-------|
| PO-2026-003 | 5250 | 5250 | paid | paid | ✅ consistent |
| RU-2026-025 | 6300 | 6300 | paid | paid | ✅ consistent |
| KA-2026-056 | 4050 | 4000 | partial | partial | is_paid flag overstated |
| KA-2026-079 | 3850 | 300 | partial | partial | is_paid flag overstated |
| KA-2026-116 | 3560 | 0 | unpaid | unpaid | ⚠️ legacy inconsistency |
| PO-2026-001 | 2540 | 0 | unpaid | unpaid | ⚠️ legacy inconsistency |
| RU-2026-002 | 5050 | 0 | unpaid | unpaid | ⚠️ legacy inconsistency |
| RU-2026-006 | 5250 | 0 | unpaid | unpaid | ⚠️ legacy inconsistency |

**لماذا 6 لم تصبح paid:**  
`compute_payment_status()` يعتمد على `paid_amount` أولاً. أربعة صفوف `is_paid=true` لكن `paid_amount=0` → `unpaid`. اثنان `paid_amount > 0` لكن أقل من `total_amount` → `partial`.

**Flag:** `arcadia_system_config.payment_backfill_needs_review` — لا تغيير في القيم.

---

## 5. Booking ID 117

| Item | Value |
|------|-------|
| Consumed ID | `KA-2026-117` |
| Consumed by | Phase 2.1 migration verification (`generate_booking_id` test) |
| Next real KA ID | `KA-2026-118` |
| Action | Documented in `booking_id_sequence_gaps` — **counter not rewound** |

---

## 6. Phase 2.0 outbound verification

| Status | Detail |
|--------|--------|
| ⏸️ **Pending** | No production outbound since deploy ~20:30 UTC |
| Last outbound | 20:15 UTC — still `[object Object]` |
| Action | Did **not** generate test traffic |

---

*Phase 2.1c complete — Phase 2.2 started separately.*
