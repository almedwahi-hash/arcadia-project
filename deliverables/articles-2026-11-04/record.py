import json, sys
sys.stdout.reconfigure(encoding='utf-8')
R = 'C:/Users/Dell/Desktop/arcadia-project-repo/'
LOG = R + 'deliverables/backups/applied-via-admin-session-2026-10-02.json'
d = json.load(open(LOG, encoding='utf-8'))
d['content_round_2026-11-04'] = {
    'owner_instruction': 'راجع الموقع بشكل عام كامل … مقالات تحتاج إضافة … الموقع دائماً في حياة وحركة',
    'review': 'crawl clean (601 URLs); last post was 16 Oct (19 days); Search Console gaps: "السياحة في بولندا للعوائل" 228 impressions at position 26.7 with no dedicated page; no New Year 2027 content',
    'published': {
        '7882 AR': '/poland-for-families-guide/ — السياحة في بولندا للعوائل (cats 19,21; featured 2247; FAQ schema)',
        '7884 EN': '/en/poland-for-families/ — Poland for Families (cats 255,267; linked as translation of 7882)',
        '7883 AR': '/new-year-2027-family-trips/ — رأس السنة 2027 للعائلات: موسكو أم وارسو أم ألماتي؟ (cats 16,19,15,21; featured 5996)',
        '7886 EN': '/en/new-year-2027-family-trips-en/ — New Year 2027 for Gulf Families (cats 259,255,263,267; translation of 7883)',
    },
    'sources_html': 'deliverables/articles-2026-11-04/*.html',
    'inbound_links_added': ['AR: poland-for-saudis-2026, best-time-visit-poland-2026, poland-family-trip-cost, russia-for-saudis-2026, kazakhstan-for-saudis-2026, winter-tourism-kazakhstan, moscow-3-days-itinerary, warsaw-3-days-itinerary', 'EN: poland-for-saudi-travellers, best-time-to-visit-poland, cost-of-a-poland-trip-for-families…, russia-for-saudi-travellers, kazakhstan-for-saudi-travellers, moscow-in-3-days, warsaw-in-3-days'],
    'facts_used': 'prices reuse the owner-approved family figures (Poland 2,600–3,900 USD summer week; Russia family 3,070–3,500 USD base +15–25% New Year; Kazakhstan family 1,820–2,600 USD) marked approximate; GCC visa-free Russia and Kazakhstan (30 days); Schengen for Poland with UAE exempt; New Year 2027 is a Friday',
    'small_fixes': {'/en/the-complete-russia-tourism-program-12-days/': 'title shortened to 66 → "Russia 12-Day Programme: Moscow, Saint Petersburg and Kazan | Arcadia"', '/en/kazakhstan-tourism-program-7-days/': 'description trimmed to 146 chars'},
    'caches': 'LiteSpeed Purge All + Cloudflare Purge Everything',
    'search_console': 'indexing requested for the four new URLs (see status section)',
}
json.dump(d, open(LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

STATUS = R + 'deliverables/seo-site-audit-sep2026-status-ar.md'
s = open(STATUS, encoding='utf-8').read().rstrip('\n') + '''

## 40) جولة محتوى: مقالان جديدان بلغتين — 4 نوفمبر 2026

| البند | النتيجة |
|-------|---------|
| المراجعة | الموقع سليم تقنياً (601 رابط)، لكن آخر مقال نُشر في 16 أكتوبر، وفي Search Console كلمة «السياحة في بولندا للعوائل» بـ228 ظهوراً في المركز 27 بلا صفحة مخصصة، ولا محتوى لرأس السنة 2027. |
| ✅ نُشر | «السياحة في بولندا للعوائل 2026/2027» (عربي + إنجليزي) و«رأس السنة 2027 للعائلات الخليجية: موسكو أم وارسو أم ألماتي؟» (عربي + إنجليزي)، كلها بصورة مشاركة وFAQ منظمة ومرتبطة كترجمات. |
| الروابط الداخلية | سطر «اقرأوا أيضاً» في 15 مقالاً ذا صلة (8 عربية و7 إنجليزية). |
| إصلاحات صغيرة | عنوان برنامج روسيا 12 يوماً الإنجليزي قُصّر، ووصف برنامج كازاخستان 7 أيام الإنجليزي قُصّر إلى 146 حرفاً. |
| الكاش والفهرسة | فُرّغ LiteSpeed وCloudflare، وطُلبت فهرسة المقالات الأربعة. |
| ملاحظة للمالك | الأسعار في المقالين تقريبية ومبنية على أرقامكم المعتمدة سابقاً مع زيادة 15–25% لليالي رأس السنة؛ صحّحوها إن اختلفت عروضكم الفعلية. |
'''
open(STATUS, 'w', encoding='utf-8').write(s)

CHK = R + 'deliverables/seo-owner-checklist-sep2026-ar.md'
c = open(CHK, encoding='utf-8').read()
head, rest = c.split('\n', 1)
block = '''
> **تحديث 4 نوفمبر، محتوى جديد:** ✅ مقالان جديدان بلغتين: «السياحة في بولندا للعوائل» و«رأس السنة 2027 للعائلات: موسكو أم وارسو أم ألماتي؟»، مع روابط من 15 مقالاً وطلبات فهرسة. 🔎 راجعوا أسعار رأس السنة في المقال (تقريبية) إن كانت عروضكم الفعلية مختلفة. 💡 حساب Merchant Center الأوكراني القديم تُرك بلا إجراء بقراركم.
'''
open(CHK, 'w', encoding='utf-8').write(head + '\n' + block + rest)
print('ok')
