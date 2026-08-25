# سجل تحسينات WordPress — 25 أغسطس 2026

**الموقع:** https://arcadia-tour.com/  
**الفرع:** `cursor/seo-full-site-audit-3b47`  
**ملاحظة Cloudflare MCP:** لم يتصل في جلسة Cloud Agent (يتطلب تفعيل MCP من لوحة cursor.com/agents).

---

## ✅ ما تم تنفيذه بنجاح

### 1) تحسين Yoast Title / Meta Description

| الصفحة | ID | بعد (مؤكد من الواجهة) |
|--------|-----|------------------------|
| العروض والحجوزات | 785 | **العروض والحجوزات \| برامج أركاديا — كازاخستان روسيا بولندا** |
| وجهاتنا السياحية | 3629 | **وجهاتنا السياحية \| أركاديا — كازاخستان روسيا بولندا أوزبكستان الصين** |

### 2) noindex — صفحات عقارات فرعية (Yoast مباشرة)

IDs: 1028, 1029, 1030, 1031, 1033, 1064, 1072, 1073, 1074, 1075, 2642, 854, 1015, 1024

### 3) noindex — صفحات علاج أمراض تفصيلية (Yoast مباشرة)

IDs: 923, 924, 925, 926, 927, 928

### 4) noindex — Code Snippet #20 (Aug 2025)

**Snippet:** `Arcadia Low-Value Pages Noindex 2026-08-25` — active via REST API

| ID | URL | نوع | الحالة |
|----|-----|-----|--------|
| 800 | `/search-programs/` | page | **noindex** ✅ |
| 604 | `/real-estate-ukraine/` | page (hub) | **noindex** ✅ |
| 555 | `/old-post-555/` | post | **noindex** ✅ |
| 559 | `/old-post-559/` | post | **noindex** ✅ |
| 564 | `/old-post-564/` | post | **noindex** ✅ |

### 5) Purge Cache

LiteSpeed Purge All + LSCache + Cloudflare (via LiteSpeed CDN) ✅

---

## ✅ قرار الإدارة — Schema 7546

**الإبقاء** — الرقم يعكس قاعدة عملاء حقيقية (+10 سنوات). لم يُمس.

---

## ❌ ما لم يُمس (حسب قراركم)

- **صفحات السياحة في أوكرانيا** — `index, follow` ✅
- **Schema aggregateRating 7546** — **يبقى كما هو** ✅
- **Rank Math** — غير مثبت

---

## ✅ جولة 5–6 — GSC + الصين (25 أغسطس 2026 — 23:10 UTC)

- **GSC:** المستخدم أكمل external action (sitemap + indexing)
- **4595** `/china-family-trip-cost-2026/` — مقال الصين
- **Snippet #22/23** محدّثان — 7 slugs + homepage hub
- **post-sitemap.xml** — كل المقالات الجديدة ✅

---

## ✅ جولة 4 — أوزبكستان + موسكو + Homepage (25 أغسطس 2026 — 22:40 UTC)

| ID | URL | ملاحظة |
|----|-----|--------|
| 4593 | `/uzbekistan-family-trip-cost-2026/` | جديد |
| 4594 | `/best-time-visit-moscow-2026/` | جديد |
| — | `/poland-family-trip-cost/` | Yoast + hub عبر Snippet #22 |
| — | `/` | Snippet #23: meta + TravelAgency + guides hub |

**Snippets:** #22 محدّث (6 slugs) · #23 جديد (Homepage SEO Hub)

---

## ✅ جولة 3 — محتوى + Snippet #22 (25 أغسطس 2026 — 22:10 UTC)

### مقالات جديدة (3)

| ID | URL | فئة |
|----|-----|-----|
| 4586 | `/kazakhstan-family-trip-cost-2026/` | كازاخستان (15) |
| 4587 | `/best-time-visit-almaty-2026/` | كازاخستان (15) |
| 4592 | `/russia-family-trip-cost-2026/` | روسيا (16) |

### Snippet #22

`Arcadia Blog SEO Engine 2026-08-25` — FAQ schema + hub footer + Yoast override بالـ slug.

### تحقق

```
/kazakhstan-family-trip-cost-2026/  → index + FAQPage + hub ✅
/best-time-visit-almaty-2026/       → index + FAQPage + hub ✅ (نص عربي مُصلَح)
/russia-family-trip-cost-2026/      → index + FAQPage + hub ✅ (جديد)
/post-sitemap.xml                   → الثلاثة URLs موجودة ✅
```

---

## التحقق النهائي (25 أغسطس 2026 — 21:42 UTC)

```
/offers-bookings/              → title محسّن + index ✅
/destinations/                 → title محسّن + index ✅
/search-programs/              → noindex ✅
/real-estate-ukraine/          → noindex ✅
/real-estate-ukraine/odessa/   → noindex ✅
/old-post-555/559/564/         → noindex ✅
/tourism-in-ukraine/           → index ✅
```

---

## ✅ جولة 7 — Alt Text + ربط 7 أدلة (25 أغسطس 2026 — 23:30 UTC)

### Snippet #24 — `Arcadia Alt Text SEO Engine 2026-08-25` (active)

- خريطة alt لـ **21** صورة SEO (infographics + heroes + بطاقات برامج)
- فلتر `wp_get_attachment_image_attributes` + `the_content` لملء alt الفارغ
- heuristics من اسم الملف: russia, poland, uzbek, kazakh, almaty, moscow, china

### Snippet #22 — تحديث

- بلوك **«دلائل الأسعار والمواسم 2026»** (`arcadia-all-guides-2026`) — روابط الـ 7 أدلة في footer كل مقال

### تحديث alt في المكتبة (REST)

IDs: 4306, 4345, 4351, 4347, 4349, 791–798, 779, 782–783, 1862–1864, 1870, 1903, 4573, 4576

### تحقق live (بعد purge + `?v=` cache-bust)

```
7/7 guides → hub + guides7 + FAQPage ✅
media 4306 → alt: إنفوجرافيك تكلفة روسيا ✅
pillar روسيا → alt على صور الوجهة ✅
```

### Outreach

- حزمة جاهزة: `deliverables/seo-outreach-pack-ar.md`

---

## الخطوة التالية (اختياري)

1. تنفيذ outreach — 10 رسائل أسبوع 1 من الحزمة  
2. Cloudflare MCP من Agent جديد لمراجعة Cache/Speed
