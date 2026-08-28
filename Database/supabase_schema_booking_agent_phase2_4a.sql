-- Arcadia Tourism — Booking Agent Phase 2.4A
-- Payment policy, booking_payments ledger, CONFIRMED gate, approval handler support
-- Rollback: Database/rollback_booking_agent_phase2_4a.sql

-- ============================================================
-- 1. Booking payment policy columns (nullable — no legacy backfill)
-- ============================================================
alter table public.bookings
  add column if not exists payment_requirement text,
  add column if not exists required_payment_amount numeric,
  add column if not exists manual_payment_approved_at timestamptz,
  add column if not exists manual_payment_approved_by text;

alter table public.bookings drop constraint if exists bookings_payment_requirement_check;
alter table public.bookings add constraint bookings_payment_requirement_check
  check (payment_requirement is null or payment_requirement = any (array[
    'full', 'deposit', 'pay_at_destination', 'manual'
  ]));

comment on column public.bookings.payment_requirement is
  'Agent payment gate: full | deposit | pay_at_destination | manual. NULL = legacy (no invented policy).';
comment on column public.bookings.required_payment_amount is
  'Minimum paid_amount (USD) for deposit policy. NULL unless payment_requirement=deposit.';

-- ============================================================
-- 2. Append-only booking_payments ledger
-- ============================================================
create table if not exists public.booking_payments (
  payment_id uuid primary key default gen_random_uuid(),
  booking_id text not null references public.bookings(booking_id) on delete cascade,
  idempotency_key text not null,
  amount_original numeric not null check (amount_original > 0),
  currency_original text not null default 'USD',
  amount_usd numeric not null check (amount_usd > 0),
  fx_rate numeric,
  fx_source text,
  payment_method text not null,
  reference text,
  notes text,
  recorded_by text not null,
  status text not null default 'success'
    check (status in ('success')),
  created_at timestamptz not null default now(),
  unique (idempotency_key)
);

create index if not exists booking_payments_booking_created_idx
  on public.booking_payments (booking_id, created_at desc);

comment on table public.booking_payments is
  'Append-only payment ledger — paid_amount derived via sync_booking_paid_amount(). Phase 2.4A: no refunds.';

-- ============================================================
-- 3. human_approval_queue — task_id for booking approvals
-- ============================================================
alter table public.human_approval_queue
  add column if not exists task_id uuid references public.booking_tasks(task_id) on delete set null;

-- ============================================================
-- 4. Skip policy + phase 2.4A test booking config
-- ============================================================
insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'booking_task_skip_policy',
  '{
    "auto_skip_allowed_types": ["tour", "other"],
    "auto_skip_allowed_reasons": ["customer_declined", "not_needed", "duplicate", "optional_declined"],
    "sensitive_required_types": ["hotel", "airport_transfer", "intercity_transfer", "train", "guide"],
    "sensitive_skip_reasons": ["supplier_unavailable", "customer_declined", "operational", "force_majeure"]
  }'::jsonb,
  'Required-task skip rules — sensitive types require manual_override approval'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

update public.arcadia_system_config
set config_value = jsonb_set(
      coalesce(config_value, '{}'::jsonb),
      '{phase24a_test_state}',
      '{
        "booking_id": "RU-2026-030",
        "lifecycle_status": "PENDING_PAYMENT",
        "payment_status": "unpaid",
        "paid_amount": 0,
        "payment_requirement": null,
        "required_payment_amount": null,
        "note": "Restore after Phase 2.4A canary"
      }'::jsonb,
      true
    ),
    updated_at = now()
where config_key = 'phase2_test_bookings';

-- ============================================================
-- 5. Payment policy satisfaction
-- ============================================================
create or replace function public.booking_payment_policy_satisfied(p_booking_id text)
returns boolean language plpgsql stable as $$
declare
  b record;
