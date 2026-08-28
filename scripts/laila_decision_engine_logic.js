// Laila WhatsApp → AI agent with lead/conversation context (conversation-behavior patch)
const phone = $json.phone;
const remoteJid = $json.remoteJid;
const text = $json.textContent || $json.text || '';
const isManager = $json.isManager || false;

const payload = {
  action: 'sendMessage',
  sessionId: String(phone || 'wa'),
  chatInput: text,
  leadContext: $json.leadStateSummary || '',
  chatHistory: $json.chatHistory || '',
  managerInstructions: $json.managerInstructions || '',
  context: $json.context || '',
  conversationHints: ($json.conversationHints || []).join('\n'),
  customerLanguage: $json.customerLanguage || 'ar',
};

let response = '';
try {
  const res = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://n8n.arcadia-tour.cloud/webhook/cc004272-5e46-4e5c-be6d-ba84fdf35258/chat',
    body: payload,
    json: true,
    timeout: 90000,
  });
  if (typeof res === 'string') {
    try {
      response = JSON.parse(res).output;
    } catch (e) {
      response = res;
    }
  } else {
    response = (res && (res.output || res.text || res.response)) || '';
  }
} catch (e) {
  response = '';
}
if (!response) {
  response =
    'أهلاً 👋 صار خطأ تقني بسيط، جرّب ترسل طلبك مرة ثانية أو تواصل معنا واتساب: https://wa.me/380936582617';
}
const followup = /دولار|\$|💵/.test(response);
return [{ json: { phone, remoteJid, response, isManager, followup } }];
