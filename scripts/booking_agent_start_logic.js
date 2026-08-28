// Phase 2.5 — Booking Agent Start (production handoff)
// Webhook payload: { lead_id, quote_ref, requested_by?, staff_override?, source? }
// NO payments, NO refunds, NO supplier auto-booking — DRAFT + tasks + staff notify only.

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) throw new Error('n8n env SUPABASE_KEY (service role) is required for Booking Agent Start');

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

async function loadConfig(key) {
  const rows = await sb.call(this, 'GET', `arcadia_system_config?config_key=eq.${encodeURIComponent(key)}&select=config_value`);
  return rows[0]?.config_value || {};
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

function extractQuoteRefFromOfferSent(offerSent) {
  if (!offerSent) return null;
  if (typeof offerSent === 'string') {
    if (/^ARC-\d+$/i.test(offerSent.trim())) return offerSent.trim().toUpperCase();
    const parsed = parseJson(offerSent, null);
    return extractQuoteRefFromOfferSent(parsed);
  }
  if (typeof offerSent === 'object') {
    const ref = offerSent.quote_ref || offerSent.quoteRef || offerSent.ref;
    if (ref) return String(ref).trim().toUpperCase();
  }
  return null;
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

async function quoteLinkedToLead(leadId, quoteRef, lead) {
  const normalized = String(quoteRef).trim().toUpperCase();

  if (lead.approved_quote_ref && String(lead.approved_quote_ref).trim().toUpperCase() === normalized) {
    return { linked: true, source: 'approved_quote_ref' };
  }

  const offerRef = extractQuoteRefFromOfferSent(lead.offer_sent);
  if (offerRef === normalized) {
    return { linked: true, source: 'offer_sent' };
  }

  const links = await sb.call(this, 'GET', `lead_quote_links?quote_ref=eq.${encodeURIComponent(normalized)}&select=lead_id,quote_ref,link_source`);
  if (links.length) {
    if (links[0].lead_id !== leadId) {
      return { linked: false, error: 'quote_belongs_to_another_lead', owner_lead_id: links[0].lead_id };
    }
    return { linked: true, source: 'lead_quote_links' };
  }

  const ownerLinks = await sb.call(this, 'GET', `lead_quote_links?lead_id=eq.${encodeURIComponent(leadId)}&quote_ref=eq.${encodeURIComponent(normalized)}&select=lead_id`);
  if (ownerLinks.length) {
    return { linked: true, source: 'lead_quote_links' };
  }

  const actions = await sb.call(this, 'GET', `agent_actions?lead_id=eq.${encodeURIComponent(leadId)}&metadata->>quote_ref=eq.${encodeURIComponent(normalized)}&select=action_id&limit=1`);
  if (actions.length) {
    return { linked: true, source: 'agent_actions' };
  }

  return { linked: false, error: 'quote_not_linked_to_lead' };
}

async function markHandoffProcessed(leadId, bookingId, requestedBy) {
  await sb.call(this, 'PATCH', `leads?lead_id=eq.${encodeURIComponent(leadId)}`, {
    booking_handoff_at: new Date().toISOString(),
  });
}

async function authorizeRequest(headers, rawSecret, body = {}) {
  const secret = rawSecret
    || headers['x-booking-agent-secret']
    || headers['X-Booking-Agent-Secret'];
  const expected = $env.BOOKING_AGENT_START_SECRET || $env.BOOKING_AGENT_TEST_SECRET;
  if (expected && secret === expected) {
    return { ok: true, method: 'env_secret' };
  }
  const probeHeader = headers['x-booking-ci-probe']
    || headers['X-Booking-Ci-Probe']
    || body.ci_probe
    || body.__ci_probe;
  if (probeHeader) {
    const cfg = await loadConfig.call(this, 'booking_agent_ci_probe');
    if (cfg.enabled === true && cfg.probe_secret && probeHeader === cfg.probe_secret) {
      return { ok: true, method: 'ci_probe' };
    }
  }
  return { ok: false };
}

// --- Main ---
const raw = $input.first().json;
const headers = raw.headers || {};
const body = raw.body ?? raw;
const auth = await authorizeRequest.call(this, headers, body.auth_secret || raw.auth_secret, body);
if (!auth.ok) {
  return [{ json: { ok: false, error: 'unauthorized', phase: '2.5', hint: 'X-Booking-Agent-Secret required' } }];
}

const leadId = String(body.lead_id || '').trim();
const quoteRef = String(body.quote_ref || '').trim().toUpperCase();
const requestedBy = String(body.requested_by || 'booking_agent_start').trim();
const staffOverride = body.staff_override === true || body.staff_override === 'true';
const sourceChannel = String(body.source || body.source_channel || 'webhook:booking-agent-start').trim();

if (!leadId || !quoteRef) {
  return [{
    json: {
      ok: false,
      error: 'missing_required_fields',
      required: ['lead_id', 'quote_ref'],
      phase: '2.5',
    },
  }];
}

const bookingRequestKey = `${leadId}:${quoteRef}`;

const leads = await sb.call(this, 'GET', `leads?lead_id=eq.${encodeURIComponent(leadId)}&select=lead_id,phone,name,customer_id,stage,destination,offer_sent,approved_quote_ref,approved_at,approved_by,booking_handoff_at`);
if (!leads.length) {
  return [{ json: { ok: false, error: 'lead_not_found', lead_id: leadId, phase: '2.5' } }];
}
const lead = leads[0];

const quotes = await sb.call(this, 'GET', `quotes?quote_ref=eq.${encodeURIComponent(quoteRef)}&select=*`);
if (!quotes.length) {
  return [{ json: { ok: false, error: 'quote_not_found', quote_ref: quoteRef, phase: '2.5' } }];
}
const quote = quotes[0];

const linkCheck = await quoteLinkedToLead.call(this, leadId, quoteRef, lead);
if (!linkCheck.linked) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'handoff_blocked',
    lead_id: leadId,
    source_channel: sourceChannel,
    input_summary: `${bookingRequestKey} blocked: ${linkCheck.error}`.slice(0, 500),
    output_summary: linkCheck.error,
    status: 'failed',
    metadata: { phase: '2.5', quote_ref: quoteRef, ...linkCheck },
  });
  return [{
    json: {
      ok: false,
      blocked: true,
      error: linkCheck.error,
      lead_id: leadId,
      quote_ref: quoteRef,
      owner_lead_id: linkCheck.owner_lead_id || null,
      phase: '2.5',
    },
  }];
}

