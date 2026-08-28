const j = $input.first().json;
let t = String(j.output || j.text || j.response || '');
const RLM = String.fromCharCode(0x200F);
const WA = 'https://wa.me/380936582617';

// Strip markdown links [text](url) → url; fix duplicated wa.me
t = t.replace(/\[([^\]]*)\]\((https?:\/\/[^)]+)\)/g, '$2');
t = t.replace(/(\[https?:\/\/[^\]]+\]\([^)]+\)\s*)+/g, (m) => {
  const u = m.match(/https?:\/\/[^\s)]+/);
  return u ? u[0] : m;
});
const waMatches = t.match(/https:\/\/wa\.me\/\d+/g) || [];
if (waMatches.length > 1) {
  const first = waMatches[0];
  t = t.replace(/https:\/\/wa\.me\/\d+/g, '');
  t = t.trim() + '\n\n' + first;
}

const lines = t.split('\n').map((s) => s.replace(/[ \t]+$/, '')).filter((s) => s.trim().length);
const arr = [];
for (let l of lines) {
  l = l.replace(/^\u200F/, '');
  const m = l.match(/^\[\[CONFIRM\]\]\s*([\s\S]*)$/);
  if (m) {
    const msg = m[1].trim() || 'تأكيد باقة Arcadia';
    arr.push(RLM + 'تمام! 🎉 للتأكيد اضغط الرابط ويكمل معك فريقنا فوراً 👇');
    arr.push(WA + '?text=' + encodeURIComponent(msg));
  } else {
    arr.push(RLM + l);
  }
}
return [{ json: { output: arr.join('\n\n') } }];
