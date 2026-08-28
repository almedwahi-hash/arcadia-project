# Package Composition — Custom Tour Days Capability Report

**Date:** 2026-08-28  
**Human-like UAT:** NOT PASS — owner continues manual testing  
**Returning-customer fix:** PASS (preserved)

---

## Pricing Engine capability: **YES — custom tour_days supported**

Custom tour counts are **not** exposed via `quote_options` (always auto-calculates). They **are** supported via:

**RPC:** `quote_package(..., p_force_tour_days := N, p_hotel_name := '<hotel>')`

Verified on production DB (Almaty, Grand Mildom, 7 nights, 2 pax):

| p_force_tour_days | final_price_usd |
|-------------------|-----------------|
| 0 | 864 |
| 2 | 1041 |
| 4 | 1218 |
| 5 (default) | 1306 |
| 6 | 1395 |
| 7 | 1483 |

No LLM arithmetic. No workaround needed.

**Gap:** `quote_options` wrapper does not accept `p_force_tour_days` — Laila Decision Engine calls `quote_package` directly for modifications.

---

## Sales rule implemented

Tour count = **current quote composition**, not a fixed customer constraint.

| Customer intent | Behavior |
|-----------------|----------|
| Explain current package | Short factual reply from `quote_options` |
| Ask flexibility (“6 جولات او كم؟”) | Sales tone: current count + offer to adjust, **no repricing** |
| Explicit modify (“خليها 6 جولات”) | `quote_package` with `p_force_tour_days`, persist to `leads.notes` |
| Casual chat | No unnecessary repricing |

**Removed:** internal formulas, “Pricing Engine”, tier jargon, rigid “must be 5 tours”, template closings.

---

## Example responses

**Flexibility** (`يعني المفترض 6 جولات او كم؟`):
```
العرض الحالي فيه 5 أيام جولات، بس عادي نقدر نعدله على راحتك 👍 إذا تحب 6 جولات أضيف لك يوم جولة وأحسب لك السعر الجديد، وإذا تحب أقل نقدر نقللها برضه.
```

**Modify** (`خليها 6 جولات`):
```
تمام 👍 خليتها 6 أيام جولات. السعر بعد التعديل صار 1395 دولار لشخصين.
```

**Explain** (`ايش 5 جولات انا عندي كم يوم`):
```
الرحلة 8 أيام / 7 ليالي 👍 العرض الحالي فيه 5 أيام جولات — ونقدر نزيدها أو نقللها على راحتك.
```

---

## Persistence

After modification, `leads.notes` stores:
`city=Almaty;nights=7;tour_days=6;hotel=Grand Mildom Hotel;last_price=1395`

Subsequent messages merge notes into trip context.

---

## Regression

Booking Agent UAT: **PASS 12/12** (unchanged)

---

## Not enabled

No new customer automation, canary, or handoff flags. Conversation routing patch only.

**STOP** — owner manual WhatsApp re-test required.
