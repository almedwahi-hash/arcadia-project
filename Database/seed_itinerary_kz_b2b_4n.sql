-- B2B base programme: Kazakhstan Almaty 5 days / 4 nights (notes_ar = nights:4)
-- Derived from approved itineraries notes_ar = nights:5, days 1-5 (city/nearby only).
-- Day 5 merges shopping/Kok-Tobe (nights:5 D5) with departure (nights:5 D6).
-- Charyn, Kolsai, Kaindy are NOT included — optional extras only.

delete from public.itineraries
where country = 'Kazakhstan'
  and city = 'Almaty'
  and notes_ar = 'nights:4';

insert into public.itineraries (
  country, city, day_number, title_ar, title_en,
  description_ar, description_en, type, notes_ar
) values
(
  'Kazakhstan', 'Almaty', 1, 'الأول', 'Day 1',
  E'الاستقبال في المطار\nالتوصيل إلى الفندق وتسليم الغرف للراحة',
  E'Airport meet and greet\nTransfer to hotel and room check-in for rest',
  'arrival', 'nights:4'
),
(
  'Kazakhstan', 'Almaty', 2, 'الثاني', 'Day 2',
  E'رحلة إلى جبل ميديو\nالصعود بالتلفريك ثلاث محطات إلى شيمبولاك — الاستمتاع بالمناظر والنشاطات الترفيهية\nالغداء في أي مطعم\nالذهاب إلى شارع أربات',
  E'Medeu mountain trip\nCable car (3 stops) to Shymbulak — scenic views and activities\nLunch at a restaurant\nWalk on Arbat Street',
  'tour', 'nights:4'
),
(
  'Kazakhstan', 'Almaty', 3, 'الثالث', 'Day 3',
  E'دخول المحميات الطبيعية (الرسوم للشخص 1$)\nرحلة إلى وادي الما-أرسان — المشي بجانب النهر (الينابيع الساخنة)\nجولة لوادي الدببة (ايوساي فيزيت سنتر)',
  E'Nature reserve entry (approx. $1/person)\nMa-Arsan valley — riverside walk (hot springs area)\nBear Valley tour (Ayusai Visit Center)',
  'tour', 'nights:4'
),
(
  'Kazakhstan', 'Almaty', 4, 'الرابع', 'Day 4',
  E'رحلة إلى منتجع أوي كاراجاي (يبعد عن المدينة 40 كم)\nدخول المنتجع بالسيارة: أيام عادية 6$ / أيام عطل 12$\nالاستمتاع بالنشاطات الترفيهية\nالعودة إلى المدينة',
  E'Oi-Qaraghay resort day trip (40 km from city)\nCar entry: weekdays $6 / holidays $12\nRecreational activities\nReturn to Almaty',
  'tour', 'nights:4'
),
(
  'Kazakhstan', 'Almaty', 5, 'الخامس', 'Day 5',
  E'تسوق داخل المدينة\nزيلوني بازار (السوق الأخضر) — سوق شعبي\nزيارة معمل الشوكولاتة رخات الأشهر في كازاخستان\nالصعود بالتلفريك إلى جبل كوك توبه المطل على المدينة\nتسليم الغرف والتوصيل إلى المطار\nالمغادرة إلى أرض الوطن',
  E'City shopping\nGreen Bazaar (Zelyoni Bazar)\nRakhat chocolate factory visit\nKok-Tobe cable car overlooking the city\nHotel checkout and airport transfer\nDeparture',
  'departure', 'nights:4'
);
