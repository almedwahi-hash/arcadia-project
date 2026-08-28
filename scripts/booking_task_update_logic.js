// Phase 2.4A — Booking Task Update (Telegram callback + test webhook)
// Deterministic — NO AI. Staff allowlist required for writes.

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) throw new Error('SUPABASE_KEY required');

const HDR = {
  apikey: KEY,
  Authorization: `Bearer ${KEY}`,
  'Content-Type': 'application/json',
  Prefer: 'return=representation',
};

const ALLOWED = {
  pending: ['requested', 'failed', 'skipped'],
  requested: ['awaiting_confirmation', 'failed', 'skipped'],
  awaiting_confirmation: ['confirmed', 'failed', 'skipped'],
  confirmed: [],
  failed: ['requested', 'skipped'],
  skipped: [],
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

async function loadSkipPolicy() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_task_skip_policy&select=config_value');
  return rows[0]?.config_value || {};
}

function isSensitiveRequiredTask(task, policy) {
  if (task.is_required === false) return false;
  const sensitive = policy.sensitive_required_types || ['hotel', 'airport_transfer', 'intercity_transfer', 'train', 'guide'];
  return sensitive.includes(task.task_type);
}

async function idempotent(key, meta) {
  const hit = await sb.call(this, 'GET', `booking_telegram_idempotency?idempotency_key=eq.${encodeURIComponent(key)}&select=idempotency_key`);
  if (hit.length) return true;
  try {
    await sb.call(this, 'POST', 'booking_telegram_idempotency', {
      idempotency_key: key,
      action_type: meta.action_type || 'callback',
      booking_id: meta.booking_id || null,
      task_id: meta.task_id || null,
      metadata: meta,
    });
  } catch (e) {
    if (String(e.message || e).includes('23505')) return true;
    throw e;
  }
  return false;
}

async function logTask(taskId, bookingId, field, oldVal, newVal, changedBy, reason, metadata) {
  await sb.call(this, 'POST', 'booking_task_status_log', {
    task_id: taskId,
    booking_id: bookingId,
    field_changed: field,
    old_value: oldVal != null ? String(oldVal) : null,
    new_value: newVal != null ? String(newVal) : null,
    changed_by: changedBy,
    reason,
    metadata: { source: 'telegram', ...(metadata || {}) },
  });
}

async function logDenied(userId, action, reason) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'task_update_denied',
    source_channel: 'telegram:staff',
    input_summary: `user=${userId} action=${action}`.slice(0, 500),
    output_summary: reason,
    status: 'failed',
    metadata: { phase: '2.4A', telegram_user_id: userId, denied: true },
  });
}

async function tgAnswer(callbackId, text, showAlert = false, simulated = false) {
  if (simulated) return;
  const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
  if (!token || !callbackId) return;
  try {
    await this.helpers.httpRequest({
      method: 'POST',
      url: `https://api.telegram.org/bot${token}/answerCallbackQuery`,
      body: { callback_query_id: callbackId, text: text || 'OK', show_alert: showAlert },
      json: true,
    });
  } catch (_e) {
    // ignore invalid callback ids in test/simulated mode
  }
}

async function tgSend(chatId, text, replyMarkup) {
  const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
  if (!token) throw new Error('TELEGRAM_BOT_TOKEN required');
  return await this.helpers.httpRequest({
    method: 'POST',
    url: `https://api.telegram.org/bot${token}/sendMessage`,
    body: { chat_id: chatId, text, parse_mode: 'Markdown', reply_markup: replyMarkup },
    json: true,
  });
}

function parseInput(raw) {
  const payload = raw.body ?? raw;
  // Test webhook simulation
  if (payload.simulate || payload.callback_data) {
    return {
      userId: String(payload.telegram_user_id || ''),
      callbackData: payload.callback_data || '',
      callbackId: payload.callback_query_id || `sim_${Date.now()}`,
      chatId: payload.chat_id || payload.telegram_chat_id,
      confirmData: payload.confirm_data || {},
      simulated: true,
    };
  }
  const upd = payload;
  const cb = upd.callback_query;
  if (!cb) return { error: 'not_a_callback' };
  return {
    userId: String(cb.from?.id || ''),
    callbackData: cb.data || '',
    callbackId: cb.id,
    chatId: cb.message?.chat?.id,
    confirmData: {},
    simulated: false,
  };
}

async function handleView(bookingId, chatId) {
  const rows = await sb.call(this, 'GET', `bookings?booking_id=eq.${encodeURIComponent(bookingId)}&select=booking_id,client_name,destination,arrival_date,departure_date,guest_count,quote_ref,lifecycle_status,payment_status`);
  if (!rows.length) return 'Booking not found.';
  const b = rows[0];
  return [
    `*Booking ${b.booking_id}*`,
    `Status: ${b.lifecycle_status} / ${b.payment_status}`,
    `Guest: ${b.client_name || 'Guest'}`,
    `Destination: ${b.destination}`,
    `Dates: ${b.arrival_date} → ${b.departure_date}`,
    `Pax: ${b.guest_count} · Quote: ${b.quote_ref}`,
  ].join('\n');
}

