# جرد الصفحات الإنجليزية بلا أصل عربي مربوط — 3 أكتوبر 2026

الطريقة: فُحص hreflang في كل الصفحات والمقالات الإنجليزية (247) والعربية (278) على الخادم مباشرة. الصفحة «اليتيمة» هي التي لا تشير إلى مقابل فعلي في اللغة الأخرى (تشير إلى الصفحة الرئيسية بسبب خلل سنِبِت hreflang الموثَّق في قائمة التنفيذ).

## الخلاصة

- **24 صفحة إنجليزية** بلا أصل عربي (ملخص الزحف كان يعرض 12 فقط لأنه يقتطع القائمة).
- **12 صفحة عربية** بلا مقابل إنجليزي: 7 مقالات معروفة (4 تكلفة تنتظر الأسعار و3 مكررة)، و5 صفحات قديمة.
- واحدة فقط من الـ24 لها أصل عربي غير مربوط يمكن ربطه فوراً. البقية ليست «ترجمات ضائعة»: إما مقالات كُتبت بالإنجليزية أصلاً، أو نسخ مكررة من صفحات لها ترجمة مربوطة، أو ترجمات قديمة حُذف أصلها العربي.
- لم يُغيَّر شيء في هذه الخطوة.

## أ) تُربط فوراً (1) — ✅ نُفّذ 3 أكتوبر 2026

تبيّن أن كل صفحة منشورة كانت مربوطة بالنسخة **المسودة** القديمة من الأخرى (العربية 1444 ← مسودة إنجليزية 2665؛ الإنجليزية 2577 ← مسودة عربية 596 «old-page-596»)، ولهذا كان hreflang يسقط إلى الصفحة الرئيسية. رُبطت الصفحتان المنشورتان ببعضهما، وتحققتُ من hreflang في الاتجاهين ومن أن المحتوى وبيانات Elementor لم تتغير. المسودتان 2665 و596 صارتا بلا ربط ولم تُحذفا؛ يمكن حذفهما.

| الإنجليزية | العربية | الإجراء |
|---|---|---|
| 2577 `/en/why-choose-tourism-in-uzbekistan/` | 1444 `/why-travel-to-uzbekistan/` «لماذا تختار السياحة في أوزبكستان؟» | ربط في Polylang (كما رُبطت مقالات النصائح السبعة) |

## ب) مقالات إنجليزية أصلية بلا مقابل عربي (5) — تبقى كما هي

سلسلة 2026 المكتوبة بالإنجليزية مباشرة؛ محتواها جيد ولا يوجد لها أصل عربي:

| المعرّف | الصفحة |
|---|---|
| 3888 | `/en/best-things-to-do-in-kazakhstan-2026/` |
| 3889 | `/en/best-things-to-do-in-russia-2026/` |
| 3890 | `/en/best-things-to-do-in-uzbekistan-2026/` |
| 3895 | `/en/best-things-to-do-in-china-2026/` |
| 3887 | `/en/top-tourist-attractions-in-poland-2026/` |

**التوصية:** لا إجراء على المحتوى. يكفي إصلاح سنِبِت hreflang حتى لا تعلن هذه الصفحات أن بديلها العربي هو الصفحة الرئيسية. (اختياري لاحقاً: ترجمتها إلى العربية إن أردتم مقابلاً عربياً.)

## ج) نسخ إنجليزية مكررة لصفحات لها ترجمة مربوطة (9) — تُحوَّل 301

لكل منها صفحة إنجليزية أخرى هي الترجمة الفعلية المربوطة بالأصل العربي؛ وجود النسختين يقسم القوة بينهما.

