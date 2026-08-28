-- Rollback Phase 2.6 UAT confirmation_ref protection

drop trigger if exists booking_tasks_guard_confirmation_ref on public.booking_tasks;
drop function if exists public.guard_booking_task_confirmation_ref();
drop function if exists public.override_task_confirmation_ref(uuid, text, text, text);
