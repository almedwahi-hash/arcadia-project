-- Arcadia Tourism — Multi-Agent Phase 1 (observability foundation)
-- Backward-compatible: ADD only — no column drops/renames on existing tables.
-- Apply via Supabase migration. Rollback: Database/rollback_multi_agent_phase1.sql
-- n8n write path: service_role (bypasses RLS). Do NOT commit service_role to git.

create extension if not exists "pgcrypto";

-- Reuse updated_at trigger if present
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- =========================
-- customers
-- =========================
create table if not exists public.customers (
  customer_id uuid primary key default gen_random_uuid(),
  phone text not null,
  name text,
  email text,
  country_code text,
  preferred_language text not null default 'ar',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists customers_phone_unique_idx
  on public.customers (phone);

drop trigger if exists customers_set_updated_at on public.customers;
create trigger customers_set_updated_at
before update on public.customers
for each row execute function public.set_updated_at();

-- =========================
-- leads — extend (source of truth; lead_state untouched)
-- =========================
alter table public.leads
  add column if not exists customer_id uuid references public.customers(customer_id) on delete set null;

alter table public.leads
  add column if not exists conversation_id uuid;

comment on column public.leads.conversation_id is
  'Active chat session UUID — reuse across lead_interactions for this lead. Set by n8n; not auto-generated per message.';

create index if not exists leads_customer_id_idx
  on public.leads (customer_id) where customer_id is not null;

create index if not exists leads_conversation_id_idx
  on public.leads (conversation_id) where conversation_id is not null;

-- =========================
-- lead_interactions — inbound BEFORE AI, outbound AFTER send success
-- conversation_id: NO default — workflow must pass same session id
-- provider_message_id: idempotency for WA/TG webhook retries
-- =========================
create table if not exists public.lead_interactions (
  interaction_id uuid primary key default gen_random_uuid(),
  lead_id uuid references public.leads(lead_id) on delete set null,
  customer_id uuid references public.customers(customer_id) on delete set null,
  conversation_id uuid not null,
  channel text not null check (channel in ('whatsapp','telegram','email','web','instagram')),
  direction text not null check (direction in ('inbound','outbound')),
  role text not null check (role in ('user','assistant','system','staff')),
  message_type text not null default 'text'
    check (message_type in ('text','image','audio','document','location','video','sticker','unknown')),
  message_text text,
  provider_message_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists lead_interactions_lead_created_idx
  on public.lead_interactions (lead_id, created_at desc);

create index if not exists lead_interactions_conversation_created_idx
  on public.lead_interactions (conversation_id, created_at);

-- Idempotency: same provider message on same channel = duplicate webhook
create unique index if not exists lead_interactions_provider_dedupe_idx
  on public.lead_interactions (channel, provider_message_id)
  where provider_message_id is not null;

-- =========================
-- agent_actions
-- =========================
create table if not exists public.agent_actions (
  action_id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  action_type text not null,
  customer_id uuid references public.customers(customer_id) on delete set null,
  lead_id uuid references public.leads(lead_id) on delete set null,
  booking_id text references public.bookings(booking_id) on delete set null,
  source_channel text,
  input_summary text,
  output_summary text,
  status text not null default 'success'
    check (status in ('success','failed','pending')),
  error_message text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists agent_actions_agent_created_idx
  on public.agent_actions (agent_name, created_at desc);

create index if not exists agent_actions_lead_created_idx
  on public.agent_actions (lead_id, created_at desc);

-- =========================
-- human_approval_queue
-- =========================
create table if not exists public.human_approval_queue (
  approval_id uuid primary key default gen_random_uuid(),
  action_type text not null,
  lead_id uuid references public.leads(lead_id) on delete set null,
  booking_id text references public.bookings(booking_id) on delete set null,
  payload jsonb not null default '{}'::jsonb,
  reason text,
  status text not null default 'pending'
    check (status in ('pending','approved','rejected','expired')),
  requested_by_agent text,
  approved_by text,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists human_approval_queue_status_created_idx
  on public.human_approval_queue (status, created_at desc);

-- =========================
-- workflow_failures — central n8n Error Workflow target
-- =========================
create table if not exists public.workflow_failures (
  failure_id uuid primary key default gen_random_uuid(),
  workflow_name text not null,
  workflow_id text,
  execution_id text,
  node_name text,
  agent_name text,
  source_channel text,
  lead_id uuid references public.leads(lead_id) on delete set null,
  booking_id text references public.bookings(booking_id) on delete set null,
  severity text not null default 'error'
    check (severity in ('info','warning','error','critical')),
  payload jsonb not null default '{}'::jsonb,
  error_message text not null,
  retry_count int not null default 0,
  status text not null default 'open'
    check (status in ('open','retrying','resolved','dead')),
  last_retry_at timestamptz,
  next_retry_at timestamptz,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists workflow_failures_status_created_idx
  on public.workflow_failures (status, created_at desc);

create index if not exists workflow_failures_execution_idx
  on public.workflow_failures (execution_id) where execution_id is not null;

-- =========================
-- bookings — extend (no status/stage changes in Phase 1)
-- =========================
alter table public.bookings
  add column if not exists lead_id uuid references public.leads(lead_id) on delete set null;

alter table public.bookings
  add column if not exists customer_id uuid references public.customers(customer_id) on delete set null;

alter table public.bookings
  add column if not exists quote_ref text;

create index if not exists bookings_lead_id_idx
  on public.bookings (lead_id) where lead_id is not null;

-- =========================
-- Backfill customers from existing leads (optional, safe)
-- =========================
insert into public.customers (phone, name, country_code)
select distinct l.phone, l.name, l.country_code
from public.leads l
where l.phone is not null and trim(l.phone) <> ''
on conflict (phone) do nothing;

-- Link leads to customers by phone (only where customer_id still null)
update public.leads l
set customer_id = c.customer_id
from public.customers c
where l.customer_id is null
  and l.phone is not null
  and trim(l.phone) <> ''
  and c.phone = l.phone;

-- =========================
-- RLS posture — new tables: locked down; n8n uses service_role
-- Phase 1: NO policy changes on existing tables (see security matrix doc)
-- =========================
alter table public.customers enable row level security;
alter table public.lead_interactions enable row level security;
alter table public.agent_actions enable row level security;
alter table public.human_approval_queue enable row level security;
alter table public.workflow_failures enable row level security;

revoke all on public.customers from anon, authenticated;
revoke all on public.lead_interactions from anon, authenticated;
revoke all on public.agent_actions from anon, authenticated;
revoke all on public.human_approval_queue from anon, authenticated;
revoke all on public.workflow_failures from anon, authenticated;
