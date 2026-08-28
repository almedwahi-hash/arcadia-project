// Phase 2.6 — Supplier draft generation (deterministic, NO AI, NO auto-send)
// Webhook: { task_id, requested_by?, regenerate?: bool }
// Or test: { simulate, task_id, ... }

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) throw new Error('SUPABASE_KEY required');

const HDR = {
  apikey: KEY,
  Authorization: `Bearer ${KEY}`,
  'Content-Type': 'application/json',
  Prefer: 'return=representation',
};

async function sb(method, path, body, extra = {}) {
  const opts = { method, url: `${SB}/rest/v1/${path}`, headers: { ...HDR, ...extra }, json: true };
  if (body !== undefined) opts.body = body;
  return await this.helpers.httpRequest(opts);
}

async function loadConfig(key) {
  const rows = await sb.call(this, 'GET', `arcadia_system_config?config_key=eq.${encodeURIComponent(key)}&select=config_value`);
  return rows[0]?.config_value || {};
}

function parseJson(v, fb) {
  if (v == null) return fb;
  if (typeof v === 'object') return v;
  try { return JSON.parse(v); } catch { return fb; }
}

function normCity(c) {
  return String(c || '').trim();
}

function factsHash(obj) {
  return JSON.stringify(obj);
}

function simpleHash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h).toString(36);
}

async function lookupHotelContact(hotelName, city) {
  if (!hotelName) return null;
  const name = String(hotelName).trim();
  const c = normCity(city);
  let rows = await sb.call(this, 'GET', `hotels?Hotel_Name=ilike.${encodeURIComponent(name)}&City=ilike.${encodeURIComponent(c)}&select=Hotel_Name,City,Phone,Email,Supplier,Website&limit=1`);
  if (rows.length) return rows[0];
  rows = await sb.call(this, 'GET', `hotels?Hotel_Name=ilike.${encodeURIComponent(`%${name.split(' ')[0]}%`)}&City=ilike.${encodeURIComponent(c)}&select=Hotel_Name,City,Phone,Email,Supplier,Website&limit=1`);
  return rows[0] || null;
}

function segmentDates(booking, task, cities) {
  const seg = Number(task.segment_index) || 1;
  const idx = Math.max(0, seg - 1);
  const meta = task.metadata || {};
  if (meta.check_in && meta.check_out) {
    return { check_in: meta.check_in, check_out: meta.check_out, source: 'task.metadata' };
  }
  if (cities.length <= 1) {
    return { check_in: booking.arrival_date, check_out: booking.departure_date, source: 'booking.trip' };
  }
  return {
    check_in: booking.arrival_date,
    check_out: booking.departure_date,
    source: 'booking.trip_whole',
    note: `Multi-city trip — verify dates for ${task.city} segment ${seg}`,
  };
}

function buildHotelDraft({ booking, task, opsCfg, contact, dates, missing }) {
  const company = booking.company_name || opsCfg.company_name || 'Arcadia Tourism';
  const lines = [
    `${company} — Hotel Reservation Request`,
    '(DRAFT — staff review; NOT sent automatically)',
    '',
    `Booking reference: ${booking.booking_id}`,
    `Hotel: ${task.supplier_name || '—'}`,
    `City: ${task.city || '—'}`,
    `Check-in: ${dates.check_in || '—'}`,
    `Check-out: ${dates.check_out || '—'}`,
    `Guests: ${booking.guest_count || '—'} pax`,
    `Lead guest: ${booking.client_name || '—'}`,
    `Room: ${task.metadata?.room_type || 'standard (confirm with hotel)'}`,
    '',
    'Please confirm availability and provide confirmation reference.',
    '',
    company,
    opsCfg.booking_email ? `Email: ${opsCfg.booking_email}` : null,
    opsCfg.booking_phone ? `Phone: ${opsCfg.booking_phone}` : null,
  ].filter(Boolean);

  if (dates.note) lines.splice(8, 0, `Note: ${dates.note}`);
  if (contact) {
    lines.push('', '--- Known hotel contact (from directory) ---');
    if (contact.Phone) lines.push(`Tel: ${contact.Phone}`);
    if (contact.Email) lines.push(`Email: ${contact.Email}`);
    if (contact.Supplier) lines.push(`Supplier channel: ${contact.Supplier}`);
  }
  if (missing.length) {
    lines.push('', '⚠ Missing required information:');
    missing.forEach(m => lines.push(`- ${m}`));
  }

  return lines.join('\n');
}

