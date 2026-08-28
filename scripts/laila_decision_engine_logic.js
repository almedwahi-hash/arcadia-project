// Decision Engine — deterministic routing + AI fallback (no extra prompt layers)
const phone = $json.phone;
const remoteJid = $json.remoteJid;
const text = $json.textContent || $json.text || '';
const isManager = $json.isManager || false;
const intent = $json.conversationIntent || 'general';
const trip = $json.tripFromHistory || null;
const chatHistory = $json.chatHistory || '';

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
const HDR = { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };

const HOTEL_ONLY_POLICY =
  'أيوه فهمتك، فندق فقط 👍 حاليًا حجوزاتنا تكون ضمن باقة مع التوصيل، ما نوفر الفندق منفرد.';
const OPS_UNKNOWN = 'أتأكد لك من الفريق وأرجع لك 👍';
const AI_IDENTITY =
  'أنا مساعدة أركاديا بالذكاء الاصطناعي 😊 وإذا احتاج طلبك تدخل موظف من الفريق أحوله لهم.';
const GOODBYE = 'العفو، حياك الله 🌷';
const FALLBACK_HANDOFF =
  'أهلاً 👋 صار خطأ تقني بسيط، جرّب ترسل طلبك مرة ثانية أو تواصل معنا واتساب: https://wa.me/380936582617';

const MONTHS = {
  يناير: 1, فبراير: 2, مارس: 3, ابريل: 4, أبريل: 4, april: 4,
  مايو: 5, يونيو: 6, يوليو: 7, أغسطس: 8, سبتمبر: 9, أكتوبر: 10, اكتوبر: 10,
  نوفمبر: 11, ديسمبر: 12,
};

function arToEnDigits(s) {
  const AR = '٠١٢٣٤٥٦٧٨٩';
  return String(s || '').replace(/[٠-٩]/g, (d) => String(AR.indexOf(d)));
}

function sanitizeReply(s) {
  let t = String(s || '');
  t = t.replace(/\[([^\]]*)\]\((https?:\/\/[^)]+)\)/g, '$2');
  const wa = t.match(/https:\/\/wa\.me\/\d+/g) || [];
  if (wa.length > 1) {
    t = t.replace(/https:\/\/wa\.me\/\d+/g, '').trim() + '\n\n' + wa[0];
  }
  t = t.replace(/\n*‏?إذا تحتاج لأي مساعدة إضافية[^\n]*/gi, '');
  t = t.replace(/\n*‏?(?:هل )?تر(?:غب|يد).*?(?:عرض رسمي|تجهيز العرض)[^\n]*/gi, '');
  return t.trim();
}

