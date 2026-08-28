// Shared trip extraction + intent flags (Parse + CRM)
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';

function arToEnDigits(s) {
  return String(s || '').replace(/[٠-٩]/g, (d) => String(AR_DIGITS.indexOf(d)));
}

function parseTripContext(history) {
  if (!history) return null;
  const h = arToEnDigits(history);
  const out = { destination: null, city: null, nights: null, adults: null, travel_dates: null, last_price: null };

  if (/ألماتي|Almaty/i.test(h)) {
    out.destination = 'كازاخستان';
    out.city = 'Almaty';
  } else if (/مоск|Moscow/i.test(h)) {
    out.destination = 'روسيا';
    out.city = 'Moscow';
  } else if (/سانت|Saint Petersburg/i.test(h)) {
    out.destination = 'روسيا';
    out.city = 'Saint Petersburg';
  } else if (/سمرقند|Samarkand/i.test(h)) {
    out.destination = 'أوزبكستان';
    out.city = 'Samarkand';
  }

  const nightsM = h.match(/(\d+)\s*ليالي/);
  if (nightsM) out.nights = parseInt(nightsM[1], 10);

  if (/شخصين|شخصان/.test(history)) out.adults = 2;
  else {
    const paxM = h.match(/(\d+)\s*(?:شخص|أشخاص|كبار|بالغ)/);
    if (paxM) out.adults = parseInt(paxM[1], 10);
  }

  const dateM = h.match(/(\d{1,2})\s*(يناير|فبراير|مارس|أبril|ابril|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s*[–-]\s*(\d{1,2})\s*(يناير|فبراير|مارس|أبril|ابril|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)/i);
  if (dateM) out.travel_dates = `${dateM[1]} ${dateM[2]} – ${dateM[3]} ${dateM[4]}`;

  const prices = [...h.matchAll(/(\d{3,4})\s*دولار/g)].map((m) => m[1]);
  if (prices.length) out.last_price = prices[0];

  if (!out.city && !out.nights && !out.adults) return null;
  return out;
}

function tripContextSummary(trip) {
  if (!trip) return '';
  const parts = [];
  if (trip.destination) parts.push('الوجهة: ' + trip.destination);
  if (trip.city) parts.push('المدينة: ' + trip.city);
  if (trip.travel_dates) parts.push('التواريخ: ' + trip.travel_dates);
  if (trip.nights != null) parts.push('الليالي: ' + trip.nights);
  if (trip.adults != null) parts.push('الكبار: ' + trip.adults);
  if (trip.last_price) parts.push('آخر سعر معروض: ' + trip.last_price + ' دولار');
  return parts.join(' | ');
}

const body = $input.first().json.body || $input.first().json;
const data = body.data || body;
const key = data.key || {};
const remoteJid = key.remoteJid || '';
const phone = remoteJid.replace('@s.whatsapp.net', '').replace('@g.us', '');

if (key.fromMe) return [];

const message = data.message || {};
const messageType = data.messageType || 'unknown';
let textContent = '';
if (messageType === 'conversation') textContent = message.conversation || '';
else if (messageType === 'extendedTextMessage') textContent = (message.extendedTextMessage || {}).text || '';
else if (messageType === 'audioMessage') textContent = '[رسالة صوتية]';
else textContent = message.conversation || message.text || '';

textContent = textContent.replace(/(\d+)\s*(ايام|أيام|يوم)/g, (m, d) => `${parseInt(d, 10) - 1} ليالي`);
textContent = textContent.replace(/اسبوعين|أسبوعين/g, '13 ليالي');
textContent = textContent.replace(/اسبوع|أسبوع/g, '7 ليالي');
textContent = textContent.replace(/عشر ايام|عشرة ايام|عشر أيام|عشرة أيام/g, '9 ليالي');
textContent = textContent.replace(/خمسة ايام|خمس ايام|خمسة أيام/g, '4 ليالي');
textContent = textContent.replace(/ستة ايام|ست ايام/g, '5 ليالي');

const MANAGER_PHONE = '380936582617';
const isManager = phone === MANAGER_PHONE;
const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '') + '/rest/v1';
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) throw new Error('SUPABASE_KEY required');
const h = { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' };

function leadHasStoredTrip(lead) {
  if (!lead) return false;
  return !!(lead.destination || lead.travel_dates || lead.pax_adults || lead.pax_children || lead.notes);
}

function buildLeadStateSummary(lead, tripCtx) {
  const parts = [];
  if (lead?.name) parts.push('الاسم: ' + lead.name);
  if (lead?.destination) parts.push('الوجهة: ' + lead.destination);
  else if (tripCtx?.destination) parts.push('الوجهة: ' + tripCtx.destination);
  if (lead?.travel_dates) parts.push('التواريخ: ' + lead.travel_dates);
  else if (tripCtx?.travel_dates) parts.push('التواريخ: ' + tripCtx.travel_dates);
  if (lead?.pax_adults != null) parts.push('الكبار: ' + lead.pax_adults);
  else if (tripCtx?.adults != null) parts.push('الكبار: ' + tripCtx.adults);
  if (lead?.pax_children != null) parts.push('الأطفال: ' + lead.pax_children);
  if (tripCtx?.nights != null) parts.push('الليالي: ' + tripCtx.nights);
  if (tripCtx?.city) parts.push('المدينة: ' + tripCtx.city);
  if (tripCtx?.last_price) parts.push('آخر سعر: ' + tripCtx.last_price + ' دولار');
  if (lead?.stage) parts.push('المرحلة: ' + lead.stage);
  if (lead?.offer_sent) parts.push('تم إرسال عرض');
  if (lead?.notes) parts.push('ملاحظات: ' + String(lead.notes).slice(0, 200));
  return parts.join(' | ');
}

const trimmed = textContent.trim();
const returningRx = /(خبرتكم|خبرتك|قلت\s*لك|قلت\s*لنا|سبق\s*و|قبل\s*كذا|انا\s*خبرت|أنا\s*خبرت|from\s*before)/i;
const newTripRx = /^(جديد|بداية\s*جديدة|new\s*trip|رحلة\s*جديدة|من\s*الاول|من\s*الأول)/i;
const greetingRx = /^(السلام|سلام|مرحبا|هلا|أهلا|ياهلا|صباح|مساء|هلو|hello|hi\b)/i;
const hotelOnlyRx = /(فندق\s*فقط|فنادق\s*بس|فندق\s*بس|بس\s*فندق|احتاج\s*فندق|hotel\s*only|هذا\s*فنادق)/i;
const priceObjectionRx = /(غالي|غالية|سعركم|السعر\s*عالي|expensive|too\s*much|ارخص|أرخص)/i;
const goodbyeRx = /(لا\s*خلاص|خلاص\s*شكر|شكر\s*بس|ما\s*بغى|ما\s*ابغى|مو\s*مهتم|not\s*interested)/i;
const aiQuestionRx = /(موظف|موظفه|موظفة|إنسان|بشر|human|robot|روبوت|bot\b|ai\b|ذكاء\s*اصطناع|انت\s*ذكاء|أنت\s*ذكاء|انتي\s*موظف|أنتي\s*موظف)/i;
const driverLangRx = /(السواق|السائق|سائق|driver).*(عربي|arabic|يتكلم|يتحدث|speak)/i;
const opsFactRx = /(الغاء|إلغاء|cancellation|طريق[ةه]\s*الدفع|payment\s*method|مرافق|facility|policy)/i;

const isReturningCustomer = returningRx.test(trimmed);
const isExplicitNewTrip = newTripRx.test(trimmed);
const isGreeting = greetingRx.test(trimmed);

let isNew = false;
let lead = null;
try {
  const r = await this.helpers.httpRequest({ method: 'GET', url: `${SB}/leads?phone=eq.${phone}&limit=1`, headers: h });
  if (r.length > 0) {
    lead = r[0];
    await this.helpers.httpRequest({
      method: 'PATCH',
      url: `${SB}/leads?phone=eq.${phone}`,
      headers: { ...h, Prefer: 'return=minimal' },
      body: { last_contact: new Date().toISOString(), updated_at: new Date().toISOString() },
    });
  } else {
    isNew = true;
    if (!isManager) {
      const r2 = await this.helpers.httpRequest({
        method: 'POST',
        url: `${SB}/leads`,
        headers: { ...h, Prefer: 'return=representation' },
        body: { phone, stage: 'new', assigned_to: 'bot', source: 'direct', last_contact: new Date().toISOString() },
      });
      lead = r2[0] || null;
    }
  }
} catch (e) {}

if (!isManager) {
  try {
    await this.helpers.httpRequest({
      method: 'POST',
      url: `${SB}/conversations`,
      headers: { ...h, Prefer: 'return=minimal' },
      body: { phone, role: 'user', message: textContent },
    });
  } catch (e) {}
}

const shouldResetLead = isExplicitNewTrip && phone && !isReturningCustomer;
if (shouldResetLead) {
  try {
    await this.helpers.httpRequest({
      method: 'PATCH',
      url: SB + '/leads?phone=eq.' + phone,
      headers: { ...h, Prefer: 'return=minimal' },
      body: {
        stage: 'new',
        destination: null,
        travel_dates: null,
        pax_adults: null,
        pax_children: null,
        children_ages: null,
        offer_sent: false,
        notes: null,
        next_followup: null,
        follow_up_count: 0,
        objection_type: null,
        needs_human: false,
        updated_at: new Date().toISOString(),
      },
    });
    if (lead) {
      lead.stage = 'new';
      lead.destination = null;
      lead.travel_dates = null;
      lead.pax_adults = null;
    }
  } catch (e) {}
}

let chatHistory = '';
try {
  const msgs = await this.helpers.httpRequest({
    method: 'GET',
    url: `${SB}/conversations?phone=eq.${phone}&order=id.asc&limit=30`,
    headers: h,
  });
  chatHistory = msgs.map((m) => (m.role === 'user' ? 'العميل' : 'ليلى') + ': ' + m.message).join('\n');
} catch (e) {}

const tripFromHistory = parseTripContext(chatHistory);

// Backfill lead CRM from chat when empty (root cause: quotes never persisted)
if (tripFromHistory && lead && !leadHasStoredTrip(lead) && phone && !isManager) {
  const patch = { updated_at: new Date().toISOString() };
  if (tripFromHistory.destination) patch.destination = tripFromHistory.destination;
  if (tripFromHistory.travel_dates) patch.travel_dates = tripFromHistory.travel_dates;
  if (tripFromHistory.adults != null) patch.pax_adults = tripFromHistory.adults;
  if (tripFromHistory.nights != null) patch.notes = `nights=${tripFromHistory.nights};city=${tripFromHistory.city || ''}`;
  try {
    await this.helpers.httpRequest({
      method: 'PATCH',
      url: `${SB}/leads?phone=eq.${phone}`,
      headers: { ...h, Prefer: 'return=minimal' },
      body: patch,
    });
    Object.assign(lead, patch);
  } catch (e) {}
}

let managerInstructions = '';
try {
  const inst = await this.helpers.httpRequest({
    method: 'GET',
    url: `${SB}/manager_instructions?active=eq.true&order=created_at.desc&limit=20`,
    headers: h,
  });
  if (inst.length > 0) managerInstructions = inst.map((i) => '- ' + i.instruction).join('\n');
} catch (e) {}

const leadStateSummary = buildLeadStateSummary(lead, tripFromHistory);
const hasTripContext = !!(leadStateSummary && !/^المرحلة:\s*new\s*$/.test(leadStateSummary));

let conversationIntent = 'general';
if (goodbyeRx.test(trimmed)) conversationIntent = 'goodbye';
else if (aiQuestionRx.test(trimmed)) conversationIntent = 'ai_identity';
else if (driverLangRx.test(trimmed) || (opsFactRx.test(trimmed) && !/طريق[ةه]\s*الدفع/.test(trimmed))) conversationIntent = 'ops_unknown';
else if (hotelOnlyRx.test(trimmed)) conversationIntent = 'hotel_only';
else if (priceObjectionRx.test(trimmed)) conversationIntent = 'price_objection';
else if (isReturningCustomer) conversationIntent = 'returning_customer';

const conversationHints = [];
if (conversationIntent === 'returning_customer' && hasTripContext) {
  conversationHints.push('استخدمي بيانات المحادثة/leadContext — لا تعيدي سؤال التفاصيل.');
}
if (conversationIntent === 'price_objection') {
  conversationHints.push('اعتراض سعر — استخدمي Pricing Engine فقط.');
}

let context = '';
if (isManager) context = 'هذا المدير أبو أمير — عامليه كمديرك.';
else if (isNew) context = 'عميل جديد — عرّفي نفسك باختصار «أنا ليلى من أركاديا» فقط إذا يلزم.';
else if (isReturningCustomer || hasTripContext) context = 'عميل سابق — لا تعرّفي نفسك ولا تسألي تفاصيل محفوظة.';
else if (isGreeting) context = 'تحية — ردّي باختصار واسألي فقط عن الناقص.';
else context = 'عميل سابق — لا تعرّفي نفسك.';
if (leadStateSummary) context += ' بيانات محفوظة: ' + leadStateSummary + '.';

const enWords = (textContent.match(/[a-zA-Z]{3,}/g) || []).length;
const totalWords = textContent.trim().split(/\s+/).length;
const customerLanguage = enWords / Math.max(totalWords, 1) > 0.5 ? 'en' : 'ar';

return [{
  json: {
    phone,
    remoteJid,
    textContent,
    customerLanguage,
    isManager,
    isNew,
    lead,
    leadStateSummary,
    tripFromHistory,
    chatHistory,
    managerInstructions,
    context,
    conversationHints,
    conversationIntent,
  },
}];
