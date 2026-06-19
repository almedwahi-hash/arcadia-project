-- Update KZ/Almaty 4N B2B group_rates: city/nearby base only; Charyn/Kolsai/Kaindy as optional extras.
-- Run in Supabase SQL Editor after group_rates rows exist (service_role or postgres).
-- Source programme: itineraries notes_ar = nights:4 (derived from approved nights:5 days 1-5).

update public.group_rates
set includes_json = jsonb_build_object(
  'program_days', 5,
  'itinerary_source', 'itineraries.notes_ar=nights:4',
  'ground_only', true,
  'hotel', '4★ downtown — Resident City or equivalent',
  'guide', 'Arabic licensed — 8h/day',
  'meals', 'daily breakfast + 2 halal lunches + 2 halal dinners',
  'entrances', jsonb_build_array(
    'Kok-Tobe',
    'Shymbulak seasonal',
    'Medeu cable car',
    'Oi-Qaraghay',
    'Bear Valley / Ayusai'
  ),
  'optional_extras', jsonb_build_array(
    'Charyn Canyon',
    'Kolsai Lakes',
    'Kaindy Lake'
  ),
  'extras_note', 'Far destinations quoted separately — not in base net rates',
  'min_pax', 15,
  'deposit_pct', 30,
  'balance_days_before', 14
) || (includes_json - 'entrances' - 'optional_extras' - 'extras_note' - 'itinerary_source')
where destination = 'KZ'
  and city = 'Almaty'
  and nights = 4
  and status = 'active';

-- Preserve vehicle per tier (merged from existing row)
update public.group_rates
set includes_json = includes_json || jsonb_build_object('vehicle', 'Coaster 20-seat')
where destination = 'KZ' and city = 'Almaty' and nights = 4 and pax_min = 15 and pax_max = 19;

update public.group_rates
set includes_json = includes_json || jsonb_build_object('vehicle', 'Coaster / mid-bus')
where destination = 'KZ' and city = 'Almaty' and nights = 4 and pax_min = 20 and pax_max = 29;

update public.group_rates
set includes_json = includes_json || jsonb_build_object('vehicle', 'Mercedes 49-seat')
where destination = 'KZ' and city = 'Almaty' and nights = 4 and pax_min = 30 and pax_max = 40;
