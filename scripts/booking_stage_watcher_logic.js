// Phase 2.5 — Stage Watcher (cron)
// Polls approved leads with explicit approved_quote_ref and invokes Booking Agent Start.
// Feature-flagged via arcadia_system_config.booking_handoff_enabled

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

const cfgRows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_handoff_enabled&select=config_value');
const handoffCfg = cfgRows[0]?.config_value || {};
const enabled = handoffCfg.enabled === true;

if (!enabled) {
  return [{
    json: {
      ok: true,
      skipped: true,
      reason: 'booking_handoff_disabled',
      phase: '2.5',
    },
  }];
}

const canaryOnly = handoffCfg.canary_lead_ids || [];
const limit = Number(handoffCfg.batch_limit || 5);

let query = 'leads?stage=eq.approved&approved_quote_ref=not.is.null&booking_handoff_at=is.null&select=lead_id,approved_quote_ref,stage&order=updated_at.asc&limit=' + limit;
if (canaryOnly.length) {
  const ids = canaryOnly.map(id => encodeURIComponent(String(id))).join(',');
  query = `leads?stage=eq.approved&approved_quote_ref=not.is.null&booking_handoff_at=is.null&lead_id=in.(${ids})&select=lead_id,approved_quote_ref,stage&order=updated_at.asc`;
}

const leads = await sb.call(this, 'GET', query);
const secret = $env.BOOKING_AGENT_START_SECRET || $env.BOOKING_AGENT_TEST_SECRET;
const n8nBase = String($env.N8N_PUBLIC_URL || 'https://n8n.arcadia-tour.cloud').replace(/\/$/, '');
const startUrl = `${n8nBase}/webhook/booking-agent/start`;

const results = [];

for (const lead of leads) {
  const leadId = lead.lead_id;
  const quoteRef = String(lead.approved_quote_ref || '').trim().toUpperCase();
  if (!quoteRef) {
    results.push({ lead_id: leadId, ok: false, error: 'missing_approved_quote_ref' });
    continue;
  }

  const existing = await sb.call(this, 'GET', `bookings?booking_request_key=eq.${encodeURIComponent(`${leadId}:${quoteRef}`)}&select=booking_id&limit=1`);
  if (existing.length) {
    await sb.call(this, 'PATCH', `leads?lead_id=eq.${encodeURIComponent(leadId)}`, {
      booking_handoff_at: new Date().toISOString(),
    });
    results.push({ lead_id: leadId, quote_ref: quoteRef, ok: true, idempotent: true, booking_id: existing[0].booking_id });
    continue;
  }

  if (!secret) {
    results.push({ lead_id: leadId, ok: false, error: 'missing_booking_agent_secret' });
    continue;
  }

  try {
    const resp = await this.helpers.httpRequest({
      method: 'POST',
      url: startUrl,
      headers: {
        'Content-Type': 'application/json',
        'X-Booking-Agent-Secret': secret,
      },
      body: {
        lead_id: leadId,
        quote_ref: quoteRef,
        requested_by: 'stage_watcher',
        source: 'cron:booking-stage-watcher',
      },
      json: true,
    });
    results.push({
      lead_id: leadId,
      quote_ref: quoteRef,
      ok: !!resp.ok,
      booking_id: resp.booking_id || null,
      idempotent: !!resp.idempotent,
      notify_staff: resp.notify_staff,
      error: resp.error || null,
    });
  } catch (err) {
    results.push({
      lead_id: leadId,
      quote_ref: quoteRef,
      ok: false,
      error: String(err.message || err).slice(0, 300),
    });
  }
}

return [{
  json: {
    ok: true,
    phase: '2.5',
    processed: results.length,
    enabled: true,
    canary_only: canaryOnly.length > 0,
    results,
  },
}];
