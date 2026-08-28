-- Arcadia Tourism — Booking Agent Phase 2.1 (schema + audited backfill)
-- ADDITIVE ONLY — extends bookings; does not recreate table.
-- Rollback: Database/rollback_booking_agent_phase2.sql
-- n8n write path: service_role (bypasses RLS). Do NOT commit service_role to git.

-- ============================================================
-- 1. System config (thresholds, Telegram ops destination)
-- ============================================================
create table if not exists public.arcadia_system_config (
  config_key text primary key,
  config_value jsonb not null default '{}'::jsonb,
  description text,
  updated_at timestamptz not null default now()
);

comment on table public.arcadia_system_config is
  'Runtime config for Booking Agent — supplier thresholds, Telegram chat id, etc.';

insert into public.arcadia_system_config (config_key, config_value, description)
values
  (
    'supplier_price_change_threshold_pct',
    '5'::jsonb,
    'Percent over quoted supplier cost that requires human approval'
  ),
  (
    'telegram_booking_ops',
    '{"chat_id": null, "bot": "Arcadia Laila Sales Bot"}'::jsonb,
    'Existing Telegram bot + configurable booking ops chat destination'
  )
on conflict (config_key) do nothing;

-- ============================================================
-- 2. Safe booking_id generation (never MAX+1)
-- ============================================================
create table if not exists public.booking_id_counters (
  prefix text not null,
  year int not null,
  last_seq int not null default 0,
  primary key (prefix, year)
);

comment on table public.booking_id_counters is
  'Atomic counters for generate_booking_id() — seeded from legacy bookings.';

create or replace function public.destination_to_booking_prefix(p_destination text)
returns text language sql immutable as $$
  select case lower(trim(coalesce(p_destination, '')))
    when 'kazakhstan' then 'KA'
    when 'russia' then 'RU'
    when 'uzbekistan' then 'UZ'
    when 'poland' then 'PO'
    else 'XX'
  end;
$$;

create or replace function public.generate_booking_id(p_destination text)
returns text language plpgsql as $$
declare
  v_prefix text;
  v_year int := extract(year from current_date)::int;
  v_seq int;
begin
  v_prefix := public.destination_to_booking_prefix(p_destination);

  insert into public.booking_id_counters (prefix, year, last_seq)
  values (v_prefix, v_year, 0)
  on conflict (prefix, year) do nothing;

  update public.booking_id_counters
  set last_seq = last_seq + 1
  where prefix = v_prefix and year = v_year
  returning last_seq into v_seq;

  if v_seq is null then
    raise exception 'generate_booking_id: counter missing for %-%', v_prefix, v_year;
  end if;

  return v_prefix || '-' || v_year || '-' || lpad(v_seq::text, greatest(length(v_seq::text), 3), '0');
end;
$$;

comment on function public.generate_booking_id(text) is
  'DB-side atomic booking_id — format PREFIX-YEAR-SEQ (e.g. KA-2026-117).';

-- Seed counters from existing bookings (safe high-water mark)
insert into public.booking_id_counters (prefix, year, last_seq)
select
  split_part(booking_id, '-', 1) as prefix,
  split_part(booking_id, '-', 2)::int as year,
  max(split_part(booking_id, '-', 3)::int) as last_seq
from public.bookings
where booking_id ~ '^[A-Z]{2}-[0-9]{4}-[0-9]+$'
group by 1, 2
on conflict (prefix, year) do update
  set last_seq = greatest(public.booking_id_counters.last_seq, excluded.last_seq);

-- ============================================================
-- 3. leads — add approved stage (formal)
-- ============================================================
alter table public.leads drop constraint if exists leads_stage_check;
alter table public.leads add constraint leads_stage_check
  check (stage = any (array[
    'new'::text, 'quoted'::text, 'interested'::text, 'followup'::text,
    'manual_quote'::text, 'closed'::text, 'lost'::text, 'handoff'::text,
    'approved'::text
  ]));

