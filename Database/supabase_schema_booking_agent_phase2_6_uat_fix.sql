-- Arcadia Tourism — Phase 2.6 UAT defect fix (confirmation_ref protection)
-- UAT-DEF-002: prevent silent overwrite of confirmation_ref on confirmed tasks
-- Rollback: Database/rollback_booking_agent_phase2_6_uat_fix.sql

-- Trigger: block direct PATCH that changes a non-null confirmation_ref unless override session flag set
create or replace function public.guard_booking_task_confirmation_ref()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'UPDATE'
     and old.confirmation_ref is not null
     and new.confirmation_ref is distinct from old.confirmation_ref
     and coalesce(current_setting('arcadia.confirmation_ref_override', true), '') <> 'allowed' then
    raise exception 'confirmation_ref_conflict'
      using errcode = 'P0001',
            detail = format('existing=%s attempted=%s', old.confirmation_ref, new.confirmation_ref);
  end if;
  return new;
end;
$$;

drop trigger if exists booking_tasks_guard_confirmation_ref on public.booking_tasks;
create trigger booking_tasks_guard_confirmation_ref
  before update of confirmation_ref on public.booking_tasks
  for each row
  execute function public.guard_booking_task_confirmation_ref();

-- Audited override path for staff correction of wrong confirmation numbers
create or replace function public.override_task_confirmation_ref(
  p_task_id uuid,
  p_new_ref text,
  p_reason text,
  p_recorded_by text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_task public.booking_tasks%rowtype;
  v_old_ref text;
begin
  if p_new_ref is null or btrim(p_new_ref) = '' then
    raise exception 'new_confirmation_ref_required' using errcode = 'P0001';
  end if;
  if p_reason is null or btrim(p_reason) = '' then
    raise exception 'override_reason_required' using errcode = 'P0001';
  end if;
  if p_recorded_by is null or btrim(p_recorded_by) = '' then
    raise exception 'recorded_by_required' using errcode = 'P0001';
  end if;

  select * into v_task from public.booking_tasks where task_id = p_task_id for update;
  if not found then
    raise exception 'task_not_found' using errcode = 'P0001';
  end if;

  v_old_ref := v_task.confirmation_ref;
  if v_old_ref is null or btrim(v_old_ref) = '' then
    raise exception 'no_existing_confirmation_ref_to_override' using errcode = 'P0001';
  end if;
  if v_old_ref = btrim(p_new_ref) then
    return jsonb_build_object(
      'ok', true,
      'idempotent', true,
      'task_id', p_task_id,
      'confirmation_ref', v_old_ref
    );
  end if;

  perform set_config('arcadia.confirmation_ref_override', 'allowed', true);

  update public.booking_tasks
  set confirmation_ref = btrim(p_new_ref),
      updated_at = now(),
      metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object(
        'confirmation_ref_override', jsonb_build_object(
          'old_value', v_old_ref,
          'new_value', btrim(p_new_ref),
          'reason', btrim(p_reason),
          'recorded_by', btrim(p_recorded_by),
          'at', now()
        )
      )
  where task_id = p_task_id;

  insert into public.booking_task_status_log (
    task_id, booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
  ) values (
    p_task_id,
    v_task.booking_id,
    'confirmation_ref',
    v_old_ref,
    btrim(p_new_ref),
    btrim(p_recorded_by),
    btrim(p_reason),
    jsonb_build_object('source', 'override_task_confirmation_ref', 'override', true)
  );

  return jsonb_build_object(
    'ok', true,
    'idempotent', false,
    'action', 'confirmation_ref_override',
    'task_id', p_task_id,
    'old_confirmation_ref', v_old_ref,
    'new_confirmation_ref', btrim(p_new_ref)
  );
end;
$$;

comment on function public.override_task_confirmation_ref is
  'Authorized staff correction of supplier confirmation reference — fully audited; requires reason.';