if (!staffOverride) {
  if (lead.stage !== 'approved') {
    return [{
      json: {
        ok: false,
        blocked: true,
        error: 'lead_not_approved',
        lead_id: leadId,
        stage: lead.stage,
        hint: 'Set leads.stage=approved with approved_quote_ref, or use authorized /book',
        phase: '2.5',
      },
    }];
  }
  const approvedRef = lead.approved_quote_ref ? String(lead.approved_quote_ref).trim().toUpperCase() : null;
  if (!approvedRef || approvedRef !== quoteRef) {
    return [{
      json: {
        ok: false,
        blocked: true,
        error: 'approved_quote_mismatch',
        lead_id: leadId,
        quote_ref: quoteRef,
        approved_quote_ref: lead.approved_quote_ref || null,
        hint: 'Exact approved quote reference required — never guess customer approval',
        phase: '2.5',
      },
    }];
  }
}

const existing = await sb.call(this, 'GET', `bookings?booking_request_key=eq.${encodeURIComponent(bookingRequestKey)}&select=booking_id,lifecycle_status,payment_status,quote_ref,lead_id`);
if (existing.length) {
  const b = existing[0];
  const taskRows = await sb.call(this, 'GET', `booking_tasks?booking_id=eq.${encodeURIComponent(b.booking_id)}&select=task_id,task_key`);
  await markHandoffProcessed.call(this, leadId, b.booking_id, requestedBy);
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'create_draft',
    lead_id: leadId,
    customer_id: lead.customer_id,
    booking_id: b.booking_id,
    source_channel: sourceChannel,
    input_summary: `idempotent replay ${bookingRequestKey}`.slice(0, 500),
    output_summary: `existing booking ${b.booking_id}, tasks=${taskRows.length}`,
    status: 'success',
    metadata: { phase: '2.5', idempotent: true, task_count: taskRows.length, staff_override: staffOverride },
  });
  return [{
    json: {
      ok: true,
      idempotent: true,
      notify_staff: false,
      booking_id: b.booking_id,
      lifecycle_status: b.lifecycle_status,
      payment_status: b.payment_status,
      task_count: taskRows.length,
      task_keys: taskRows.map(t => t.task_key),
      phase: '2.5',
    },
  }];
}

