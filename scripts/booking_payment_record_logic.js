// Phase 2.4A — Record booking payment (Telegram staff action + test webhook)
// Deterministic — NO AI. Staff allowlist required. Append-only ledger via RPC.

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

async function sbRpc(fn, args) {
  const rows = await sb.call(this, 'POST', `rpc/${fn}`, args);
  return Array.isArray(rows) ? rows[0] : rows;
}

async function loadAllowlist() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_staff_telegram_allowlist&select=config_value');
  return (rows[0]?.config_value?.user_ids || []).map(String);
}

async function idempotent(key, meta) {
  const hit = await sb.call(this, 'GET', `booking_telegram_idempotency?idempotency_key=eq.${encodeURIComponent(key)}&select=idempotency_key`);
  if (hit.length) return true;
  try {
    await sb.call(this, 'POST', 'booking_telegram_idempotency', {
      idempotency_key: key,
      action_type: meta.action_type || 'payment_record',
      booking_id: meta.booking_id || null,
      metadata: meta,
    });
  } catch (e) {
    if (String(e.message || e).includes('23505')) return true;
    throw e;
  }
  return false;
}

function parseInput(raw) {
  const payload = raw.body ?? raw;
  return {
    userId: String(payload.telegram_user_id || payload.user_id || ''),
    bookingId: String(payload.booking_id || '').trim(),
    amount: Number(payload.amount),
    currency: String(payload.currency || 'USD').toUpperCase(),
    paymentMethod: String(payload.payment_method || '').trim(),
    reference: payload.reference || null,
    notes: payload.notes || null,
    amountUsd: payload.amount_usd != null ? Number(payload.amount_usd) : null,
    fxRate: payload.fx_rate != null ? Number(payload.fx_rate) : null,
    fxSource: payload.fx_source || null,
    idempotencyKey: String(payload.idempotency_key || payload.action_key || '').trim(),
    simulated: !!(payload.simulate || payload.test_mode),
  };
}

// --- Main ---
const raw = $input.first().json;
const input = parseInput(raw);

if (!input.bookingId || !input.paymentMethod) {
  return [{ json: { ok: false, error: 'missing_booking_or_method', phase: '2.4A' } }];
}
if (!input.amount || input.amount <= 0) {
  return [{ json: { ok: false, error: 'invalid_amount', phase: '2.4A' } }];
}

const allowlist = await loadAllowlist.call(this);
if (!allowlist.includes(input.userId)) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'payment_record_denied',
    booking_id: input.bookingId,
    source_channel: 'telegram:staff',
    input_summary: `user=${input.userId} booking=${input.bookingId}`.slice(0, 500),
    output_summary: 'unauthorized_telegram_user',
    status: 'failed',
    metadata: { phase: '2.4A', denied: true },
  });
  return [{ json: { ok: false, error: 'unauthorized', phase: '2.4A', denied: true } }];
}

const idemKey = input.idempotencyKey || `pay:${input.bookingId}:${input.amount}:${input.currency}:${input.reference || 'noref'}`;
const actionIdem = `payment_action:${idemKey}`;
if (await idempotent.call(this, actionIdem, { action_type: 'payment_record', booking_id: input.bookingId, idempotency_key: idemKey })) {
  const existing = await sbRpc.call(this, 'record_booking_payment', {
    p_booking_id: input.bookingId,
    p_idempotency_key: idemKey,
    p_amount_original: input.amount,
    p_currency_original: input.currency,
    p_payment_method: input.paymentMethod,
    p_recorded_by: `staff:${input.userId}`,
    p_amount_usd: input.amountUsd,
    p_reference: input.reference,
    p_notes: input.notes,
    p_fx_rate: input.fxRate,
    p_fx_source: input.fxSource,
  });
  return [{ json: { ok: true, idempotent: true, phase: '2.4A', simulated: input.simulated, ...existing } }];
}

let result;
try {
  result = await sbRpc.call(this, 'record_booking_payment', {
    p_booking_id: input.bookingId,
    p_idempotency_key: idemKey,
    p_amount_original: input.amount,
    p_currency_original: input.currency,
    p_payment_method: input.paymentMethod,
    p_recorded_by: `staff:${input.userId}`,
    p_amount_usd: input.amountUsd,
    p_reference: input.reference,
    p_notes: input.notes,
    p_fx_rate: input.fxRate,
    p_fx_source: input.fxSource,
  });
} catch (e) {
  const msg = String(e.message || e);
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'payment_record_failed',
    booking_id: input.bookingId,
    source_channel: 'telegram:staff',
    input_summary: `${input.amount} ${input.currency} ${input.paymentMethod}`.slice(0, 500),
    output_summary: msg.slice(0, 500),
    status: 'failed',
    metadata: { phase: '2.4A', idempotency_key: idemKey },
  });
  return [{ json: { ok: false, error: 'payment_record_failed', message: msg, phase: '2.4A' } }];
}

await sb.call(this, 'POST', 'agent_actions', {
  agent_name: 'booking',
  action_type: 'payment_record',
  booking_id: input.bookingId,
  source_channel: 'telegram:staff',
  input_summary: `${input.amount} ${input.currency} via ${input.paymentMethod}`.slice(0, 500),
  output_summary: `paid=${result.paid_amount} lifecycle=${result.lifecycle_status}`.slice(0, 500),
  status: 'success',
  metadata: {
    phase: '2.4A',
    payment_id: result.payment_id,
    idempotency_key: idemKey,
    idempotent: !!result.idempotent,
    telegram_user_id: input.userId,
  },
});

return [{
  json: {
    ok: true,
    phase: '2.4A',
    simulated: input.simulated,
    booking_id: input.bookingId,
    ...result,
  },
}];
