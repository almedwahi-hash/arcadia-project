# Arcadia Internal UAT Dry-Run Report — Kazakhstan Almaty Booking

**UAT tag:** `internal_uat_kz_almaty_20260828`  
**Tested:** 2026-08-28 UTC  
**Overall result:** **FAIL — do not proceed to customer canary**

Phase 2 remains closed. This was an operational dry-run only — no new features, no supplier sends, no payments.

---

## Scenario

| Field | Value |
|-------|-------|
| Destination | Almaty, Kazakhstan |
| Guests | 2 adults |
| Duration | 8 days / 7 nights |
| Hotel | Mildom Residence Hotel (eco tier from quote packages) |
| Tours | 5 (Almaty) |
| Quote | `ARC-459161` ($1,275) |
| Channel | WhatsApp/Laila (acceptance simulated via `lead.stage=approved`) |

---

## IDs Created (test data — preserved for audit)

| Entity | ID |
|--------|-----|
| Lead | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| Phone | `uat_kz_almaty_20260828` |
| Quote | `ARC-459161` |
| Booking | **`KA-2026-118`** |
| booking_request_key | `f47ac10b-58cc-4372-a567-0e02b2c3d479:ARC-459161` |
| Hotel task | `c621cf83-845a-4b54-bd8c-cfda6a679f0a` (`hotel:almaty:1`) |
| Hotel supplier draft | `f306841c-3ace-4f53-923b-df6170fc4bec` |

Lead notes: `UAT_TAG:internal_uat_kz_almaty_20260828 | Almaty 2pax 7nights | DO NOT CONTACT`

---

## Step-by-Step Results

| # | Step | Result | Notes |
|---|------|--------|-------|
| 1 | Customer starts conversation | **FAIL** | `phase1-laila-scenario-test` webhook 404 — not registered |
| 2 | Laila collects trip info | **NOT TESTED** | Lead pre-seeded; live Laila not available |
| 3 | Pricing Engine quote | **PASS** | `ARC-459161` in DB; deterministic total $1,275 |
| 4 | Quote presented to customer | **NOT TESTED** | WhatsApp UI not exercised |
| 5 | Customer acceptance | **PASS** | `lead.stage=approved`, `approved_quote_ref=ARC-459161` |
| 6 | Staff identifies lead + quote | **PASS** | IDs known from lead record / notify |
| 7 | `/book <lead_id> <quote_ref>` | **PASS** | Safe staff test webhook |
| 8 | ONE DRAFT booking | **PASS** | Single `KA-2026-118`; duplicate `/book` idempotent |
| 9 | Lead/quote linkage | **PASS** | All foreign keys consistent |
| 10 | Dates, pax, hotel, services | **PASS** | See consistency table below |
| 11 | Deterministic tasks | **PASS** | 8 tasks, no duplicates |
| 12 | Telegram Booking Ops notify | **PASS** | Message sent to chat `493831958` |
| 12b | Tasks list callback | **FAIL** | HTTP 200 **empty body** `{}` |
| 13 | Open hotel task | **FAIL** | HTTP 200 **empty body** `{}` |
| 14 | Generate supplier draft | **PASS** | Draft generated; `auto_send=false` |
| 15 | Draft facts vs quote | **PASS** | All core fields match |
| 16 | No actual supplier send | **PASS** | No outbound supplier messages |
| 17 | Mark sent manually | **PASS** | `sent_manually` + task → `requested` |
| 18 | Supplier confirmed (test ref) | **PASS** | `UAT-KZ-HTL-20260828` recorded |
| 19 | Lifecycle recompute | **PASS** | `DRAFT` → `PARTIALLY_CONFIRMED` |
| 20 | Continue workflow | **PASS** | Airport arrival → `requested`; airport drafts generated |

---

## Negative Tests

| Test | Result |
|------|--------|
| Duplicate `/book` | **PASS** — idempotent, same booking |
| Wrong `quote_ref` | **PASS** — blocked (400) |
| Quote belongs to another lead | **PASS** — blocked (403) |
| Unauthorized Telegram user | **PASS** — 403 unauthorized |
| Malformed callback (invalid draft id) | **PASS** — 403 draft_not_found |
| Malformed callback (`bk:invalid`) | **FAIL** — HTTP 200 empty body |
| Duplicate supplier conf (same idempotency_key) | **PASS** — idempotent |
| Duplicate supplier conf (different key) | **FAIL** — overwrote `confirmation_ref` |
| Missing hotel supplier | **PASS** — `needs_information` + `hotel_name` |
| Missing airport supplier | **PASS** — draft still generated (by design) |
| Duplicate customer message | **NOT TESTED** — requires live Laila |

---

## Data Consistency: Customer → Lead → Quote → Booking → Tasks → Draft

### Quote `ARC-459161` → Booking `KA-2026-118`

