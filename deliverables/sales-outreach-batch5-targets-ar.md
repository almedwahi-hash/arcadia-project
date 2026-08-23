# Batch 5

> **الحالة:** ailed — SMTP OK لكن **553 relay** — 0/28 مرسل، GCC 0/5
 — أهداف B2B جديدة (مُتحقّقة) | أركاديا

> **التاريخ:** 25 يونيو 2026  
> **العدد:** **28** وكالة — **لم يُرسل لها outreach بعد**  
> **الشركة:** DMC ألماتي | info@arcadia-tour.com | WA +77051181845  
> **تنبيه:** مسودات للمراجعة — **لا إرسال بدون موافقة صريحة**  
> **PDF:** `scripts/generate-pdf-safe.py` فقط عند الطلب

---

## 1. ملخص

### SMTP المطلوب في .env

| المتغير | مطلوب | الافتراضي في السكربت |
|---------|-------|----------------------|
| SMTP_PASS أو ZOHO_SMTP_PASS أو SMTP_PASSWORD أو ZOHO_PASS | **موجود** (مخفي) | ✓ |
| SMTP_USER أو ZOHO_SMTP_USER أو ZOHO_USER | اختياري | info@arcadia-tour.com |
| SMTP_HOST أو ZOHO_SMTP_HOST | اختياري | smtp.zoho.eu |
| SMTP_PORT أو ZOHO_SMTP_PORT | اختياري | 465 |

**اختبار batch4:** بدون كلمة مرور السكربت يتوقف قبل اتصال SMTP؛ --dry-run يعمل. الإرسال السابق احتاج ZOHO_SMTP_PASS غير موجود حالياً في .env.

| البند | العدد |
|-------|------:|
| **أهداف batch 5** | **28** |
| **مُرسَل batch 5** | **0** |
| **GCC follow-ups مرسل** | **0/5** |
| **Priority A** | 14 |
| **Priority B** | 11 |
| **Priority C** | 3 |
| **مُستبعد (already sent)** | 30 — GCC week1 + batch2 + batch4 |

**منهجية التحقّق:** صفحة Contact/About/Footer على الموقع الرسمي · لا تخمين · Yahoo/Gmail/Naver مقبول إذا منشور على الموقع.

---

## 2. جدول الأهداف — 28 وكالة

