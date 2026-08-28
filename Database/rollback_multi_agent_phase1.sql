-- Rollback Arcadia Multi-Agent Phase 1
-- Run manually if Phase 1 must be reversed. Order matters (FK dependencies).

-- bookings extensions
alter table public.bookings drop column if exists quote_ref;
alter table public.bookings drop column if exists customer_id;
alter table public.bookings drop column if exists lead_id;

-- observability tables
drop table if exists public.workflow_failures;
drop table if exists public.human_approval_queue;
drop table if exists public.agent_actions;
drop table if exists public.lead_interactions;

-- leads extensions
alter table public.leads drop column if exists conversation_id;
alter table public.leads drop column if exists customer_id;

drop table if exists public.customers;