begin
  select payment_requirement, required_payment_amount, paid_amount, total_amount, manual_payment_approved_at
  into b
  from public.bookings
  where booking_id = p_booking_id;

  if not found then
    return false;
  end if;

  -- Legacy rows: no invented payment requirements
  if b.payment_requirement is null then
    return true;
  end if;

  case b.payment_requirement
    when 'full' then
      return coalesce(b.total_amount, 0) > 0
        and coalesce(b.paid_amount, 0) >= b.total_amount;
    when 'deposit' then
      return b.required_payment_amount is not null
        and coalesce(b.paid_amount, 0) >= b.required_payment_amount;
    when 'pay_at_destination' then
      return true;
    when 'manual' then
      return b.manual_payment_approved_at is not null;
    else
      return false;
  end case;
end;
$$;

-- ============================================================
-- 6. Sync paid_amount from ledger (trusted path)
-- ============================================================
create or replace function public.sync_booking_paid_amount(
  p_booking_id text,
  p_changed_by text default 'system:payment_sync'
)
returns numeric language plpgsql as $$
declare
  v_sum numeric;
begin
  select coalesce(sum(amount_usd), 0)
  into v_sum
  from public.booking_payments
  where booking_id = p_booking_id
    and status = 'success';

  perform set_config('arcadia.trusted_payment_update', '1', true);

  update public.bookings
  set
    paid_amount = v_sum,
    is_paid = case
      when coalesce(total_amount, 0) > 0 and v_sum >= total_amount then true
      else coalesce(is_paid, false)
    end,
    modified_by = coalesce(nullif(p_changed_by, ''), 'system:payment_sync')
  where booking_id = p_booking_id;

  return v_sum;
end;
$$;

-- ============================================================
-- 7. Record payment (idempotent, staff/system only)
-- ============================================================
create or replace function public.record_booking_payment(
  p_booking_id text,
  p_idempotency_key text,
  p_amount_original numeric,
  p_currency_original text,
  p_payment_method text,
  p_recorded_by text,
  p_amount_usd numeric default null,
  p_reference text default null,
  p_notes text default null,
  p_fx_rate numeric default null,
  p_fx_source text default null
)
returns jsonb language plpgsql as $$
declare
  v_existing record;
  v_payment_id uuid;
  v_amount_usd numeric;
  v_currency text;
  v_paid numeric;
  v_lifecycle text;
begin
  if p_amount_original is null or p_amount_original <= 0 then
    raise exception 'payment amount must be positive' using errcode = 'P0001';
  end if;

  if coalesce(p_idempotency_key, '') = '' then
    raise exception 'idempotency_key required' using errcode = 'P0001';
  end if;

  if not exists (select 1 from public.bookings where booking_id = p_booking_id) then
    raise exception 'booking not found: %', p_booking_id using errcode = 'P0001';
  end if;

  select *
  into v_existing
  from public.booking_payments
  where idempotency_key = p_idempotency_key;

  if found then
    v_paid := public.sync_booking_paid_amount(p_booking_id, p_recorded_by);
    v_lifecycle := public.recompute_booking_lifecycle(p_booking_id);
    return jsonb_build_object(
      'idempotent', true,
      'payment_id', v_existing.payment_id,
      'paid_amount', v_paid,
      'lifecycle_status', v_lifecycle
    );
  end if;

  v_currency := upper(coalesce(nullif(trim(p_currency_original), ''), 'USD'));

  if v_currency = 'USD' then
    v_amount_usd := p_amount_original;
  else
    if p_amount_usd is null or p_amount_usd <= 0 then
      raise exception 'non-USD payment requires explicit trusted amount_usd (no AI FX conversion)'
        using errcode = 'P0001';
    end if;
    v_amount_usd := p_amount_usd;
  end if;

  insert into public.booking_payments (
    booking_id, idempotency_key, amount_original, currency_original, amount_usd,
    fx_rate, fx_source, payment_method, reference, notes, recorded_by
  ) values (
    p_booking_id, p_idempotency_key, p_amount_original, v_currency, v_amount_usd,
    p_fx_rate, p_fx_source, p_payment_method, p_reference, p_notes, p_recorded_by
  )
  returning payment_id into v_payment_id;

  insert into public.booking_status_log (
    booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
  )
  select
    p_booking_id,
    'paid_amount',
    coalesce(b.paid_amount, 0)::text,
    (coalesce(b.paid_amount, 0) + v_amount_usd)::text,
    p_recorded_by,
    'booking_payment_recorded',
    jsonb_build_object(
      'payment_id', v_payment_id,
      'idempotency_key', p_idempotency_key,
      'amount_original', p_amount_original,
      'currency_original', v_currency,
      'amount_usd', v_amount_usd,
      'payment_method', p_payment_method,
      'reference', p_reference
    )
  from public.bookings b
  where b.booking_id = p_booking_id;

  v_paid := public.sync_booking_paid_amount(p_booking_id, p_recorded_by);
  v_lifecycle := public.recompute_booking_lifecycle(p_booking_id);

  return jsonb_build_object(
    'idempotent', false,
    'payment_id', v_payment_id,
    'paid_amount', v_paid,
    'lifecycle_status', v_lifecycle,
    'payment_policy_satisfied', public.booking_payment_policy_satisfied(p_booking_id)
  );
