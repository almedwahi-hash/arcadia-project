# B2B Database Research Log | سجل بحث قاعدة بيانات B2B

> Date: 2026-07-05 | Researcher: Cloud Agent | Mode: research only — **no emails sent**

## 1. Methodology

1. Built `deliverables/exclude_emails.txt` (65 emails / 53 domains) from `.tmp_batch4/5/6_sent.json` + all outreach/b2b/sales markdown files. Every candidate checked against it (email + company + domain).
2. Search passes per bucket (EN + AR + ID + VN queries): "[country] outbound tour operator group tours", "halal travel agency [city]", "Central Asia tour operator [country]", "Silk Road package wholesaler", "paket wisata muslim Asia Tengah", "رحلات كازاخستان/أذربيجان".
3. **Every accepted row verified by fetching the agency's own website** and extracting the contact email from the page. `verified_source_url` = the exact page where the email appears. Zero guessed/fabricated emails.
4. Prioritized agencies showing group departures, halal focus, CIS/Stans/Kazakhstan product lines.
5. Rejections logged with reason (below).

## 2. Stats

| Metric | Value |
|---|---|
| Candidates researched (search hits triaged) | ~70 |
| Sites fetched for verification | 38 |
| **Accepted (NEW, verified)** | **19** |
| Rejected / logged | 36 |
| Deduped vs sent logs & prior target lists | 12 (incl. Hayatun Tour caught at final QA) |
| Priority A share | **17/19 = 89%** (bar: ≥40% ✅) |
| Unverified emails in CSVs | **0** ✅ |
| Duplicate companies/emails across files | 0 ✅ |

### Breakdown by country
UAE 4 · KSA 3 · Qatar 2 · Oman 2 · Kuwait 1 · Bahrain 1 (**GCC = 13**) | India 2 · Indonesia 1 · Malaysia 1 · Singapore 1 · USA (Tier B Muslim market) 1 (**Asia/Tier B = 6**)

### Quota status — ⚠️ shortfall (honest accounting)
| Bucket | Min | Delivered |
|---|---|---|
| GCC | 30 | **13** |
| Malaysia + Indonesia | 20 | **2** |
| VN + KR + SG | 20 | **1** |
| India + Tier B | 10 | **3** |
| TOTAL | ≥80 | **19** |

**Why:** the zero-unverified-email quality bar eliminated most volume. ~40% of strong-fit agencies hide email behind JS-rendered pages, web forms, or WhatsApp-only contact (list in §4). Vietnam→CIS outbound is near-nonexistent; Korean operators (Hana/Mode/VeryGood) use Korean-only portals with no public email — both markets under-deliver structurally, not for lack of search.

**To close the gap (next session):** (1) browser-assisted pass (real Chrome) on the §4 list — est. +15–20 verified; (2) MATTA/ASITA/NATAS member directories for MY/ID/SG; (3) KATA (Korea) member list with a Korean-speaking pass; (4) GCC second sweep: Ajman/RAK/Fujairah agencies + Saudi Umrah operators adding Central Asia lines.

## 3. Rejected entries (36) — main reasons
- **Already contacted / in prior lists (dedupe):** Akbar (all units), Tabeer, Regency, Rayna, Almosafer, Kanoo, ITL World, Gulf Air Holidays, Global Travel BH, Tailwinds SG, Hayatun Tour, Musafir, Al Rostamani…
- **No public email (JS/form/WhatsApp-only) despite strong fit:** Apple Vacations MY (Almaty group series KZALA07 + B2B dept!), CIT Malaysia (KZ+UZ Muslim packages), Dwins Halal Tour ID (KZ/UZ/3-Stan 2026 departures), Fly World KW (Georgia line), Target Travels QA, TravelPoint OM, Cozmo UAE, GoKite UAE, Holiday Factory UAE, Orient Travel UAE, Usrah/Senyum/Fayyaz/Dreamcation SG, Flamingo IN, ARBY ID (Cloudflare-obfuscated). **← highest-value follow-up list.**
- **OTA/airline/marketplace:** flydubai Holidays, Yatra, Myholidays, HalalTrip.
- **Competitors (KZ/UZ-based DMCs):** SUVTOURS, Baltas, Advantour, Anur, Central Asia Travel.

Full machine-readable logs: accepted/rejected JSONL retained in session workspace; CSVs are authoritative.

## 4. Top 10 Priority A for first outreach batch (batch 7)

