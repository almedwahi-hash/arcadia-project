# Phase 2.4A Test Report — Payment Gate + CONFIRMED + Approvals

**Tested at:** 2026-08-28T21:14:34Z  
**Booking:** `RU-2026-030` (`phase2_test`)  
**Result:** ✅ PASS

## Scope delivered (2.4A only)

- Booking payment policy columns (`payment_requirement`, `required_payment_amount`, manual approval fields) — nullable, no legacy backfill
- Append-only `booking_payments` ledger + `record_booking_payment()` RPC
- CONFIRMED gate in `recompute_booking_lifecycle()` (required tasks + payment policy + no pending approvals)
- Supplier cost variance approvals (`supplier_price_change`) with threshold from `arcadia_system_config.supplier_price_change_threshold_pct` (5%)
- Required-task skip blocking + `manual_override` approval path
- n8n workflows:
  - `Arcadia - Booking Payment Record` (`ij0ifJadW0wkJp3m`) — webhook `booking-payment-record`
  - `Arcadia - Booking Approval Handler` (`3sb3wXkJsnDGMrbm`) — webhook `booking-approval-callback-test`
  - Updated `Arcadia - Booking Task Update` (`PCNLpZ6CE5wBEIup`)

## Test matrix (RU-2026-030)

| # | Step | Expected | Actual | Status |
|---|------|----------|--------|--------|
| 1 | Start PENDING_PAYMENT, unpaid, deposit=500 | baseline | `PENDING_PAYMENT`, paid=0 | ✅ |
| 2 | Record 200 USD (below deposit) | stay PENDING_PAYMENT | lifecycle=PENDING_PAYMENT, policy=false | ✅ |
| 3 | Replay same payment idempotency key | no duplicate ledger row | `idempotent:true`, same payment_id | ✅ |
| 4 | Record remaining 300 USD | deposit satisfied | paid=500, policy=true | ✅ |
| 5 | Required tasks confirmed + deposit met | CONFIRMED | lifecycle=CONFIRMED | ✅ |
| 6 | Confirm hotel task with cost 120 vs quoted 100 (+20%) | one pending approval | approval_created, blocked confirm | ✅ |
| 7 | Replay variance request | no duplicate approval | approval_exists, same approval_id | ✅ |
| 8 | Unauthorized approval attempt | denied | `ok:false, denied:true` | ✅ |
| 9 | Authorized staff deny + audit | rejected + agent_actions | decision=rejected, lifecycle=PARTIALLY_CONFIRMED | ✅ |
| 10 | workflow_failures during canary | none new | 0 open failures after 21:14 UTC | ✅ |

## Evidence

Results JSON: `deliverables/arcadia-phase2-4a-test-results.json`

Key excerpts:
- Partial payment: `lifecycle_status=PENDING_PAYMENT`, `payment_policy_satisfied=false`
- Full deposit: `lifecycle_status=CONFIRMED`, `paid_amount=500`
- Variance: `approval_id=d6c1d71f-9673-4404-a0dc-9a5b16534e00`, `pct_change=20`, `threshold_pct=5`
- Deny: `decision=rejected`, `action_type=supplier_price_change`

## Restored test booking state

After canary, `RU-2026-030` restored to documented Phase 2 test baseline:

```
lifecycle_status:  PENDING_PAYMENT
payment_status:    unpaid
paid_amount:       0
payment_requirement: null   (legacy — no invented policy)
required_payment_amount: null
booking_source:    phase2_test
```

Required hotel task `hotel:moscow:1` reset to `confirmed` (quoted/supplier cost cleared).  
Test payment rows (`phase24a_*` idempotency keys) removed from ledger.

## Not in scope (deferred)

- Refunds / cancellation (Phase 2.4B)
- Laila / stage watcher / Orchestrator / `/book` production
- Customer payment links / auto-charge / supplier auto-booking

## Open carry-forward

- **Phase 2.0:** verify first natural Laila outbound stores real text in `lead_interactions.message_text` (not `[object Object]`)
