-- Rollback Phase 2.5 handoff schema (does NOT delete bookings/tasks)
-- Manual apply via Supabase SQL editor

delete from public.arcadia_system_config
where config_key in ('booking_handoff_enabled', 'booking_agent_start_webhook');

drop index if exists public.leads_approved_handoff_idx;
drop table if exists public.lead_quote_links;

alter table public.leads
  drop column if exists approved_quote_ref,
  drop column if exists approved_at,
  drop column if exists approved_by,
  drop column if exists booking_handoff_at;