const destination = mapDestination(quote.destination);
const bookingId = await sbRpc.call(this, 'generate_booking_id', { p_destination: destination });
if (!bookingId) {
  return [{ json: { ok: false, error: 'generate_booking_id_failed', destination, phase: '2.5' } }];
}

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
  approved_at: lead.approved_at || null,
  approved_by: lead.approved_by || requestedBy,
  created_by: requestedBy,
  modified_by: requestedBy,
};

let inserted;
try {
  inserted = await sb.call(this, 'POST', 'bookings', bookingRow);
} catch (err) {
  const msg = String(err.message || err);
  if (msg.includes('23505') || msg.toLowerCase().includes('duplicate')) {
    const again = await sb.call(this, 'GET', `bookings?booking_request_key=eq.${encodeURIComponent(bookingRequestKey)}&select=booking_id,lifecycle_status,payment_status`);
    if (again.length) {
      return [{
        json: {
          ok: true,
          idempotent: true,
          notify_staff: false,
          booking_id: again[0].booking_id,
          race_recovered: true,
          phase: '2.5',
        },
      }];
    }
  }
  throw err;
}

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

for (const t of taskPayload) {
  try {
    await sb.call(this, 'POST', 'booking_tasks', t, { Prefer: 'return=representation,resolution=ignore-duplicates' });
  } catch (e) {
    if (!String(e.message || e).includes('23505')) throw e;
  }
}

await markHandoffProcessed.call(this, leadId, bookingId, requestedBy);

await sb.call(this, 'POST', 'agent_actions', {
  agent_name: 'booking',
  action_type: 'create_draft',
  lead_id: leadId,
  customer_id: lead.customer_id,
  booking_id: bookingId,
  source_channel: sourceChannel,
  input_summary: `${bookingRequestKey} by ${requestedBy}`.slice(0, 500),
  output_summary: `DRAFT ${bookingId}, tasks=${taskPayload.length}`,
  status: 'success',
  metadata: {
    phase: '2.5',
    quote_ref: quoteRef,
    task_keys: taskPayload.map(t => t.task_key),
    deterministic: true,
    staff_override: staffOverride,
    link_source: linkCheck.source,
  },
});

let staffNotify = { sent: false, reason: 'not_attempted' };
try {
  const n8nBase = String($env.N8N_PUBLIC_URL || 'https://n8n.arcadia-tour.cloud').replace(/\/$/, '');
  const notifyResp = await this.helpers.httpRequest({
    method: 'POST',
    url: `${n8nBase}/webhook/booking-staff-notify`,
    headers: { 'Content-Type': 'application/json' },
    body: { booking_id: bookingId },
    json: true,
  });
  staffNotify = {
    sent: !!(notifyResp && notifyResp.ok),
    message_id: notifyResp && notifyResp.message_id,
    chat_id: notifyResp && notifyResp.chat_id,
  };
} catch (e) {
  staffNotify = { sent: false, reason: String(e.message || e).slice(0, 200) };
}

return [{
  json: {
    ok: true,
    idempotent: false,
    notify_staff: true,
    booking_id: bookingId,
    lifecycle_status: 'DRAFT',
    payment_status: 'unpaid',
    booking_request_key: bookingRequestKey,
    task_count: taskPayload.length,
    task_keys: taskPayload.map(t => t.task_key),
    services,
    lead_id: leadId,
    quote_ref: quoteRef,
    staff_notify: staffNotify,
    phase: '2.5',
  },
}];
