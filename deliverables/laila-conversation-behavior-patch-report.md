# Laila Conversation-Behavior Patch Report

**Date:** 2026-08-28  
**Branch:** `cursor/laila-conversation-patch-29b5`  
**Scope:** Laila WhatsApp + AI Agent conversation behavior only  
**Human-like WhatsApp UAT:** NOT declared PASS — owner manual re-test required  
**Booking Agent UAT regression:** PASS 12/12 (unchanged)

---

## What changed

| Workflow | n8n ID | Nodes / logic |
|----------|--------|----------------|
| Laila V4 - Final Phase1 Final Candidate | `RSVg9pYlWWa5yege` | `Parse + CRM`, `Decision Engine` |
| Laila (AI Agent) | `TuoZdJ08EHQMk1RO` | `Normalize`, system prompt addendum |

**Repo sources**

- `scripts/laila_parse_crm_logic.js`
- `scripts/laila_decision_engine_logic.js`
- `scripts/laila_normalize_logic.js`
- `scripts/laila_conversation_prompt_addendum.txt`
- `scripts/embed_laila_conversation_patch.py`
- `scripts/n8n_laila_conversation_patch.py`
- `n8n Workflows/Arcadia - Laila V4 Final Phase1 Production.json`
- `n8n Workflows/Arcadia - Laila AI Agent.json`

**Not changed:** Booking Agent, Pricing Engine RPC/tools, payments, supplier automation, Phase 3, safety flags.

---

## Root cause — context not reused (“انا خبرتكم قبل”)

1. **`Decision Engine`** posted only `{ chatInput, sessionId }` to the AI webhook. `lead`, `chatHistory`, and `context` from `Parse + CRM` were dropped before the agent ran.
2. **`Parse + CRM` context** included only `name` + `destination`; travel dates, pax, stage, notes were not summarized for the model.
3. **Session reset on any greeting** could wipe lead fields when the customer said “مرحبا/هلا” even with stored trip data.

---

## Patch behavior

### Parse + CRM

- Builds full `leadStateSummary` (destination, dates, pax, stage, notes, …).
- Detects returning-customer phrases, hotel-only corrections, price objections, goodbye, AI questions → `conversationHints`.
- Resets lead data **only** on explicit new-trip intent (`رحلة جديدة`, `بداية جديدة`, …) — not on simple greetings or “خبرتكم قبل”.
- Uses `$env.SUPABASE_KEY` / `$env.SUPABASE_SERVICE_ROLE_KEY` (no hardcoded service role in repo).

### Decision Engine

- Forwards `leadContext`, `chatHistory`, `context`, `managerInstructions`, `conversationHints` to the AI webhook with `chatInput`.

### Normalize (AI Agent)

- Prepends stored lead + recent chat + hints to `chatInput` before the LangChain agent runs.

### Prompt addendum

- Short natural WhatsApp tone, one step at a time, no template closings.
- Price objection → brief ack + pricing tools (no invented discounts).
- Operational facts unknown → “أتأكد لك من الفريق وأرجع لك.”
- Honest if asked about AI; no false human claim.

---

## Driver-language question (UAT example)

**Before patch:** Answer would be **LLM-generated** — no trusted Arcadia field or tool for driver languages in prompt or Supabase lead data.

**After patch:** Prompt addendum instructs: do not invent; respond “أتأكد لك من الفريق وأرجع لك.” Staff follow-up still required until a trusted data source exists.

---

## Regression

```
python3 scripts/run_internal_uat_rerun.py
→ acceptance_passed: 12/12, overall: PASS
```

---

## Deploy

```bash
python3 scripts/embed_laila_conversation_patch.py
python3 scripts/n8n_laila_conversation_patch.py deploy
```

Deployed to production n8n on 2026-08-28.

---

## Manual follow-up (owner)

Re-run Human-like WhatsApp UAT scenarios:

- “انا خبرتكم قبل” with existing lead data
- “هذا فنادق بس” / “احتاج بس فندق”
- “سعركم غالي”
- Driver language / operational fact question
- “لا خلاص شكرا”
- Direct “هل أنت AI?” question

**Do not mark Human-like UAT PASS until owner confirms on live WhatsApp.**