-- ============================================================
-- 4. bookings — nullable lifecycle/payment columns (NO defaults on legacy)
-- ============================================================
alter table public.bookings
  add column if not exists lifecycle_status text,
  add column if not exists payment_status text,
  add column if not exists lifecycle_backfilled_at timestamptz,
  add column if not exists lifecycle_backfill_source text,
  add column if not exists payment_backfilled_at timestamptz,
  add column if not exists approved_at timestamptz,
  add column if not exists approved_by text,
  add column if not exists cancelled_at timestamptz,
  add column if not exists cancellation_reason text,
  add column if not exists booking_source text;

comment on column public.bookings.lifecycle_status is
  'Agent lifecycle enum — nullable until backfill/agent create. Legacy ops app uses status.';
comment on column public.bookings.payment_status is
  'Derived payment state — updated only via trusted staff/system paths.';
comment on column public.bookings.booking_source is
  'legacy_ops | booking_agent — distinguishes pre-agent rows';

-- CHECK constraints allow NULL during transition
alter table public.bookings drop constraint if exists bookings_lifecycle_status_check;
alter table public.bookings add constraint bookings_lifecycle_status_check
  check (lifecycle_status is null or lifecycle_status = any (array[
    'DRAFT','PENDING_SUPPLIER','PENDING_PAYMENT','PARTIALLY_CONFIRMED',
    'CONFIRMED','IN_PROGRESS','COMPLETED','CANCELLED'
  ]));

alter table public.bookings drop constraint if exists bookings_payment_status_check;
alter table public.bookings add constraint bookings_payment_status_check
  check (payment_status is null or payment_status = any (array[
    'unpaid','partial','paid','refund_pending','refunded'
  ]));

create index if not exists bookings_lifecycle_status_idx
  on public.bookings (lifecycle_status) where lifecycle_status is not null;