function buildAirportDraft({ booking, task, opsCfg, missing }) {
  const company = booking.company_name || opsCfg.company_name || 'Arcadia Tourism';
  const dir = (task.metadata && task.metadata.direction) || 'transfer';
  const lines = [
    `${company} — Airport Transfer Request`,
    '(DRAFT — staff review; NOT sent automatically)',
    '',
    `Booking reference: ${booking.booking_id}`,
    `City: ${task.city || '—'}`,
    `Direction: ${dir}`,
    `Date: ${dir === 'arrival' ? booking.arrival_date : booking.departure_date}`,
    `Guests: ${booking.guest_count || '—'} pax`,
    `Lead guest: ${booking.client_name || '—'}`,
    '',
    'Please confirm driver/vehicle availability.',
    '',
    company,
    opsCfg.booking_phone ? `Phone: ${opsCfg.booking_phone}` : null,
  ].filter(Boolean);
  if (missing.length) {
    lines.push('', '⚠ Missing:', ...missing.map(m => `- ${m}`));
  }
  return lines.join('\n');
}

function buildIntercityDraft({ booking, task, opsCfg, missing }) {
  const company = booking.company_name || opsCfg.company_name || 'Arcadia Tourism';
  const meta = task.metadata || {};
  const lines = [
    `${company} — Intercity Transfer Request`,
    '(DRAFT — staff review; NOT sent automatically)',
    '',
    `Booking reference: ${booking.booking_id}`,
    `Route: ${meta.from || '—'} → ${meta.to || '—'}`,
    `Guests: ${booking.guest_count || '—'} pax`,
    `Lead guest: ${booking.client_name || '—'}`,
    '',
    'Please confirm availability and rate.',
    '',
    company,
  ];
  if (missing.length) lines.push('', '⚠ Missing:', ...missing.map(m => `- ${m}`));
  return lines.join('\n');
}

function buildTourDraft({ booking, task, opsCfg, missing }) {
  const company = booking.company_name || opsCfg.company_name || 'Arcadia Tourism';
  const lines = [
    `${company} — Tour Booking Request`,
    '(DRAFT — staff review; NOT sent automatically)',
    '',
    `Booking reference: ${booking.booking_id}`,
    `City: ${task.city || '—'}`,
    `Tour #: ${(task.metadata && task.metadata.tour_number) || task.segment_index || 1}`,
    `Guests: ${booking.guest_count || '—'} pax`,
    '',
    'Please confirm guide/tour availability.',
    '',
    company,
  ];
  if (missing.length) lines.push('', '⚠ Missing:', ...missing.map(m => `- ${m}`));
  return lines.join('\n');
}

