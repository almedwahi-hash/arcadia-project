// Decision Engine — deterministic routing + AI fallback (no extra prompt layers)
const phone = $json.phone;
const remoteJid = $json.remoteJid;
const text = $json.textContent || $json.text || '';
const isManager = $json.isManager || false;
const intent = $json.conversationIntent || 'general';
const trip = $json.tripFromHistory || null;
const requestedTourDays = $json.requestedTourDays ?? null;
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
const PRICING_RETRY = 'لحظة أتأكد لك من السعر بعد التعديل 👍';

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
  t = t.replace(/https:\/\/wa\.me\/\d+[^\s\n]*/g, '');
  t = t.replace(/تواصل مباشرة[^\n]*/gi, '');
  t = t.replace(/ما قدرت أكمل طلبك[^\n]*/gi, '');
  t = t.replace(/خدمة عملائنا[^\n]*/gi, '');
  t = t.replace(/\n*‏?إذا تحتاج لأي مساعدة إضافية[^\n]*/gi, '');
  t = t.replace(/\n*‏?إذا يناسبك خبرني[^\n]*/gi, '');
  t = t.replace(/\n*‏?أنا هنا ل(?:مساعدتك|خدمتك)[^\n]*/gi, '');
  t = t.replace(/\n*‏?(?:هل )?تر(?:غب|يد).*?(?:عرض رسمي|تجهيز العرض)[^\n]*/gi, '');
  return t.trim();
}

function isCircularHandoff(s) {
  return /wa\.me|تواصل مباشرة|ما قدرت أكمل طلبك|خدمة عملائنا/.test(String(s || ''));
}