| اليتيمة | النسخة المربوطة (هدف التحويل) |
|---|---|
| 2478 `/en/offers-and-reservations/` | `/en/offers-and-reservations-en/` |
| 2555 `/en/study-in-kazakhstan/` | `/en/study-in-kazakhstan-your-comprehensive-guide-to-the-best-universit…/` |
| 2551 `/en/tourist-activities-in-kazakhstan/` | `/en/unforgettable-experiences-distinctive-activities-when-tourism-in-k…/` |
| 2628 `/en/uzbekistan-festivals-2026-the-most-prominent-cultural-and-tourism-…/` | `/en/uzbekistan-festivals-2026-with-arcadia-tourism-nowruz-and-east-tar…/` |
| 2513 `/en/5-reasons-why-traveling-to-almaty-is-a-great-choice/` | `/en/almaty-guide-en/` |
| 2512 `/en/tourism-in-almaty-arab-travelers/` | `/en/almaty-guide-en/` |
| 2515 `/en/the-cost-of-tourism-in-kazakhstan/` | ترجمة «تكلفة رحلة كازاخستان» بعد تصحيح الأسعار ونشرها |
| 2503 `/en/the-cost-of-tourism-in-russia-with-arcadia-company-surprising-prices/` | `/en/a-practical-guide-to-the-cost-of-tourism-in-russia-daily-budget-and-most-importa/` |
| 2539 `/en/tourism-in-odessa-and-the-most-important-landmarks-of-the-ukrainia…/` | `/en/tourism-in-odessa-and-its-most-important-beautiful-landmarks/` (صفحة أوكرانيا؛ قراركم) |

**تنبيه:** استخدمتُ 2628 و2515 و2513 كروابط داخلية في بعض الترجمات الجديدة لأنها كانت أقرب صفحة متاحة. قبل التحويل تُراجع بيانات Search Console: إن كانت اليتيمة تجلب زيارات فالتحويل 301 يحفظها؛ والروابط الداخلية أحدّثها بعد التحويل.

## د) ترجمات قديمة حُذف أصلها العربي أو دُمج (9) — قرار بحسب الزيارات

| المعرّف | الصفحة | أقرب صفحة حالية |
|---|---|---|
| 2526 | `/en/the-10-most-important-tourist-attractions-in-kazakhstan/` | `/en/hidden-nature-of-kazakhstan/` أو `/en/best-things-to-do-in-kazakhstan-2026/` |
| 2490 | `/en/the-best-tourist-destinations-in-kazakhstan/` | `/en/best-things-to-do-in-kazakhstan-2026/` |
| 2523 | `/en/tourism-in-kazakhstan-discover-the-secrets-of-the-seven-cities/` | `/en/tourism-in-kazakhstan/` |
| 2625 | `/en/the-best-family-tourist-trips-in-kazakhstan-with-a-suggested-7-day-program/` | `/en/a-one-week-tourist-program-in-kazakhstan-…/` |
| 2524 | `/en/arcadia-tourism-company-is-the-ideal-choice-for-traveling-to-kazak…/` | `/en/tourism-in-kazakhstan/` |
| 2629 | `/en/tourism-in-uzbekistan-with-arcadia-tourism-company-distinctive-tri…/` | `/en/tourism-in-uzbekistan/` |
| 2627 | `/en/uzbekistan-the-jewel-of-central-asia-…/` | `/en/tourism-in-uzbekistan/` |
| 2510 | `/en/an-enjoyable-tour-of-the-most-famous-tourist-places-in-poland/` | `/en/top-tourist-attractions-in-poland-2026/` |
| 2509 | `/en/tourism-in-poland-arab-travelers/` | `/en/tourism-in-poland/` |

**التوصية:** هذه تحتاج بيانات Search Console (النقرات والظهور لكل صفحة في آخر 3 أشهر). ما يجلب زيارات يبقى ويُحسَّن؛ وما لا يجلب يُحوَّل 301 إلى أقرب صفحة. بدون تلك البيانات لا أوصي بحذف أو تحويل أي منها.

## الصفحات العربية بلا مقابل إنجليزي (12)

| المعرّف | الصفحة | الوضع |
|---|---|---|
| 4595، 4592، 4593، 4586 | مقالات تكلفة الصين وروسيا وأوزبكستان وكازاخستان | الترجمات جاهزة ومؤجَّلة حتى تُعتمد الأسعار |
| 4827، 4824، 4809 | مدن الصين، VPN الصين، السياحة الشتوية (نسخة ثانية) | مكررة الموضوع؛ يُوصى بالدمج والتحويل 301 |
| 1444 | لماذا تختار السياحة في أوزبكستان؟ | تُربط بـ2577 (القسم أ) |
| 1439 | السياحة بمذاق أوروبي في شتاء كراكوف وزاكوباني (صفحة) | نسخة مكررة من مقال بالعنوان نفسه له ترجمة مربوطة؛ تُحوَّل 301 إلى المقال |
| 1441 | تنظيم الرحلات الجماعية والقروبات إلى بولندا | صفحة خدمات قديمة بلا مقابل إنجليزي؛ قراركم |
| 611 | تذاكر الطيران وتأجير السيارات (`/خدماتنا/old-page-611/`) | صفحة قديمة برابط «old-page»؛ تُراجع أو تُحوَّل |
| 2642 | Odessa real estate (صفحة إنجليزية العنوان مصنَّفة عربية) | من صفحات أوكرانيا/العقار؛ خارج النطاق بقراركم |

