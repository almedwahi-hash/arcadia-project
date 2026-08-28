// Phase 2.2 — Deterministic Booking Agent (NO AI/LLM)
// Webhook payload: { lead_id, quote_ref, requested_by }
// Uses n8n env SUPABASE_URL + SUPABASE_KEY (service role) — same as Contract Processor.

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) {
  throw new Error('n8n env SUPABASE_KEY (service role) is required for Booking Agent Test');
}
const HDR = {
  apikey: KEY,
  Authorization: `Bearer ${KEY}`,
  'Content-Type': 'application/json',
  Prefer: 'return=representation',
};

async function sb(method, path, body, extraHeaders = {}) {
  const opts = {
    method,
    url: `${SB}/rest/v1/${path}`,
    headers: { ...HDR, ...extraHeaders },
    json: true,
  };
  if (body !== undefined) opts.body = body;
  return await this.helpers.httpRequest(opts);
}

async function sbRpc(fn, args) {
  const rows = await sb.call(this, 'POST', `rpc/${fn}`, args);
  return Array.isArray(rows) ? rows[0] : rows;
}

function slugify(name) {
  return String(name || 'unknown')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '') || 'unknown';
}

const DEST_MAP = { RU: 'russia', KZ: 'kazakhstan', UZ: 'uzbekistan', PO: 'poland', PL: 'poland' };

function mapDestination(code) {
  const c = String(code || '').trim().toUpperCase();
  return DEST_MAP[c] || String(code || '').toLowerCase();
}

function parseJson(val, fallback) {
  if (val == null) return fallback;
  if (typeof val === 'object') return val;
  try { return JSON.parse(val); } catch { return fallback; }
}

function buildTasks(quote) {
  const cities = parseJson(quote.cities, []);
  const packages = parseJson(quote.packages, []);
  const toursByCity = parseJson(quote.tours_by_city, []);
  const eco = packages.find(p => p.tier === 'eco') || packages[0] || {};
  const hotels = eco.hotels || [];

  const tasks = [];
  const routeCounts = {};

  function routeKey(from, to) {
    return `${slugify(from)}-${slugify(to)}`;
  }

  function nextRouteIndex(key) {
    routeCounts[key] = (routeCounts[key] || 0) + 1;
    return routeCounts[key];
  }

  // Hotels — one per city segment
  cities.forEach((city, idx) => {
    const seg = idx + 1;
    tasks.push({
      task_key: `hotel:${slugify(city)}:${seg}`,
      task_type: 'hotel',
      city,
      segment_index: seg,
      supplier_name: hotels[idx] || null,
      is_required: true,
      metadata: { tier: 'eco', segment: seg },
    });
  });

  // Airport arrival / departure
  if (cities.length > 0) {
    const first = cities[0];
    const last = cities[cities.length - 1];
    tasks.push({
      task_key: `airport:${slugify(first)}:arrival`,
      task_type: 'airport_transfer',
      city: first,
      segment_index: 1,
      is_required: true,
      metadata: { direction: 'arrival' },
    });
    tasks.push({
      task_key: `airport:${slugify(last)}:departure`,
      task_type: 'airport_transfer',
      city: last,
      segment_index: cities.length,
      is_required: true,
      metadata: { direction: 'departure' },
    });
  }

  // Intercity transfers between consecutive segments
  for (let i = 0; i < cities.length - 1; i++) {
    const from = cities[i];
    const to = cities[i + 1];
    const rk = routeKey(from, to);
    const segIdx = nextRouteIndex(rk);
    tasks.push({
      task_key: `intercity_transfer:${rk}:${segIdx}`,
      task_type: 'intercity_transfer',
      city: from,
      segment_index: segIdx,
      is_required: true,
      metadata: { from, to, leg: i + 1 },
    });
  }

  // Tours by city — tour_index within each city (aggregate tours_by_city entries per city slug)
  const tourCounts = {};
  for (const entry of toursByCity) {
    const city = entry.city;
    const count = Number(entry.tours) || 0;
    if (count <= 0 || !city) continue;
    const cs = slugify(city);
    for (let t = 1; t <= count; t++) {
      tourCounts[cs] = (tourCounts[cs] || 0) + 1;
      const tourIdx = tourCounts[cs];
      tasks.push({
        task_key: `tour:${cs}:${tourIdx}`,
        task_type: 'tour',
        city,
        segment_index: tourIdx,
        is_required: false,
        metadata: { tour_number: tourIdx, source: 'tours_by_city' },
      });
    }
  }

  return tasks;
}

