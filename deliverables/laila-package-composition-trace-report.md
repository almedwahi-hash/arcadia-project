# Package Composition UAT — Trace & Fix Report

**Date:** 2026-08-28  
**Quote traced:** Grand Mildom Basic — **1306 USD** (Almaty, 2 adults)  
**Human-like UAT:** NOT PASS — owner continues manual testing  
**Returning-customer fix:** PASS (preserved)

---

## Authoritative source — 1306 USD quote

**RPC:** `quote_options('Almaty', '2026-09-15', '2026-09-22', 2, 0, null, 'full')`

| Field | Value | Source |
|-------|-------|--------|
| nights | 7 | `quote_options.nights` |
| trip_days (calendar) | 8 | `nights + 1` (`quote_package`) |
| tour_days | 5 | `options[Basic].tour_days` |
| free_days | 1 | `quote_package`: `total_days >= 8 → 1` |
| price_usd | 1306 | `options[Basic].price_usd` |
| hotel | Grand Mildom Hotel | quote_options |
| arrival / departure labels | **Not stored in API JSON** | — |

**Tour allocation formula** (from `public.quote_package` — Pricing Engine):

```
total_days  = nights + 1
free_days   = (total_days >= 14 ? 2 : total_days >= 8 ? 1 : 0)
tour_days   = max(nights - 1 - free_days, 0)
```

For 7 nights: `8 total days`, `free_days = 1`, `tour_days = 7 - 1 - 1 = 5`.

**Why not 6 tours:** 8 calendar days does not imply 6 tours. Tour count comes from the pricing formula above, not `days - 2`.

**Not stored today:** per-day schedule, explicit arrival/departure flags, named tour itinerary.

---

## Production execution trace (FAIL messages)

| Message | WA exec | routedBy | Source | Problem |
|---------|---------|----------|--------|---------|
| `تمام هذا البكج كيف` | 60521 | ai_agent | LLM | Full quote re-sent instead of composition explain |
| `ايش 5 جولات انا عندي كم يوم` | 60526 | ai_agent | LLM | Vague LLM guess + template closing |
| `تمام انا عندي 7 ليالي` | 60531 | ai_agent | LLM | Confirmed nights only + template closing |
| `ايه يعني المفترض 6 جولات او كم` | 60536 | ai_agent | LLM | Stated 5 tours but no derivation; wrong tier (Premium) |

**PASS preserved:** `انا خبرتكم من قبل` → `60517` → `deterministic:returning_customer`

---

## Fix applied

1. **`package_composition` intent** in Parse+CRM (tour/day/package questions when trip context exists)
2. **Decision Engine** calls `quote_options` (`full` mode), picks tier matching `last_price` (1306 → Basic)
3. **Deterministic reply** from Pricing Engine fields + `quote_package` free-day formula
4. **No new prompt layer** — bypasses LLM for this intent
5. **sanitizeReply** strips template closings from any path

---

## Example deterministic response (1306 / 7 nights)

```
الرحلة 8 أيام / 7 ليالي 👍
العرض (Basic) محسوب على 5 أيام جولات — التسعير يخصّص 1 يوم راحة.
حسب محرك التسعير: 7 ليالي − يوم الوصول − 1 راحة = 5 جولات (مو 6).
```

(`يوم الوصول` reflects the `-1` in `quote_package`; departure day is not separately labeled in API data.)
