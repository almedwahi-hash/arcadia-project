# سجل إرسال الدفعة 8 — الموجة 1 | Arcadia B2B

> آخر تحديث: 2026-07-09 22:45 (Asia/Almaty) | الطريقة: **Zoho Webmail (متصفح، يدوي)** — وليس SMTP
> السبب: بيئة الـ sandbox لا تسمح بالاتصال الخارجي عبر SMTP (فشل `smtplib` بسبب عزل الشبكة)
> المصدر: 10 وكالات فيتنامية + 5 وكالات بريطانية من `outreach-batch8-queue.csv` (الموجة 1 من 48 هدفاً)
> المرفق: `Arcadia-B2B-Rate-Sheet-Almaty.pdf` (112.8 KB) مع كل رسالة | المُرسِل: Arcadia Tourism Company <info@arcadia-tour.com>
> كل رسالة رُوجعت بصرياً (نص كامل + مرفق) قبل الإرسال بناءً على طلب المستخدم

## النتيجة — ✅ 14/15 وصل بنجاح، 1 ارتد (bounce)

| البند | القيمة |
|-------|--------:|
| المُرسَل فعلياً (Zoho قَبِل الإرسال) | **15 / 15** |
| وصل للصندوق (تأكيد) | **14 / 15** |
| ارتد (bounce) | **1** — HaloBay Travel (info@halobay.vn) |
| فشل إرسال (لم يُرسَل إطلاقاً) | **0** |

## جدول الإرسال

| # | الشركة | To | الحالة | التوقيت (Almaty) |
|---|--------|-----|--------|------------------|
| 1 | Authentic Asia | sales@authentic-asia.com | ✅ sent | 2026-07-09 21:32 |
| 2 | DH Travel (Du Lich Quoc Te DH) | director@dhtravel.com.vn | ✅ sent | 2026-07-09 21:37 |
| 3 | Fiditour JSC | info@fiditour.com | ✅ sent | 2026-07-09 21:43 |
| 4 | HaloBay Travel | info@halobay.vn | ⚠️ **sent → bounced** | 2026-07-09 21:49 |
| 5 | Le Phong Travel | info@lephongtravel.com.vn | ✅ sent | 2026-07-09 21:55 |
| 6 | Mai Tours | info@maitours.vn | ✅ sent | 2026-07-09 22:03 |
| 7 | Premier Tour Vietnam | info@premiertour.com.vn | ✅ sent | 2026-07-09 22:11 |
| 8 | Saigontourist Travel | info@saigontourist.net | ✅ sent | 2026-07-09 22:22 |
| 9 | VGC Travel | info@vgctravel.com.vn | ✅ sent | 2026-07-09 22:30 |
| 10 | Vietrantour | booking@vietrantour.com.vn | ✅ sent | 2026-07-09 22:33 |
| 11 | Exodus Adventure Travels | privatedepartures@exodus.co.uk | ✅ sent | 2026-07-09 22:35 |
| 12 | Go Russia Ltd | info@justgorussia.co.uk | ✅ sent | 2026-07-09 22:38 |
| 13 | HF Holidays | groups@hfholidays.co.uk | ✅ sent | 2026-07-09 22:40 |
| 14 | Jules Verne (VJV) | agents@vjv.com | ✅ sent | 2026-07-09 22:43 |
| 15 | Regent Holidays | regent@regentholidays.co.uk | ✅ sent | 2026-07-09 22:45 |

## تفصيل الارتداد (Bounce) — HaloBay Travel

- Zoho نجح في تسليم الرسالة إلى خوادم المستلم (Google)، لكن Google رفضها فوراً.
- رسالة الارتداد الواردة من `mailer-daemon@mail.zoho.eu`: **"Undelivered Mail Returned to Sender"**، `ERROR CODE: 550 5.1.1 — The email account that you tried to reach does not exist.`
- `Final-Recipient: rfc822; info@halobay.vn`
- **الإجراء المتخذ:** أُضيف `info@halobay.vn` إلى `deliverables/exclude_emails.txt` (سطر 141) لمنع إعادة المحاولة مستقبلاً.

## ملاحظات التشغيل