function deriveServices(tasks) {
  const types = new Set(tasks.map(t => t.task_type));
  const services = [];
  if (types.has('hotel')) services.push('hotel');
  if (types.has('airport_transfer')) services.push('airport');
  if (types.has('tour')) services.push('tours');
  if (types.has('intercity_transfer')) services.push('intercity_transfer');
  if (types.has('train')) services.push('train');
  if (types.has('guide')) services.push('guide');
  return services;
}

function buildCityHotels(cities, hotels) {
  const out = {};
  cities.forEach((city, idx) => {
    if (hotels[idx]) out[city] = hotels[idx];
  });
  return out;
}

// --- Main ---
const raw = $input.first().json;
const headers = raw.headers || {};
const secret = headers['x-booking-agent-secret'] || headers['X-Booking-Agent-Secret'] || raw.auth_secret;
const expected = $env.BOOKING_AGENT_TEST_SECRET;
if (!expected || secret !== expected) {
  return [{ json: { ok: false, error: 'unauthorized', phase: '2.2', hint: 'X-Booking-Agent-Secret required' } }];
}

const body = raw.body ?? raw;
const leadId = String(body.lead_id || '').trim();
const quoteRef = String(body.quote_ref || '').trim();
const requestedBy = String(body.requested_by || 'booking_agent_test').trim();

if (!leadId || !quoteRef) {
  return [{
    json: {
      ok: false,
      error: 'missing_required_fields',
      required: ['lead_id', 'quote_ref'],
      phase: '2.2',
    },
  }];
}

const bookingRequestKey = `${leadId}:${quoteRef}`;

// 1) Exact lead validation
const leads = await sb.call(this, 'GET', `leads?lead_id=eq.${encodeURIComponent(leadId)}&select=lead_id,phone,name,customer_id,stage,destination`);
if (!leads.length) {
  return [{ json: { ok: false, error: 'lead_not_found', lead_id: leadId, phase: '2.2' } }];
}
const lead = leads[0];

// 2) Exact quote_ref validation
const quotes = await sb.call(this, 'GET', `quotes?quote_ref=eq.${encodeURIComponent(quoteRef)}&select=*`);
if (!quotes.length) {
  return [{ json: { ok: false, error: 'quote_not_found', quote_ref: quoteRef, phase: '2.2' } }];
}
const quote = quotes[0];

// 3) Idempotency pre-check
const existing = await sb.call(this, 'GET', `bookings?booking_request_key=eq.${encodeURIComponent(bookingRequestKey)}&select=booking_id,lifecycle_status,payment_status,quote_ref,lead_id`);
if (existing.length) {
  const b = existing[0];
  const taskRows = await sb.call(this, 'GET', `booking_tasks?booking_id=eq.${encodeURIComponent(b.booking_id)}&select=task_id,task_key`);
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'create_draft',
    lead_id: leadId,
    customer_id: lead.customer_id,
    booking_id: b.booking_id,
    source_channel: 'webhook:booking-agent-test',
    input_summary: `idempotent replay ${bookingRequestKey}`.slice(0, 500),
    output_summary: `existing booking ${b.booking_id}, tasks=${taskRows.length}`,
    status: 'success',
    metadata: { phase: '2.2', idempotent: true, task_count: taskRows.length },
  });
  return [{
    json: {
      ok: true,
      idempotent: true,
      booking_id: b.booking_id,
      lifecycle_status: b.lifecycle_status,
      payment_status: b.payment_status,
      task_count: taskRows.length,
      task_keys: taskRows.map(t => t.task_key),
      phase: '2.2',
    },
  }];
}

// 4) Generate booking_id
const destination = mapDestination(quote.destination);
const bookingId = await sbRpc.call(this, 'generate_booking_id', { p_destination: destination });
if (!bookingId) {
  return [{ json: { ok: false, error: 'generate_booking_id_failed', destination, phase: '2.2' } }];
}