end;
$$;

-- ============================================================
-- 8. Supplier price change approval (idempotent)
-- ============================================================
create or replace function public.get_supplier_price_threshold_pct()
returns numeric language plpgsql stable as $$
declare
  v_cfg jsonb;
  v_threshold numeric;
begin
  select config_value into v_cfg
  from public.arcadia_system_config
  where config_key = 'supplier_price_change_threshold_pct';

  if v_cfg is null then
    raise exception 'supplier_price_change_threshold_pct not configured' using errcode = 'P0001';
  end if;

  v_threshold := (v_cfg #>> '{}')::numeric;
  if v_threshold is null then
    v_threshold := (v_cfg->>'value')::numeric;
  end if;

  if v_threshold is null then
    raise exception 'supplier_price_change_threshold_pct not configured' using errcode = 'P0001';
  end if;

  return v_threshold;
end;
$$;

create or replace function public.maybe_create_supplier_price_change_approval(
  p_task_id uuid,
  p_proposed_cost numeric,
  p_requested_by text,
  p_reason text default null
)
returns jsonb language plpgsql as $$
declare
  v_task record;
  v_threshold numeric;
  v_quoted numeric;
  v_pct_change numeric;
  v_idem_key text;
  v_approval_id uuid;
  v_existing record;
begin
  if p_proposed_cost is null or p_proposed_cost <= 0 then
    raise exception 'proposed supplier cost must be positive' using errcode = 'P0001';
  end if;

  select * into v_task from public.booking_tasks where task_id = p_task_id;
  if not found then
    raise exception 'task not found' using errcode = 'P0001';
  end if;

  v_quoted := coalesce(
    v_task.quoted_cost_usd,
    nullif(v_task.metadata->>'quoted_cost', '')::numeric,
    0
  );

  if v_quoted <= 0 then
    update public.booking_tasks
    set metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object('cost_review_required', true),
        updated_at = now()
    where task_id = p_task_id;

    return jsonb_build_object(
      'action', 'cost_review_required',
      'baseline_available', false,
      'task_id', p_task_id
    );
  end if;

  v_threshold := public.get_supplier_price_threshold_pct();
  v_pct_change := ((p_proposed_cost - v_quoted) / v_quoted) * 100;

  if v_pct_change <= v_threshold then
    return jsonb_build_object(
      'action', 'within_threshold',
      'approval_required', false,
      'pct_change', v_pct_change,
      'threshold_pct', v_threshold
    );
  end if;

  v_idem_key := format('supplier_price_change:%s:%s', p_task_id, round(p_proposed_cost::numeric, 2));

  select approval_id, status
  into v_existing
  from public.human_approval_queue
  where action_type = 'supplier_price_change'
    and booking_id = v_task.booking_id
    and idempotency_key = v_idem_key
  limit 1;

  if found then
    return jsonb_build_object(
      'action', 'approval_exists',
      'idempotent', true,
      'approval_id', v_existing.approval_id,
      'status', v_existing.status
    );
  end if;

  insert into public.human_approval_queue (
    action_type, booking_id, task_id, payload, reason, status,
    requested_by_agent, idempotency_key
  ) values (
    'supplier_price_change',
    v_task.booking_id,
    p_task_id,
    jsonb_build_object(
      'task_id', p_task_id,
      'task_key', v_task.task_key,
      'task_type', v_task.task_type,
      'quoted_cost_usd', v_quoted,
      'proposed_cost_usd', p_proposed_cost,
      'old_cost_usd', v_task.supplier_cost_usd,
      'pct_change', v_pct_change,
      'threshold_pct', v_threshold
    ),
    coalesce(p_reason, format('Supplier cost +%.1f%% exceeds threshold %.1f%%', v_pct_change, v_threshold)),
    'pending',
    p_requested_by,
    v_idem_key
  )
  returning approval_id into v_approval_id;

  update public.booking_tasks
  set metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'pending_supplier_price_change', true,
        'proposed_supplier_cost_usd', p_proposed_cost,
        'quoted_cost_usd', v_quoted
      ),
      updated_at = now()
  where task_id = p_task_id;

  perform public.recompute_booking_lifecycle(v_task.booking_id);

  return jsonb_build_object(
    'action', 'approval_created',
    'idempotent', false,
    'approval_id', v_approval_id,
    'pct_change', v_pct_change,
    'threshold_pct', v_threshold
  );