- **طريقة الإرسال:** متصفح Zoho Webmail يدوياً (وليس `send_batch8_outreach.py` عبر SMTP) — بسبب فشل الاتصال الخارجي من بيئة التنفيذ. **لم يُسجَّل أي شيء تلقائياً عبر السكربت** — هذا السجل مبني يدوياً من مجلد "Отправленные" (Sent) في Zoho.
- **المراجعة:** كل رسالة رُوجعت حرفياً (تمرير كامل للنص + التحقق من المرفق) قبل الضغط على "Отправить" — بناءً على تعليمات المستخدم الصريحة.
- **أخطاء تنسيق طفيفة أُصلحت أثناء المراجعة:** انقطاع فراغ بين "Silk Road" و"Groups" في سطر الموضوع (Zoho أسقطت مسافة بعد "Road" بشكل متكرر عبر معظم الرسائل) — تم تصحيحها يدوياً بالنقر المزدوج وإعادة الكتابة في كل رسالة تأثرت قبل الإرسال. رسالتان (Mai Tours #6، Saigontourist #8) تعرضتا لانقطاع اتصال متصفح مؤقت أدى لدمج فقرة/نقطة أثناء الكتابة — تم اكتشافه وإصلاحه أثناء المراجعة الكاملة قبل الإرسال.
- **الملف الآلي:** `.tmp_batch8_sent.json` (15 سجلاً، منها سجل واحد بحالة `sent_bounced`) | `.tmp_batch8_remaining.json` بعد الحذف يحتوي 33 هدفاً متبقياً (الموجة 2، #16–#48).
- **المرفق:** `Arcadia-B2B-Rate-Sheet-Almaty.pdf` (112.8 KB) — أُرفق وأُكِّد ("Вложения: 1") في كل رسالة قبل الإرسال.
- **الموجة القادمة:** 33 هدفاً متبقياً (#16 Steppes Travel → #48) بانتظار موافقة المستخدم الصريحة قبل الإرسال الجماعي.

---

*سجل الدفعة 8 (الموجة 1) — 9 يوليو 2026*

---

## الموجة 2 — ⚠️ 33/33 قُبلت للإرسال، لكن 7 ارتدت + 2 معلّقة (SMTP Zoho)

> **آخر تحديث:** 2026-07-10 (تصحيح بعد مراجعة صندوق الوارد فعلياً) | **الطريقة:** `scripts/send_batch8_outreach.py` — Zoho SMTP `smtp.zoho.eu:465` + مرفق PDF
> **⚠️ تنبيه:** الجدول أدناه كان يُظهر سابقاً "33/33 sent، 0 فشل" — هذا **غير دقيق**. راجعتُ صندوق الوارد الفعلي (`mailer-daemon@mail.zoho.eu` + `googlemail.com` + `greenradar.com`) ووجدت **7 ارتدادات نهائية** و**2 تأخير مستمر** لم تكن مُوثّقة. الجدول والملخص تحتهما مُصحَّحان الآن.

| الملخص | العدد |
|--------|------:|
| الموجة 2 — قُبلت من Zoho للإرسال (#16–#48) | **33 / 33** |
| **وصلت فعلياً (مؤكَّد)** | **24 / 33** |
| **ارتدت نهائياً (bounce)** | **7 / 33** |
| **متأخرة — لا تزال تُعاد المحاولة (4 أيام)** | **2 / 33** |
| إجمالي Batch 8 (#1–#48) | 47 قُبلت مبدئياً + **8 ارتدت فعلياً** (1 من الموجة 1 + 7 من الموجة 2) + 2 معلّقة |

### سجل الموجة 2 (مُصحَّح)

| # | الشركة | To | الحالة الفعلية | الوقت (Almaty) |
|---|--------|-----|--------|----------------|
| 16 | Steppes Travel | info@steppestravel.com | ✅ وصلت | 2026-07-10 02:10 |
| 17 | Wendy Wu Tours UK | info@wendywutours.co.uk | ✅ وصلت | 2026-07-10 02:12 |
| 18 | Wild Frontiers Travel | info@wildfrontierstravel.com | ✅ وصلت (رد آلي مستلَم) | 2026-07-10 02:12 |
| 19 | Adventure International Tours (AITI) | reservations@tdgtravel.ph | ✅ وصلت | 2026-07-10 02:13 |
| 20 | Blue Horizons Travel & Tours Inc. | info@bluehorizons.travel | ✅ وصلت | 2026-07-10 02:14 |
| 21 | FCM Travel Philippines | sales@ph.fcm.travel | ✅ وصلت | 2026-07-10 02:15 |
| 22 | Pan Pacific Travel | info@panpacifictravel.com.ph | ✅ وصلت | 2026-07-10 02:15 |
| 23 | Premiere Travel and Tours Inc. | anicar@premieretravel.ph | ✅ وصلت | 2026-07-10 02:16 |
| 24 | Travelite Express | info@travelite.com.ph | ✅ وصلت | 2026-07-10 02:17 |
| 25 | CIS Tour (Korea) | info@cis-tour.com | ✅ وصلت | 2026-07-10 02:18 |
| 26 | Small Star Tour (Jageunbyeol) | smallstar@smallstartour.com | ✅ وصلت | 2026-07-10 02:18 |
| 27 | Very Good Tour (Korea) | info@verygoodtour.com | ❌ **ارتدت** — 505 unknown user | 2026-07-10 02:19 |
| 28 | Go Jordan Travel and Tourism | info@gojordantours.com | ✅ وصلت | 2026-07-10 02:20 |
| 29 | Jordan Tours & Travel | sales@jordantour-travel.com | ❌ **ارتدت** — DNS NXDOMAIN | 2026-07-10 02:21 |
| 30 | Petra Travel & Tourism (Jordan) | info@petratravel.com | ❌ **ارتدت** — العنوان غير موجود | 2026-07-10 02:22 |
| 31 | Petra Travel and Tourism Co. | awni.kawar@petratours.com | ✅ وصلت | 2026-07-10 02:22 |
| 32 | Asia Exotic Expeditions | tours@asiaexotic.com | ⏳ **متأخرة** — Host not reachable (تُعاد المحاولة 4 أيام) | 2026-07-10 02:23 |
| 33 | Cheria Holiday (PT Cheria) | info@cheria-travel.com | ✅ وصلت | 2026-07-10 02:24 |
| 34 | DeWonder Travel | info@dewonder.travel | ✅ وصلت | 2026-07-10 02:25 |
| 35 | EGL Tours | egltours@egltours.com | ❌ **ارتدت** — 550 access denied | 2026-07-10 02:25 |
| 36 | EU Holidays | enquiry@euholidays.com.sg | ✅ وصلت | 2026-07-10 02:26 |
| 37 | Five Star Club (Japan) | info@fivestar-club.co.jp | ✅ وصلت | 2026-07-10 02:27 |
| 38 | Hayatun Tour | info@hayatuntour.com | ❌ **ارتدت** — 550 user doesn't exist | 2026-07-10 02:28 |
| 39 | Indus Travel Co. | industokyo@indus-travel.com | ✅ وصلت | 2026-07-10 02:28 |
| 40 | KOP Travel | info@koptravel.com.my | ✅ وصلت | 2026-07-10 02:29 |
| 41 | MNG Turizm | info@mngturizm.com | ✅ وصلت | 2026-07-10 02:30 |
| 42 | Nam Ho Travel | info@namho.com.sg | ❌ **ارتدت** — 550 access denied | 2026-07-10 02:31 |
| 43 | SOTC Travel | groups@sotc.in | ✅ وصلت | 2026-07-10 02:31 |
| 44 | TripsTide Pvt Ltd | sales@tripstide.com | ✅ وصلت | 2026-07-10 02:32 |
| 45 | Atlas Voyages (Morocco) | contact@atlasvoyages.com | ✅ وصلت | 2026-07-10 02:33 |
| 46 | Lef El Donia Travel | info@lefeldonia.com | ⏳ **متأخرة** — Host not reachable (تُعاد المحاولة 4 أيام) | 2026-07-10 02:34 |
| 47 | Mondial Voyages Maroc | contact@mondialvoayage.com | ❌ **ارتدت** — DNS NXDOMAIN (خطأ إملائي في الدومين؟) | 2026-07-10 02:34 |
| 48 | Muker Travel | contact@mukertravel.com | ✅ وصلت | 2026-07-10 02:35 |

### تفصيل الارتدادات السبعة (Wave 2)

| # | الشركة | العنوان | كود الخطأ | السبب |
|---|--------|---------|-----------|-------|
| 27 | Very Good Tour (Korea) | info@verygoodtour.com | 505 | "this account is unknown user" |
| 29 | Jordan Tours & Travel | sales@jordantour-travel.com | 512 / DNS NXDOMAIN | الدومين jordantour-travel.com غير موجود |
| 30 | Petra Travel & Tourism (Jordan) | info@petratravel.com | 5.1.3 | "does not exist" (Google) |
| 35 | EGL Tours | egltours@egltours.com | 550 5.4.1 | Recipient address rejected (Outlook/Exchange) |
| 38 | Hayatun Tour | info@hayatuntour.com | 550 5.1.1 | "User doesn't exist" (Hostinger) |
| 42 | Nam Ho Travel | info@namho.com.sg | 550 5.4.1 | Recipient address rejected (Outlook/Exchange) |
| 47 | Mondial Voyages Maroc | contact@mondialvoayage.com | 512 / DNS NXDOMAIN | الدومين mondialvoayage.com غير موجود — يُحتمل خطأ إملائي في العنوان المصدر (قد يكون mondialvoyage.com) |

**العنوانان المتأخران (32، 46)** لا يزالان قيد إعادة المحاولة من Zoho لمدة تصل إلى 4 أيام — قد يصلا لاحقاً أو يرتدّان. يُنصح بالمتابعة بعد 2026-07-14.

### ملاحظات

- **الملف:** `.tmp_batch8_sent.json` (48 سجلًا — يحتاج تحديث ليعكس حالات الارتداد) | `.tmp_batch8_remaining.json` فارغ بعد `--build-from-md`
- **exclude:** جميع عناوين #16–#48 مُضافة إلى `deliverables/exclude_emails.txt` كسجل "تم التواصل معه" (وليس بالضرورة "عنوان سيّئ") — العناوين السبعة المرتدة موجودة بالفعل ضمنها فلن تُستهدف مجدداً بأي حال
- **⚠️ سبب التصحيح:** السجل الأصلي لهذا القسم افترض "0 فشل" دون مراجعة صندوق الوارد الفعلي بعد الإرسال — تمت مراجعته الآن يدوياً (2026-07-11) وفق تعليمات المستخدم الصريحة بمراجعة البريد

---

*سجل Batch 8 — الموجة 2 صُحِّحت بعد تدقيق فعلي لصندوق الوارد — 2026-07-11*