// 5) Build booking + tasks
const cities = parseJson(quote.cities, []);
const packages = parseJson(quote.packages, []);
const eco = packages.find(p => p.tier === 'eco') || packages[0] || {};
const hotels = eco.hotels || [];
const tasks = buildTasks(quote);
const services = deriveServices(tasks);
const cityHotels = buildCityHotels(cities, hotels);

let customerName = lead.name;
if (!customerName && lead.customer_id) {
  const customers = await sb.call(this, 'GET', `customers?customer_id=eq.${lead.customer_id}&select=name`);
  if (customers.length) customerName = customers[0].name;
}

const bookingRow = {
  booking_id: bookingId,
  client_name: customerName || 'Guest',
  client_phone: lead.phone || null,
  guest_count: quote.adults || 1,
  destination,
  cities,
  trip_type: 'tourism',
  city_hotels: cityHotels,
  arrival_date: quote.check_in,
  departure_date: quote.check_out,
  days_count: quote.nights || null,
  services,
  number_of_tours: tasks.filter(t => t.task_type === 'tour').length,
  airport_pickup: true,
  total_amount: quote.total_usd,
  paid_amount: 0,
  is_paid: false,
  payment_method: 'company',
  status: 'pending',
  lifecycle_status: 'DRAFT',
  payment_status: 'unpaid',
  lead_id: leadId,
  customer_id: lead.customer_id || null,
  quote_ref: quoteRef,
  booking_request_key: bookingRequestKey,
  booking_source: 'booking_agent',
  created_by: requestedBy,
  modified_by: requestedBy,
};

let inserted;
try {
  inserted = await sb.call(this, 'POST', 'bookings', bookingRow);
} catch (err) {
  const msg = String(err.message || err);
  if (msg.includes('23505') || msg.toLowerCase().includes('duplicate')) {
    const again = await sb.call(this, 'GET', `bookings?booking_request_key=eq.${encodeURIComponent(bookingRequestKey)}&select=booking_id`);
    if (again.length) {
      return [{
        json: {
          ok: true,
          idempotent: true,
          booking_id: again[0].booking_id,
          race_recovered: true,
          phase: '2.2',
        },
      }];
    }
  }
  throw err;
}

const booking = Array.isArray(inserted) ? inserted[0] : inserted;

// 6) Insert tasks (idempotent via UNIQUE booking_id+task_key)
const taskPayload = tasks.map(t => ({
  booking_id: bookingId,
  task_key: t.task_key,
  task_type: t.task_type,
  city: t.city,
  segment_index: t.segment_index,
  supplier_name: t.supplier_name || null,
  is_required: t.is_required !== false,
  status: 'pending',
  metadata: t.metadata || {},
}));

let insertedTasks = [];
for (const t of taskPayload) {
  try {
    const row = await sb.call(this, 'POST', 'booking_tasks', t, { Prefer: 'return=representation,resolution=ignore-duplicates' });
    if (row && row.length) insertedTasks.push(row[0]);
  } catch (e) {
    // ignore duplicate task_key
    if (!String(e.message || e).includes('23505')) throw e;
  }
}

// 7) agent_actions log
await sb.call(this, 'POST', 'agent_actions', {
  agent_name: 'booking',
  action_type: 'create_draft',
  lead_id: leadId,
  customer_id: lead.customer_id,
  booking_id: bookingId,
  source_channel: 'webhook:booking-agent-test',
  input_summary: `${bookingRequestKey} by ${requestedBy}`.slice(0, 500),
  output_summary: `DRAFT ${bookingId}, tasks=${taskPayload.length}`,
  status: 'success',
  metadata: {
    phase: '2.2',
    quote_ref: quoteRef,
    task_keys: taskPayload.map(t => t.task_key),
    deterministic: true,
  },
});

// 8) Telegram — delegated to Arcadia - Booking Staff Notify (Phase 2.3)
let telegram = { sent: false, reason: 'delegated_to_staff_notify_workflow' };

return [{
  json: {
    ok: true,
    idempotent: false,
    booking_id: bookingId,
    lifecycle_status: 'DRAFT',
    payment_status: 'unpaid',
    booking_request_key: bookingRequestKey,
    task_count: taskPayload.length,
    task_keys: taskPayload.map(t => t.task_key),
    services,
    telegram,
    phase: '2.2',
  },
}];
