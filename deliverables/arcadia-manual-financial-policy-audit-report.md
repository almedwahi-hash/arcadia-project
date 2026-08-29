# Arcadia Booking Agent — Manual Financial Operations Policy Audit

**Date:** 2026-08-29  
**Scope:** Phase 2.4A financial stack alignment (minimum changes)  
**Laila:** NOT modified (Human-like UAT PASS baseline preserved)  
**Phase 3 / supplier auto-send / customer canary:** NOT enabled  

---

## 1. Current Phase 2.4A financial architecture

Phase 2.4A is already **bookkeeping / gating only** — no payment gateway, no banking API, no supplier payout execution.

```
Staff performs payment manually (outside Arcadia)
        ↓
Authorized staff records via Telegram/webhook
        ↓
n8n → record_booking_payment() RPC
        ↓
booking_payments ledger (append-only)
        ↓
sync_booking_paid_amount() → bookings.paid_amount
        ↓
booking_payment_policy_satisfied() + approval checks
        ↓
recompute_booking_lifecycle() → CONFIRMED (status only)
```

### Database (`Database/supabase_schema_booking_agent_phase2_4a.sql`)

| Component | Purpose |
|-----------|---------|
| `bookings.payment_requirement` | Gate policy: `full` / `deposit` / `pay_at_destination` / `manual` / NULL (legacy) |
| `bookings.required_payment_amount` | Deposit minimum USD |
| `bookings.manual_payment_approved_*` | Manual policy staff approval timestamp |
| `booking_payments` | Append-only customer payment ledger (`amount > 0`, idempotent key) |
| `record_booking_payment()` | Idempotent ledger insert + audit log + lifecycle recompute |
| `sync_booking_paid_amount()` | Sum ledger → `paid_amount` (trusted path) |
| `booking_payment_policy_satisfied()` | CONFIRMED gate — never moves money |
| `maybe_create_supplier_price_change_approval()` | Flags supplier cost variance |
| `resolve_booking_approval()` | Staff approve/reject variance, skip, manual payment gate |
| `recompute_booking_lifecycle()` | CONFIRMED when tasks + payment policy + zero pending approvals |

### n8n workflows

| Workflow | Entry | Behavior |
|----------|-------|----------|
| `Arcadia - Booking Payment Record` | `POST /booking-payment-record` | Staff allowlist → `record_booking_payment` |
| `Arcadia - Booking Approval Handler` | `POST /booking-approval-callback-test` | Staff allowlist → `resolve_booking_approval` |
| `Arcadia - Booking Task Update` | Telegram + test webhook | Supplier cost variance, task confirm, skip approvals |
| `Arcadia - Booking Agent Start` | Secret-protected webhook | DRAFT + tasks only — **explicitly NO payments** |

### Supplier payments

**No `supplier_payments` table.** Supplier cost tracked on `booking_tasks.supplier_cost_usd` with `human_approval_queue` for variance. **No automated supplier payout.**

### `booking_financial_commit`

Placeholder gate in `recompute_booking_lifecycle()` — blocks CONFIRMED if pending, but **no workflow creates or resolves this approval type** today.

---

## 2. KEEP / MODIFY / DISABLE / REMOVE

| Component | Classification | Rationale |
|-----------|----------------|-----------|
| `booking_payments` ledger | **KEEP** | Append-only manual record — core bookkeeping |
| `record_booking_payment()` | **KEEP** | Idempotent staff recording; rejects negative amounts |
| `sync_booking_paid_amount()` | **KEEP** | Derived state from ledger |
| `payment_requirement` + gate functions | **KEEP** | Status gating only — no money movement |
| `recompute_booking_lifecycle()` CONFIRMED gate | **KEEP** | Policy + approval checks |
| `supplier_price_change` approvals | **KEEP** | Staff decision on cost variance — no auto-pay |
| `manual_override` (skip / manual payment) | **KEEP** | Staff approval metadata |
| `bookings_before_update_sync` payment guard | **KEEP** | Blocks untrusted `paid_amount` edits |
| Booking Payment Record workflow | **MODIFY** | Added webhook secret auth + manual-only policy comments |
| Booking Approval Handler workflow | **MODIFY** | Added webhook secret auth on test/simulate path |
| `booking_financial_commit` approval type | **DISABLE** (creation) | Gate exists; do not create until defined — no money effect anyway |
| Payment gateways / Stripe / refunds | **REMOVE** (never existed) | Confirmed absent from active booking workflows |
| Laila conversation patch | **KEEP** (untouched) | Owner baseline — not modified |
| AI payment inference from WhatsApp | **DISABLE** (by design) | No code path records payment from Laila |

---

## 3. Safety risks discovered