1. **AFC Holidays** (UAE) — mail@afcholidays.com — UAE's #1 escorted-group operator, KZ/UZ/KG lines, MICE
2. **Travelon Tours** (Kuwait) — info@travelontourskw.com — dedicated Kazakhstan page + "Become Our Partner" B2B page
3. **Al Hashar Travels** (Oman) — holidays@alhashartravels.com — WTA Oman winner, Caucasus lines
4. **Sabsan Holidays** (UAE) — contact@sabsanholidays.com — UZ/KG/AZ/AM/GE lines
5. **Mahira Travel** (Malaysia) — booking@mahiratravels.com — 11D halal 3-Stan group incl. Kazakhstan
6. **Adinda Azzahra** (Indonesia) — contact@adindaazzahra.com — 9D Turkey+UZ+KZ wisata muslim
7. **Travel Knits** (Bahrain) — info@travelknits.com — live Kazakhstan 3N4D + AZ/GE/Moscow packages
8. **Aataa Holidays** (Qatar) — info@aataaholidays.com — Georgia/Azerbaijan lines, 24/7
9. **Saraya Travel** (KSA) — Ahmed.hagag@sarayatravel.net — UZ+Russia destinations, Arabic
10. **Holidaymakers** (UAE) — support@holidaymakers.com — KZ/UZ destinations, groups to 50 pax

---

## 5. الملخص النهائي (عربي)

**النتيجة:** **19 وكالة جديدة موثّقة** (بريد مؤكّد من موقع الوكالة نفسها + رابط مصدر لكل صف) — **صفر بريد مخمّن**.

**التوزيع:** الخليج 13 (الإمارات 4، السعودية 3، قطر 2، عُمان 2، الكويت 1، البحرين 1) | آسيا وTier B: الهند 2، إندونيسيا 1، ماليزيا 1، سنغافورة 1، أمريكا (سوق مسلم) 1.

**الجودة:** أولوية A = 89% (المطلوب ≥40%)، لا تكرار، لا تعارض مع سجلات الإرسال (تم استبعاد 12 مكرراً، منها Hayatun اكتُشف في الفحص النهائي).

**الفجوة:** الحصص (≥80) لم تكتمل — السبب معيار «صفر بريد غير موثّق»: ~15–20 وكالة قوية المطابقة (Apple Vacations، CIT، Dwins، Fly World…) تخفي بريدها خلف JavaScript أو نماذج فقط — جاهزة للاستكمال بجلسة متصفح حقيقي (القائمة في §3-4).

**أفضل 10 للدفعة القادمة:** القسم §4 أعلاه — تبدأ بـ AFC Holidays وTravelon (صفحة شراكة B2B جاهزة).

**الملفات:** `b2b-database-gcc-verified.csv` (13) · `b2b-database-asia-verified.csv` (6) · `b2b-database-master-verified.csv` (19, مرتّبة بالأولوية) · `exclude_emails.txt` (65).

*لا يُرسل أي بريد من هذا الملف — بحث وتوثيق فقط.*

---

# Batch 8 | الدفعة الثامنة

> Date: 2026-07-07 | Researcher: Cloud Agent (scheduled task) | Mode: research only — **no emails sent**

## 1. Methodology

1. Rebuilt `deliverables/exclude_emails.txt` from scratch: merged `.tmp_batch4/5/6/7_sent.json`, `.tmp_batch7_followup_remaining.json`, and every email in `deliverables/*.md` + `deliverables/*.csv` (regex extraction, since one source JSON had mojibake that broke strict JSON parsing). Result: 122 pre-existing emails → **140 after adding batch 8's 18 new ones**. Every candidate this round was checked against this list by email AND by company-owned domain (generic webmail providers — gmail.com, yahoo.co.id — were only excluded at the specific-address level, not domain-wide).
2. Search passes: MATTA (Malaysia) / ASITA (Indonesia) / NATAS (Singapore) / TAAI-IATO (India) member and trade-fair signal search, GCC Umrah/package operators, Korean/Vietnamese/Philippine outbound queries, and Arabic-language Saudi query — each followed by a fetch of the agency's own contact/product page.
3. **Zero-unverified-email bar maintained**: every accepted row's email was read directly off the agency's own website (contact page, footer, or product-page mailto/text) — no third-party directory emails (ZoomInfo, RocketReach, Lusha, etc.) accepted even when suggested by search snippets.
4. Retried the batch-7 "highest-value blocked" list with alternate pages (contact-us, about-us, product page instead of homepage): **Holiday Factory (UAE) and MITRA Malaysia both unblocked this way** — Holiday Factory's `corporate@holiday-factory.com` and MITRA's `info@mitra.travel` were both sitting in plain text on their own contact pages once the right URL was tried. Apple Vacations MY and Orient Travel UAE resurfaced but at domains already contacted in batch 7 (rejected as dedupe, not re-verified). Cozmo Travel, TravelPoint Oman, and TM Fouzy/Al Fattah (Singapore) remained blocked (JS-rendered or Cloudflare email-obfuscated pages that returned empty/undecodable content on fetch).

