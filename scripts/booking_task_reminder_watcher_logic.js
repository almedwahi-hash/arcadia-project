// Phase 2.6 — Overdue task reminder watcher (design — OFF by default)
// Cron: scans booking_tasks for overdue supplier ops; dedupes via booking_task_reminder_log.
// Does NOT auto-send supplier messages — staff Telegram notify only when enabled.

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

async function loadPolicy() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_task_reminder_policy&select=config_value');
  return rows[0]?.config_value || {};
}

async function loadStaffChatIds() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_staff_telegram_allowlist&select=config_value');
  return (rows[0]?.config_value?.user_ids || []).map(String);
}

function hoursAgo(h) {
  return new Date(Date.now() - h * 3600 * 1000).toISOString();
}

function daysFromNow(d) {
  return new Date(Date.now() + d * 86400 * 1000).toISOString().slice(0, 10);
}

async function reminderAlreadySent(idempotencyKey) {
  const rows = await sb.call(this, 'GET', `booking_task_reminder_log?idempotency_key=eq.${encodeURIComponent(idempotencyKey)}&select=reminder_id`);
  return rows.length > 0;
}

async function recordReminder({ taskId, bookingId, reminderType, idempotencyKey, chatId, metadata }) {
  try {
    await sb.call(this, 'POST', 'booking_task_reminder_log', {
      task_id: taskId,
      booking_id: bookingId,
      reminder_type: reminderType,
      idempotency_key: idempotencyKey,
      chat_id: chatId || null,
      metadata: metadata || {},
    });
    return true;
  } catch (e) {
    if (String(e.message || e).includes('23505')) return false;
    throw e;
  }
}

async function tgSend(chatId, text) {
  const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
  if (!token) return { sent: false, reason: 'no_token' };
  const resp = await this.helpers.httpRequest({
    method: 'POST',
    url: `https://api.telegram.org/bot${token}/sendMessage`,
    body: { chat_id: chatId, text, parse_mode: 'Markdown' },
    json: true,
  });
  return { sent: true, message_id: resp.result?.message_id };
}

const policy = await loadPolicy.call(this);
if (policy.enabled !== true) {
  return [{
    json: {
      ok: true,
      skipped: true,
      reason: 'reminder_policy_disabled',
      phase: '2.6',
    },
  }];
}

const cooldownHours = Number(policy.cooldown_hours || 24);
const requestNotSentAfter = Number(policy.request_not_sent_after_hours || 48);
const awaitingResponseAfter = Number(policy.awaiting_response_after_hours || 72);
const approachingArrivalDays = Number(policy.approaching_arrival_days || 7);
const cooldownSince = hoursAgo(cooldownHours);
const arrivalCutoff = daysFromNow(approachingArrivalDays);

const staffChats = await loadStaffChatIds.call(this);
const reminders = [];

// 1) Supplier request not sent — pending required task past threshold, no sent_manually draft
const pendingTasks = await sb.call(
  this,
  'GET',
  `booking_tasks?status=eq.pending&is_required=eq.true&created_at=lt.${encodeURIComponent(hoursAgo(requestNotSentAfter))}&select=task_id,booking_id,task_key,task_type,city,created_at,due_at`,
);

for (const task of pendingTasks) {
  const drafts = await sb.call(
    this,
    'GET',
    `booking_supplier_drafts?task_id=eq.${encodeURIComponent(task.task_id)}&status=eq.sent_manually&select=draft_id&limit=1`,
  );
  if (drafts.length) continue;

  const idemKey = `reminder:request_not_sent:${task.task_id}:${Math.floor(Date.now() / (cooldownHours * 3600 * 1000))}`;
  if (await reminderAlreadySent.call(this, idemKey)) continue;

  const text = `⏰ *Supplier request not sent*\nBooking \`${task.booking_id}\`\nTask \`${task.task_key}\` (${task.task_type})`;
  for (const chatId of staffChats) {
    const sendResult = await tgSend.call(this, chatId, text);
    await recordReminder.call(this, {
      taskId: task.task_id,
      bookingId: task.booking_id,
      reminderType: 'request_not_sent',
      idempotencyKey: idemKey,
      chatId,
      metadata: { task_key: task.task_key, send: sendResult },
    });
  }
  reminders.push({ type: 'request_not_sent', task_id: task.task_id, booking_id: task.booking_id });
}

