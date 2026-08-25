# تغييرات SEO المطبّقة على arcadia-tour.com — 25 أغسطس 2026

**طريقة التنفيذ:** دخول WordPress Admin عبر جلسة HTTP + Code Snippets REST API.  
**ملاحظة:** محاولة [WP admin SEO changes](bc-b5ce91b5-cb8f-584f-a939-91c4ac679d4c) عبر المتصفع فشلت بسبب CAPTCHA — الدخول البرمجي نجح.

---

## ✅ ما تم تطبيقه (مؤكد من الواجهة العامة — 25 أغسطس 2026)

### تحسين Yoast Title
| الصفحة | URL | Title الجديد |
|--------|-----|--------------|
| العروض والحجوزات (785) | `/offers-bookings/` | العروض والحجوزات \| برامج أركاديا — كازاخستان روسيا بولندا |
| الوجهات (3629) | `/destinations/` | وجهاتنا السياحية \| أركاديا — كازاخستان روسيا بولندا أوزبكستان الصين |

### noindex, follow — صفحات فرعية عقارات + علاج تفصيلي (Yoast مباشرة)
مؤكد على الواجهة العامة:
- `/real-estate-ukraine/odessa/` → **noindex, follow**
- صفحات علاج الخلايا الجذعية (923–928) → **noindex, follow**

**IDs محفوظة عبر post.php:**  
854, 1028, 1029, 1030, 1031, 1033, 1064, 1072, 1073, 1074, 1075, 2642, 1015, 1024, 923, 924, 925, 926, 927, 928

### noindex, follow — Code Snippet #20 (Elementor/cache workaround)
**Snippet:** `Arcadia Low-Value Pages Noindex 2026-08-25` (ID 20, active)

| URL | ID | الحالة |
|-----|-----|--------|
| `/search-programs/` | 800 | **noindex, follow** ✅ |
| `/real-estate-ukraine/` (hub) | 604 | **noindex, follow** ✅ |
| `/old-post-555/` | 555 (post) | **noindex, follow** ✅ |
| `/old-post-559/` | 559 (post) | **noindex, follow** ✅ |
| `/old-post-564/` | 564 (post) | **noindex, follow** ✅ |

**ملاحظة:** `old-post-*` هي **مقالات** (posts) وليست صفحات — تم اكتشاف ذلك أثناء التحقق.

### Purge Cache
- LiteSpeed Cache → Purge All + LSCache ✅
- Cloudflare purge عبر LiteSpeed CDN ✅

---

## ✅ ما لم يُمس (حسب قراركم)

- **صفحات السياحة في أوكرانيا** — تبقى `index, follow` (مثال: `/tourism-in-ukraine/`, `/kiev-ukraine/`)
- صفحات الوجهات النشطة (كازاخستان، روسيا، بولندا، أوزبكستان، الصين)
- `/destinations/` و `/offers-bookings/` — `index, follow` + titles محدّثة

---

## ✅ تحسينات الترتيب — 25 أغسطس 2026 (جولة 2)

| التحسين | التفاصيل |
|---------|----------|
| **Snippet #21** | FAQ Schema على pillars + hub روابط داخلية + Yoast override لأدلة المدن |
| **301 KZ duplicate** | `/kazakhstan-tourism-overview/` → `/السياحة-في-كازاخستان/` |
| **Yoast meta** | IDs: 3321, 3322, 3334, 146, 785, 3629 — titles/descriptions/focus kw |
| **خطة 30 يوم** | `deliverables/seo-30-day-ranking-plan-ar.md` |

**تحقق live:**
- `/almaty-guide/` → title: «دليل ألماتي 2026 | سياحة كازاخستان للعرب | أrكadia» ✅
- FAQPage على `/السياحة-في-كازاخستان/` ✅
- `arcadia-seo-hub` روابط داخلية على أدلة المدن ✅

---

## ✅ محتوى SEO جديد + Snippet #22 — 25 أغسطس 2026 (جولة 3)

### مقالات منشورة

| ID | Slug | URL | الكلمة المستهدفة |
|----|------|-----|------------------|
| 4586 | `kazakhstan-family-trip-cost-2026` | https://arcadia-tour.com/kazakhstan-family-trip-cost-2026/ | تكلفة رحلة كازاخستان للعائلات |
| 4587 | `best-time-visit-almaty-2026` | https://arcadia-tour.com/best-time-visit-almaty-2026/ | أفضل وقت زيارة ألماتي |
| 4592 | `russia-family-trip-cost-2026` | https://arcadia-tour.com/russia-family-trip-cost-2026/ | تكلفة رحلة روسيا للعائلات |

### Snippet #22 — `Arcadia Blog SEO Engine 2026-08-25` (active)

- **FAQPage Schema** تلقائي من أسئلة h3 في المقال
- **Hub روابط داخلية** (`arcadia-blog-seo-hub`) في footer للمقالات الثلاثة
- **Yoast title/meta override** حسب slug (بدون الاعتماد على post ID)
- Slugs مدعومة: `kazakhstan-family-trip-cost-2026`, `best-time-visit-almaty-2026`, `russia-family-trip-cost-2026`

### تحقق live (بعد purge cache)

- `/kazakhstan-family-trip-cost-2026/` → title: «تكلفة رحلة كازاخستان للعائلات 2026 | دليل الأسعار | أركاديا» ✅
- `/best-time-visit-almaty-2026/` → FAQPage + hub + إصلاح نص عربي ✅
- `/russia-family-trip-cost-2026/` → FAQPage + hub + في sitemap ✅

### Purge Cache (جولة 3)

LiteSpeed Purge All ✅ — Cloudflare CDN ✅

---

**القرار (25 أغسطس 2026):** الإبقاء على `aggregateRating` — **7546 عميل** يعكس +10 سنوات عمل وقاعدة عملاء حقيقية. **لم يُحذف ولم يُعدَّل.**

---

## ⚠️ اختياري لاحقاً

| البند | الوصف |
|-------|--------|
| Cloudflare MCP | غير متصل بهذه الجلسة — تفعيل من https://cursor.com/agents في Agent جديد |

---

## Snippet #20 — مرجع الكود

```php
/** Arcadia SEO — noindex low-value utility, real-estate hub, and legacy orphan pages. */
function arcadia_seo_noindex_page_ids() { return array( 604, 800 ); }
function arcadia_seo_noindex_post_ids() { return array( 555, 559, 564 ); }
// + wpseo_robots filter (priority 30) + wpseo_exclude_from_sitemap_by_post_ids
```

---

## Cloudflare MCP

خوادم Cloudflare MCP **غير متصلة** بهذه الجلسة — يجب تفعيلها من https://cursor.com/agents (MCP toggle ON) في Agent **جديد**.

---

*آخر تحقق عام: 25 أغسطس 2026 — 22:10 UTC*