## 2. Stats

| Metric | Value |
|---|---|
| Candidates researched (search hits triaged) | ~55 |
| Sites fetched for verification | 28 |
| **Accepted (NEW, verified)** | **18** |
| Rejected / logged | 22 |
| Deduped vs sent logs & batch 4-7 target lists | 6 |
| Priority A share | **17/18 = 94%** (bar: ≥40% ✅) |
| Unverified emails in CSV | **0** ✅ |
| Duplicate companies/emails across files | 0 ✅ |

### Breakdown by country
Malaysia 7 (incl. 1 Tier-B) · Singapore 3 · Indonesia 2 · India 2 · Oman 1 · Vietnam 1 · UAE 1 · Philippines 1

### Quota status — ⚠️ shortfall (honest accounting, same structural cause as batch 7)
| Bucket | Target | Delivered |
|---|---|---|
| Malaysia/Indonesia/Singapore (MATTA/ASITA/NATAS) | 20 | **12** |
| GCC (Umrah operators adding CIS) | 10 | **2** (Bahwan, Holiday Factory) |
| India/Tier B | 5 | **2** |
| Trade-fair exhibitor leads (ATM Dubai/MITT) | 5 | **0** — no usable public emails surfaced this round |
| New markets (Philippines, Vietnam) | — | **2** (bonus, not in original target buckets) |
| TOTAL | 30–40 | **18** |

**Why:** the zero-unverified-email bar is doing the same work it did in batch 7 — a large share of otherwise strong-fit agencies (Golden Rama Indonesia, Smiletrip Indonesia, Cozmo UAE, TravelPoint Oman, TM Fouzy/Al Fattah Singapore) advertise Kazakhstan/Uzbekistan/Kyrgyzstan product lines but only expose WhatsApp, a contact form, or a Cloudflare-obfuscated `mailto` on their own site — no plain-text email to verify. GCC trade-fair exhibitor lists (ATM Dubai 2026, MITT) did not yield fresh public-email leads this round; most exhibitor directories list company names/booth numbers only, not contacts.

