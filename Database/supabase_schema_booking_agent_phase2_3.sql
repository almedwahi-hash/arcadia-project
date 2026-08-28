-- Arcadia Tourism — Booking Agent Phase 2.3 (staff notify + task update)
-- Rollback: Database/rollback_booking_agent_phase2_3.sql

-- ============================================================
-- 1. is_required on booking_tasks
-- ============================================================
alter table public.booking_tasks
  add column if not exists is_required boolean not null default true;

comment on column public.booking_tasks.is_required is
  'Required tasks block lifecycle until confirmed/skipped. Optional (e.g. tours) do not.';

-- Phase 2 test booking: hotels/transfers required; tours optional
update public.booking_tasks
set is_required = case
  when task_type in ('hotel', 'airport_transfer', 'intercity_transfer', 'train', 'guide') then true
  when task_type in ('tour', 'other') then false
  else true
end
where booking_id = 'RU-2026-030';

-- ============================================================
-- 2. Task status audit log (separate from booking_status_log)
-- ============================================================
create table if not exists public.booking_task_status_log (
  log_id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.booking_tasks(task_id) on delete cascade,
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  field_changed text not null default 'status'
    check (field_changed in ('status', 'confirmation_ref', 'supplier_name', 'supplier_cost_usd', 'notes')),
  old_value text,
  new_value text,
  changed_by text not null,
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists booking_task_status_log_task_created_idx
  on public.booking_task_status_log (task_id, created_at desc);

create index if not exists booking_task_status_log_booking_created_idx
  on public.booking_task_status_log (booking_id, created_at desc);

-- ============================================================
-- 3. Telegram callback idempotency
-- ============================================================
create table if not exists public.booking_telegram_idempotency (
  idempotency_key text primary key,
  action_type text not null,
  booking_id text,
  task_id uuid,
  processed_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

comment on table public.booking_telegram_idempotency is
  'Prevents duplicate Telegram callback effects — key = callback_query_id or deterministic action key.';

-- ============================================================
-- 4. Staff allowlist + telegram ops + webhook auth config
-- ============================================================
insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'booking_staff_telegram_allowlist',
  '{"user_ids": [493831958], "note": "Authorized Telegram user IDs for booking task updates"}'::jsonb,
  'Staff Telegram allowlist — no DB writes for unauthorized senders'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

update public.arcadia_system_config
set config_value = jsonb_set(
      coalesce(config_value, '{}'::jsonb),
      '{chat_id}',
      '493831958'::jsonb,
      true
    ),
    updated_at = now()
where config_key = 'telegram_booking_ops';

insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'booking_agent_test_webhook',
  '{"auth_header": "X-Booking-Agent-Secret", "note": "Secret value in n8n env BOOKING_AGENT_TEST_SECRET — workflow deactivated after canary"}'::jsonb,
  'Phase 2.2 test webhook security config'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'phase2_test_bookings',
  '{"bookings": [{"booking_id": "RU-2026-030", "marked_at": "2026-08-28", "cleanup": "archive after phase2 canary complete"}]}'::jsonb,
  'Documented test bookings — do not rewind counters on cleanup'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

-- ============================================================
-- 5. Mark test booking RU-2026-030
-- ============================================================
update public.bookings
set
  booking_source = 'phase2_test',
  modified_by = 'phase2_3_setup'
where booking_id = 'RU-2026-030';

-- ============================================================
-- 6. Lifecycle recompute helper
-- ============================================================
create or replace function public.recompute_booking_lifecycle(p_booking_id text)
returns text language plpgsql as $$
declare
  v_required int;
  v_terminal int;
  v_confirmed int;
  v_open int;
  v_new text;
  v_old text;
begin
  select lifecycle_status into v_old from public.bookings where booking_id = p_booking_id;

  select
    count(*) filter (where coalesce(is_required, true)),
    count(*) filter (where coalesce(is_required, true) and status in ('confirmed', 'skipped')),
    count(*) filter (where coalesce(is_required, true) and status = 'confirmed'),
    count(*) filter (where coalesce(is_required, true) and status in ('pending', 'requested', 'awaiting_confirmation', 'failed'))
  into v_required, v_terminal, v_confirmed, v_open
  from public.booking_tasks
  where booking_id = p_booking_id;

  if v_required = 0 then
    v_new := 'PENDING_PAYMENT';
  elsif v_terminal = v_required then
    v_new := 'PENDING_PAYMENT';
  elsif v_confirmed > 0 and v_open > 0 then
    v_new := 'PARTIALLY_CONFIRMED';
  else
    v_new := 'PENDING_SUPPLIER';
  end if;

  if v_new in ('CONFIRMED', 'IN_PROGRESS', 'COMPLETED') then
    v_new := coalesce(v_old, 'DRAFT');
  end if;

  if v_old is distinct from v_new then
    update public.bookings
    set lifecycle_status = v_new,
        modified_by = 'system:lifecycle_recompute'
    where booking_id = p_booking_id;
  end if;

  return v_new;
end;
$$;

-- ============================================================
-- 7. RLS on new tables
-- ============================================================
alter table public.booking_task_status_log enable row level security;
alter table public.booking_telegram_idempotency enable row level security;
revoke all on public.booking_task_status_log from anon, authenticated;
revoke all on public.booking_telegram_idempotency from anon, authenticated;
