# Laila Human-like UAT — Production Trace Report (Re-test FAIL)

**Date:** 2026-08-28  
**Phone tested:** `77051181845`  
**Human-like UAT:** NOT PASS (owner re-test required)  
**Booking regression:** PASS 12/12  

---

## Executive summary

Production execution data shows the previous patch **was deployed and active** (context forwarded to AI Agent), but failures persisted because:

1. **Lead CRM never stored trip data** — `leadContext` was only `المرحلة: new`; quotes lived in `chatHistory` only.
2. **LLM ignored hints** for AI identity, driver language, hotel-only tone, and price objection fallback.
3. **Price objection:** `list_hotels` ran successfully but **AI Agent still emitted the handoff template** with malformed markdown `wa.me` link.
4. **WhatsApp workflow `error` status** was from `Arcadia - Phase1 Outbound Log` missing Supabase credentials — **not** blocking sends.

**Fix applied (minimum, no new prompt layer):** deterministic routing in `Decision Engine` for known intents + CRM backfill from chat + direct `quote_options` RPC for price objections + `format_reply` URL sanitizer.

---

## Response-path tables (production executions)

### PASS — «لا خلاص شكرا»

| Step | Value |
|------|--------|
| Customer message | `لا خلاص شكرا` |
| Workflow | `Laila V4` (`RSVg9pYlWWa5yege`) → AI `Laila` (`TuoZdJ08EHQMk1RO`) |
| Branch | Parse+CRM → Phase1 pipeline → Decision Engine → AI webhook |
| WA exec / AI exec | `60485` (error*) / `60487` (success) |
| leadContext | `المرحلة: new` (empty trip fields) |
| chatHistory | 4765 chars forwarded ✓ |
| conversationHints | goodbye hint ✓ |
| Response source | AI Agent (honored hint) |
| Final response | `العفو، حياك الله 🌷` ✓ |

\*WA error = Outbound Log credentials only; message still sent.

---

### FAIL 1 — «انا خبرتكم من قبل»

| Step | Value |
|------|--------|
| Customer message | `انا خبرتكم من قبل` |
| WA exec / AI exec | `60437` / `60439` |
| Parse+CRM | hint fired ✓; **leadStateSummary = `المرحلة: new` only** |
| Supabase `leads` | `destination/travel_dates/pax` all **NULL** |
| chatHistory | Full quote thread (Almaty, 7 nights, 2 pax, $1306) ✓ |
| Response source | AI Agent (LLM) |
| Final response | Generic follow-up — **did not reuse quote from history** |
| Root cause | CRM empty + hint said “use leadContext only” while leadContext empty; LLM did not reliably parse chatHistory |

**Fix:** Extract trip from `chatHistory` → backfill `leads`; deterministic `returning_customer` reply when trip parsed.

---

### FAIL 2 — «هذا فنادق بس» / «احتاج فندق بس»

| Step | Value |
|------|--------|
| Messages | `هذا فنادق بس` (60443/60445), `احتاج فندق بس` (60467/60469) |
| Parse+CRM | Hint on first message only; **`فندق بس` regex missed** second phrasing |
| Policy source | AI system prompt golden rule #2: min package = hotel + airport transfer (not standalone hotel) |
| Response source | AI Agent (long template) |
| Root cause | No deterministic policy branch; LLM verbose despite hint |

**Fix:** Regex `فندق بس|احتاج فندق`; deterministic `HOTEL_ONLY_POLICY` from trusted prompt policy text.

---

### FAIL 3 — «سعركم غالي»

| Step | Value |
|------|--------|
| WA exec / AI exec | `60473` / `60475` |
| Parse+CRM | price objection hint ✓ |
| AI tools | `list_hotels` **success** (no error) |
| AI Agent output | Handoff template: `للأسف ما قدرت أكمل طلبك هنا...` |
| URL defect | `[https://wa.me/380936582617](https://wa.me/380936582617)` markdown |
| Root cause | LLM chose fallback **after successful tool call**; not a routing/HTTP error |

**Fix:** Bypass LLM for price objection → direct `quote_options` RPC (`p_mode=no_tours`); sanitize markdown links in `format_reply` + Decision Engine post-process.

---

### FAIL 4 — «السواق يتكلم عربي»

| Step | Value |
|------|--------|
| WA exec / AI exec | `60479` / `60481` |
| Parse+CRM | **No hint** (`السواق` not matched — regex had `السايق` only) |
| Trusted data | **None** for driver languages |
| Response source | AI Agent — **hallucinated** EN/RU drivers + Arabic guides |
| Root cause | No deterministic ops guard; prompt addendum ignored by LLM |

**Fix:** Deterministic `ops_unknown` + `needs_human=true`; no fabricated guide availability.

---

### FAIL 5 — «انتي موظفه ولا AI»

| Step | Value |
|------|--------|
| WA exec / AI exec | `60491` / `60493` |
| Parse+CRM | AI hint present ✓ |
| Response source | AI Agent |
| Final response | `أنا ليلى، مساعدة أركاديا...` — **evaded direct question** |
| Root cause | LLM ignored hint; no hard routing |

**Fix:** Deterministic truthful AI identity reply (short-circuit before AI).

---

## Patch v2 changes (this commit)

| File | Change |
|------|--------|
| `scripts/laila_parse_crm_logic.js` | Trip extraction from chatHistory; CRM backfill; intent flags; regex fixes |
| `scripts/laila_decision_engine_logic.js` | Deterministic branches + direct Pricing Engine RPC; URL sanitize |
| `scripts/laila_format_reply_logic.js` | Strip markdown wa.me duplication |
| `Arcadia - Laila V4...json` | Outbound Log `continueOnFail` (stop false error status) |

**Not changed:** Booking Agent, payment, supplier, Phase 3, AI system prompt (no new addendum).

---

## Owner manual re-test checklist

- [ ] `انا خبرتكم من قبل` → references stored trip/quote
- [ ] `هذا فنادق بس` → short policy line
- [ ] `سعركم غالي` → cheaper options from Pricing Engine, no handoff
- [ ] `السواق يتكلم عربي` → team confirmation, no invented languages
- [ ] `انتي موظفه ولا AI` → truthful AI answer
- [ ] `لا خلاص شكرا` → short goodbye (preserve)

**Do not declare Human-like UAT PASS until owner confirms.**
