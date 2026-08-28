// Phase 2.3 — Booking Staff Notify (Execute Workflow Trigger)
// Input: { booking_id, notify_type?: 'draft'|'test' }
// NO AI — summary only, no sensitive PII beyond ops needs

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

const input = $input.first().json;
const payload = input.body ?? input;
const bookingId = String(payload.booking_id || '').trim();
if (!bookingId) {
  return [{ json: { ok: false, error: 'missing_booking_id', phase: '2.3' } }];
}

const bookings = await sb.call(this, 'GET', `bookings?booking_id=eq.${encodeURIComponent(bookingId)}&select=booking_id,client_name,destination,arrival_date,departure_date,guest_count,quote_ref,lifecycle_status,payment_status,booking_source`);
if (!bookings.length) {
  return [{ json: { ok: false, error: 'booking_not_found', booking_id: bookingId, phase: '2.3' } }];
}
const booking = bookings[0];

const tasks = await sb.call(this, 'GET', `booking_tasks?booking_id=eq.${encodeURIComponent(bookingId)}&select=task_id,task_key,task_type,status,city,is_required&order=task_key`);
const summary = { hotel: 0, airport_transfer: 0, intercity_transfer: 0, tour: 0, train: 0, guide: 0, other: 0 };
for (const t of tasks) {
  if (['pending', 'requested', 'awaiting_confirmation'].includes(t.status)) {
    summary[t.task_type] = (summary[t.task_type] || 0) + 1;
  }
}
const pendingCount = Object.values(summary).reduce((a, b) => a + b, 0);

const tgCfgRows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.telegram_booking_ops&select=config_value');
const tgCfg = tgCfgRows[0]?.config_value || {};
const chatId = tgCfg.chat_id;
if (!chatId) {
  return [{ json: { ok: false, error: 'telegram_chat_id_not_configured', booking_id: bookingId, phase: '2.3' } }];
}

const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
if (!token) throw new Error('TELEGRAM_BOT_TOKEN env required for Laila Sales Bot');

const lines = [
  '📋 *New DRAFT Booking*',
  '',
  `🆔 \`${booking.booking_id}\``,
  `👤 ${booking.client_name || 'Guest'}`,
  `🌍 ${booking.destination || '—'}`,
  `📅 ${booking.arrival_date || '—'} → ${booking.departure_date || '—'}`,
  `👥 Pax: ${booking.guest_count || 1}`,
  `💬 Quote: ${booking.quote_ref || '—'}`,
  `📊 Tasks: ${tasks.length} total · ${pendingCount} pending`,
  '',
  '*Pending by type:*',
  `🏨 Hotels: ${summary.hotel}`,
  `✈️ Airport: ${summary.airport_transfer}`,
  `🚌 Intercity: ${summary.intercity_transfer}`,
  `🎯 Tours: ${summary.tour}`,
].filter(Boolean);

const text = lines.join('\n');
const replyMarkup = {
  inline_keyboard: [
    [
      { text: '👁 View booking', callback_data: `bk:view:${bookingId}` },
      { text: '📝 Pending tasks', callback_data: `bk:tasks:${bookingId}` },
    ],
  ],
};

const tgResp = await this.helpers.httpRequest({
  method: 'POST',
  url: `https://api.telegram.org/bot${token}/sendMessage`,
  headers: { 'Content-Type': 'application/json' },
  body: { chat_id: chatId, text, parse_mode: 'Markdown', reply_markup: replyMarkup },
  json: true,
});

await sb.call(this, 'POST', 'agent_actions', {
  agent_name: 'booking',
  action_type: 'staff_notify',
  booking_id: bookingId,
  source_channel: 'telegram:booking_ops',
  input_summary: `notify ${bookingId}`.slice(0, 500),
  output_summary: `sent chat_id=${chatId} pending=${pendingCount}`,
  status: 'success',
  metadata: { phase: '2.3', message_id: tgResp?.result?.message_id, pending_count: pendingCount },
});

return [{
  json: {
    ok: true,
    booking_id: bookingId,
    chat_id: chatId,
    message_id: tgResp?.result?.message_id,
    pending_tasks: pendingCount,
    phase: '2.3',
  },
}];
