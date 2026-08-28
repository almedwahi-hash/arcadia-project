-- Rollback Booking Agent Phase 2.3

drop function if exists public.recompute_booking_lifecycle(text);

drop table if exists public.booking_telegram_idempotency;
drop table if exists public.booking_task_status_log;

alter table public.booking_tasks drop column if exists is_required;

delete from public.arcadia_system_config
where config_key in (
  'booking_staff_telegram_allowlist',
  'booking_agent_test_webhook',
  'phase2_test_bookings'
);

update public.arcadia_system_config
set config_value = jsonb_set(config_value, '{chat_id}', 'null'::jsonb, true),
    updated_at = now()
where config_key = 'telegram_booking_ops';

update public.bookings
set booking_source = 'booking_agent'
where booking_id = 'RU-2026-030' and booking_source = 'phase2_test';