## الترتيب المقترح

1. ربط 2577 ↔ 1444 (دقيقة واحدة، بلا مخاطرة).
2. إصلاح سنِبِت hreflang (PHP، من جهتكم): يعالج القسم (ب) كله ويزيل الإعلان الخاطئ من كل الصفحات اليتيمة في اللغتين.
3. تحويلات القسم (ج) من إضافة Redirection، بعد نظرة على Search Console.
4. القسم (د) بعد توفر بيانات Search Console.

---

## تحديث: فحص حقول الربط في Polylang للصفحات الـ23 الباقية (قراءة فقط) — 3 أكتوبر 2026

قرأتُ حقل «الترجمة العربية» في شاشة تحرير كل صفحة إنجليزية يتيمة، ثم فحصتُ حالة العنصر العربي المربوط، وإلى أين يُحوَّل رابطه القديم اليوم.

### النتيجة

- **18 من 23 مربوطة فعلاً بأصل عربي، لكن الأصل «مسودة».** الأصول العربية الثمانية عشر أُلغي نشرها بين 23 أغسطس و1 سبتمبر 2026 ضمن تنظيف سابق، وحُوّلت روابطها 301 إلى صفحات عربية مدمجة. النسخ الإنجليزية المقابلة **بقيت منشورة ولم تُعالَج** — فهي بقايا ذلك التنظيف، لا صفحات مستقلة.
- **5 بلا أي ربط** (حقل الترجمة = 0): سلسلة Best Things to Do 2026 المكتوبة بالإنجليزية أصلاً. تصنيفها في القسم (ب) صحيح.
- لا توجد حالة أخرى تُحلّ بربط بسيط كما في 2577 ↔ 1444.

هذا يغيّر التوصية: الفئتان (ج) و(د) أعلاه هما في الحقيقة فئة واحدة. القرار اتُّخذ فعلاً في النسخة العربية (دمج وتحويل)، والمطلوب تطبيق القرار نفسه على النسخة الإنجليزية. ولكل صفحة وجهة محددة: **المقابل الإنجليزي للصفحة العربية التي حُوّل إليها الأصل**.

### الوجهة الدقيقة لكل صفحة

