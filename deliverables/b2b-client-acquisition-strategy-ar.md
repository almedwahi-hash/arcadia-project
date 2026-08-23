# استراتيجية اكتساب عملاء B2B — أركاديا السياحية

> **التاريخ:** 25 يونيو 2026  
> **المالك:** محمد علي — info@arcadia-tour.com | واتساب +77051181845  
> **الهدف:** أول **عقد/quote مجموعة** خلال 30 يوم — ليس مستندات إضافية  
> **تنبيه:** لا إرسال بريد/WA/أتمتة Safeer بدون موافقة صريحة — المسودات في `sales-outreach-batch5-targets-ar.md`

---

## 1. ما تبيعه أركاديا (الوجهات)

### 1.1 المنتج الأساسي — كازاخستان (ألماتي)

| البند | التفاصيل |
|-------|----------|
| **الدور** | DMC ground handling — B2B مجموعات 15–40 pax |
| **البرامج** | 4N/5D (B2B rate sheet) · 5–7N FIT · إضافات: شارين، كولساي، كايندي |
| **المصدر** | Supabase `itineraries` — `country = Kazakhstan`, `notes_ar: nights:4–7` |
| **التسعير** | `group_rates` — KZ/Almaty/4N — شرائح 15–19 / 20–29 / 30–40 pax |
| **PDF** | `scripts/generate-pdf-safe.py` → rate sheet EN |

### 1.2 امتدادات المحفظة (عبر شريك واحد)

| الوجهة | دور أركاديا | ملاحظة |
|--------|-------------|--------|
| **أوزبكستان** (طشقند/سمرقند) | ground + مرشد عربي/EN | white-label لبرامج 3–5 Stans |
| **قيرغيزستان** (bishkek) | ground segment | halal groups ID/MY/SG |
| **روسيا** (موسكو) | تنسيق عبر شبكة — pitch مع KZ | GCC/QA/KSA catalogs |
| **طاجيكستان** | segment في 4-Stans | Hayatun/Rabbani/VN operators |

**ما لا نبيعه مباشرة اليوم:** الصين/ألمانيا FIT (مرشد محلي مطلوب) · باكستان (تأشيرة) · FIT صغير <8 pax.

### 1.3 موسمية vs محفظة

```
GCC (37%)     → رمضان/عيد/صيف — هامش عالي + عربي
آسيا (38%)    → IN/ID/MY/SG/VN/KR — يملأ سب–أكت عندما يهدأ GCC
تركيا/أخرى (25%) → Setur/Ayanis — مايو–أكتو
```

---

## 2. ثلاث مستويات أولوية للأسواق

### المستوى 1 — S (إيراد + لغة + مجموعات نشطة)

| السوق | لماذا الآن (25 يون 2026) | مشغّلون | هدف 30 يوم |
|-------|-------------------------|---------|------------|
| **GCC (UAE/KSA/QA/BH/KW)** | 30 بريد مُرسل — **0 رد** → المشكلة **قناة** لا سوق | Citron, Tabeer, Alqaed, Musafir, CTC… | **5 WA + 3 مكالمات** → 1 quote |
| **إندونيسيا halal** | Hayatun 28 سب · Villa/Rabbani batch | Hayatun 🔴, Villa ✅ sent, Rabbani batch5 | **Hayatun WA اليوم** → segment KZ |
| **ماليزيا halal** | AMI sent · Nuh/Selamatbercuti 3-Stans | AMI, Nuh, Selamatbercuti | 1 مكالمة AMI follow-up |

**لماذا S:** مرشد عربي = USP · مجموعات 15–40 = margin · deadlines Sep–Oct 2026.

### المستوى 2 — A (حجم + موسمية تُكمّل GCC)

| السوق | لماذا | مشغّلون | هدف 30 يوم |
|-------|-------|---------|------------|
| **سنغافورة** | SGTREK 4 سب · CTC 12 deps · SGD قوي | SGTREK, CTC, Tailwinds, EU Holidays | follow-up + 2 WA |
| **الهند** | 113K+ وافد KZ · Veena/Kesari/SOTC groups | Kesari, Thomas Cook (batch5) | 2 outreach بعد موافقة |
| **فيتنام** | Thang Long/VGC سب–أكت · xúc tiến KZ | Thang Long, VietnamTourist, Dat Viet | 2 outreach EN |
| **تركيا** | 103K وافد · Setur/Ayanis مايو–أكت | Ayanis (batch5) | 1 partnership call |

**لماذا A:** ذروة سب–أكت = هدوء خليجي · منتج CA مجموعات ناضج.

### المستوى 3 — B (تنويع + pipeline Q3–Q4)

| السوق | لماذا | مشغّلون | هدف 30 يوم |
|-------|-------|---------|------------|
| **كوريا** | +25% وافدين · Culture/Majung/Tienshan | Culture Tour, Majung, Tienshan, Very Good | 2 outreach EN |
| **UAE Dec groups** | Travel House/Euro 1–6 ديس planning يبدأ الآن | Travel House Dubai (batch5) | 1 email + WA |
| **الكويت/البحرين** | Alghanim/FTTC sent — KITTC/Global BH جديد | KITTC, Global Travel BH | nurture |

---

## 3. شرائح العملاء (Segments)

