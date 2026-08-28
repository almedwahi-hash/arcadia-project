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

// Normalize days → nights
textContent = textContent.replace(/(\d+)\s*(ايام|أيام|يوم)/g, (m, d) => {
  const nights = parseInt(d, 10) - 1;
  return nights + ' ليالي';
});
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

function buildLeadStateSummary(lead) {
  if (!lead) return '';
  const parts = [];
  if (lead.name) parts.push('الاسم: ' + lead.name);
  if (lead.destination) parts.push('الوجهة: ' + lead.destination);
  if (lead.travel_dates) parts.push('التواريخ: ' + lead.travel_dates);
  if (lead.pax_adults != null) parts.push('الكبار: ' + lead.pax_adults);
  if (lead.pax_children != null) parts.push('الأطفال: ' + lead.pax_children);
  if (lead.children_ages) parts.push('أعمار الأطفال: ' + lead.children_ages);
  if (lead.stage) parts.push('المرحلة: ' + lead.stage);
  if (lead.offer_sent) parts.push('تم إرسال عرض');
  if (lead.objection_type) parts.push('اعتراض سابق: ' + lead.objection_type);
  if (lead.notes) parts.push('ملاحظات: ' + String(lead.notes).slice(0, 300));
  return parts.join(' | ');
}

const trimmed = textContent.trim();
const returningRx = /(خبرتكم|خبرتك|قلت\s*لك|قلت\s*لنا|قلت\s*لهم|سبق\s*و|قبل\s*كذا|قبل\s*قلت|انا\s*خبرت|أنا\s*خبرت|already\s*told|told\s*you)/i;
const newTripRx = /^(جديد|بداية\s*جديدة|new\s*trip|رحلة\s*جديدة|من\s*الاول|من\s*الأول)/i;
const greetingRx = /^(السلام|سلام|مرحبا|هلا|أهلا|ياهلا|صباح|مساء|هلو|hello|hi\b)/i;
const hotelOnlyRx = /(فندق\s*فقط|فنادق\s*بس|بس\s*فندق|فقط\s*فندق|hotel\s*only|بدون\s*جولات|بدون\s*استقبال|هذا\s*فنادق)/i;
const priceObjectionRx = /(غالي|غالية|سعركم|السعر\s*عالي|expensive|too\s*much|ارخص|أرخص)/i;
const goodbyeRx = /(لا\s*خلاص|خلاص\s*شكر|شكر\s*بس|ما\s*بغى|ما\s*ابغى|مو\s*مهتم|not\s*interested|thanks?\s*bye)/i;
const aiQuestionRx = /(انت\s*ذكاء|أنت\s*ذكاء|روبوت|bot|ai\b|ذكاء\s*اصطناع|إنسان|بشر|human)/i;

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

// Session reset ONLY on explicit new-trip intent — never wipe stored lead on simple greeting or returning customer
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
      lead.pax_children = null;
      lead.children_ages = null;
      lead.offer_sent = false;
      lead.notes = null;
    }
  } catch (e) {}
  try {
    const cutoff = new Date(Date.now() - 30000).toISOString();
    await this.helpers.httpRequest({
      method: 'DELETE',
      url: `${SB}/conversations?phone=eq.${phone}&created_at=lt.${encodeURIComponent(cutoff)}`,
      headers: h,
      returnFullResponse: true,
    });
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

let managerInstructions = '';
try {
  const inst = await this.helpers.httpRequest({
    method: 'GET',
    url: `${SB}/manager_instructions?active=eq.true&order=created_at.desc&limit=20`,
    headers: h,
  });
  if (inst.length > 0) managerInstructions = inst.map((i) => '- ' + i.instruction).join('\n');
} catch (e) {}

const leadStateSummary = buildLeadStateSummary(lead);
const conversationHints = [];
if (isReturningCustomer) {
  conversationHints.push('العميل يقول إنه سبق وأخبرنا — لا تعيدي سؤال التفاصيل المحفوظة؛ استخدمي leadContext فقط واسألي عن الناقص.');
}
if (leadHasStoredTrip(lead) && !isExplicitNewTrip) {
  conversationHints.push('يوجد بيانات رحلة محفوظة — لا تطلبي وجهة/تواريخ/عدد إذا موجودة؛ أكملي من حيث توقفتم.');
}
if (hotelOnlyRx.test(trimmed)) {
  conversationHints.push('تصحيح نطاق: العميل يريد فندق فقط — أكدي باختصار ثم طبّقي سياسة أركاديا (الحد الأدنى فندق+استقبال، جولات اختيارية).');
}
if (priceObjectionRx.test(trimmed)) {
  conversationHints.push('اعتراض سعر — ردّي باختصار «تمام، خليني أشوف لك خيارات أوفر 👍» ثم list_hotels أو get_package_quote؛ لا خصم مخترع.');
}
if (goodbyeRx.test(trimmed)) {
  conversationHints.push('العميل ينهي المحادثة — ردّ قصير طبيعي مثل «العفو، حياك الله 🌷» بدون فقرة ختامية طويلة.');
}
if (aiQuestionRx.test(trimmed)) {
  conversationHints.push('سؤال عن AI/إنسان — لا تدّعي أنكِ بشرية؛ قولي باختصار أنكِ ليلى مساعدة أركاديا.');
}

let context = '';
if (isManager) context = 'هذا المدير أبو أمير — عامليه كمديرك.';
else if (isNew) context = 'عميل جديد — عرّفي نفسك باختصار «أنا ليلى من أركاديا» فقط إذا يلزم.';
else if (isReturningCustomer || leadHasStoredTrip(lead)) context = 'عميل سابق — لا تعرّفي نفسك ولا تسألي تفاصيل محفوظة.';
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
    chatHistory,
    managerInstructions,
    context,
    conversationHints,
  },
}];
