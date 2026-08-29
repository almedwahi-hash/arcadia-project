-- Arcadia Booking Agent — Manual financial operations policy lock (Phase 2.4A alignment)
-- Does NOT change money-movement behavior (already manual). Documents policy + config flag.
-- Apply after: Database/supabase_schema_booking_agent_phase2_4a.sql

insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'booking_financial_policy',
  '{
    "mode": "manual_only",
    "automated_money_movement": false,
    "customer_payments": "staff_record_after_manual_transfer",
    "supplier_payments": "staff_record_after_manual_transfer",
    "ai_may_record_payment": false,
    "ai_may_execute_payment": false,
    "refunds_automated": false,
    "payment_gateways": [],
    "note": "All real money movement is performed by Arcadia staff outside automation. System tracks, records, verifies, reminds, and audits only."
  }'::jsonb,
  'Owner policy: manual-only financial operations — no automated charge/transfer/refund'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

comment on function public.record_booking_payment is
  'Append-only customer payment ledger entry (staff/system). MANUAL-ONLY: records payment after staff confirms it happened outside automation. No gateway execution.';

comment on function public.booking_payment_policy_satisfied is
  'Lifecycle gate only — checks recorded paid_amount vs policy. Never triggers money movement.';

comment on function public.resolve_booking_approval is
  'Staff approval for cost variance / manual override / financial commit gate. Metadata updates only — no payment execution.';

comment on table public.booking_payments is
  'Append-only customer payment ledger (manual record). paid_amount derived via sync_booking_paid_amount(). No refunds in Phase 2.4A. No automated money movement.';