async function handleTasksList(bookingId, chatId) {
  const tasks = await sb.call(this, 'GET', `booking_tasks?booking_id=eq.${encodeURIComponent(bookingId)}&select=task_id,task_key,task_type,status,city,is_required&order=task_key`);
  const open = tasks.filter(t => ['pending', 'requested', 'awaiting_confirmation'].includes(t.status));
  const lines = open.slice(0, 8).map(t => `• \`${t.task_key}\` [${t.status}]${t.is_required === false ? ' (opt)' : ''}`);
  const keyboard = open.slice(0, 5).map(t => ([
    { text: `→ req ${t.task_key.split(':').slice(0, 2).join(':')}`, callback_data: `bk:task:${t.task_id}:to:requested` },
  ]));
  if (open.length > 5) keyboard.push([{ text: `+${open.length - 5} more tasks`, callback_data: `bk:tasks:${bookingId}` }]);
  await tgSend.call(this, chatId, [`*Pending tasks* (${open.length})`, ...lines].join('\n'), { inline_keyboard: keyboard });
  return { listed: open.length };
}

async function handleTaskTransition({ taskId, toStatus, userId, callbackId, chatId, confirmData, simulated }) {
  const staffTag = `staff:${userId}`;

  const idemKey = `cb:${callbackId}`;
  if (await idempotent.call(this, idemKey, { action_type: 'task_transition', task_id: taskId, to: toStatus })) {
    const existing = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=task_key,status,booking_id`);
    const t = existing[0] || {};
    return { ok: true, idempotent: true, task_id: taskId, status: t.status, booking_id: t.booking_id, task_key: t.task_key };
  }

  const tasks = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=*`);
  if (!tasks.length) return { ok: false, error: 'task_not_found' };
  const task = tasks[0];
  const fromStatus = task.status;

  if (!(ALLOWED[fromStatus] || []).includes(toStatus)) {
    return { ok: false, error: 'transition_not_allowed', from: fromStatus, to: toStatus };
  }

  const skipPolicy = await loadSkipPolicy.call(this);

  if (toStatus === 'skipped' && isSensitiveRequiredTask(task, skipPolicy)) {
    const skipReason = confirmData.reason || confirmData.notes || 'unspecified';
    const skipResult = await sbRpc.call(this, 'request_required_task_skip', {
      p_task_id: taskId,
      p_requested_by: staffTag,
      p_skip_reason: skipReason,
      p_idempotency_key: `manual_override:skip:${taskId}:${skipReason}`,
    });
    await sb.call(this, 'POST', 'agent_actions', {
      agent_name: 'booking',
      action_type: 'task_skip_approval_requested',
      booking_id: task.booking_id,
      source_channel: 'telegram:staff',
      input_summary: `${task.task_key} skip:${skipReason}`.slice(0, 500),
      output_summary: JSON.stringify(skipResult).slice(0, 500),
      status: 'success',
      metadata: { phase: '2.4A', task_id: taskId, telegram_user_id: userId },
    });
    await tgAnswer.call(this, callbackId, 'Skip requires approval', true, simulated);
    return {
      ok: true,
      skip_blocked: true,
      approval_required: true,
      task_id: taskId,
      booking_id: task.booking_id,
      ...skipResult,
    };
  }

  const patch = { status: toStatus, updated_at: new Date().toISOString() };
  if (toStatus === 'requested') patch.requested_at = new Date().toISOString();
  if (toStatus === 'confirmed') {
    patch.confirmed_at = new Date().toISOString();
    patch.confirmation_ref = confirmData.confirmation_ref || task.confirmation_ref || `REF-${Date.now()}`;
    if (confirmData.supplier_name || task.supplier_name) patch.supplier_name = confirmData.supplier_name || task.supplier_name;
    if (confirmData.notes) patch.notes = confirmData.notes;
    if (confirmData.supplier_cost_usd != null) {
      const newCost = Number(confirmData.supplier_cost_usd);
      const variance = await sbRpc.call(this, 'maybe_create_supplier_price_change_approval', {
        p_task_id: taskId,
        p_proposed_cost: newCost,
        p_requested_by: staffTag,
        p_reason: confirmData.variance_reason || null,
      });
      if (variance.action === 'approval_created' || variance.action === 'approval_exists') {
        await sb.call(this, 'POST', 'agent_actions', {
          agent_name: 'booking',
          action_type: 'supplier_price_change_pending',
          booking_id: task.booking_id,
          source_channel: 'telegram:staff',
          input_summary: `${task.task_key} cost=${newCost}`.slice(0, 500),
          output_summary: JSON.stringify(variance).slice(0, 500),
          status: 'success',
          metadata: { phase: '2.4A', task_id: taskId, telegram_user_id: userId },
        });
        await tgAnswer.call(this, callbackId, 'Supplier cost approval required', true, simulated);
        const lifecycle = await sbRpc.call(this, 'recompute_booking_lifecycle', { p_booking_id: task.booking_id });
        return {
          ok: false,
          error: 'supplier_price_change_approval_required',
          task_id: taskId,
          booking_id: task.booking_id,
          lifecycle_status: lifecycle,
          variance,
        };
      }
      if (variance.action === 'cost_review_required') {
        await tgAnswer.call(this, callbackId, 'Cost review required — no baseline', true, simulated);
        return { ok: false, error: 'cost_review_required', task_id: taskId, booking_id: task.booking_id, variance };
      }
      if (variance.action === 'within_threshold' && newCost > 0) {
        patch.supplier_cost_usd = newCost;
      } else if (newCost > 0 && task.quoted_cost_usd == null && !task.metadata?.quoted_cost) {
        patch.supplier_cost_usd = newCost;
      }
    }
  }
  if (toStatus === 'skipped') {
    patch.notes = confirmData.notes || confirmData.reason || 'skipped_by_staff';
  }

  const updated = await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}`, patch);
  const newTask = updated[0] || { ...task, ...patch };

  await logTask.call(this, taskId, task.booking_id, 'status', fromStatus, toStatus, staffTag, 'telegram_task_update', { callback_id: callbackId });

  const newLifecycle = await sbRpc.call(this, 'recompute_booking_lifecycle', { p_booking_id: task.booking_id });

  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'task_update',
    booking_id: task.booking_id,
    source_channel: 'telegram:staff',
    input_summary: `${task.task_key} ${fromStatus}->${toStatus}`.slice(0, 500),
    output_summary: `lifecycle=${newLifecycle}`,
    status: 'success',
    metadata: { phase: '2.4A', task_id: taskId, telegram_user_id: userId, idempotent: false },
  });

  await tgAnswer.call(this, callbackId, `${task.task_key}: ${fromStatus} → ${toStatus}`, false, simulated);

  return {
    ok: true,
    idempotent: false,
    simulated: !!simulated,
    task_id: taskId,
    task_key: task.task_key,
    from: fromStatus,
    to: toStatus,
    booking_id: task.booking_id,
    lifecycle_status: newLifecycle,
  };
}

// --- Main ---
const raw = $input.first().json;
const parsed = parseInput(raw);
if (parsed.error) {
  return [{ json: { ok: false, error: parsed.error, phase: '2.4A', simulated: true } }];
}

const { userId, callbackData, callbackId, chatId, confirmData, simulated } = parsed;
const allowlist = await loadAllowlist.call(this);
const authorized = allowlist.includes(userId);

const parts = (callbackData || '').split(':');
// bk:view:{bookingId} | bk:tasks:{bookingId} | bk:task:{taskId}:to:{status}

if (!authorized) {
  await logDenied.call(this, userId, callbackData, 'unauthorized_telegram_user');
  if (callbackId) await tgAnswer.call(this, callbackId, 'Access denied.', true);
  return [{ json: { ok: false, error: 'unauthorized', phase: '2.4A', denied: true, simulated } }];
}

if (parts[0] !== 'bk') {
  return [{ json: { ok: false, error: 'unknown_callback', phase: '2.4A' } }];
}

const viewIdem = `cb:${callbackId}:view`;
if (parts[1] === 'view' && parts[2]) {
  if (await idempotent.call(this, viewIdem, { action_type: 'view_booking', booking_id: parts[2] })) {
    await tgAnswer.call(this, callbackId, 'Already viewed.');
    return [{ json: { ok: true, idempotent: true, action: 'view', booking_id: parts[2], phase: '2.4A' } }];
  }
  const text = await handleView.call(this, parts[2], chatId);
  await tgSend.call(this, chatId, text);
  await tgAnswer.call(this, callbackId, 'Booking loaded');
  return [{ json: { ok: true, action: 'view', booking_id: parts[2], phase: '2.4A' } }];
}

if (parts[1] === 'tasks' && parts[2]) {
  const listIdem = `cb:${callbackId}:tasks`;
  if (await idempotent.call(this, listIdem, { action_type: 'list_tasks', booking_id: parts[2] })) {
    await tgAnswer.call(this, callbackId, 'Already listed.');
    return [{ json: { ok: true, idempotent: true, action: 'tasks', booking_id: parts[2], phase: '2.4A' } }];
  }
  const result = await handleTasksList.call(this, parts[2], chatId);
  await tgAnswer.call(this, callbackId, `Tasks: ${result.listed}`);
  return [{ json: { ok: true, action: 'tasks', booking_id: parts[2], ...result, phase: '2.4A' } }];
}

if (parts[1] === 'task' && parts[2] && parts[3] === 'to' && parts[4]) {
  const result = await handleTaskTransition.call(this, {
    taskId: parts[2],
    toStatus: parts[4],
    userId,
    callbackId,
    chatId,
    confirmData,
    simulated,
  });
  return [{ json: { ...result, phase: '2.4A', simulated } }];
}

return [{ json: { ok: false, error: 'invalid_callback', callback_data: callbackData, phase: '2.4A' } }];