-- ============================================================
-- 5. booking_status_log — audit all status/payment changes
-- ============================================================
create table if not exists public.booking_status_log (
  log_id uuid primary key default gen_random_uuid(),
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  field_changed text not null
    check (field_changed in (
      'status','lifecycle_status','payment_status',
      'paid_amount','is_paid','payment_method'
    )),
  old_value text,
  new_value text,
  changed_by text not null,
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists booking_status_log_booking_created_idx
  on public.booking_status_log (booking_id, created_at desc);

-- ============================================================
-- 6. booking_tasks — task_key idempotency
-- ============================================================
-- Deterministic task_key rules (Phase 2.2 generator must follow):
--   hotel:{city_slug}:{segment_index}
--   airport:{city_slug|arrival}:transfer
--   tour:{city_slug}:{tour_index}
--   train:{segment_from}-{segment_to}
--   intercity_transfer:{from_slug}-{to_slug}
--   guide:{city_slug}:guide
--   other:{slug}:misc
create table if not exists public.booking_tasks (
  task_id uuid primary key default gen_random_uuid(),
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  task_key text not null,
  task_type text not null
    check (task_type in (
      'hotel','airport_transfer','intercity_transfer',
      'tour','train','guide','other'
    )),
  city text,
  segment_index int not null default 1,
  supplier_name text,
  supplier_channel text,
  status text not null default 'pending'
    check (status in (
      'pending','requested','awaiting_confirmation',
      'confirmed','failed','cancelled','skipped'
    )),
  confirmation_ref text,
  supplier_cost_usd numeric,
  quoted_cost_usd numeric,
  due_at timestamptz,
  requested_at timestamptz,
  confirmed_at timestamptz,
  assigned_to text,
  notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (booking_id, task_key)
);

create index if not exists booking_tasks_booking_status_idx
  on public.booking_tasks (booking_id, status);

drop trigger if exists booking_tasks_set_updated_at on public.booking_tasks;
create trigger booking_tasks_set_updated_at
before update on public.booking_tasks
for each row execute function public.set_updated_at();

-- ============================================================
-- 7. human_approval_queue — idempotency
-- ============================================================
alter table public.human_approval_queue
  add column if not exists idempotency_key text;

create unique index if not exists human_approval_pending_idempotency_idx
  on public.human_approval_queue (action_type, coalesce(booking_id, ''), idempotency_key)
  where status = 'pending' and idempotency_key is not null;

-- ============================================================
-- 8. Mapping helpers (trigger created AFTER backfill)
-- ============================================================
create or replace function public.map_legacy_status_to_lifecycle(p_status text)
returns text language sql immutable as $$
  select case p_status
    when 'pending' then 'PENDING_SUPPLIER'
    when 'confirmed' then 'CONFIRMED'
    when 'in_hotel' then 'IN_PROGRESS'
    when 'cancelled' then 'CANCELLED'
    else null
  end;
$$;

create or replace function public.map_lifecycle_to_legacy_status(p_lifecycle text)
returns text language sql immutable as $$
  select case p_lifecycle
    when 'DRAFT' then 'pending'
    when 'PENDING_SUPPLIER' then 'pending'
    when 'PENDING_PAYMENT' then 'pending'
    when 'PARTIALLY_CONFIRMED' then 'pending'
    when 'CONFIRMED' then 'confirmed'
    when 'IN_PROGRESS' then 'in_hotel'
    when 'COMPLETED' then 'confirmed'
    when 'CANCELLED' then 'cancelled'
    else null
  end;
$$;

create or replace function public.compute_payment_status(
  p_is_paid boolean, p_paid_amount numeric, p_total_amount numeric
)
returns text language sql immutable as $$
  select case
    when coalesce(p_paid_amount, 0) <= 0 and not coalesce(p_is_paid, false) then 'unpaid'
    when coalesce(p_is_paid, false) and coalesce(p_total_amount, 0) > 0
         and coalesce(p_paid_amount, 0) >= p_total_amount then 'paid'
    when coalesce(p_is_paid, false) and coalesce(p_total_amount, 0) = 0 then 'paid'
    when coalesce(p_paid_amount, 0) > 0 then 'partial'
    else 'unpaid'
  end;
$$;

create or replace function public.bookings_before_update_sync()
returns trigger language plpgsql as $$
declare
  v_mapped_lifecycle text;
  v_mapped_legacy text;
  v_trusted_payment boolean;
begin
  v_trusted_payment :=
    coalesce(current_setting('arcadia.trusted_payment_update', true), '0') = '1'
    or coalesce(new.modified_by, '') in ('admin', 'staff', 'system', 'ops_app');

  -- Payment guard: only trusted paths may change financial fields
  if (
    old.paid_amount is distinct from new.paid_amount
    or old.is_paid is distinct from new.is_paid
    or old.payment_method is distinct from new.payment_method
  ) and not v_trusted_payment then
    raise exception 'payment change blocked: set arcadia.trusted_payment_update=1 or modified_by admin/staff/system'
      using errcode = 'P0001';
  end if;

  -- Sync payment_status when trusted payment fields change
  if v_trusted_payment and (
    old.paid_amount is distinct from new.paid_amount
    or old.is_paid is distinct from new.is_paid
  ) then
    new.payment_status := public.compute_payment_status(new.is_paid, new.paid_amount, new.total_amount);
  end if;

  -- Legacy status changed (ops app) — log + mirror to lifecycle when mappable
  if old.status is distinct from new.status then
    insert into public.booking_status_log (
      booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
    ) values (
      new.booking_id, 'status', old.status, new.status,
      coalesce(nullif(new.modified_by, ''), 'ops_app'),
      'legacy_status_update',
      jsonb_build_object('source', coalesce(new.booking_source, 'legacy_ops'))
    );

    v_mapped_lifecycle := public.map_legacy_status_to_lifecycle(new.status);
    if v_mapped_lifecycle is not null
       and new.lifecycle_status is distinct from v_mapped_lifecycle then
      insert into public.booking_status_log (
        booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
      ) values (
        new.booking_id, 'lifecycle_status', old.lifecycle_status, v_mapped_lifecycle,
        'system:legacy_sync', 'mapped_from_status',
        jsonb_build_object('legacy_status', new.status)
      );
      new.lifecycle_status := v_mapped_lifecycle;
    end if;
  end if;

  -- Lifecycle changed (agent) — log + dual-write legacy status for ops app
  if old.lifecycle_status is distinct from new.lifecycle_status then
    insert into public.booking_status_log (
      booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
    ) values (
      new.booking_id, 'lifecycle_status', old.lifecycle_status, new.lifecycle_status,
      coalesce(nullif(new.modified_by, ''), 'booking_agent'),
      'lifecycle_update', '{}'::jsonb
    );

    v_mapped_legacy := public.map_lifecycle_to_legacy_status(new.lifecycle_status);
    if v_mapped_legacy is not null and new.status is distinct from v_mapped_legacy then
      insert into public.booking_status_log (
        booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
      ) values (
        new.booking_id, 'status', old.status, v_mapped_legacy,
        'system:lifecycle_sync', 'mapped_from_lifecycle',
        jsonb_build_object('lifecycle_status', new.lifecycle_status)
      );
      new.status := v_mapped_legacy;
    end if;
  end if;

  -- Log trusted payment_status transitions
  if old.payment_status is distinct from new.payment_status then
    insert into public.booking_status_log (
      booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
    ) values (
      new.booking_id, 'payment_status', old.payment_status, new.payment_status,
      coalesce(nullif(new.modified_by, ''), 'system'),
      case when v_trusted_payment then 'trusted_payment_update' else 'computed' end,
      jsonb_build_object(
        'paid_amount', new.paid_amount,
        'is_paid', new.is_paid,
        'total_amount', new.total_amount
      )
    );
  end if;

  new.last_modified := now();
  return new;
end;
$$;

-- ============================================================
-- 9. RLS — new Phase 2 tables (anon blocked)
-- ============================================================
alter table public.arcadia_system_config enable row level security;
alter table public.booking_id_counters enable row level security;
alter table public.booking_status_log enable row level security;
alter table public.booking_tasks enable row level security;

revoke all on public.arcadia_system_config from anon, authenticated;
revoke all on public.booking_id_counters from anon, authenticated;
revoke all on public.booking_status_log from anon, authenticated;
revoke all on public.booking_tasks from anon, authenticated;

-- ============================================================
-- 10. Audited backfill (legacy rows — explicit mapping)
-- ============================================================
update public.bookings
set
  booking_source = coalesce(booking_source, 'legacy_ops'),
  lifecycle_status = case status
    when 'confirmed' then 'CONFIRMED'
    when 'pending' then 'PENDING_SUPPLIER'
    when 'in_hotel' then 'IN_PROGRESS'
    when 'cancelled' then 'CANCELLED'
    else null
  end,
  lifecycle_backfilled_at = now(),
  lifecycle_backfill_source = 'phase2_legacy_status_v1'
where lifecycle_status is null;

insert into public.booking_status_log (
  booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
)
select
  b.booking_id,
  'lifecycle_status',
  null,
  b.lifecycle_status,
  'phase2_backfill',
  'initial_legacy_status_mapping',
  jsonb_build_object(
    'legacy_status', b.status,
    'backfill_source', b.lifecycle_backfill_source
  )
from public.bookings b
where b.lifecycle_backfilled_at >= now() - interval '5 minutes'
  and b.lifecycle_status is not null;

-- Payment status backfill (audited — does not change paid_amount/is_paid)
update public.bookings
set
  payment_status = public.compute_payment_status(is_paid, paid_amount, total_amount),
  payment_backfilled_at = now()
where payment_status is null;

insert into public.booking_status_log (
  booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
)
select
  b.booking_id,
  'payment_status',
  null,
  b.payment_status,
  'phase2_backfill',
  'initial_payment_derivation',
  jsonb_build_object(
    'is_paid', b.is_paid,
    'paid_amount', b.paid_amount,
    'total_amount', b.total_amount
  )
from public.bookings b
where b.payment_backfilled_at >= now() - interval '5 minutes'
  and b.payment_status is not null;

-- ============================================================
-- 11. Status sync + payment guard trigger (after backfill)
-- ============================================================
drop trigger if exists bookings_before_update_sync_trg on public.bookings;
create trigger bookings_before_update_sync_trg
before update on public.bookings
for each row execute function public.bookings_before_update_sync();