end;
$$;

-- ============================================================
-- 9. Resolve booking approval (staff/system)
-- ============================================================
create or replace function public.resolve_booking_approval(
  p_approval_id uuid,
  p_decision text,
  p_resolved_by text,
  p_reason text default null
)
returns jsonb language plpgsql as $$
declare
  v_appr record;
  v_task record;
  v_proposed numeric;
  v_lifecycle text;
begin
  if p_decision not in ('approved', 'rejected') then
    raise exception 'decision must be approved or rejected' using errcode = 'P0001';
  end if;

  select * into v_appr
  from public.human_approval_queue
  where approval_id = p_approval_id
  for update;

  if not found then
    raise exception 'approval not found' using errcode = 'P0001';
  end if;

  if v_appr.status <> 'pending' then
    return jsonb_build_object(
      'idempotent', true,
      'approval_id', p_approval_id,
      'status', v_appr.status,
      'already_resolved', true
    );
  end if;

  update public.human_approval_queue
  set
    status = case when p_decision = 'approved' then 'approved' else 'rejected' end,
    approved_by = p_resolved_by,
    resolved_at = now(),
    reason = coalesce(p_reason, reason)
  where approval_id = p_approval_id;

  if v_appr.action_type = 'supplier_price_change' and p_decision = 'approved' then
    v_proposed := (v_appr.payload->>'proposed_cost_usd')::numeric;
    if v_appr.task_id is not null and v_proposed is not null then
      update public.booking_tasks
      set
        supplier_cost_usd = v_proposed,
        metadata = coalesce(metadata, '{}'::jsonb)
          - 'pending_supplier_price_change'
          - 'proposed_supplier_cost_usd'
          || jsonb_build_object('supplier_price_change_approved_at', now(), 'approved_by', p_resolved_by),
        updated_at = now()
      where task_id = v_appr.task_id;
    end if;
  elsif v_appr.action_type = 'supplier_price_change' and p_decision = 'rejected' then
    if v_appr.task_id is not null then
      update public.booking_tasks
      set metadata = coalesce(metadata, '{}'::jsonb)
          - 'pending_supplier_price_change'
          - 'proposed_supplier_cost_usd'
          || jsonb_build_object('supplier_price_change_rejected_at', now(), 'rejected_by', p_resolved_by),
        updated_at = now()
      where task_id = v_appr.task_id;
    end if;
  elsif v_appr.action_type = 'manual_override' and p_decision = 'approved' then
    if (v_appr.payload->>'override_type') = 'required_task_skip' and v_appr.task_id is not null then
      select * into v_task from public.booking_tasks where task_id = v_appr.task_id;

      update public.booking_tasks
      set
        status = 'skipped',
        notes = coalesce(v_appr.payload->>'skip_reason', notes, 'skipped_via_manual_override'),
        metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object('skip_approved_by', p_resolved_by),
        updated_at = now()
      where task_id = v_appr.task_id;

      insert into public.booking_task_status_log (
        task_id, booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
      ) values (
        v_appr.task_id, v_task.booking_id, 'status', v_task.status, 'skipped', p_resolved_by,
        'manual_override_approved', jsonb_build_object('approval_id', p_approval_id)
      );
    elsif (v_appr.payload->>'override_type') = 'manual_payment' and v_appr.booking_id is not null then
      perform set_config('arcadia.trusted_payment_update', '1', true);
      update public.bookings
      set
        manual_payment_approved_at = now(),
        manual_payment_approved_by = p_resolved_by,
        modified_by = p_resolved_by
      where booking_id = v_appr.booking_id;
    end if;
  end if;

  if v_appr.booking_id is not null then
    v_lifecycle := public.recompute_booking_lifecycle(v_appr.booking_id);
  end if;

  return jsonb_build_object(
    'idempotent', false,
    'approval_id', p_approval_id,
    'action_type', v_appr.action_type,
    'decision', p_decision,
    'booking_id', v_appr.booking_id,
    'lifecycle_status', v_lifecycle
  );