**To close the gap (next session):** (1) browser-assisted pass to decode Cloudflare email-protection spans on TravelConnect.sg, TravelPoint Oman, TM Fouzy, Al Fattah; (2) a KATA Korea member-list pass with Korean-speaking search (this round's Korean query again surfaced only Hana Tour, already contacted); (3) Saudi Umrah-operator sweep needs an Arabic browser session — text search alone kept surfacing visa-service and DMC pages instead of agency contact pages; (4) MATTA/NATAS/ASITA official member directories should be paged through directly rather than via search snippets, which mostly surface the same ~15 agencies already found across batches 6-8.

## 3. Rejected entries (22) — main reasons
- **No public email on own site despite strong CIS product fit (WhatsApp/form/JS only):** Golden Rama Tours & Travel (Indonesia — dedicated "Favorite Three Stans" & "Four Stans" product lines), Smiletrip.id (Indonesia — dedicated 7D6N Kazakhstan/Kyrgyzstan/Uzbekistan product), Cozmo Travel (UAE), TravelPoint Oman (Cloudflare-obfuscated `mailto`), TM Fouzy Travel & Tours (Singapore), Al-Fattah Travel & Tours (Singapore), TravelConnect.sg (Cloudflare-obfuscated `mailto`, despite an Uzbekistan-trip customer testimonial on their homepage), eTravel PH (Philippines — contact form only, no visible email despite a dedicated Kazakhstan & Uzbekistan 14-day package page).
- **Already contacted / same company domain as batch 4-7 (dedupe):** Apple Vacations Malaysia (applevacations.my), Orient Travel UAE (orienttravels.com — new individual mailboxes `sales@`/`asim@` found but same previously-contacted domain), Al Qaed Travel (Saudi, alqaedtravel.com).
- **Competitors (KZ/UZ/CIS-based inbound DMCs, not outbound sellers):** Advantour, Anur Tour, Central Asia Travel, Kolsai Tour, SUVTOURS, Global Air DMC, Agate Travel, Central Asia Guide — all resurfaced repeatedly across GCC/Qatar/Bahrain/Philippines search passes; consistently rejected per batch-7 precedent.
- **OTA/marketplace/aggregator noise:** Yatra, Myholidays, flydubai Holidays, Wego, TravelChinaGuide — all appeared in "Kazakhstan tour packages from [country]" searches but are inbound OTA listings, not the outbound agencies' own sites.
- **Korean market structurally blocked again:** Korean-language query surfaced only Hana Tour (already contacted in batch 7); no new Korean operator with a public email found.

## 4. Top 10 Priority A for next outreach batch (batch 8)

1. **MITRA Malaysia Sdn Bhd** — info@mitra.travel — MATTA member with a live, priced (RM8,195) 11D10N Kazakhstan+Uzbekistan package and downloadable itinerary flyer — strongest product-fit find this round
2. **Holiday Factory Package Tours LLC** (UAE) — corporate@holiday-factory.com — UAE's #1 online package operator since 2011, dedicated Group/Corporate inbox; previously on the "blocked" list, unblocked this session
3. **Senyum Travel** (Singapore) — hello@senyum.com.sg — dedicated Uzbekistan Group Tours page, NATAS/bizSAFE member, recent (June 2026) Uzbekistan-trip reviews
4. **Usrah Travel Pte Ltd** (Singapore) — enquiries@usrahtravel.sg — Muslim halal tours + corporate travel services, STB-licensed
5. **Dream Holidays / PT Legacy Tourism Indonesia** — dreamholidays.co.id@gmail.com — ASITA member, dedicated "3 Stan" (UZ/KG/KZ) open-trip product
6. **Rakso Air Travel & Tours Inc.** (Philippines) — support@raksotravel.com — IATA-accredited, 25+ years, dedicated Central Asia Silk Road group product — first Philippines agency in the database
7. **Bahwan Travel Agencies LLC** (Oman) — info@bahwantravels.com — major Oman outbound operator
8. **Flamingo Transworld Pvt Ltd** (India) — world@flamingotravels.co.in — large outbound wholesaler, unblocked via alternate contact page
9. **MN Ajwa Travel & Tours / Destinasi2u** (Malaysia) — salesmntt@gmail.com — halal/Muslim group tours incl. 3-Stan
10. **Callista Tour** (Indonesia) — tour@callistatour.com — halal group tours incl. Central Asia

## 5. الملخص النهائي (عربي) — الدفعة الثامنة

**النتيجة:** **18 وكالة جديدة موثّقة** (بريد مؤكّد من موقع الوكالة نفسها + رابط مصدر لكل صف) — **صفر بريد مخمّن**.

**التوزيع:** ماليزيا 7 (منها فئة B واحدة) | سنغافورة 3 | إندونيسيا 2 | الهند 2 | عُمان 1 | فيتنام 1 | الإمارات 1 | الفلبين 1 (سوق جديد).

**الجودة:** أولوية A = 94% (المطلوب ≥40%)، لا تكرار، لا تعارض مع سجلات الإرسال (تم فحص 140 بريدًا مستبعدًا بعد التحديث).

**الإنجاز البارز:** تم فك حظر شركتين من قائمة الدفعة السابعة عالية القيمة — **Holiday Factory الإمارات** و**MITRA ماليزيا** — بالوصول المباشر لصفحة الاتصال الرسمية بدلاً من الصفحة الرئيسية.

**الفجوة:** لم تكتمل الحصة (30-40) للسبب نفسه في الدفعة السابعة — معيار «صفر بريد غير موثّق» يستبعد وكالات قوية المطابقة (Golden Rama، Smiletrip، Cozmo، TravelPoint عُمان، TravelConnect، TM Fouzy، Al-Fattah) تُخفي بريدها خلف واتساب أو نماذج أو حماية Cloudflare — قائمة جاهزة لجلسة متصفح حقيقي في القسم §3.

**أفضل الوكالات للدفعة القادمة:** القسم §4 أعلاه — تبدأ بـ MITRA ماليزيا وHoliday Factory الإمارات.

**الملفات:** `b2b-database-batch8-verified.csv` (18) · `exclude_emails.txt` (140، محدّث).

*لا يُرسل أي بريد من هذا الملف — بحث وتوثيق فقط.*