| الشريحة | من | Pitch | قناة أولى |
|---------|-----|-------|-----------|
| **A — وكالات صادرة GCC** | دبي/جدة/الدوحة | ground B2B + مرشد عربي + حلال | **WA + مكالمة** ثم بريد |
| **B — halal Asia (ID/MY)** | Hayatun, Rabbani, Nuh | white-label segment KZ · 4-Stans consistency | EN email + WA ops |
| **C — مجموعات SG/VN/IN** | CTC, SGTREK, Thang Long, Kesari | Almaty segment net rates · Sep–Oct dates | EN email · LinkedIn BD |
| **D — inbound KZ partners** | Tienshan (مكتب ALA), Kazakh Tourism | **ليس منافساً** — B2B overflow / Arabic layer | EN/KR email |

**قاعدة:** OTA كبير (Musafir) → `packages@` / LinkedIn Partnerships — لا تعتمد auto-reply ticket.

---

## 4. إيقاع العمل الأسبوعي (Rhythm)

| اليوم | 9–11 ص (Almaty) = 6–8 ص GMT+4 | 14–17 | 17–19 |
|-------|-------------------------------|-------|-------|
| **الإثنين** | 3 WA hot leads (Hayatun, Citron, SGTREK) | 2 follow-up Reply (GCC يوم 5) | LinkedIn: 2 DMs BD managers |
| **الثلاثاء** | 2 مكالمات 15 د (أرقام الموقع) | مسودة outreach batch5 (بعد موافقة) | تحديث `b2b-pipeline-hot-leads-ar.md` |
| **الأربعاء** | 1 post LinkedIn (Sep groups Almaty) | follow-up CTC/Tailwinds/Villa (sent 25 يون) | rate sheet PDF (أسعار net مملوءة) |
| **الخميس** | WA يوم 10 للبريد 16–19 يون | ITB Asia / ATM Dubai registration | KPI review |
| **الجمعة** | إغلاق leads بارد (3 touches max) | تخطيط الأسبوع القادم | تقرير عربي للمدير |

**Cadence موحّد لكل lead:**

| بعد | إجراء |
|-----|--------|
| يوم 0 | بريد + subject مخصّص (9–11 Almaty) |
| يوم 3 | WA قصير (≤4 أسطر) |
| يوم 5 | Reply-thread follow-up |
| يوم 10 | WA + «15-min call?» |
| يوم 21 | إغلاق أو nurture — لا أكثر من 4 لمسات |

---

## 5. Playbook — عند أول رد

| نوع الرد | إجراء خلال 24h | مرفق | هدف |
|----------|----------------|------|-----|
| «Send rates» | PDF rate sheet **بأرقام net** (15/25/35 pax) | `generate-pdf-safe.py` | quote لتاريخ محدد |
| «Which dates?» | جدول Sep–Oct 2026 + capacity 2 groups/week | sample 5D itinerary | LOI call |
| «We have DMC» | Arabic layer + halal + 7500 GCC track record | case study 1 صفحة | trial 10 pax |
| «Too expensive» | module 4N فقط vs full Stans | لا خصم بدون تاريخ مؤكد | hold dates |
| MICE/corporate | ITL World pitch · incentive Astana/Shymbulak | — | Q4 booking |

**تحويل → عقد:** LOI 1 صفحة → `templates/b2b-ground-handling-agreement-en.html` — **بعد** مكالمة + quote مaccepted.

---

## 6. KPI — 30 يوم (26 يون – 25 يول 2026)

| المؤشر | هدف | Actual |
|--------|-----|--------|
| **Quote request / rate sheet مطلوب** | **≥2** | 0 |
| **مكالمات B2B 15 د** | **≥5** | 0 |
| **WA sent (named leads)** | **≥15** | 0 |
| **ردود B2B (any channel)** | **≥3** | 0 |
| **LOI / trial group** | **≥1** | 0 |
| **Outreach جديد (batch5)** | **10** (بعد موافقة) | 0 |
| **ATM Dubai visitor registered** | **1** | 0 |
| **Groups confirmed (ops)** | **≥1** (even 10 pax trial) | 0 |

**تعريف النجاح:** وكالة تطلب **أسعار لتاريخ مغادرة** أو **trial group** أو **LOI موقّع**.

---

## 7. ما لا تفعل (30 يوم)

| ❌ | ✅ |
|----|---|
| Safeer / n8n auto-outreach | WA يدوي + Zoho يدوي |
| MOU جديد بدون lead | rate sheet 1 صفحة بأسعار |
| batch5 إرسال بدون موافقة | مراجعة `sales-outreach-batch5-targets-ar.md` |
| انتظار رد بريد >48h | WA + هاتف |
| SEO/guest posts | **بعد** 3 مكالمات B2B |

---

## 8. ملفات التنفيذ

| الملف | الاستخدام |
|-------|-----------|
| `b2b-pipeline-hot-leads-ar.md` | Hot leads + إجراءات مؤرّخة |
| `sales-outreach-batch5-targets-ar.md` | 28 هدف جديد + مسودات |
| `b2b-get-clients-now-ar.md` | scripts WA فورية |
| `outreach-sent-log-batch4-ar.md` | 30 agency contacted |
| `program-model-ar.md` | برامج KZ 4N–7N |
| `kz-outbound-markets-research-ar.md` | محفظة 37/38/25 |

---

*25 يونيو 2026 — Focus: WA 70% · GCC+Halal Asia+SG/VN · customers not docs.*
