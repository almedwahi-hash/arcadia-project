# سجل بحث دفعة 8 — قاعدة بيانات B2B موثّقة

> **التاريخ:** 2026-07-09  
> **الهدف:** 50–80 وكالة جديدة موثّقة | **المحقق:** 48 وكالة

## الملخص

- **إيميلات جديدة مُضافة:** 48
- **قائمة الاستبعاد المحمّلة:** 140 إيميل
- **مرفوض (تكرار / غير موثّق / خطأ اتصال):** 17
- **مستبعد (قائمة exclude/blocklist):** 0
- **طريقة التحقق:** ظهور الإيميل نصّاً أو mailto على صفحة رسمية (Contact/About/Footer/Product)

## توزيع الدول (أعلى 12)

| الدولة | العدد |
|--------|------:|
| Vietnam | 10 |
| United Kingdom | 8 |
| Philippines | 6 |
| Jordan | 4 |
| South Korea | 3 |
| Morocco | 3 |
| Singapore | 3 |
| Japan | 2 |
| India | 2 |
| Hong Kong | 2 |
| Indonesia | 2 |
| Turkey | 1 |

## الملفات المُنتَجة

- `deliverables/b2b-database-batch8-new.csv` — صفوف الدفعة 8 فقط
- `deliverables/b2b-database-master-verified.csv` — مدمج مع الدفعات السابقة
- `deliverables/b2b-database-batch8-research-log-ar.md` — هذا الملف

## مناطق لا تزال دون الحصة المستهدفة

- **اليابان:** 2 فقط (Five Star Club، Indus Travel) — تحتاج 5–8 إضافية
- **كوريا:** 3 (CIS Tour، Small Star، Very Good Tour) — تحتاج 5+ إضافية
- **مصر/الأردن/المغرب:** 3 مجتمعة — تحتاج 5–10 لكل منطقة MENA صادرة
- **هونغ كونغ:** 2 (DeWonder، EGL) — GLO Travel موقوف مؤقتاً
- **GCC جديد:** 1 فقط (Holiday Factory + Bahwan عُمان) — الإمارات/السعودية مُستنفدة سابقاً

## عينة تحقق يدوي (Top 10 للدفعة 9)

1. **TripsTide Pvt Ltd** — `sales@tripstide.com` — [https://tripstide.com/](https://tripstide.com/)
2. **Five Star Club (Japan)** — `info@fivestar-club.co.jp` — [https://www.fivestar-club.jp/tour/?tcd=7UK72-AOZ-X](https://www.fivestar-club.jp/tour/?tcd=7UK72-AOZ-X)
3. **Indus Travel Co.** — `industokyo@indus-travel.com` — [https://www.otoa.com/english/full_member/detail.php?serial=297](https://www.otoa.com/english/full_member/detail.php?serial=297)
4. **CIS Tour (Korea)** — `info@cis-tour.com` — [http://cis-tour.com/about](http://cis-tour.com/about)
5. **MNG Turizm** — `info@mngturizm.com` — [https://www.mngturizm.com/iletisim](https://www.mngturizm.com/iletisim)
6. **Go Russia Ltd** — `info@justgorussia.co.uk` — [https://www.justgorussia.co.uk/pdf/SR-08.pdf](https://www.justgorussia.co.uk/pdf/SR-08.pdf)
7. **Wendy Wu Tours UK** — `info@wendywutours.co.uk` — [https://www.wendywutours.co.uk/contact-us](https://www.wendywutours.co.uk/contact-us)
8. **Wild Frontiers Travel** — `info@wildfrontierstravel.com` — [https://www.wildfrontierstravel.com/en_GB/contact-us](https://www.wildfrontierstravel.com/en_GB/contact-us)
9. **DH Travel (Du Lich Quoc Te DH)** — `director@dhtravel.com.vn` — [https://dhtravel.com.vn/tour-trung-a-kham-pha-con-duong-to-lua-huyen-thoai-dip-tet-ba-tu-nowruz](https://dhtravel.com.vn/tour-trung-a-kham-pha-con-duong-to-lua-huyen-thoai-dip-tet-ba-tu-nowruz)
10. **VGC Travel** — `info@vgctravel.com.vn` — [https://vgctravel.com.vn](https://vgctravel.com.vn)

## مستبعد من الدفعة 8 (كان في batch8-verified لكنه مُرسَل/محظور)


## مرفوضات بارزة

- `info@setur.com.tr` — مُرسَل سابقاً (batch 7)
- `almatykim@hotmail.com` / `tour@culturetour.co.kr` — قائمة الاستبعاد
- ATNT Travel — لا إيميل على صفحة Contact (نموذج فقط)
- GLO Travel HK — الموقع موقوف (suspended)
- DMC منافسون في KZ (EZ Tours، KazVibe، Advantour Almaty) — مستبعدون حسب السياسة

## منهجية

1. تحميل `exclude_emails.txt` + كل CSVs السابقة
2. بحث ويب حسب المنطقة: Vietnam Trung Á، Korea 중앙아시아، UK Silk Road، PH outbound
3. جلب صفحة المصدر والتحقق من وجود الإيميل
4. دمج بدون تكرار → master

*Arcadia Tourism — batch 8 research log — 2026-07-09*