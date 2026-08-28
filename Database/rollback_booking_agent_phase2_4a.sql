-- Rollback Phase 2.4A — restores recompute_booking_lifecycle to Phase 2.3 behavior

drop function if exists public.request_required_task_skip(uuid, text, text, text);
drop function if exists public.resolve_booking_approval(uuid, text, text, text);
drop function if exists public.maybe_create_supplier_price_change_approval(uuid, numeric, text, text);
drop function if exists public.get_supplier_price_threshold_pct();
drop function if exists public.record_booking_payment(text, text, numeric, text, text, text, numeric, text, text, numeric, text);
drop function if exists public.sync_booking_paid_amount(text, text);
drop function if exists public.booking_payment_policy_satisfied(text);

drop table if exists public.booking_payments;

alter table public.human_approval_queue drop column if exists task_id;

alter table public.bookings
  drop constraint if exists bookings_payment_requirement_check,
  drop column if exists payment_requirement,
  drop column if exists required_payment_amount,
  drop column if exists manual_payment_approved_at,
  drop column if exists manual_payment_approved_by;

delete from public.arcadia_system_config where config_key = 'booking_task_skip_policy';

-- Phase 2.3 lifecycle recompute (no CONFIRMED gate)
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
