# Laila Sequential Package Modification — Production Trace & Fix Report

**Date:** 2026-08-28  
**Phone tested:** `77051181845`  
**Human-like UAT:** NOT PASS — owner manual re-test required  
**Booking regression:** PASS 12/12  

---

## Executive summary

Live WhatsApp UAT failed on sequential tour-day modifications after a successful 6-tour repricing. Production execution traces show **one root cause for the modify failure** and **separate root causes for follow-up failures**:

| # | Message | Result | Root cause |
|---|---------|--------|------------|
| 1 | `طيب لو اخليها 6 جولات كم يصير؟` | PASS | Routed `package_tour_modify` → `quote_package` |
| 2 | `غالي خلها 3 جولات` | **FAIL** | `price_objection` checked **before** `package_tour_modify`; `غالي` won despite explicit `خلها 3 جولات` |
| 3 | `هذا السعر مع 3 جولات؟` | **FAIL** | No `package_price_confirm` intent → AI agent → circular wa.me handoff |
| 4 | `طيب رجعها 5 جولات` | **FAIL** | `رجعها` not in modify regex → `general` → AI handoff |
| 5 | `الفندق نفس الذي قبل` | **FAIL** | No `package_same_hotel` intent → AI empty → `FALLBACK_HANDOFF` wa.me |

**State at failure:** notes held `city=Almaty;nights=7;tour_days=6;hotel=Grand Mildom Hotel;last_price=1395` — hotel was known; modify path was never invoked for messages 2–4.

---

## Production execution trace (before fix)

### PASS — exec 60598 — `طيب لو اخليها 6 جولات كم يصير؟`

| Field | Value |
|-------|-------|
| intent | `package_tour_modify` |
| requestedTourDays | 6 |
| routedBy | `deterministic:package_tour_modify` |
| trip | Almaty, 7 nights, 2 pax, Grand Mildom, tour_days=5 |
| response | `تمام 👍 خليتها 6 أيام جولات. السعر بعد التعديل صار 1395 دولار لـشخصين.` |
| notes after | `tour_days=6;hotel=Grand Mildom Hotel;last_price=1395` |

### FAIL — exec 60602 — `غالي خلها 3 جولات`

| Field | Value |
|-------|-------|
| intent | **`price_objection`** (wrong) |
| requestedTourDays | 3 (parsed but ignored) |
| routedBy | `deterministic:pricing_engine` |
| trip | Grand Mildom, tour_days=6, last_price=1395 |
| response | Cheaper hotel options list (864 / 1324) — **changed offer context** |
| root cause | Intent order: `priceObjectionRx` line 296 before `package_tour_modify` line 298 |

### FAIL — exec 60606 — `هذا السعر مع 3 جولات؟`

| Field | Value |
|-------|-------|
| intent | `general` |
| requestedTourDays | 3 |
| routedBy | `ai_agent` |
| notes | Still `tour_days=6` (modify never ran) |
| response | `للأسف… تواصل مباشرة… wa.me/380936582617` |
| root cause | No price-confirmation intent; AI handoff template |

### FAIL — exec 60611 — `طيب رجعها 5 جولات`

| Field | Value |
|-------|-------|
| intent | `general` |
| requestedTourDays | 5 |
| routedBy | `ai_agent` |
| response | AI handoff with wa.me |
| root cause | `رجعها` missing from modify-verb regex |

### FAIL — exec 60616 — `الفندق نفس الذي قبل`

| Field | Value |
|-------|-------|
| intent | `general` |
| trip | Grand Mildom present in context |
| routedBy | `ai_agent` → empty → `FALLBACK_HANDOFF` |
| response | Circular wa.me link |
| root cause | No same-hotel intent; fallback sent customer back to WhatsApp |

---

## Fixes applied

### 1. Intent precedence (Parse + CRM)

**Explicit package modification now beats price objection:**

```
package_tour_modify  →  package_price_confirm  →  package_same_hotel  →  price_objection
```

- `detectTourModify()` — adds `رجع|رجعها|ارجع|اخلي|لو اخلي`; contextual `طيب 4؟` after tour discussion (Arabic `؟` supported)
- `package_price_confirm` — `هذا السعر مع N جولات؟`
- `package_same_hotel` — `الفندق نفس الذي قبل`

### 2. Current quote state preserved (Decision Engine)

- `fetchQuotePackage`: when `trip.hotel` is set, **omit** `p_hotel_tier: 'cheapest'` — only pass `p_hotel_name`
- Modify / confirm / restore all call `quote_package` with existing hotel + dates + pax
- `persistPackagePrefs` updates `leads.notes` after every successful repricing

### 3. Circular handoff removed

- Replaced `FALLBACK_HANDOFF` wa.me with: `لحظة أتأكد لك من السعر بعد التعديل 👍`
- `sanitizeReply` + `format_reply` strip wa.me / «تواصل مباشرة» / template closings
- Package-context AI failures → pricing retry + `needs_human=true` (no fabricated price)

### 4. Expected routing after fix

| Message | Intent | Action |
|---------|--------|--------|
| `غالي خلها 3 جولات` | `package_tour_modify` | Same Grand Mildom, `force_tour_days=3`, reprice |
| `هذا السعر مع 3 جولات؟` | `package_price_confirm` | Confirm from stored state (or reprice if mismatch) |
| `طيب رجعها 5 جولات` | `package_tour_modify` | Same package, `force_tour_days=5`, reprice |
| `الفندق نفس الذي قبل` | `package_same_hotel` | Confirm Grand Mildom + current tour_days/price |
| `طيب 4؟` (after tour chat) | `package_tour_modify` | Contextual 4 tour days |
| `غالي` alone | `price_objection` | Cheaper alternatives (unchanged) |

---

## Regression

Booking Agent UAT: **PASS 12/12** (unchanged)

---

## Not enabled

No canary, no new customer automation, no Booking Agent / payment / supplier changes.

**STOP** — owner manual WhatsApp re-test required for the 5-message sequence above.