async function buildDraftForTask(taskId, requestedBy, regenerate = false) {
  const tasks = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=*`);
  if (!tasks.length) return { ok: false, error: 'task_not_found', task_id: taskId };
  const task = tasks[0];

  const bookings = await sb.call(this, 'GET', `bookings?booking_id=eq.${encodeURIComponent(task.booking_id)}&select=booking_id,client_name,guest_count,arrival_date,departure_date,city_hotels,company_name,destination,quote_ref,lifecycle_status`);
  if (!bookings.length) return { ok: false, error: 'booking_not_found', booking_id: task.booking_id };
  const booking = bookings[0];
  const cities = parseJson(booking.city_hotels, {});
  const cityList = Object.keys(cities).length ? Object.keys(cities) : [task.city].filter(Boolean);

  const opsCfg = await loadConfig.call(this, 'booking_supplier_ops');
  const missing = [];

  if (!task.supplier_name && task.task_type === 'hotel') missing.push('hotel_name');
  if (!booking.guest_count) missing.push('guest_count');
  if (!booking.arrival_date || !booking.departure_date) missing.push('trip_dates');
  if (!booking.client_name) missing.push('lead_guest_name');

  let contact = null;
  let supplierChannel = task.supplier_channel || null;
  if (task.task_type === 'hotel' && task.supplier_name) {
    contact = await lookupHotelContact.call(this, task.supplier_name, task.city);
    if (contact) {
      if (contact.Email) supplierChannel = supplierChannel || 'email';
      else if (contact.Phone) supplierChannel = supplierChannel || 'phone';
      if (contact.Supplier) supplierChannel = supplierChannel || String(contact.Supplier).toLowerCase();
    }
  }

  const dates = segmentDates(booking, task, cityList);
  let draftText = '';
  if (task.task_type === 'hotel') {
    draftText = buildHotelDraft({ booking, task, opsCfg, contact, dates, missing });
  } else if (task.task_type === 'airport_transfer') {
    draftText = buildAirportDraft({ booking, task, opsCfg, missing });
  } else if (task.task_type === 'intercity_transfer') {
    draftText = buildIntercityDraft({ booking, task, opsCfg, missing });
  } else if (task.task_type === 'tour') {
    draftText = buildTourDraft({ booking, task, opsCfg, missing });
  } else {
    draftText = [`${opsCfg.company_name || 'Arcadia Tourism'} — Supplier Request`, `(DRAFT) Booking: ${booking.booking_id}`, `Task: ${task.task_key}`, `Type: ${task.task_type}`].join('\n');
  }

  const facts = {
    booking_id: booking.booking_id,
    task_id: task.task_id,
    task_key: task.task_key,
    task_type: task.task_type,
    city: task.city,
    supplier_name: task.supplier_name,
    guest_count: booking.guest_count,
    client_name: booking.client_name,
    arrival_date: booking.arrival_date,
    departure_date: booking.departure_date,
    check_in: dates.check_in,
    check_out: dates.check_out,
    quote_ref: booking.quote_ref,
  };

  const status = missing.length ? 'needs_information' : 'draft';
  const idempotencyKey = `draft:${taskId}:${simpleHash(factsHash(facts))}`;

  if (!regenerate) {
    const existing = await sb.call(this, 'GET', `booking_supplier_drafts?idempotency_key=eq.${encodeURIComponent(idempotencyKey)}&select=*`);
    if (existing.length) {
      return {
        ok: true,
        idempotent: true,
        draft_id: existing[0].draft_id,
        status: existing[0].status,
        draft_text: existing[0].draft_text,
        missing_fields: existing[0].missing_fields,
        facts: existing[0].facts,
        task_id: taskId,
        booking_id: task.booking_id,
        auto_send: false,
        phase: '2.6',
      };
    }
  } else {
    await sb.call(this, 'DELETE', `booking_supplier_drafts?task_id=eq.${encodeURIComponent(taskId)}&status=neq.sent_manually`);
  }

  const inserted = await sb.call(this, 'POST', 'booking_supplier_drafts', {
    task_id: taskId,
    booking_id: task.booking_id,
    draft_type: task.task_type,
    status,
    draft_text: draftText,
    facts,
    missing_fields: missing,
    supplier_name: task.supplier_name,
    supplier_channel: supplierChannel,
    contact_snapshot: contact || {},
    idempotency_key: idempotencyKey,
    created_by: requestedBy,
  });

  const draft = inserted[0];

  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'supplier_draft_generated',
    booking_id: task.booking_id,
    source_channel: 'booking:supplier_ops',
    input_summary: `${task.task_key} missing=${missing.length}`.slice(0, 500),
    output_summary: `draft ${draft.draft_id} status=${status}`,
    status: 'success',
    metadata: { phase: '2.6', task_id: taskId, draft_id: draft.draft_id, missing_fields: missing, auto_send: false },
  });

  return {
    ok: true,
    idempotent: false,
    draft_id: draft.draft_id,
    status,
    draft_text: draftText,
    missing_fields: missing,
    facts,
    contact_snapshot: contact,
    supplier_channel: supplierChannel,
    task_id: taskId,
    booking_id: task.booking_id,
    auto_send: false,
    phase: '2.6',
  };
}

// --- Webhook main ---
const raw = $input.first().json;
const body = raw.body ?? raw;
const taskId = String(body.task_id || '').trim();
const requestedBy = String(body.requested_by || 'supplier_draft_webhook').trim();
const regenerate = body.regenerate === true || body.regenerate === 'true';

if (!taskId) {
  return [{ json: { ok: false, error: 'missing_task_id', phase: '2.6' } }];
}

try {
  const result = await buildDraftForTask.call(this, taskId, requestedBy, regenerate);
  return [{ json: result }];
} catch (err) {
  return [{ json: { ok: false, error: 'draft_generation_failed', message: String(err.message || err), phase: '2.6' } }];
}
