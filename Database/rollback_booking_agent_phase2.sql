-- Rollback Booking Agent Phase 2.1 (reverse order)
-- Does NOT drop Phase 1 columns lead_id/customer_id/quote_ref on bookings.

drop trigger if exists bookings_before_update_sync_trg on public.bookings;
drop function if exists public.bookings_before_update_sync();
drop function if exists public.generate_booking_id(text);
drop function if exists public.destination_to_booking_prefix(text);
drop function if exists public.map_legacy_status_to_lifecycle(text);
drop function if exists public.map_lifecycle_to_legacy_status(text);
drop function if exists public.compute_payment_status(boolean, numeric, numeric);

drop table if exists public.booking_tasks;
drop table if exists public.booking_status_log;
drop table if exists public.booking_id_counters;
drop table if exists public.arcadia_system_config;

alter table public.human_approval_queue drop column if exists idempotency_key;

alter table public.bookings
  drop constraint if exists bookings_lifecycle_status_check,
  drop constraint if exists bookings_payment_status_check;

alter table public.bookings
  drop column if exists lifecycle_status,
  drop column if exists payment_status,
  drop column if exists lifecycle_backfilled_at,
  drop column if exists lifecycle_backfill_source,
  drop column if exists payment_backfilled_at,
  drop column if exists approved_at,
  drop column if exists approved_by,
  drop column if exists cancelled_at,
  drop column if exists cancellation_reason,
  drop column if exists booking_source;

-- Restore leads stage constraint without approved
alter table public.leads drop constraint if exists leads_stage_check;
alter table public.leads add constraint leads_stage_check
  check (stage = any (array[
    'new'::text, 'quoted'::text, 'interested'::text, 'followup'::text,
    'manual_quote'::text, 'closed'::text, 'lost'::text, 'handoff'::text
  ]));