function addDays(iso, days) {
  const d = new Date(iso + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function resolveDates(tripCtx, history) {
  const h = arToEnDigits(history || '');
  const m = h.match(/(\d{1,2})\s*(يناير|فبراير|مارس|ابريل|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر)/i);
  if (m) {
    const day = parseInt(m[1], 10);
    const monKey = m[2].replace(/أ/g, 'ا');
    const mon = MONTHS[monKey] || MONTHS[m[2].toLowerCase()];
    if (mon) {
      const year = new Date().getUTCFullYear();
      let checkin = `${year}-${String(mon).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      if (new Date(checkin) < new Date()) checkin = `${year + 1}-${String(mon).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const nights = tripCtx?.nights || 7;
      return { checkin, checkout: addDays(checkin, nights) };
    }
  }
  const checkin = addDays(new Date().toISOString().slice(0, 10), 30);
  const nights = tripCtx?.nights || 7;
  return { checkin, checkout: addDays(checkin, nights) };
}

// Mirrors public.quote_package() — authoritative tour-day allocation
function freeDaysFromEngine(nights) {
  const totalDays = nights + 1;
  if (totalDays >= 14) return 2;
  if (totalDays >= 8) return 1;
  return 0;
}

function tourDaysFromEngine(nights) {
  return Math.max(nights - 1 - freeDaysFromEngine(nights), 0);
}

async function fetchQuoteOptions(tripCtx, mode) {
  if (!KEY || !tripCtx?.city) return null;
  const dates = resolveDates(tripCtx, chatHistory);
  try {
    let data = await this.helpers.httpRequest({
      method: 'POST',
      url: SB + '/rest/v1/rpc/quote_options',
      headers: HDR,
      body: {
        p_city: tripCtx.city,
        p_checkin: dates.checkin,
        p_checkout: dates.checkout,
        p_adults: tripCtx.adults || 2,
        p_rooms: 0,
        p_mode: mode || 'full',
      },
      json: true,
    });
    if (data && data.quote_options) data = data.quote_options;
    if (data && Array.isArray(data.options)) return data;
    return null;
  } catch (e) {
    return null;
  }
}

function pickQuoteOption(quoteData, lastPrice) {
  const opts = quoteData.options || [];
  if (lastPrice) {
    const hit = opts.find((o) => String(o.price_usd) === String(lastPrice));
    if (hit) return hit;
  }
  return opts.find((o) => /basic|أساس/i.test(String(o.tier || ''))) || opts[0];
}

function formatPackageComposition(quoteData, option) {
  const nights = quoteData.nights;
  const totalDays = nights + 1;
  const tourDays = option.tour_days;
  const freeDays = freeDaysFromEngine(nights);
  const engineTourDays = tourDaysFromEngine(nights);
  const tier = option.tier || 'Basic';

  let msg = `الرحلة ${totalDays} أيام / ${nights} ليالي 👍`;
  msg += `\nالعرض (${tier}) محسوب على ${tourDays} أيام جولات`;
  if (freeDays > 0) msg += ` — التسعير يخصّص ${freeDays} ${freeDays === 1 ? 'يوم راحة' : 'أيام راحة'}`;
  msg += '.';

  if (engineTourDays === tourDays) {
    msg += `\nحسب محرك التسعير: ${nights} ليالي − يوم الوصول`;
    if (freeDays > 0) msg += ` − ${freeDays} راحة`;
    msg += ` = ${tourDays} جولات (مو ${tourDays + 1}).`;
  }
  return msg;
}

function formatQuoteReply(tripCtx, quoteData, intro) {
  const opts = quoteData.options || [];
  const basic = opts.find((r) => /basic|أساس|eco/i.test(String(r.tier || ''))) || opts[0];
  const rec = opts.find((r) => /recommend|موص/i.test(String(r.tier || ''))) || opts[1] || opts[0];
  const lines = [intro || 'تمام، خليني أشوف لك خيارات أوفر 👍', ''];
  if (basic) lines.push(`1️⃣ أساسية — ${basic.hotel || 'فندق'} — ${basic.price_usd} دولار`);
  if (rec && rec !== basic) lines.push(`2️⃣ موصى بها — ${rec.hotel || 'فندق'} — ${rec.price_usd} دولار`);
  lines.push('', 'إذا يناسبك خبرني 👍');
  return lines.join('\n');
}

async function flagNeedsHuman() {
  if (!KEY || !phone) return;
  try {
    await this.helpers.httpRequest({
      method: 'PATCH',
      url: SB + '/rest/v1/leads?phone=eq.' + phone,
      headers: { ...HDR, Prefer: 'return=minimal' },
      body: { needs_human: true, updated_at: new Date().toISOString() },
    });
  } catch (e) {}
}

let response = '';
let routedBy = 'ai_agent';

if (intent === 'goodbye') {
  response = GOODBYE;
  routedBy = 'deterministic:goodbye';
} else if (intent === 'ai_identity') {
  response = AI_IDENTITY;
  routedBy = 'deterministic:ai_identity';
} else if (intent === 'ops_unknown') {
  response = OPS_UNKNOWN;
  routedBy = 'deterministic:ops_unknown';
  await flagNeedsHuman.call(this);
} else if (intent === 'hotel_only') {
  response = HOTEL_ONLY_POLICY;
  routedBy = 'deterministic:hotel_only_policy';
} else if (intent === 'returning_customer' && trip) {
  const bits = [];
  if (trip.destination) bits.push(trip.destination);
  if (trip.nights) bits.push(trip.nights + ' ليالي');
  if (trip.adults) bits.push(trip.adults + ' أشخاص');
  response = `تمام، عندي طلبك: ${bits.join('، ') || 'طلبك السابق'} 👍`;
  if (trip.last_price) response += `\nآخر عرض كان ${trip.last_price} دولار — تبي أرسله لك مرة ثانية؟`;
  else response += '\nتبي أرسل لك آخر عرض؟';
  routedBy = 'deterministic:returning_customer';
} else if (intent === 'package_composition' && trip?.city) {
  routedBy = 'deterministic:package_composition';
  const quoteData = await fetchQuoteOptions.call(this, trip, 'full');
  if (quoteData) {
    const option = pickQuoteOption(quoteData, trip.last_price);
    if (option) response = formatPackageComposition(quoteData, option);
  }
  if (!response) response = OPS_UNKNOWN;
} else if (intent === 'price_objection') {
  routedBy = 'deterministic:pricing_engine';
  const quoteData = await fetchQuoteOptions.call(this, trip, 'no_tours');
  if (quoteData) response = formatQuoteReply(trip, quoteData, 'تمام، خليني أشوف لك خيارات أوفر 👍');
  if (!response) {
    const quoteFull = await fetchQuoteOptions.call(this, trip, 'full');
    if (quoteFull) response = formatQuoteReply(trip, quoteFull, 'تمام، خليني أشوف لك خيارات أوفر 👍');
  }
}

if (!response) {
  const payload = {
    action: 'sendMessage',
    sessionId: String(phone || 'wa'),
    chatInput: text,
    leadContext: $json.leadStateSummary || '',
    chatHistory,
    managerInstructions: $json.managerInstructions || '',
    context: $json.context || '',
    conversationHints: ($json.conversationHints || []).join('\n'),
    customerLanguage: $json.customerLanguage || 'ar',
  };
  try {
    const res = await this.helpers.httpRequest({
      method: 'POST',
      url: 'https://n8n.arcadia-tour.cloud/webhook/cc004272-5e46-4e5c-be6d-ba84fdf35258/chat',
      body: payload,
      json: true,
      timeout: 90000,
    });
    if (typeof res === 'string') {
      try { response = JSON.parse(res).output; } catch (e) { response = res; }
    } else {
      response = (res && (res.output || res.text || res.response)) || '';
    }
  } catch (e) {
    response = '';
  }
  routedBy = 'ai_agent';
}

response = sanitizeReply(response);

if (intent === 'price_objection' && /ما قدرت أكمل طلبك|تواصل مباشرة/.test(response) && trip?.city) {
  const quoteData = await fetchQuoteOptions.call(this, trip, 'no_tours');
  if (quoteData) {
    response = formatQuoteReply(trip, quoteData, 'تمام، خليني أشوف لك خيارات أوفر 👍');
    routedBy = 'deterministic:pricing_engine_retry';
  }
}

if (!response) response = FALLBACK_HANDOFF;

const followup = /دولار|\$|💵/.test(response);
return [{ json: { phone, remoteJid, response, isManager, followup, routedBy } }];
