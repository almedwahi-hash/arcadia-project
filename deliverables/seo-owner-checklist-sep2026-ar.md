# قائمة التنفيذ الموحّدة — arcadia-tour.com (30 سبتمبر 2026)

كل ما تبقّى بعد الفحص، مرتّب حسب الأولوية. نفّذه بالترتيب. أمام كل بند مكان التنفيذ بالضبط.

## أ) داخل WordPress (https://arcadia-tour.com/wp-admin/)

### 1. الإضافات
- **الإضافات → Jetpack → تعطيل** (ثم حذف إن لم تحتاجه).
- (اختياري، أمان) **الإضافات → Cowboy MCP → تعطيل** و **WPVibe → تعطيل** إن لم تستخدمهما فعلياً — لهما صلاحية كتابة ملفات وتشغيل أوامر على الموقع.

### 2. قواعد التحويل — أدوات → Redirection → Add new
أضف كل سطر كقاعدة منفصلة. عمود Regex يعني تعليم مربع «Regex».

| # | Source URL | Regex | Target URL |
|---|-----------|-------|------------|
| 1 | `^/t-en/?$` | ✓ | `/en/home/` |
| 2 | `^/t-(fr-fr\|ar\|ru\|de\|tr)/?$` | ✓ | `/` |
| 3 | `^/t-[a-z-]+/(.+)$` | ✓ | `/$1` |
| 4 | `/kazakhstan-family-children-trip/` | | `/kazakhstan-family-trip-cost-2026/` |
| 5 | `/kolsai-lake-day-trip/` | | `/almaty-guide/` |
| 6 | `/mountain-resorts-south-poland/` | | `/poland-guide/` |
| 7 | `^/السياحه-في-اوكرانيا/?$` | ✓ | `/السياحة-في-أوكرانيا/` |
| 8 | `^/أخبار-أوكرانيا/?$` | ✓ | `/category/ukraine/` |
| 9 | `/?p=528` — وفي خيارات المطابقة (Query parameters) اختر **Exact match** | | `/almaty-guide/` |
| 10 | `/?page_id=596` — نفس الخيار Exact match | | `/why-travel-to-uzbekistan/` |

ثم: **Redirection → Options → 404 Logs: تفعيل لمدة أسبوع** لالتقاط ما تبقّى.

### 3. Snippet #23 — Snippets → «Arcadia Homepage SEO Hub»
ابحث عن السطر الثاني من نوع `if ( ! is_front_page() || is_admin() ) {` (الموجود داخل `add_action( 'wp_footer', ...` )، وبعد قوس الإغلاق `}` الذي يليه مباشرة أضف:
```php
if ( function_exists( 'pll_current_language' ) && 'ar' !== pll_current_language( 'slug' ) ) { return; }
```
احفظ. النتيجة: الكتلة العربية «أدلة السفر 2026» تختفي من الرئيسية الإنجليزية فقط.

### 4. Schema المكررة — WPCode → Header & Footer
ابحث في مربع Header عن `aggregateRating` و عن `FAQPage`. إن وجدتهما:
- كتلة `TravelAgency/LocalBusiness` مع التقييم 7546: اتركها للرئيسية فقط. الأسهل: احذفها من WPCode (الرئيسية تحتوي أصلاً على TravelAgency + التقييم من Snippet #23).
- كتلة FAQ الشركة (3 أسئلة: الدول، كيف أحجز، مرشدون عرب): احذفها من WPCode، وأضف الأسئلة الثلاثة كـ FAQ block من Yoast داخل صفحة «تواصل معنا» أو الرئيسية فقط.
إن لم تجدهما في WPCode، ابحث في: **Snippets → Settings**، ثم **Elementor → Custom Code**.

### 5. السرعة — LiteSpeed Cache
- **Page Optimization → JS Settings:** Load JS Deferred = **Delayed**. Delayed JS Inclusion أضف:
  ```
  googletagmanager.com
  connect.facebook.net
  analytics.tiktok.com
  ```
- **Page Optimization → Media Settings:** Lazy Load Images = **ON**.
- **Image Optimization:** Image WebP Replacement = **ON** → ثم زر **Send Optimization Request**.
- **Cache → Browser Cache = ON.**
- افتح الموقع على الجوال بعدها وتأكد أن القوائم والأزرار تعمل. إن تعطّل شيء، أرجع Load JS Deferred إلى **Deferred**.

### 6. صورة المشاركة الاجتماعية للرئيسية الإنجليزية
**الصفحات → Home (English) → Yoast SEO → Social → Facebook image** → اختر نفس صورة الرئيسية العربية (`normal_67d61036a4336.jpg`) → تحديث.

### 7. تفريغ الكاش (بعد كل ما سبق)
- **LiteSpeed Cache → Purge All.**
- Cloudflare → الموقع → **Caching → Configuration → Purge Everything.**

### 8. أمان الحساب (في النهاية)
- **المستخدمون → ملفك الشخصي → Application Passwords → Revoke** لكلمة مرور التطبيق `claude`.
- **غيّر كلمة مرور حساب admin** (كانت مكشوفة في ملفات المشروع).

## ب) خارج WordPress

### 9. Google Search Console (https://search.google.com/search-console)
- الملكية الأساسية: `https://arcadia-tour.com/` (بدون www).
- **Sitemaps** → أرسل `https://arcadia-tour.com/sitemap_index.xml`.
- **Removals → New request → Remove all URLs with this prefix:** `https://www.arcadia-tour.com/t-en/` ثم `https://www.arcadia-tour.com/t-fr-fr/` (بعد إضافة التحويلات).
- **URL Inspection → Request indexing** للرئيسية العربية والإنجليزية وصفحة «تواصل معنا» حتى يظهر الرقم الجديد.

### 10. Google Business Profile
تأكد أن رقم الهاتف/واتساب هو `+7 706 400 7561`.

### 11. Hostinger (https://hpanel.hostinger.com)
- إن كان الموقع على الـ VPS `srv1164410`: **VPS → Backups → فعّل Daily backups** (الرسائل تقول إنها غير مفعّلة).
- إن كان على استضافة WordPress المُدارة: **Websites → arcadia-tour.com → Backups** وتأكد من وجود نسخة خلال آخر 24 ساعة.
- **Security → SSL:** الشهادة نشطة + Force HTTPS.
- (لاحقاً) أنشئ **API token** من Account → API لأراجع الاستضافة مباشرة.

### 12. Windsor.ai (بيانات Search Console)
https://onboard.windsor.ai/app/ → افصل الحسابات غير الضرورية وأبقِ `searchconsole → https://arcadia-tour.com/` فقط، أو رقِّ الخطة.

## بعد الانتهاء
اكتب «تم» في المحادثة، وسأفحص الموقع كاملاً من جديد (التحويلات، الكاش، الرئيسية الإنجليزية، السرعة) وأعطيك تقرير ما قبل/بعد.