| الإنجليزية اليتيمة | الأصل العربي (مسودة) | رابط الأصل يُحوَّل اليوم إلى | الوجهة الإنجليزية المقابلة |
|---|---|---|---|
| 2478 `/en/offers-and-reservations/` | 163 | `/offers-bookings/` | `/en/offers-and-reservations-en/` |
| 2512 `/en/tourism-in-almaty-arab-travelers/` | 528 | `/almaty-guide/` | `/en/almaty-guide-en/` |
| 2513 `/en/5-reasons-why-traveling-to-almaty-is-a-great-choice/` | 529 | `/almaty-guide/` | `/en/almaty-guide-en/` |
| 2490 `/en/the-best-tourist-destinations-in-kazakhstan/` | 506 | صفحة «المدن في كازاخستان» | `/en/cities-in-kazakhstanlearn-about-the-9-most-important-tou…/` |
| 2523 `/en/tourism-in-kazakhstan-discover-the-secrets-of-the-seven-cities/` | 539 | صفحة «المدن في كازاخستان» | نفسها |
| 2526 `/en/the-10-most-important-tourist-attractions-in-kazakhstan/` | 542 | صفحة «المدن في كازاخستان» | نفسها |
| 2551 `/en/tourist-activities-in-kazakhstan/` | 570 | صفحة «المدن في كازاخستان» | نفسها |
| 2524 `/en/arcadia-tourism-company-is-the-ideal-choice-…/` | 540 | `/اكتشف-أفضل-شركة-سياحة-في-كازاخستان-راح/` | `/en/discover-the-best-kazakhstan-tourism-company-…/` |
| 2625 `/en/the-best-family-tourist-trips-in-kazakhstan-…/` | 960 | `/برنامج-سياحي-لمدة-أسبوع-في-كازاخستان-ج/` | `/en/a-one-week-tourist-program-in-kazakhstan-…/` |
| 2627 `/en/uzbekistan-the-jewel-of-central-asia-…/` | 962 | `/أوزبكستان-جوهرة-آسيا-الوسطى-التي-تجمع/` | `/en/uzbekistan-2026-the-jewel-of-central-asia-silk-road-and-…/` |
| 2628 `/en/uzbekistan-festivals-2026-the-most-prominent-…/` | 963 | `/مهرجانات-أوزبكستان-2026-أبرز-الفعاليات-ا/` | `/en/uzbekistan-festivals-2026-with-arcadia-tourism-nowruz-…/` |
| 2629 `/en/tourism-in-uzbekistan-with-arcadia-tourism-company-…/` | 964 | `/سياحة-في-أوزبكستان-مع-شركة-أركاديا-الس/` | `/en/distinctive-tourist-trips-to-uzbekistan-2026-arcadia-tou…/` |
| 2509 `/en/tourism-in-poland-arab-travelers/` | 525 | `/poland-guide/` | `/en/poland-guide-en/` |
| 2510 `/en/an-enjoyable-tour-of-the-most-famous-tourist-places-in-poland/` | 526 | `/أهم-10-وجهات-سياحية-في-بولندا/` | `/en/discover-the-top-10-tourist-destinations-in-poland/` |
| 2503 `/en/the-cost-of-tourism-in-russia-with-arcadia-company-…/` | 519 | `/تكلفة-السياحة-في-روسيا-الميزانية-اليو/` | `/en/a-practical-guide-to-the-cost-of-tourism-in-russia-…/` |
| 2515 `/en/the-cost-of-tourism-in-kazakhstan/` | 531 | `/kazakhstan-family-trip-cost-2026/` | لا مقابل إنجليزي بعد (الترجمة مؤجَّلة حتى تُعتمد الأسعار) |
| 2555 `/en/study-in-kazakhstan/` | 574 | الرابط القديم يعطي 404 | `/en/study-in-kazakhstan-your-comprehensive-guide-to-the-best-universit…/` (أقرب صفحة) |
| 2539 `/en/tourism-in-odessa-and-the-most-important-landmarks-…/` | 555 | صفحة أوديسا | `/en/tourism-in-odessa-and-its-most-important-beautiful-landmarks/` (أوكرانيا؛ قراركم) |

### الحالة المعكوسة: ثلاث صفحات عربية منشورة ومقابلها الإنجليزي مسودة

| العربية المنشورة | المقابل الإنجليزي (مسودة) |
|---|---|
| 1439 «السياحة بمذاق أوروبي في شتاء كراكوف وزاكوباني» (صفحة) | 2663 |
| 1441 «تنظيم الرحلات الجماعية والقروبات إلى بولندا» | 2664 |
| 611 «تذاكر الطيران وتأجير السيارات» (`old-page-611`) | 2583 |

هنا أُلغي نشر الإنجليزية وبقيت العربية. إن كان الإلغاء مقصوداً فالصفحات العربية الثلاث مرشحة للمعاملة نفسها.

### التوصية المحدَّثة

1. **تطبيق ما طُبّق على العربية:** لكل صفحة من الـ16 الأولى في الجدول، تحويل 301 إلى وجهتها الإنجليزية ثم تحويل الصفحة إلى مسودة. هذا يُكمل تنظيف أغسطس ولا يحتاج قراراً جديداً في المحتوى.
2. **2515** ينتظر نشر ترجمة مقال التكلفة؛ **2539** صفحة أوكرانيا (قراركم)؛ **2555** يُحوَّل إلى دليل الدراسة الإنجليزي، ورابط أصله العربي القديم `/الدراسه-في-كازاخستان/` يعطي 404 ويحتاج تحويلاً هو الآخر.
3. **قبل التحويل:** خمس من هذه الصفحات مستخدمة روابطَ داخلية في الترجمات الجديدة (2526، 2515، 2628، 2513، 2625). الروابط ستبقى تعمل عبر 301، وأحدّثها إلى الوجهات المباشرة ضمن التنفيذ.
4. **سنِبِت hreflang** يبقى مطلوباً للمقالات الخمس الأصلية.

