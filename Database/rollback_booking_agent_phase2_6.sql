-- Rollback Phase 2.6 supplier ops tables (does not drop hotels or booking_tasks columns)

delete from public.arcadia_system_config
where config_key in ('booking_supplier_ops', 'booking_task_reminder_policy');

drop table if exists public.booking_task_reminder_log;
drop table if exists public.booking_supplier_responses;
drop table if exists public.booking_supplier_drafts;