| Risk | Severity | Status |
|------|----------|--------|
| Financial webhooks relied on spoofable `telegram_user_id` + allowlist only | **High** | **Mitigated:** require `BOOKING_AGENT_*_SECRET` when env configured |
| RPC trusts `p_recorded_by` string (no DB caller identity) | Medium | Documented — caller auth at n8n layer |
| Legacy `payment_requirement=NULL` auto-passes gate | Medium | **KEEP** — intentional for legacy bookings; staff sets policy on new bookings |
| `booking_financial_commit` stub could block CONFIRMED if row inserted manually | Low | **DISABLE** creation until defined |
| Service role key compromise bypasses RLS | Medium | Standard ops hygiene — not in scope |
| No supplier payment ledger table | Low | **Reported** — recommended minimal extension below |

**Confirmed absent:** Stripe, PayPal, auto-charge, refund RPC, banking APIs in 10 booking workflows scanned.

---

## 4. Exact minimal changes made

1. **`scripts/booking_payment_record_logic.js`** — manual-only policy header; webhook secret auth before allowlist
2. **`scripts/booking_approval_handler_logic.js`** — same auth on simulate/test webhook path
3. **`Database/supabase_schema_booking_agent_manual_financial_policy.sql`** — `booking_financial_policy` config + SQL comments (applied to production DB)
4. **`scripts/embed_booking_financial_logic.py`** — embed JS into workflow JSON
5. **`scripts/n8n_booking_phase24a_test.py`** — pass `auth_secret` when env secret configured
6. **`scripts/n8n_booking_manual_financial_policy_test.py`** — policy verification test suite
7. **Workflow JSON** — embedded updated logic (Payment Record + Approval Handler)

**NOT changed:** Laila, Booking Agent Start logic, payment formulas, Phase 3, supplier auto-send.

---

## 5. Manual customer-payment tracking test

**Via production Supabase RPC (test data `RU-2026-030`):**

| Test | Result |
|------|--------|
| Record 250 USD manual payment | PASS — ledger row created |
| Replay same idempotency key | PASS — `idempotent: true`, single ledger row |
| Negative amount (-100) | PASS — rejected `payment amount must be positive` |
| `booking_financial_policy` config | PASS — `mode=manual_only`, `automated_money_movement=false` |

---

## 6. Manual supplier-payment tracking status

**Current:** `booking_tasks.supplier_cost_usd` + `human_approval_queue` (`supplier_price_change`) — cost accounting and variance approval only.

**No supplier payout execution exists.**

**Recommended minimal extension (future, not implemented):**

```sql
-- Append-only mirror of booking_payments for supplier side
booking_supplier_payments (
  payment_id uuid PK,
  booking_id text FK,
  task_id uuid FK nullable,
  supplier_name text,
  amount_usd numeric check (> 0),
  currency_original text,
  payment_method text,
  reference text,
  notes text,
  recorded_by text,
  idempotency_key text unique,
  created_at timestamptz
)
```

Staff records after manual bank transfer to hotel/driver/guide — same pattern as customer ledger.

---

## 7. Authorization tests

| Test | Result |
|------|--------|
| Unauthorized Telegram user (999999001) on approval | PASS (existing Phase 2.4A test) |
| Webhook without secret when env secret set | Requires n8n deploy + secret env — logic added |
| Allowlist-only legacy when secret env unset | PASS — backward compatible |

---

## 8. Confirmation-gate tests

| `payment_requirement` | Expected | Verified |
|-----------------------|----------|----------|
| NULL (legacy) | satisfied | PASS |
| `pay_at_destination` | satisfied without payment | PASS |
| `manual` + `manual_payment_approved_at` | satisfied | PASS |
| `full` / `deposit` | satisfied when ledger meets threshold | Via Phase 2.4A test script (deposit flow) |

Gate controls **lifecycle status only** — never triggers money movement.

---

## 9. Evidence: ZERO automated money movement

- Static scan: **10 booking workflows**, **0 forbidden payment API patterns**
- `record_booking_payment`: positive amounts only, append-only, no gateway calls
- Booking Agent Start: explicit comment "NO payments, NO refunds"
- n8n financial nodes: Supabase RPC + Telegram API only
- Laila: no financial mutation paths (unchanged)

---

## 10. Recommended next operational step

1. **Owner:** Ensure `BOOKING_AGENT_START_SECRET` is set in n8n production env (financial webhooks now require it when configured).
2. **Deploy** updated Payment Record + Approval Handler workflows to n8n.
3. **Staff SOP:** After manual customer/supplier payment outside Arcadia → authorized staff records in Telegram Booking Bot with reference + amount.
4. **Future (optional):** Add `booking_supplier_payments` table when supplier payment tracking is needed — do not build until owner approves schema.
5. **Do NOT** connect Stripe/banks, enable refunds automation, or modify Laila.

---

## Regression

| Suite | Result |
|-------|--------|
| Booking Agent UAT (`run_internal_uat_rerun.py`) | **PASS 12/12** |
| Laila | **Unmodified** |
| Static financial policy scan | **PASS** |

**STOP** — awaiting owner approval before any payment automation or supplier-payment subsystem.
