-- Arcadia Tourism — Booking Agent Phase 2.5 (real booking handoff)
-- ADDITIVE ONLY — explicit approved quote, quote-lead linkage, handoff config.
-- Rollback: Database/rollback_booking_agent_phase2_5.sql

-- ============================================================
-- 1. leads — explicit approval metadata (deterministic handoff)
-- ============================================================
alter table public.leads
  add column if not exists approved_quote_ref text,
  add column if not exists approved_at timestamptz,
  add column if not exists approved_by text,
  add column if not exists booking_handoff_at timestamptz;

comment on column public.leads.approved_quote_ref is
  'Exact quote_ref customer/staff approved — required for automatic booking handoff.';
comment on column public.leads.booking_handoff_at is
  'When Booking Agent handoff completed (idempotent marker for stage watcher).';

create index if not exists leads_approved_handoff_idx
  on public.leads (stage, approved_quote_ref)
  where stage = 'approved' and approved_quote_ref is not null and booking_handoff_at is null;

-- ============================================================
-- 2. lead_quote_links — one quote belongs to one lead (no guessing)
-- ============================================================
create table if not exists public.lead_quote_links (
  link_id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references public.leads(lead_id) on delete cascade,
  quote_ref text not null,
  link_source text not null default 'manual'
    check (link_source in ('manual', 'pricing', 'staff', 'migration', 'canary')),
  linked_at timestamptz not null default now(),
  linked_by text,
  metadata jsonb not null default '{}'::jsonb,
  unique (lead_id, quote_ref)
);

create unique index if not exists lead_quote_links_quote_ref_uidx
  on public.lead_quote_links (quote_ref);

comment on table public.lead_quote_links is
  'Explicit lead↔quote association. quote_ref is globally unique per lead.';

-- ============================================================
-- 3. Runtime config — handoff feature flag (OFF by default)
-- ============================================================
insert into public.arcadia_system_config (config_key, config_value, description)
values
  (
    'booking_handoff_enabled',
    '{
      "enabled": false,
      "canary_lead_ids": [],
      "batch_limit": 5,
      "note": "Set enabled=true only after Phase 2.5 canary passes. Use canary_lead_ids to limit scope."
    }'::jsonb,
    'Stage watcher cron — automatic approved-lead → booking handoff'
  ),
  (
    'booking_agent_start_webhook',
    '{
      "path": "booking-agent/start",
      "auth_header": "X-Booking-Agent-Secret",
      "note": "Secret in n8n env BOOKING_AGENT_START_SECRET"
    }'::jsonb,
    'Production Booking Agent Start webhook metadata'
  ),
  (
    'booking_agent_ci_probe',
    '{
      "enabled": true,
      "probe_secret": "arcadia-phase25-ci-probe-2026",
      "note": "CI/canary only — X-Booking-Ci-Probe header. Disable after cutover if desired."
    }'::jsonb,
    'Controlled CI probe auth for Phase 2.5 automated tests (not for production staff use)'
  )
on conflict (config_key) do nothing;

-- ============================================================
-- 4. Canary seed — Phase 2.5 controlled test lead (idempotent)
-- ============================================================
insert into public.lead_quote_links (lead_id, quote_ref, link_source, linked_by, metadata)
values
  (
    'b6fada92-a0c4-45a9-a5f7-2e60897af3c8'::uuid,
    'ARC-367344',
    'canary',
    'phase2_5_migration',
    '{"note": "Phase 2.2/2.4A test fixture — idempotency canary"}'::jsonb
  ),
  (
    'cb874bb1-d10c-4f0f-82c1-166ccbb3c75c'::uuid,
    'ARC-884991',
    'canary',
    'phase2_5_migration',
    '{"note": "Phase 2.5 fresh-create canary"}'::jsonb
  ),
  (
    'ed03316f-cbf6-4d40-91d4-59f9cccba6df'::uuid,
    'ARC-089651',
    'canary',
    'phase2_5_migration',
    '{"note": "Phase 2.5 non-approved block test"}'::jsonb
  )
on conflict (lead_id, quote_ref) do nothing;

-- Do NOT auto-set approved stage — tests set explicitly via test script
