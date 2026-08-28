const j = $input.first().json;
let t = String(j.chatInput || '');
t = t.replace(/(\d+)\s*(ايام|أيام|يوم|يوماً)/g, (m, d) => {
  const n = parseInt(d, 10) - 1;
  return (n > 0 ? n : 1) + ' ليالي';
});
t = t.replace(/اسبوعين|أسبوعين/g, '13 ليالي');
t = t.replace(/(\d+)\s*(اسابيع|أسابيع)/g, (m, wk) => {
  const n = parseInt(wk, 10) * 7 - 1;
  return n + ' ليالي';
});
t = t.replace(/اسبوع|أسبوع/g, '6 ليالي');

const blocks = [];
if (j.leadContext) blocks.push('[بيانات العميل المحفوظة]\n' + j.leadContext);
if (j.chatHistory) {
  const hist = String(j.chatHistory);
  blocks.push('[آخر المحادثة]\n' + hist.slice(Math.max(0, hist.length - 2500)));
}
if (j.conversationHints) blocks.push('[إشارات]\n' + String(j.conversationHints));
if (j.context) blocks.push('[سياق]\n' + j.context);
if (j.managerInstructions) blocks.push('[تعليمات المدير]\n' + j.managerInstructions);

const prefix = blocks.length ? blocks.join('\n\n') + '\n\n[رسالة العميل]\n' : '';
const enriched = prefix + t;

return [{ json: Object.assign({}, j, { chatInput: enriched }) }];