end;
$$;

-- ============================================================
-- 10. Required-task skip approval request
-- ============================================================
create or replace function public.request_required_task_skip(
  p_task_id uuid,
  p_requested_by text,
  p_skip_reason text,
  p_idempotency_key text default null
)
returns jsonb language plpgsql as $$
declare
  v_task record;
  v_idem text;
  v_existing record;
  v_approval_id uuid;
begin
  select * into v_task from public.booking_tasks where task_id = p_task_id;
  if not found then
    raise exception 'task not found' using errcode = 'P0001';
  end if;

  if not coalesce(v_task.is_required, true) then
    raise exception 'task is optional — skip directly without approval' using errcode = 'P0001';
  end if;

  v_idem := coalesce(
    p_idempotency_key,
    format('manual_override:skip:%s:%s', p_task_id, coalesce(p_skip_reason, 'unspecified'))
  );

  select approval_id, status into v_existing
  from public.human_approval_queue
  where action_type = 'manual_override'
    and booking_id = v_task.booking_id
    and idempotency_key = v_idem
  limit 1;

  if found then
    return jsonb_build_object('idempotent', true, 'approval_id', v_existing.approval_id, 'status', v_existing.status);
  end if;

  insert into public.human_approval_queue (
    action_type, booking_id, task_id, payload, reason, status,
    requested_by_agent, idempotency_key
  ) values (
    'manual_override',
    v_task.booking_id,
    p_task_id,
    jsonb_build_object(
      'override_type', 'required_task_skip',
      'task_id', p_task_id,
      'task_key', v_task.task_key,
      'task_type', v_task.task_type,
      'skip_reason', p_skip_reason
    ),
    format('Required task skip approval: %s', coalesce(p_skip_reason, 'unspecified')),
    'pending',
    p_requested_by,
    v_idem
  )
  returning approval_id into v_approval_id;

  perform public.recompute_booking_lifecycle(v_task.booking_id);

  return jsonb_build_object('idempotent', false, 'approval_id', v_approval_id, 'pending', true);
end;
$$;

-- ============================================================
-- 11. Lifecycle recompute with CONFIRMED gate
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
  v_pending_approvals int;
  v_payment_ok boolean;
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

  -- CONFIRMED gate (Phase 2.4A)
  if v_new = 'PENDING_PAYMENT' then
    select count(*) into v_pending_approvals
    from public.human_approval_queue
    where booking_id = p_booking_id
      and status = 'pending'
      and action_type in ('supplier_price_change', 'booking_financial_commit', 'manual_override');

    v_payment_ok := public.booking_payment_policy_satisfied(p_booking_id);

    if v_payment_ok and v_pending_approvals = 0 then
      v_new := 'CONFIRMED';
    end if;
  end if;

  -- Downgrade from CONFIRMED if required tasks reopened
  if v_old = 'CONFIRMED' and v_open > 0 then
    if v_confirmed > 0 then
      v_new := 'PARTIALLY_CONFIRMED';
    else
      v_new := 'PENDING_SUPPLIER';
    end if;
  elsif v_old in ('CONFIRMED', 'IN_PROGRESS', 'COMPLETED') and v_new not in ('CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') then
    if v_old in ('IN_PROGRESS', 'COMPLETED') then
      v_new := v_old;
    end if;
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
-- 12. RLS on booking_payments
-- ============================================================
alter table public.booking_payments enable row level security;
revoke all on public.booking_payments from anon, authenticated;
