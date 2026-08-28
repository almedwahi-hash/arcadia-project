-- Rollback Booking Agent Phase 2.1c (reverse order)

drop trigger if exists bookings_after_insert_audit_trg on public.bookings;
drop function if exists public.bookings_after_insert_audit();

drop index if exists public.bookings_booking_request_key_uidx;

alter table public.bookings drop column if exists booking_request_key;

delete from public.arcadia_system_config
where config_key in ('payment_backfill_needs_review', 'booking_id_sequence_gaps');