// 2) Awaiting supplier response — requested/awaiting_confirmation past threshold
const awaitingTasks = await sb.call(
  this,
  'GET',
  `booking_tasks?status=in.(requested,awaiting_confirmation)&is_required=eq.true&updated_at=lt.${encodeURIComponent(hoursAgo(awaitingResponseAfter))}&select=task_id,booking_id,task_key,status,updated_at`,
);

for (const task of awaitingTasks) {
  const idemKey = `reminder:awaiting_response:${task.task_id}:${Math.floor(Date.now() / (cooldownHours * 3600 * 1000))}`;
  if (await reminderAlreadySent.call(this, idemKey)) continue;

  const text = `⏰ *Awaiting supplier response*\nBooking \`${task.booking_id}\`\nTask \`${task.task_key}\` [${task.status}]`;
  for (const chatId of staffChats) {
    await tgSend.call(this, chatId, text);
    await recordReminder.call(this, {
      taskId: task.task_id,
      bookingId: task.booking_id,
      reminderType: 'awaiting_supplier_response',
      idempotencyKey: idemKey,
      chatId,
      metadata: { task_key: task.task_key, status: task.status },
    });
  }
  reminders.push({ type: 'awaiting_supplier_response', task_id: task.task_id, booking_id: task.booking_id });
}

// 3) Approaching arrival with unconfirmed required tasks
const bookings = await sb.call(
  this,
  'GET',
  `bookings?arrival_date=lte.${encodeURIComponent(arrivalCutoff)}&arrival_date=gte.${encodeURIComponent(new Date().toISOString().slice(0, 10))}&lifecycle_status=not.in.(COMPLETED,CANCELLED)&select=booking_id,arrival_date,client_name`,
);

for (const booking of bookings) {
  const unconfirmed = await sb.call(
    this,
    'GET',
    `booking_tasks?booking_id=eq.${encodeURIComponent(booking.booking_id)}&is_required=eq.true&status=not.in.(confirmed,skipped)&select=task_id,task_key,status&limit=5`,
  );
  if (!unconfirmed.length) continue;

  for (const task of unconfirmed) {
    const idemKey = `reminder:arrival_unconfirmed:${task.task_id}:${booking.arrival_date}`;
    if (await reminderAlreadySent.call(this, idemKey)) continue;

    const text = `⚠️ *Arrival ${booking.arrival_date} — unconfirmed task*\nBooking \`${booking.booking_id}\`\nTask \`${task.task_key}\` [${task.status}]`;
    for (const chatId of staffChats) {
      await tgSend.call(this, chatId, text);
      await recordReminder.call(this, {
        taskId: task.task_id,
        bookingId: booking.booking_id,
        reminderType: 'approaching_arrival_unconfirmed',
        idempotencyKey: idemKey,
        chatId,
        metadata: { arrival_date: booking.arrival_date, task_key: task.task_key },
      });
    }
    reminders.push({ type: 'approaching_arrival_unconfirmed', task_id: task.task_id, booking_id: booking.booking_id });
  }
}

return [{
  json: {
    ok: true,
    phase: '2.6',
    enabled: true,
    reminders_sent: reminders.length,
    reminders,
    policy: {
      cooldown_hours: cooldownHours,
      request_not_sent_after_hours: requestNotSentAfter,
      awaiting_response_after_hours: awaitingResponseAfter,
      approaching_arrival_days: approachingArrivalDays,
    },
  },
}];