function tourDaysLabel(n) {
  if (n === 2) return 'جولتين';
  return `${n} أيام جولات`;
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

async function fetchQuotePackage(tripCtx, forceTourDays) {
  if (!KEY || !tripCtx?.city || forceTourDays == null) return null;
  const dates = resolveDates(tripCtx, chatHistory);
  const body = {
    p_city: tripCtx.city,
    p_checkin: dates.checkin,
    p_checkout: dates.checkout,
    p_adults: tripCtx.adults || 2,
    p_rooms: 0,
    p_star: null,
    p_mode: 'recommended',
    p_markup: 0.2,
    p_include_transfer: true,
    p_force_tour_days: forceTourDays,
    p_hotel_name: tripCtx.hotel || null,
  };
  if (!tripCtx.hotel) body.p_hotel_tier = 'cheapest';
  try {
    const data = await this.helpers.httpRequest({
      method: 'POST',
      url: SB + '/rest/v1/rpc/quote_package',
      headers: HDR,
      body,
      json: true,
    });
    if (data && data.error) return null;
    if (data && data.final_price_usd != null) return data;
    return null;
  } catch (e) {
    return null;
  }
}

async function persistPackagePrefs(tripCtx, tourDays, price, hotelName) {
  if (!KEY || !phone) return;
  const notes = [
    tripCtx.city ? `city=${tripCtx.city}` : '',
    tripCtx.nights != null ? `nights=${tripCtx.nights}` : '',
    `tour_days=${tourDays}`,
    hotelName ? `hotel=${hotelName}` : tripCtx.hotel ? `hotel=${tripCtx.hotel}` : '',
    `last_price=${price}`,
  ]
    .filter(Boolean)
    .join(';');
  try {
    await this.helpers.httpRequest({
      method: 'PATCH',
      url: SB + '/rest/v1/leads?phone=eq.' + phone,
      headers: { ...HDR, Prefer: 'return=minimal' },
      body: { notes, updated_at: new Date().toISOString() },
    });
  } catch (e) {}
}

function pickQuoteOption(quoteData, tripCtx) {
  const opts = quoteData.options || [];
  if (tripCtx?.last_price) {
    const hit = opts.find((o) => String(o.price_usd) === String(tripCtx.last_price));
    if (hit) return hit;
  }
  if (tripCtx?.tour_days != null) {
    const byTour = opts.find((o) => o.tour_days === tripCtx.tour_days);
    if (byTour) return byTour;
  }
  return opts.find((o) => /basic|أساس/i.test(String(o.tier || ''))) || opts[0];
}

function currentTourDays(quoteData, option, tripCtx) {
  if (tripCtx?.tour_days != null) return tripCtx.tour_days;
  return option?.tour_days ?? quoteData?.nights;
}

function formatPackageExplain(quoteData, option, tripCtx) {
  const nights = quoteData.nights;
  const totalDays = nights + 1;
  const tourDays = currentTourDays(quoteData, option, tripCtx);
  return `الرحلة ${totalDays} أيام / ${nights} ليالي 👍 العرض الحالي فيه ${tourDays} أيام جولات — ونقدر نزيدها أو نقللها على راحتك.`;
}

function formatTourFlexibility(quoteData, option, tripCtx) {
  const tourDays = currentTourDays(quoteData, option, tripCtx);
  const next = tourDays + 1;
  return `العرض الحالي فيه ${tourDays} أيام جولات، بس عادي نقدر نعدله على راحتك 👍 إذا تحب ${next} جولات أضيف لك يوم جولة وأحسب لك السعر الجديد، وإذا تحب أقل نقدر نقللها برضه.`;
}

function formatTourModify(pkg, tourDays, adults) {
  const pax = adults || 2;
  const paxLabel = pax === 2 ? 'شخصين' : `${pax} أشخاص`;
  return `تمام، خليتها ${tourDaysLabel(tourDays)} 👍 السعر صار ${pkg.final_price_usd} دولار لـ${paxLabel}.`;
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
} else if (intent === 'package_tour_modify' && trip?.city && requestedTourDays != null) {
  routedBy = 'deterministic:package_tour_modify';
  const pkg = await fetchQuotePackage.call(this, trip, requestedTourDays);
  if (pkg) {
    const hotelName = pkg.hotel?.name || trip.hotel || null;
    response = formatTourModify(pkg, requestedTourDays, trip.adults);
    await persistPackagePrefs.call(this, trip, requestedTourDays, pkg.final_price_usd, hotelName);
  } else {
    response = PRICING_RETRY;
    await flagNeedsHuman.call(this);
  }
} else if (intent === 'package_price_confirm' && trip?.city) {
  routedBy = 'deterministic:package_price_confirm';
  const askedDays = requestedTourDays ?? trip.tour_days;
  if (askedDays != null && trip.tour_days === askedDays && trip.last_price) {
    response = `أيوه، هذا السعر على نفس ${trip.hotel || 'الفندق'} مع ${tourDaysLabel(askedDays)} 👍`;
  } else if (askedDays != null) {
    const pkg = await fetchQuotePackage.call(this, trip, askedDays);
    if (pkg) {
      const hotelName = pkg.hotel?.name || trip.hotel || null;
      response = `أيوه 👍 ${tourDaysLabel(askedDays)} على ${hotelName} — ${pkg.final_price_usd} دولار لشخصين.`;
      await persistPackagePrefs.call(this, trip, askedDays, pkg.final_price_usd, hotelName);
    } else {
      response = PRICING_RETRY;
      await flagNeedsHuman.call(this);
    }
  } else {
    response = PRICING_RETRY;
    await flagNeedsHuman.call(this);
  }
} else if (intent === 'package_same_hotel' && trip?.hotel) {
  routedBy = 'deterministic:package_same_hotel';
  response = `أيوه، نفس ${trip.hotel} 👍`;
  if (trip.tour_days != null && trip.last_price) {
    response += ` ${tourDaysLabel(trip.tour_days)} — ${trip.last_price} دولار لشخصين.`;
  }
} else if ((intent === 'package_tour_flexibility' || intent === 'package_composition') && trip?.city) {
  routedBy = 'deterministic:' + intent;
  const quoteData = await fetchQuoteOptions.call(this, trip, 'full');
  if (quoteData) {
    const option = pickQuoteOption(quoteData, trip);
    if (option) {
      response =
        intent === 'package_tour_flexibility'
          ? formatTourFlexibility(quoteData, option, trip)
          : formatPackageExplain(quoteData, option, trip);
    }
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

const packageIntents = [
  'package_tour_modify',
  'package_price_confirm',
  'package_same_hotel',
  'package_tour_flexibility',
  'package_composition',
];

if (isCircularHandoff(response) || (!response && packageIntents.includes(intent))) {
  response = PRICING_RETRY;
  routedBy = 'deterministic:pricing_retry';
  await flagNeedsHuman.call(this);
} else if (!response && trip?.city && /جول/.test(text)) {
  response = PRICING_RETRY;
  routedBy = 'deterministic:pricing_retry';
  await flagNeedsHuman.call(this);
}

if (intent === 'price_objection' && isCircularHandoff(response) && trip?.city) {
  const quoteData = await fetchQuoteOptions.call(this, trip, 'no_tours');
  if (quoteData) {
    response = formatQuoteReply(trip, quoteData, 'تمام، خليني أشوف لك خيارات أوفر 👍');
    routedBy = 'deterministic:pricing_engine_retry';
  }
}

if (!response) {
  response = PRICING_RETRY;
  routedBy = 'deterministic:pricing_retry';
  await flagNeedsHuman.call(this);
}

const followup = /دولار|\$|💵/.test(response);
return [{ json: { phone, remoteJid, response, isManager, followup, routedBy } }];