### الهند 🇮🇳 (2)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 1 | **Kesari Tours** | **A** | holiday@kesari.in | [kesari.in](https://www.kesari.in/contact-us) — Mail في footer | Tashkent–Samarkand–Almaty groups | C |
| 2 | **Thomas Cook India** | **A** | enquiry@thomascook.in | [thomascook.in/contact-us](https://www.thomascook.in/contact-us) | KZ packages · 200+ branches | C |

### إندونيسيا 🇮🇩 (2)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 3 | **Rabbani Tour** | **A** | kemitraanrabbanitour@gmail.com | [rabbanitour.id/contact](https://rabbanitour.id/contact) | 4-Stans halal 11D | B |
| 4 | **Wishtravelers (WT)** | **A** | wt@wishtravelers.com | [wishtravelers.com](https://wishtravelers.com/) — company block | 4-Stans rombongan 2025–26 | B |

### ماليزيا 🇲🇾 (2)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 5 | **Nuh Travel & Tours** | **A** | sales.hq@nuhtravel.com.my | [umrahimani.com/hubungi-kami](https://www.umrahimani.com/hubungi-kami/) — HQ same group | 12D 3-Stans KZ+KG+UZ | B |
| 6 | **Selamatbercuti** | **A** | info@selamatbercuti.com | [selamatbercuti.com/about-us](https://selamatbercuti.com/about-us/) | 11H9M UZ+KG+KZ — Sep 2026 | B |

### سنغافورة 🇸🇬 (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 7 | **EU Holidays** | **B** | sales@euholidays.com.sg | [euholidays.com.sg/contact-us](https://www.euholidays.com.sg/contact-us) + TA footer | Asia outbound groups | C |

### فيتنام 🇻🇳 (3)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 8 | **Thang Long Tours** | **A** | info@thanglongtourvn.com | [thanglongtourvn.com/lien-he](https://thanglongtourvn.com/lien-he) | 14–22D Silk Road Sep–Oct | C |
| 9 | **VietnamTourist JSC** | **A** | info@vietnamtouristjsc.vn | [vietnamtouristjsc.vn/gioi-thieu](https://www.vietnamtouristjsc.vn/gioi-thieu/) | 22N21D 5-Stans | C |
| 10 | **Dat Viet Tour** | **B** | datvietravel@gmail.com | [b2b-partner-targets.md](deliverables/b2b-partner-targets.md) VN6 — catalog KZ/Moscow groups | khách đoàn KZ+RU | C |

### تركيا 🇹🇷 (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 11 | **Ayanis Tur** | **A** | ayanis@ayanis.com.tr | [ayanis.com.tr/iletisim](https://www.ayanis.com.tr/iletisim) | 4D3N KZ+KG — 7 deps 2026 | C |

### كوريا 🇰🇷 (4)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 12 | **Culture Tour** | **A** | tour@culturetour.co.kr | [culturetour.co.kr](https://www.culturetour.co.kr) footer | 3–5 Stans 단체 | C |
| 13 | **Tienshan Tour** | **A** | almatykim@hotmail.com | [tienshan.co.kr](https://tienshan.co.kr) contact block | KZ specialist · office Almaty | D |
| 14 | **Majung Travel** | **A** | kimcwman@naver.com | [majung.net](http://www.majung.net) product pages | CA + Russia groups | C |
| 15 | **Very Good Tour** | **B** | vgtmp@verygoodtour.com | partner targets KR6 — marketing partnerships | CA series catalog | C |

### الإمارات 🇦🇪 (3)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 16 | **Travel House Dubai** | **A** | info@travelhousedubai.com | [travelhousedubai.com/contact](https://travelhousedubai.com/contact/) | 5D KZ Dec 2026 National Day | A |
| 17 | **Akbar Travels (Holidays)** | **B** | packages@akbargulf.com | [aeagents.akbartravels.com/RegionalSupport](https://aeagents.akbartravels.com/MyAccount/RegionalSupport) | Russia/KZ holiday packages | A |
| 18 | **ITL World UAE** | **C** | uae@itlworld.com | b2b-partner-targets U12 | TMC leisure/MICE | A |

### الكويت 🇰🇼 (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 19 | **KITTC** | **B** | kittc@diabehbehani.com | [kittc.com](https://www.kittc.com) Contact section | tailor-made groups worldwide | A |

### البحرين 🇧🇭 (2)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 20 | **Global Travel & Tours BH** | **B** | info@globaltravelbh.com | [globaltravelbh.com](https://www.globaltravelbh.com) footer | outbound holidays | A |
| 21 | **Kanoo Travel (BH desk)** | **B** | helpdesk.travel@kanoo.com | b2b-partner-targets B1 | IATA legacy · GCC network | A |

### السعودية 🇸🇦 (2)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 22 | **Almosafer** | **B** | support@almosafer.com | almosafer.com — Russia packages | OTA #1 KSA | A |
| 23 | **ITL World KSA** | **C** | ksa.khobar@itlworld.com | b2b-partner-targets S6 | corporate + leisure | A |

### قطر 🇶🇦 (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 24 | **Al Maha Travels Doha** | **B** | almahateam@hotmail.com | qataryello listing + operator email | outbound established | A |

### ماليزيا B2B agent (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 25 | **Selamatbercuti (Agent desk)** | **B** | agent@selamatbercuti.com | [selamatbercuti.com/agent/contact](https://www.selamatbercuti.com/agent/include/contact.php) | agent/B2B 3-Stans | B |

### فيتنام (alt email) (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 26 | **Thang Long (alt)** | **B** | toursthanglong@gmail.com | [thanglongtourvn.com/lien-he](https://thanglongtourvn.com/lien-he) | same operator — backup inbox | C |

### الهند B2B (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 27 | **Akbar Gulf (alt holidays)** | **B** | support@akbargulf.com | [akbartravels.com/AE holidays footer](https://www.akbartravels.com/AE/HOLIDAYS/) | UAE holidays support | A |

### إندونيسيا (alt) (1)

| # | الشركة | Priority | البريد | صفحة التحقّق | المنتج | Segment |
|---|--------|----------|--------|--------------|--------|---------|
| 28 | **Wishtravelers CS** | **B** | cs@wishtravelers.com | industry listing — use if wt@ bounce | 4-Stans open trip | B |

---

## 3. تعريف Segments (للقوالب)

| Code | الشريحة | اللغة | Pitch core |
|------|---------|-------|------------|
| **A** | GCC outbound groups | EN/AR | Arabic guide · halal · B2B net · Dubai/Doha/Jeddah deps |
| **B** | Halal Asia ID/MY | EN | white-label KZ segment · rombongan/kumpulan · prayer/halal |
| **C** | SG/VN/IN/TR/KR groups | EN | Almaty segment · Sep–Oct 2026 dates · single contract KZ+UZ |
| **D** | KZ-based partner | EN/KR | overflow capacity · Arabic layer · not competitor |

---

## 4. قوالب بريد EN — حسب Segment

### Segment A — GCC (مثال: Travel House Dubai #16)

**To:** info@travelhousedubai.com  
**Subject:** B2B Ground Partner — Kazakhstan Dec 2026 Groups | Arcadia Tourism (Almaty)

```
Dear Travel House Dubai Team,

We noted your Kazakhstan National Day group packages (1–6 December) from Dubai — a strong fit for a dedicated Almaty ground partner with Arabic-speaking operations.

Arcadia Tourism Company is an Almaty-based DMC (10+ years, 7,500+ Arabic/GCC clients):
• Net B2B ground rates for groups (15–40 pax)
• Arabic guides + halal coordination + direct hotel contracts
• 5-day Almaty module + optional Samarkand extension
• 24/7 WhatsApp support during the tour

Would you be open to a 15-minute call to share our B2B rate sheet for your December 2026 departures?

WhatsApp: +77051181845
info@arcadia-tour.com
https://arcadia-tour.com/

Best regards,
Mohammad Ali
Business Development Manager
Arcadia Tourism Company
Almaty, Kazakhstan
```

---

### Segment B — Halal Asia (مثال: Rabbani Tour #3)

**To:** kemitraanrabbanitour@gmail.com  
**Subject:** B2B DMC Partner — Kazakhstan Segment | 4-Stans Halal Groups | Arcadia Tourism

```
Dear Rabbani Tour Team,

Your halal Central Asia programmes (4-Stans) align with our daily ground operations in Almaty and across Kazakhstan.

Arcadia Tourism Company — Almaty DMC (10+ years, 7,500+ Muslim/Arabic clients):
• Net B2B rates for groups (15–40 pax)
• Arabic-speaking guides for mixed Indonesian/Arabic groups
• Halal meals, prayer times, female guide options
• Single ground partner for KZ + KG + UZ segments
• 24/7 WhatsApp with your tour leader

Shall we share our B2B rate sheet and a 5-day Almaty sample for your next rombongan departure?

WhatsApp: +77051181845
info@arcadia-tour.com
https://arcadia-tour.com/

Best regards,
Mohammad Ali
Arcadia Tourism Company
```

---

### Segment C — SG/VN/IN/TR/KR (مثال: Thang Long #8)

**To:** info@thanglongtourvn.com  
**Subject:** B2B Ground Partner — Kazakhstan Segment | Silk Road Groups 2026 | Arcadia Tourism (Almaty)

```
Dear Thang Long Tours Team,

Your Central Asia Silk Road portfolio with scheduled September–October departures is exactly the group volume we support on the ground in Kazakhstan.

Arcadia Tourism Company is an Almaty-based DMC (10+ years, 7,500+ clients):
• End-to-end ground for the Kazakhstan segment (Almaty, Charyn Canyon, Kolsai, Talgar)
• B2B net rates for groups (15–30 pax)
• English & Russian-speaking guides (Arabic coordinator on request)
• Direct hotel blocks — better margins vs. multi-supplier setup
• 24/7 WhatsApp emergency line for your tour leader

Shall we share our B2B rate sheet and discuss your 2026 Almaty segment dates?

WhatsApp: +77051181845
info@arcadia-tour.com
https://arcadia-tour.com/

Best regards,
Mohammad Ali
Arcadia Tourism Company
Almaty, Kazakhstan
```

---

### Segment C — India (مثال: Kesari #1)

**To:** holiday@kesari.in  
**Subject:** B2B Ground Rates — Tashkent/Samarkand/Almaty Groups | Arcadia Tourism

```
Dear Kesari Tours Team,

Your Tashkent–Samarkand–Bukhara–Almaty combined group itineraries show serious Central Asia commitment — we can optimize your Kazakhstan ground costs.

Arcadia Tourism Company (Almaty HQ):
• B2B net rates for Indian group departures (15–40 pax)
• English & Arabic-speaking guides (NRI/GCC mixed groups)
• Hotel blocks, transport, vegetarian/halal meal planning
• Single invoice for Almaty + Samarkand segments

Can we schedule a 15-minute call to share our rate sheet and 2026 departure coordination?

WhatsApp: +77051181845
info@arcadia-tour.com
https://arcadia-tour.com/

Best regards,
Mohammad Ali
Arcadia Tourism Company
```

---

## 5. WA Openers — Arabic + English

### Segment A — GCC

**AR:**
```
السلام عليكم — محمد علي من أركاديا السياحية (DMC ألماتي).

نقدّم ground B2B لمجموعات كازاخستان — مرشد عربي، أسعار net، حلال.

هل يناسبكم مكالمة 15 دقيقة لمشاركة rate sheet؟

+77051181845
```

**EN:**
```
Hi — Mohammad Ali, Arcadia Tourism (Almaty DMC). B2B ground for Kazakhstan groups — Arabic guides, net rates, halal coordination. 15-min call this week? +77051181845
```

---

### Segment B — Halal Asia

**EN (primary):**
```
Hi [Name] — Mohammad Ali, Arcadia Tourism Almaty. We support halal 4-Stans groups on the ground (KZ segment) — Arabic guides, B2B net rates, white-label for your rombongan. Can we share rates for your next departure? +77051181845
```

**AR (for mixed groups):**
```
السلام عليكم — أركاديا ألماتي، شريك ground لبرامج halal Central Asia. segment كازاخستان + مرشد عربي. مكالمة قصيرة؟ +77051181845
```

---

### Segment C — SG/VN/IN/KR/TR

**EN:**
```
Hi — Mohammad Ali, Arcadia Tourism (Almaty DMC). We handle the Kazakhstan segment for Silk Road group series — net B2B rates, English/RU guides, Sep–Oct 2026 dates. 15-min call? +77051181845
```

**AR (optional for mixed Muslim groups):**
```
مرحباً — DMC ألماتي لمجموعات Central Asia. أسعار B2B + مرشد عربي اختياري. +77051181845
```

---

## 6. ترتيب الإرسال المقترح (بعد الموافقة)

| الأسبوع | # | أهداف | السبب |
|---------|---|--------|-------|
| **1** | 1–4 | Kesari, Thomas Cook, Rabbani, Wishtravelers | halal + India volume |
| **1** | 5–6 | Nuh, Selamatbercuti | MY 3-Stans Sep |
| **2** | 8–10 | Thang Long, VietnamTourist, Dat Viet | VN Sep–Oct deps |
| **2** | 11 | Ayanis | TR May–Oct |
| **2** | 12–15 | Culture, Tienshan, Majung, Very Good | KR Silk Road |
| **3** | 16–18 | Travel House, Akbar packages, ITL UAE | UAE Dec planning |
| **3** | 19–24 | KITTC, Global BH, Kanoo BH, Almosafer, ITL KSA, Al Maha | GCC expand |

**قواعد:** 9–11 ص Almaty · 1 بريد/10 د · WA يوم 3 · لا Safeer · لا JS جماعي.

---

## 7. Top 10 Batch 5 — أول إرسال بعد الموافقة

| # | الشركة | Priority | لماذا أولاً |
|---|--------|----------|------------|
| 1 | **Rabbani Tour** | A | halal 4-Stans — بديل/تكميل Hayatun |
| 2 | **Kesari Tours** | A | India groups CA — volume |
| 3 | **Thang Long Tours** | A | Sep–Oct 2026 deps confirmed |
| 4 | **Travel House Dubai** | A | Dec 2026 — planning الآن |
| 5 | **Nuh Travel** | A | 3-Stans MY — AMI follow-on |
| 6 | **Selamatbercuti** | A | 11H9M 3-Stans Sep 2026 |
| 7 | **Ayanis Tur** | A | TR groups May–Oct |
| 8 | **Culture Tour** | A | KR Silk Road 단체 |
| 9 | **VietnamTourist JSC** | A | 22N 5-Stans |
| 10 | **Wishtravelers** | A | ID 4-Stans rombongan |

---

## 8. ملفات مرتبطة

| الملف | |
|-------|---|
| `b2b-client-acquisition-strategy-ar.md` | استراتيجية 30 يوم |
| `b2b-pipeline-hot-leads-ar.md` | hot leads + WA اليوم |
| `outreach-sent-log-batch4-ar.md` | 30 already sent |
| `b2b-partner-targets.md` | 113 master list |

---

*25 يونيو 2026 — 28 targets · drafts only · no auto-send.*
