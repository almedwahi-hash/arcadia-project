// Phase 2.5 — Telegram /book <lead_id> <quote_ref> staff command
// Authorized staff only — same Booking Agent Start entry path with staff_override=true

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

async function loadAllowlist() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_staff_telegram_allowlist&select=config_value');
  return (rows[0]?.config_value?.user_ids || []).map(String);
}

async function loadCiProbe() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_agent_ci_probe&select=config_value');
  const cfg = rows[0]?.config_value || {};
  if (cfg.enabled === true && cfg.probe_secret) return cfg.probe_secret;
  return null;
}

async function tgSend(chatId, text, simulated = false) {
  if (simulated) return { skipped: true };
  const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
  if (!token) throw new Error('TELEGRAM_BOT_TOKEN required');
  return await this.helpers.httpRequest({
    method: 'POST',
    url: `https://api.telegram.org/bot${token}/sendMessage`,
    body: { chat_id: chatId, text, parse_mode: 'Markdown' },
    json: true,
  });
}

function parseInput(raw) {
  const payload = raw.body ?? raw;
  if (payload.simulate || payload.command_text) {
    return {
      userId: String(payload.telegram_user_id || ''),
      chatId: payload.chat_id || payload.telegram_chat_id,
      text: String(payload.command_text || '').trim(),
      simulated: true,
    };
  }
  const msg = payload.message || payload;
  return {
    userId: String(msg.from?.id || ''),
    chatId: msg.chat?.id,
    text: String(msg.text || '').trim(),
    simulated: false,
  };
}

const raw = $input.first().json;
const { userId, chatId, text, simulated } = parseInput(raw);

if (!text.startsWith('/book')) {
  return [{ json: { ok: false, error: 'not_book_command', phase: '2.5', simulated } }];
}

const allowlist = await loadAllowlist.call(this);
if (!allowlist.includes(userId)) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'book_command_denied',
    source_channel: 'telegram:staff',
    input_summary: text.slice(0, 500),
    output_summary: `unauthorized user ${userId}`,
    status: 'failed',
    metadata: { phase: '2.5', telegram_user_id: userId },
  });
  if (chatId) await tgSend.call(this, chatId, '⛔ `/book` — access denied.', simulated);
  return [{ json: { ok: false, error: 'unauthorized', phase: '2.5', denied: true, simulated } }];
}

const parts = text.split(/\s+/).filter(Boolean);
const leadId = parts[1];
const quoteRef = parts[2] ? String(parts[2]).trim().toUpperCase() : null;

if (!leadId || !quoteRef) {
  const help = 'Usage: `/book <lead_id> <quote_ref>`\nExample: `/book b6fada92-a0c4-45a9-a5f7-2e60897af3c8 ARC-367344`';
  if (chatId) await tgSend.call(this, chatId, help, simulated);
  return [{ json: { ok: false, error: 'invalid_syntax', phase: '2.5', simulated } }];
}

const secret = $env.BOOKING_AGENT_START_SECRET || $env.BOOKING_AGENT_TEST_SECRET;
const ciProbe = await loadCiProbe.call(this);

const n8nBase = String($env.N8N_PUBLIC_URL || 'https://n8n.arcadia-tour.cloud').replace(/\/$/, '');
const startUrl = `${n8nBase}/webhook/booking-agent/start`;

const startHeaders = { 'Content-Type': 'application/json' };
if (secret) startHeaders['X-Booking-Agent-Secret'] = secret;

let resp;
try {
  resp = await this.helpers.httpRequest({
    method: 'POST',
    url: startUrl,
    headers: startHeaders,
    body: {
      lead_id: leadId,
      quote_ref: quoteRef,
      requested_by: `staff:${userId}`,
      staff_override: true,
      source: 'telegram:/book',
      ci_probe: ciProbe || undefined,
    },
    json: true,
  });
} catch (err) {
  const msg = String(err.message || err);
  if (chatId) await tgSend.call(this, chatId, `❌ Booking start failed:\n\`${msg.slice(0, 200)}\``, simulated);
  return [{ json: { ok: false, error: 'start_request_failed', message: msg, phase: '2.5', simulated } }];
}

if (!resp.ok) {
  const reason = resp.error || 'blocked';
  if (chatId) {
    await tgSend.call(this, chatId, [
      '⛔ *Booking blocked*',
      `Lead: \`${leadId}\``,
      `Quote: \`${quoteRef}\``,
      `Reason: \`${reason}\``,
    ].join('\n'), simulated);
  }
  return [{ json: { ok: false, blocked: true, ...resp, phase: '2.5', simulated } }];
}

if (resp.notify_staff && !resp.staff_notify?.sent) {
  try {
    await this.helpers.httpRequest({
      method: 'POST',
      url: `${n8nBase}/webhook/booking-staff-notify`,
      headers: { 'Content-Type': 'application/json' },
      body: { booking_id: resp.booking_id },
      json: true,
    });
  } catch (_e) {
    // staff notify failure should not fail /book — booking already created
  }
}

const lines = [
  resp.idempotent ? '♻️ *Existing booking* (idempotent)' : '✅ *DRAFT booking created*',
  `🆔 \`${resp.booking_id}\``,
  `📋 Tasks: ${resp.task_count || '—'}`,
  `💬 Quote: \`${quoteRef}\``,
  `📊 Status: ${resp.lifecycle_status || 'DRAFT'} / ${resp.payment_status || 'unpaid'}`,
];
if (chatId) await tgSend.call(this, chatId, lines.join('\n'), simulated);

return [{
  json: {
    ok: true,
    phase: '2.5',
    simulated,
    staff_override: true,
    lead_id: leadId,
    quote_ref: quoteRef,
    ...resp,
  },
}];
