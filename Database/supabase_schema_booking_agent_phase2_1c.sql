-- Arcadia Tourism — Booking Agent Phase 2.1c (idempotency + INSERT audit + task_key docs)
-- Apply after phase2_1 / phase2_1b. Rollback: Database/rollback_booking_agent_phase2_1c.sql

-- ============================================================
-- 1. Booking-level idempotency (race-safe backstop for webhooks)
-- ============================================================
alter table public.bookings
  add column if not exists booking_request_key text;

comment on column public.bookings.booking_request_key is
  'Deterministic idempotency key e.g. {lead_id}:{quote_ref}. NULL for legacy rows.';

create unique index if not exists bookings_booking_request_key_uidx
  on public.bookings (booking_request_key)
  where booking_request_key is not null;

-- ============================================================
-- 2. booking_tasks — corrected deterministic task_key rules (Phase 2.2 generator)
-- ============================================================
comment on table public.booking_tasks is
  'Operational tasks per booking. task_key must be deterministic — same payload => same keys.

  Patterns (segment_index / tour_index are 1-based):
    hotel:{city_slug}:{segment_index}
    airport:{city_slug}:arrival
    airport:{city_slug}:departure
    tour:{city_slug}:{tour_index}
    train:{from_slug}-{to_slug}:{segment_index}
    intercity_transfer:{from_slug}-{to_slug}:{segment_index}
    guide:{city_slug}:{segment_index}
    other:{slug}:{index}

  city_slug = lowercase ASCII, spaces -> underscore.
  Repeated city visits use distinct segment_index (e.g. Moscow segment 1 vs 3).
  Multiple trains/transfers on same route increment segment_index.';

-- ============================================================
-- 3. INSERT audit trigger — initial lifecycle + payment_status
-- ============================================================
create or replace function public.bookings_after_insert_audit()
returns trigger language plpgsql as $$
begin
  if new.lifecycle_status is not null then
    insert into public.booking_status_log (
      booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
    ) values (
      new.booking_id, 'lifecycle_status', null, new.lifecycle_status,
      coalesce(nullif(new.created_by, ''), 'system'),
      'initial_insert',
      jsonb_build_object(
        'source', coalesce(new.booking_source, 'unknown'),
        'booking_request_key', new.booking_request_key
      )
    );
  end if;

  if new.payment_status is not null then
    insert into public.booking_status_log (
      booking_id, field_changed, old_value, new_value, changed_by, reason, metadata
    ) values (
      new.booking_id, 'payment_status', null, new.payment_status,
      coalesce(nullif(new.created_by, ''), 'system'),
      'initial_insert',
      jsonb_build_object(
        'paid_amount', new.paid_amount,
        'is_paid', new.is_paid,
        'total_amount', new.total_amount
      )
    );
  end if;

  return new;
end;
$$;

drop trigger if exists bookings_after_insert_audit_trg on public.bookings;
create trigger bookings_after_insert_audit_trg
after insert on public.bookings
for each row execute function public.bookings_after_insert_audit();

-- ============================================================
-- 4. Payment backfill anomaly flag (report only — no value changes)
-- ============================================================
insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'payment_backfill_needs_review',
  '{
    "flagged_at": "2026-08-28",
    "reason": "legacy is_paid=true inconsistent with paid_amount=0 on 4/8 rows",
    "booking_ids": ["KA-2026-116","PO-2026-001","RU-2026-002","RU-2026-006"],
    "note": "compute_payment_status prioritizes paid_amount; do not invent payment state"
  }'::jsonb,
  'Legacy payment backfill anomalies — manual review required'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();

-- ============================================================
-- 5. Booking ID sequence gap documentation (KA-2026-117)
-- ============================================================
insert into public.arcadia_system_config (config_key, config_value, description)
values (
  'booking_id_sequence_gaps',
  '{
    "gaps": [
      {
        "booking_id": "KA-2026-117",
        "consumed_by": "phase2_1_migration_verification",
        "consumed_at": "2026-08-28",
        "note": "generate_booking_id test — not a real booking. Next real ID: KA-2026-118"
      }
    ]
  }'::jsonb,
  'Documented booking_id counter gaps — never rewind counters'
)
on conflict (config_key) do update
  set config_value = excluded.config_value,
      description = excluded.description,
      updated_at = now();
