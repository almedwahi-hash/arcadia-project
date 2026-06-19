-- Arcadia Tourism — B2B group rates, partners, outreach, quote offers
-- Apply after supabase_schema_arcadia_sales_automation.sql (shares set_updated_at).
-- Write path: n8n service_role. Optional anon SELECT on group_rates for read-only tools.

create extension if not exists "pgcrypto";

-- Reuse updated_at trigger if sales schema already applied
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- =========================
-- Group rates (15–40 pax bands — not covered by Pricing Engine FIT)
-- =========================
create table if not exists public.group_rates (
  rate_id uuid primary key default gen_random_uuid(),
  destination text not null,              -- KZ, RU, ...
  city text not null,                     -- Almaty, Moscow, ...
  nights int not null check (nights > 0),
  pax_min int not null check (pax_min > 0),
  pax_max int not null check (pax_max >= pax_min),
  tier text not null default 'standard' check (tier in ('standard', 'premium')),
  net_pp_usd numeric(10, 2) not null,
  currency text not null default 'USD',
  season_start date,
  season_end date,
  includes_json jsonb not null default '{}'::jsonb,
  status text not null default 'active' check (status in ('active', 'draft', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists group_rates_lookup_idx
  on public.group_rates (destination, city, nights, status)
  where status = 'active';

drop trigger if exists group_rates_set_updated_at on public.group_rates;
create trigger group_rates_set_updated_at
before update on public.group_rates
for each row execute function public.set_updated_at();

-- =========================
-- B2B partners (GCC / Asia outreach CRM)
-- =========================
create table if not exists public.b2b_partners (
  partner_id uuid primary key default gen_random_uuid(),
  company_name text not null,
  country text,
  email text,
  website text,
  contact_name text,
  market text,                            -- GCC, CIS, EU, ...
  group_focused boolean not null default true,
  tier text default 'prospect' check (tier in ('prospect', 'active', 'strategic', 'inactive')),
  status text not null default 'new' check (status in ('new', 'contacted', 'quoted', 'negotiating', 'won', 'lost', 'paused')),
  last_contact_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists b2b_partners_status_idx on public.b2b_partners (status);
create index if not exists b2b_partners_email_idx on public.b2b_partners (lower(email)) where email is not null;

drop trigger if exists b2b_partners_set_updated_at on public.b2b_partners;
create trigger b2b_partners_set_updated_at
before update on public.b2b_partners
for each row execute function public.set_updated_at();

-- =========================
-- Outreach log (email / WhatsApp correspondence)
-- =========================
create table if not exists public.outreach_log (
  log_id uuid primary key default gen_random_uuid(),
  partner_id uuid references public.b2b_partners(partner_id) on delete set null,
  channel text not null check (channel in ('email', 'whatsapp', 'telegram', 'linkedin', 'other')),
  direction text not null check (direction in ('outbound', 'inbound')),
  subject text,
  body_preview text,
  sent_at timestamptz not null default now(),
  status text not null default 'sent' check (status in ('draft', 'sent', 'delivered', 'opened', 'replied', 'bounced', 'failed')),
  follow_up_date date,
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists outreach_log_partner_sent_idx
  on public.outreach_log (partner_id, sent_at desc);
create index if not exists outreach_log_follow_up_idx
  on public.outreach_log (follow_up_date) where follow_up_date is not null;

-- =========================
-- Quote offers (FIT + group — structured archive for BD)
-- =========================
create table if not exists public.quote_offers (
  offer_id uuid primary key default gen_random_uuid(),
  quote_ref text unique,
  partner_id uuid references public.b2b_partners(partner_id) on delete set null,
  offer_type text not null check (offer_type in ('fit', 'group')),
  payload jsonb not null default '{}'::jsonb,
  total_usd numeric(12, 2),
  pdf_path text,
  status text not null default 'draft' check (status in ('draft', 'sent', 'accepted', 'expired', 'revised', 'cancelled')),
  valid_until date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists quote_offers_partner_idx on public.quote_offers (partner_id, created_at desc);
create index if not exists quote_offers_ref_idx on public.quote_offers (quote_ref) where quote_ref is not null;

drop trigger if exists quote_offers_set_updated_at on public.quote_offers;
create trigger quote_offers_set_updated_at
before update on public.quote_offers
for each row execute function public.set_updated_at();

-- =========================
-- Seed: Almaty 4N group tiers (example — manager approval before send)
-- Matches deliverables/example-group-offer-20pax-almaty-ar.md
-- =========================
insert into public.group_rates (
  destination, city, nights, pax_min, pax_max, tier, net_pp_usd, currency,
  season_start, season_end, includes_json, status
)
select v.destination, v.city, v.nights, v.pax_min, v.pax_max, v.tier, v.net_pp_usd, v.currency,
       v.season_start::date, v.season_end::date, v.includes_json::jsonb, v.status
from (values
  (
    'KZ', 'Almaty', 4, 15, 19, 'standard', 745.00, 'USD',
    '2026-06-01', '2026-10-31',
    '{"program_days":5,"itinerary_source":"itineraries.notes_ar=nights:4","ground_only":true,"hotel":"4★ downtown — Resident City or equivalent","vehicle":"Coaster 20-seat","guide":"Arabic licensed — 8h/day","meals":"daily breakfast + 2 halal lunches + 2 halal dinners","entrances":["Kok-Tobe","Shymbulak seasonal","Medeu cable car","Oi-Qaraghay","Bear Valley / Ayusai"],"optional_extras":["Charyn Canyon","Kolsai Lakes","Kaindy Lake"],"extras_note":"Far destinations quoted separately — not in base net rates","min_pax":15,"deposit_pct":30,"balance_days_before":14}',
    'active'
  ),
  (
    'KZ', 'Almaty', 4, 20, 29, 'standard', 685.00, 'USD',
    '2026-06-01', '2026-10-31',
    '{"program_days":5,"itinerary_source":"itineraries.notes_ar=nights:4","ground_only":true,"hotel":"4★ downtown — Resident City or equivalent","vehicle":"Coaster / mid-bus","guide":"Arabic licensed — 8h/day","meals":"daily breakfast + 2 halal lunches + 2 halal dinners","entrances":["Kok-Tobe","Shymbulak seasonal","Medeu cable car","Oi-Qaraghay","Bear Valley / Ayusai"],"optional_extras":["Charyn Canyon","Kolsai Lakes","Kaindy Lake"],"extras_note":"Far destinations quoted separately — not in base net rates","min_pax":15,"deposit_pct":30,"balance_days_before":14}',
    'active'
  ),
  (
    'KZ', 'Almaty', 4, 30, 40, 'standard', 625.00, 'USD',
    '2026-06-01', '2026-10-31',
    '{"program_days":5,"itinerary_source":"itineraries.notes_ar=nights:4","ground_only":true,"hotel":"4★ downtown — Resident City or equivalent","vehicle":"Mercedes 49-seat","guide":"Arabic licensed — 8h/day","meals":"daily breakfast + 2 halal lunches + 2 halal dinners","entrances":["Kok-Tobe","Shymbulak seasonal","Medeu cable car","Oi-Qaraghay","Bear Valley / Ayusai"],"optional_extras":["Charyn Canyon","Kolsai Lakes","Kaindy Lake"],"extras_note":"Far destinations quoted separately — not in base net rates","min_pax":15,"deposit_pct":30,"balance_days_before":14}',
    'active'
  )
) as v(destination, city, nights, pax_min, pax_max, tier, net_pp_usd, currency, season_start, season_end, includes_json, status)
where not exists (
  select 1 from public.group_rates g
  where g.destination = 'KZ' and g.city = 'Almaty' and g.nights = 4 and g.pax_min = 15
);

insert into public.b2b_partners (
  company_name, country, email, website, contact_name, market, group_focused, tier, status, notes
)
select v.company_name, v.country, v.email, v.website, v.contact_name, v.market, v.group_focused, v.tier, v.status, v.notes
from (values (
  'Tabeer Tours', 'UAE', 'inquiries@tabeertours.com', 'https://www.tabeertours.com/',
  'BD Team', 'GCC', true, 'prospect', 'contacted',
  'Example partner from example-group-offer-20pax-almaty-ar.md — Dubai, group-focused.'
)) as v(company_name, country, email, website, contact_name, market, group_focused, tier, status, notes)
where not exists (
  select 1 from public.b2b_partners p where lower(p.company_name) = lower('Tabeer Tours')
);

-- =========================
-- RLS posture
-- n8n: use service_role (bypasses RLS). Do NOT commit service_role to git.
-- Optional: grant anon SELECT on group_rates only for ai-quote.mjs / public rate lookup.
-- =========================
alter table public.group_rates enable row level security;
alter table public.b2b_partners enable row level security;
alter table public.outreach_log enable row level security;
alter table public.quote_offers enable row level security;

revoke all on public.group_rates from anon, authenticated;
revoke all on public.b2b_partners from anon, authenticated;
revoke all on public.outreach_log from anon, authenticated;
revoke all on public.quote_offers from anon, authenticated;

-- Optional read-only for group_rates (uncomment if ai-quote uses anon key):
-- grant select on public.group_rates to anon;
-- create policy group_rates_anon_select on public.group_rates
--   for select to anon using (status = 'active');
