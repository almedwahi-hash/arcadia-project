-- Arcadia Tourism — Booking Agent Phase 2.6 (Supplier Operations Assistant)
-- ADDITIVE ONLY — reuses hotels table + booking_tasks fields; no duplicate supplier master.
-- Rollback: Database/rollback_booking_agent_phase2_6.sql

-- ============================================================
-- 1. Supplier draft storage (preview only — NO auto-send)
-- ============================================================
create table if not exists public.booking_supplier_drafts (
  draft_id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.booking_tasks(task_id) on delete cascade,
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  draft_type text not null
    check (draft_type in ('hotel','airport_transfer','intercity_transfer','tour','train','guide','other')),
  status text not null default 'draft'
    check (status in ('draft','needs_information','previewed','sent_manually','superseded')),
  draft_text text,
  facts jsonb not null default '{}'::jsonb,
  missing_fields jsonb not null default '[]'::jsonb,
  supplier_name text,
  supplier_channel text,
  contact_snapshot jsonb not null default '{}'::jsonb,
  idempotency_key text not null,
  created_by text not null default 'booking_agent',
  sent_manually_at timestamptz,
  sent_manually_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (idempotency_key)
);

create index if not exists booking_supplier_drafts_task_created_idx
  on public.booking_supplier_drafts (task_id, created_at desc);

comment on table public.booking_supplier_drafts is
  'Staff-preview supplier reservation drafts. NEVER auto-sent in Phase 2.6.';

-- ============================================================
-- 2. Supplier response log (operational — no customer financial change)
-- ============================================================
create table if not exists public.booking_supplier_responses (
  response_id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.booking_tasks(task_id) on delete cascade,
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  draft_id uuid references public.booking_supplier_drafts(draft_id) on delete set null,
  response_type text not null
    check (response_type in (
      'confirmed','unavailable','alternative_offered','waiting','needs_information'
    )),
  confirmation_ref text,
  supplier_quoted_cost_usd numeric,
  notes text,
  recorded_by text not null,
  idempotency_key text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (idempotency_key)
);

create index if not exists booking_supplier_responses_task_idx
  on public.booking_supplier_responses (task_id, created_at desc);

-- ============================================================
-- 3. Reminder dedupe log (design — watcher OFF by default)
-- ============================================================
create table if not exists public.booking_task_reminder_log (
  reminder_id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.booking_tasks(task_id) on delete cascade,
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  reminder_type text not null
    check (reminder_type in (
      'request_not_sent','awaiting_supplier_response','approaching_arrival_unconfirmed'
    )),
  idempotency_key text not null,
  chat_id text,
  message_id bigint,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (idempotency_key)
);

create index if not exists booking_task_reminder_log_task_type_idx
  on public.booking_task_reminder_log (task_id, reminder_type, created_at desc);

-- ============================================================
-- 4. Config — company identity, reminder policy; handoff stays OFF
-- ============================================================
insert into public.arcadia_system_config (config_key, config_value, description)
values
  (
    'booking_supplier_ops',
    '{
      "company_name": "Arcadia Tourism",
      "company_name_ar": "أركاديا للسياحة",
      "booking_email": "bookings@arcadia-tour.cloud",
      "booking_phone": "+380936582617",
      "auto_send_enabled": false,
      "note": "Phase 2.6 — drafts only; staff sends manually"
    }'::jsonb,
    'Supplier draft identity + Phase 2.6 safety flags'
  ),
  (
    'booking_task_reminder_policy',
    '{
      "enabled": false,
      "cooldown_hours": 24,
      "request_not_sent_after_hours": 48,
      "awaiting_response_after_hours": 72,
      "approaching_arrival_days": 7,
      "note": "Reminder watcher OFF by default; dedupe via booking_task_reminder_log"
    }'::jsonb,
    'Overdue task reminder policy — no spam'
  )
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

-- Global handoff OFF — preserve existing canary_lead_ids; only merge safety note
update public.arcadia_system_config
set config_value = jsonb_set(
  config_value || '{"note":"Global OFF. Use canary_lead_ids for selected leads only."}'::jsonb,
  '{enabled}',
  'false'::jsonb,
  true
)
where config_key = 'booking_handoff_enabled';