| Field | Quote | Booking | Match |
|-------|-------|---------|-------|
| Destination | KZ | kazakhstan | Normalized ✓ |
| City | Almaty | ["Almaty"] | ✓ |
| Check-in | 2026-06-05 | 2026-06-05 | ✓ |
| Check-out | 2026-06-12 | 2026-06-12 | ✓ |
| Adults / pax | 2 | guest_count 2 | ✓ |
| Nights | 7 | days_count 7 | ✓ (field = nights) |
| Hotel (eco) | Mildom Residence Hotel | city_hotels.Almaty | ✓ |
| Tours | 5 | number_of_tours 5 | ✓ |
| Total USD | 1275 | 1275 | ✓ |
| Services | hotel, airport, tours | same | ✓ |

**No lost information** in booking creation. No wrong dates, pax, hotel, or missing tours.

### Booking → Tasks (8 total)

| task_key | type | required | supplier | status (end of UAT) |
|----------|------|----------|----------|---------------------|
| hotel:almaty:1 | hotel | yes | Mildom Residence Hotel | confirmed |
| airport:almaty:arrival | airport_transfer | yes | — | requested |
| airport:almaty:departure | airport_transfer | yes | — | pending |
| tour:almaty:1–5 | tour | no | — | pending |

No duplicate tasks. No intercity transfers (correct for single-city quote).

### Hotel supplier draft vs source

| Fact | Quote/Booking | Draft | Match |
|------|---------------|-------|-------|
| Booking ref | KA-2026-118 | KA-2026-118 | ✓ |
| Hotel | Mildom Residence Hotel | Mildom Residence Hotel | ✓ |
| City | Almaty | Almaty | ✓ |
| Check-in/out | 2026-06-05 / 2026-06-12 | same | ✓ |
| Guests | 2 | 2 pax | ✓ |
| Lead guest | UAT KZ Almaty Guest | same | ✓ |
| Quote ref | ARC-459161 | ARC-459161 | ✓ |
| Arabic draft | N/A (hotel) | English only | N/A |

Draft explicitly marked `(DRAFT — staff review; NOT sent automatically)`.

---

## Safety Checks

| Check | Status |
|-------|--------|
| `booking_handoff_enabled` | **false** |
| `auto_send_enabled` | **false** |
| Reminder watcher | **disabled** |
| Supplier messages sent | **0** |
| Payments / refunds | **0** |
| Real suppliers contacted | **No** |
| Production customers affected | **No** |
| UAT records tagged | **Yes** |
| Audit history deleted | **No** |

---

## Defects Found (STOP — report only, no auto-fix)

### UAT-DEF-001 — BLOCKER: Empty webhook responses for Telegram UX callbacks

**Affected:** `bk:tasks:`, `bk:view:`, `bk:task:*:open`, some malformed callbacks  
**Symptom:** HTTP 200 with empty body `{}`  
**Likely cause:** `Respond to Webhook` node requires `$json.simulated === true`, but several return paths omit `simulated`. Telegram messages may still send, but callers get no JSON.  
**Impact:** Cannot verify Telegram UX in automated UAT; breaks test harness observability.

### UAT-DEF-002 — HIGH: Duplicate supplier confirmation overwrites ref

**Evidence:** Two `booking_supplier_responses` rows; task `confirmation_ref` ended as `UAT-KZ-HTL-DUP` after second confirmed callback with a new idempotency key.  
**Impact:** Staff can accidentally overwrite a valid supplier confirmation reference.

### UAT-DEF-003 — MEDIUM: Laila scenario harness not deployed

**Evidence:** `POST /webhook/phase1-laila-scenario-test` → 404  
**Impact:** Full WhatsApp customer journey cannot be automated for UAT.

---

## Operational Observations (non-blocking)

1. **Mildom Residence Hotel** has no phone/email in the hotels directory — draft shows "Direct Contract" only.
2. **`days_count`** on bookings stores nights (7), not calendar days (8) — may confuse staff in summaries.
3. **`/book` requires lead UUID** — staff must copy from notify message or CRM; no phone-based shortcut in Telegram command.

---

## Recommendation

**Do not expose Booking Agent to real customers until:**

1. **UAT-DEF-001** is fixed or accepted with a documented workaround for Telegram callback testing.
2. **UAT-DEF-002** is reviewed — confirmed tasks should not accept overwriting confirmation refs without explicit override.
3. **UAT-DEF-003** — deploy Laila UAT harness OR complete manual WhatsApp walkthrough for steps 1–4.

The core booking pipeline (`/book` → tasks → supplier draft → mark sent → supplier response → lifecycle) **works correctly** when exercised via webhooks that return structured JSON. The Telegram callback response path and duplicate-confirmation guard need attention before canary.

---

*Arcadia Tourism · Internal UAT · Phase 2 closed · No Phase 3*
