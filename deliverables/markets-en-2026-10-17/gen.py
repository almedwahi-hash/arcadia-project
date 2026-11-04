# -*- coding: utf-8 -*-
import json, os, html
OUT = '/home/user/arcadia-project/deliverables/markets-en-2026-10-17'
WA = "https://wa.me/77064007561?text="
def wa(txt): 
    import urllib.parse; return WA + urllib.parse.quote(txt.replace('{NL}','\n'))
MAIL = "mailto:info@arcadia-tour.com?subject="
L = {
 'hub':'https://arcadia-tour.com/en/visa-free-travel/',
 'kz':'https://arcadia-tour.com/en/tourism-in-kazakhstan/','uz':'https://arcadia-tour.com/en/tourism-in-uzbekistan/',
 'ru':'https://arcadia-tour.com/en/tourism-in-russia/','pl':'https://arcadia-tour.com/en/tourism-in-poland/','cn':'https://arcadia-tour.com/en/china-main-en/',
 'mice':'https://arcadia-tour.com/en/corporate-incentive-travel/','mice_kz':'https://arcadia-tour.com/en/corporate-incentive-travel/kazakhstan-corporate-trips/',
 'mice_uz':'https://arcadia-tour.com/en/corporate-incentive-travel/uzbekistan-corporate-trips/','mice_cn':'https://arcadia-tour.com/en/corporate-incentive-travel/china-corporate-trips/',
 'mice_pl':'https://arcadia-tour.com/en/corporate-incentive-travel/poland-corporate-trips/',
 'almaty3':'https://arcadia-tour.com/en/almaty-in-3-days/','astana2':'https://arcadia-tour.com/en/astana-in-2-days/','tashkent2':'https://arcadia-tour.com/en/tashkent-in-two-days/',
 'kzuz10':'https://arcadia-tour.com/en/kazakhstan-uzbekistan-10-days/','shanghai3':'https://arcadia-tour.com/en/shanghai-in-3-days/','warsaw3':'https://arcadia-tour.com/en/warsaw-in-3-days/',
 'moscow3':'https://arcadia-tour.com/en/moscow-in-3-days/','spb3':'https://arcadia-tour.com/en/saint-petersburg-in-3-days/',
 'hotels_almaty':'https://arcadia-tour.com/en/the-best-hotels-in-almaty-2026-your-comprehensive-guide-to-an-exceptional-trip-i/','hotels_astana':'https://arcadia-tour.com/en/best-hotels-in-astana/',
 'shymbulak':'https://arcadia-tour.com/en/shymbulak-medeu-guide/','burabay':'https://arcadia-tour.com/en/burabay-guide/',
 'kz_cost':'https://arcadia-tour.com/en/kazakhstan-trip-cost-2026/','uz_cost':'https://arcadia-tour.com/en/uzbekistan-trip-cost-2026/','uz_time':'https://arcadia-tour.com/en/best-time-to-visit-uzbekistan/',
 'uz_islam':'https://arcadia-tour.com/en/uzbekistan-islamic-heritage-guide/','bukhara':'https://arcadia-tour.com/en/bukhara-travel-guide/','halal_cn':'https://arcadia-tour.com/en/china-halal-food-en/',
 'kz_things':'https://arcadia-tour.com/en/best-things-to-do-in-kazakhstan-2026/','uz_things':'https://arcadia-tour.com/en/best-things-to-do-in-uzbekistan-2026/','cn_things':'https://arcadia-tour.com/en/best-things-to-do-in-china-2026/',
 'pl_things':'https://arcadia-tour.com/en/top-tourist-attractions-in-poland-2026/','ru_things':'https://arcadia-tour.com/en/best-things-to-do-in-russia-2026/',
 'canton':'https://arcadia-tour.com/en/canton-fair-business-mission/','teambuild':'https://arcadia-tour.com/en/team-building-kazakhstan/',
 'my':'https://arcadia-tour.com/en/visa-free-travel/malaysia/','kr':'https://arcadia-tour.com/en/visa-free-travel/south-korea/','sg':'https://arcadia-tour.com/en/visa-free-travel/singapore/',
 'au':'https://arcadia-tour.com/en/visa-free-travel/australia-new-zealand/','uk':'https://arcadia-tour.com/en/visa-free-travel/united-kingdom/',
}
L['jp']='https://arcadia-tour.com/en/visa-free-travel/japan/'; L['id']='https://arcadia-tour.com/en/visa-free-travel/indonesia/'
L['th']='https://arcadia-tour.com/en/visa-free-travel/thailand/'; L['ph']='https://arcadia-tour.com/en/visa-free-travel/philippines/'; L['in']='https://arcadia-tour.com/en/visa-free-travel/india/'
GREEN='#168b52'; NAVY='#17324d'
def cta(title, text, wa_text, mail_subj, top=False):
    m = "margin:22px 0" if top else "margin:30px 0 10px"
    return f'''  <section style="{m};padding:22px 18px;text-align:center;background:#eef8f1;border-radius:14px">
    <h2 style="margin:0 0 8px;color:{NAVY}">{title}</h2>
    <p style="margin:0 0 13px;line-height:1.8">{text}</p>
    <a href="{wa(wa_text)}" target="_blank" rel="noopener noreferrer" style="display:inline-block;margin:4px;padding:12px 20px;border-radius:9px;background:{GREEN};color:#fff;text-decoration:none;font-weight:700">Chat on WhatsApp</a>
    <a href="{MAIL}{mail_subj}" style="display:inline-block;margin:4px;padding:12px 20px;border-radius:9px;background:{NAVY};color:#fff;text-decoration:none;font-weight:700">Send a request by email</a>
  </section>
'''
def note():
    return '<p style="font-size:.93em;color:#555;border-top:1px solid #e3e8ee;padding-top:10px"><strong>Please note:</strong> entry rules are set by each government and can change. The information above reflects official announcements as of October 2026 for ordinary passports and tourism or business visits; confirm with the relevant embassy before you book. Arcadia provides tourism and logistics services only and does not issue visas. Where a visa is required, we supply hotel confirmations and programme letters to support your own application.</p>'
def table(rows):
    s='<table style="width:100%;border-collapse:collapse;margin:12px 0 18px"><thead><tr style="background:#f0f4f8"><th style="padding:9px;border:1px solid #d9e1ea;text-align:left">Destination</th><th style="padding:9px;border:1px solid #d9e1ea;text-align:left">Visa-free?</th><th style="padding:9px;border:1px solid #d9e1ea;text-align:left">Details</th></tr></thead><tbody>'
    for d,v,t in rows:
        col = GREEN if v.startswith('Yes') else '#b54708'
        s+=f'<tr><td style="padding:9px;border:1px solid #d9e1ea"><strong>{d}</strong></td><td style="padding:9px;border:1px solid #d9e1ea;color:{col};font-weight:700">{v}</td><td style="padding:9px;border:1px solid #d9e1ea;line-height:1.7">{t}</td></tr>'
    return s+'</tbody></table>'
def faq(items):
    return '<h2>Frequently asked questions</h2>'+''.join(f'<h3>{q}</h3><p>{a}</p>' for q,a in items)
def readalso(pairs):
    return '<p class="arcadia-read-also">Read also: '+' · '.join(f'<a href="{u}">{t}</a>' for t,u in pairs)+'.</p>'
def ul(items): return '<ul style="line-height:2">'+''.join(f'<li>{i}</li>' for i in items)+'</ul>'

pages = {}

# ---------------- HUB ----------------
hub_rows = [
 ("Malaysia", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days · Poland 90 days", "Russia: visa required (e-visa online). <a href='"+L['my']+"'>Guide for Malaysian travellers</a>"),
 ("South Korea", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days · Poland 90 days · Russia 60 days", "The only market on this list that is visa-free for all five destinations. <a href='"+L['kr']+"'>Guide for Korean travellers</a>"),
 ("Singapore", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days · Poland 90 days", "Russia: visa required (e-visa online). <a href='"+L['sg']+"'>Guide for Singaporean travellers</a>"),
 ("Japan", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days · Poland 90 days", "Russia: visa required (e-visa online). <a href='"+L['jp']+"'>Guide for Japanese travellers</a>"),
 ("Australia and New Zealand", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days · Poland 90 days", "Russia: visa required. <a href='"+L['au']+"'>Guide for Australian and New Zealand travellers</a>"),
 ("United Kingdom", "Kazakhstan 30 days · Uzbekistan 30 days · Poland 90 days", "China: 240-hour visa-free transit only; Russia: visa required. <a href='"+L['uk']+"'>Guide for UK travellers</a>"),
 ("United States and Canada", "Kazakhstan 30 days · Poland 90 days", "Uzbekistan: visa-free only from age 55 (US), 30 days (Canada); China: 240-hour transit only; Russia: visa required."),
 ("Thailand", "Kazakhstan 30 days · China 30 days · Russia 30 days", "Uzbekistan and Poland: visa required. <a href='"+L['th']+"'>Guide for Thai travellers</a>"),
 ("Indonesia", "Kazakhstan 30 days · Uzbekistan 30 days", "China: 240-hour transit only; Poland and Russia: visa required. <a href='"+L['id']+"'>Guide for Indonesian travellers</a>"),
 ("Philippines", "Kazakhstan 30 days", "Uzbekistan, China, Poland and Russia: visa required. <a href='"+L['ph']+"'>Guide for Filipino travellers</a>"),
 ("India", "Kazakhstan 14 days", "Up to 14 days per visit and 42 days in 180. Uzbekistan and Russia: e-visa; China and Poland: visa required. <a href='"+L['in']+"'>Guide for Indian travellers</a>"),
 ("Vietnam", "Kazakhstan 30 days", "Uzbekistan: visa-free only from age 55; China, Poland and Russia: visa required (Russia e-visa online)."),
 ("UAE", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days · Poland 90 days · Russia 90 days", "Visa-free for all five destinations."),
 ("Saudi Arabia", "Kazakhstan 30 days · Uzbekistan 30 days · China 30 days", "Poland: Schengen visa required; Russia: e-visa online."),
 ("Qatar", "Kazakhstan 30 days · Uzbekistan 30 days (short stay) · China 30 days", "Poland: Schengen visa required; Russia: e-visa online."),
 ("Oman, Kuwait, Bahrain", "Kazakhstan 30 days · Uzbekistan (short stay) · China 30 days", "Poland: Schengen visa required; Russia: e-visa online."),
 ("Türkiye", "Kazakhstan 90 days · Uzbekistan 30 days · Russia 30 days", "China and Poland: visa required."),
]
def hubtable(rows):
    s='<table style="width:100%;border-collapse:collapse;margin:12px 0 18px"><thead><tr style="background:#f0f4f8"><th style="padding:9px;border:1px solid #d9e1ea;text-align:left">Your passport</th><th style="padding:9px;border:1px solid #d9e1ea;text-align:left">Visa-free destinations</th><th style="padding:9px;border:1px solid #d9e1ea;text-align:left">Notes</th></tr></thead><tbody>'
    for d,v,t in rows:
        s+=f'<tr><td style="padding:9px;border:1px solid #d9e1ea"><strong>{d}</strong></td><td style="padding:9px;border:1px solid #d9e1ea;line-height:1.7;color:{GREEN};font-weight:600">{v}</td><td style="padding:9px;border:1px solid #d9e1ea;line-height:1.7">{t}</td></tr>'
    return s+'</tbody></table>'

pages['hub'] = dict(
 slug='visa-free-travel', parent=0,
 title='Visa-Free Travel to Kazakhstan, Uzbekistan, Russia, Poland and China: Who Enters Without a Visa in 2026',
 yoast_title='Visa-Free Travel to Kazakhstan, Uzbekistan & China 2026',
 yoast_desc='Which passports enter Kazakhstan, Uzbekistan, China, Poland and Russia visa-free in 2026: Malaysia, Korea, Singapore, Australia, UK and more. Tours by Arcadia.',
 focuskw='visa-free travel Kazakhstan',
 body=f'''<article class="arcadia-market-hub-2026" lang="en" dir="ltr">
  <p><strong>Arcadia</strong> is a destination management company based in Almaty that organises private tours, family holidays and <a href="{L['mice']}">corporate trips</a> in Kazakhstan, Uzbekistan, Russia, Poland and China. Many of our guests choose these destinations because they can simply board a plane: no consulate visit, no visa fee and no waiting. This page summarises which passports enter each of our five destinations <strong>visa-free</strong> in 2026, and links to detailed guides for the markets we serve most in English.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> Kazakhstan is the easiest entry point in the region, with 30-day visa-free access for Malaysia, Singapore, South Korea, Japan, Australia, New Zealand, the UK, the US, Canada, Thailand, Indonesia, the Philippines, Vietnam and all Gulf states, and 14 days for India. Uzbekistan matches most of that list. China offers 30 days to Malaysia, Singapore, Korea, Japan, Australia, New Zealand and the Gulf. Poland (Schengen) admits Malaysia, Singapore, Korea, Japan, Australia, New Zealand, the UK and the UAE for 90 days. Russia is visa-free for Korea, the UAE, Thailand and Türkiye.</aside>
{cta("Plan a visa-free trip with a local team", "Tell us your passport, dates and group size. We confirm the entry rule for your route and send a full proposal within 48 hours.", "Hello Arcadia, we would like a proposal for a trip.{NL}Passport: {NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request", top=True)}
  <h2>Visa-free entry by passport (October 2026)</h2>
  <p>Ordinary passports, tourism and business visits. Durations are per visit unless stated; Kazakhstan also applies a general limit of 90 days in any 180-day period for visa-free visitors.</p>
{hubtable(hub_rows)}
  <h2>Market guides</h2>
{ul([
 f'<a href="{L["my"]}"><strong>Malaysia</strong></a>: direct AirAsia X flights to Almaty and Tashkent, halal food everywhere, and a visa-free Central Asia and China circuit.',
 f'<a href="{L["kr"]}"><strong>South Korea</strong></a>: nonstop flights from Seoul, a large Korean community in Almaty and Tashkent, and visa-free access to all five destinations.',
 f'<a href="{L["sg"]}"><strong>Singapore</strong></a>: one-stop connections via Kuala Lumpur or Seoul, a strong passport for the whole region, and short-break itineraries.',
 f'<a href="{L["au"]}"><strong>Australia and New Zealand</strong></a>: Silk Road and mountain itineraries of two to three weeks for long-haul travellers.',
 f'<a href="{L["uk"]}"><strong>United Kingdom</strong></a>: direct London flights to Almaty and Tashkent, and 30-day visa-free entry to both.',
 f'<a href="{L["jp"]}"><strong>Japan</strong></a>: nonstop Tokyo to Tashkent flights and visa-free access to Kazakhstan, Uzbekistan, China and Poland.',
 f'<a href="{L["id"]}"><strong>Indonesia</strong></a>: visa-free Kazakhstan and Uzbekistan with halal food, Islamic heritage and a single connection via Kuala Lumpur.',
 f'<a href="{L["th"]}"><strong>Thailand</strong></a>: nonstop Bangkok and Phuket flights to Almaty, snow weeks, and visa-free Kazakhstan, China and Russia.',
 f'<a href="{L["ph"]}"><strong>Philippines</strong></a>: 30 days visa-free in Kazakhstan, snow and mountains one connection from Manila.',
 f'<a href="{L["in"]}"><strong>India</strong></a>: 14 days visa-free in Kazakhstan, nonstop Delhi and Mumbai flights, vegetarian and Jain meals.',
])}
  <h2>What stays the same wherever you come from</h2>
{ul([
 '<strong>Passport validity:</strong> most of our destinations require at least six months of validity beyond your entry date (China asks for three), plus one blank page.',
 '<strong>Registration:</strong> hotels in Kazakhstan and Uzbekistan register foreign guests automatically. If you stay privately, registration is your own responsibility; our team explains the steps when needed.',
 '<strong>Onward ticket and funds:</strong> border officers may ask for a return ticket and hotel confirmation. We send both with every booking.',
 '<strong>Russia e-visa:</strong> for passports that are not visa-free, Russia offers an online e-visa (16 days) to citizens of over 60 countries including Malaysia, Singapore, Japan, India, Vietnam, Saudi Arabia and the Gulf. We do not apply on your behalf, but we provide the hotel confirmation the form requires.',
 '<strong>Schengen (Poland):</strong> the ETIAS online authorisation for visa-free nationals is expected to start in late 2026 with a transition period; it is a short online form, not a visa.',
])}
  <h2>Our five destinations at a glance</h2>
{ul([
 f'<a href="{L["kz"]}"><strong>Kazakhstan</strong></a>: Almaty with the Tian Shan mountains next door, Astana and the steppe. Four to five hours from the Gulf, seven to eight from Kuala Lumpur or Seoul.',
 f'<a href="{L["uz"]}"><strong>Uzbekistan</strong></a>: Samarkand, Bukhara and Khiva, the heart of the Silk Road, usually combined with Tashkent in six to eight nights.',
 f'<a href="{L["cn"]}"><strong>China</strong></a>: Guangzhou, Shanghai and Beijing for leisure and business, plus the Canton Fair and Yiwu market for trade missions.',
 f'<a href="{L["pl"]}"><strong>Poland</strong></a>: Warsaw, Kraków and Zakopane, an affordable Schengen destination with easy connections across Europe.',
 f'<a href="{L["ru"]}"><strong>Russia</strong></a>: Moscow and Saint Petersburg, with the Hermitage, Red Square and the imperial palaces.',
])}
{faq([
 ("Do you arrange visas?", "No. We are a tourism company and do not process visas. This page helps you choose destinations where your passport does not need one. Where a visa is required, we send the hotel confirmation and programme letter for your own application."),
 ("Can I combine two visa-free countries in one trip?", "Yes. The most popular combinations are Kazakhstan with Uzbekistan (a two-hour flight or a comfortable train from Almaty to Tashkent) and Kazakhstan with China via Urumqi or direct flights to Guangzhou and Shanghai. Each entry counts separately against the visa-free allowance."),
 ("Is the 30-day limit per visit or per year?", "Per visit in most cases. Kazakhstan additionally caps visa-free stays at 90 days in any 180-day period, and South Korean citizens have a 60-day cap in Kazakhstan. Longer stays require a visa or permit, which we do not handle."),
 ("Do children need anything extra?", "Children travel on their own passports and the same visa-free rules apply. A child travelling with one parent should carry a consent letter from the other parent for Kazakhstan, Uzbekistan and Russia."),
])}
{readalso([("Corporate travel and MICE",L['mice']),("Almaty in 3 days",L['almaty3']),("Tashkent in two days",L['tashkent2']),("Kazakhstan and Uzbekistan in 10 days",L['kzuz10']),("Shanghai in 3 days",L['shanghai3']),("Warsaw in 3 days",L['warsaw3'])])}
{note()}
{cta("Ready to travel without a visa?", "Hotels, transport, licensed guides and programmes under one contract, with prices on request for every group size.", "Hello Arcadia, we would like a proposal for a trip.{NL}Passport: {NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request")}
</article>''')

# ---------------- shared pieces ----------------
hotels_par = f'''<h2>Where you will stay</h2>
  <p>We work with four- and five-star hotels and choose by location first. In Almaty our partner hotels include the <strong>Swissôtel Almaty</strong> (five-star, at the foot of the mountains), <strong>Novotel Almaty City Center</strong> and the landmark <strong>Kazakhstan Hotel</strong> (both four-star, in the city centre). In Tashkent, Samarkand and Bukhara we use international chains and the best boutique hotels inside the old towns. See our guides to <a href="{L['hotels_almaty']}">hotels in Almaty</a> and <a href="{L['hotels_astana']}">hotels in Astana</a>.</p>'''
def mice_par(links):
    return f'''<h2>Travelling with your company?</h2>
  <p>Arcadia also runs <a href="{L['mice']}">incentive trips, conferences and team-building programmes</a> for companies of any size, with venue, equipment, transport and gala dinner under one contract. See our pages for {links}.</p>'''

# ---------------- MALAYSIA ----------------
pages['my'] = dict(
 slug='malaysia', parent='hub',
 title='Visa-Free Holidays for Malaysian Travellers: Kazakhstan, Uzbekistan, China and Poland Without a Visa 2026',
 yoast_title='Kazakhstan & Uzbekistan for Malaysians: Visa-Free 2026',
 yoast_desc='Malaysian passport holders enter Kazakhstan, Uzbekistan, China and Poland visa-free. Direct AirAsia X flights, halal food, itineraries and hotels by Arcadia.',
 focuskw='Kazakhstan visa-free for Malaysians',
 body=f'''<article class="arcadia-market-my-2026" lang="en" dir="ltr">
  <p>A <strong>Malaysian passport</strong> opens most of Central Asia and the Silk Road without a visa: <strong>30 days in Kazakhstan</strong>, <strong>30 days in Uzbekistan</strong>, <strong>30 days in China</strong> under the mutual exemption that took effect in July 2025, and <strong>90 days in Poland</strong> and the rest of the Schengen area. With AirAsia X now flying nonstop from Kuala Lumpur to both Almaty and Tashkent, a Malaysian family or group can be in the mountains above Almaty or the squares of Samarkand within eight hours of leaving KLIA. Arcadia, a destination management company based in Almaty, plans and runs the whole trip: hotels, transport, licensed English-speaking guides and halal meals.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan, Uzbekistan, China or Poland. Russia requires an e-visa applied for online. Halal food is the norm in Kazakhstan and Uzbekistan, both Muslim-majority countries, and mosques are everywhere. Best months: April to June and September to October; December to March for snow in Almaty.</aside>
{cta("Get a proposal for your Malaysian group", "Send your dates, number of travellers and the cities you have in mind. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from Malaysia and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Malaysia", top=True)}
  <h2>Where Malaysians travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period. Hotels register you automatically."),
 ("Uzbekistan","Yes, 30 days","Visa-free since 2018. Keep your hotel registration slips; our guides collect them for you."),
 ("China","Yes, 30 days","Mutual visa exemption between Malaysia and China for ordinary passports, in force since 17 July 2025, for tourism, business, family visits and transit."),
 ("Poland (Schengen)","Yes, 90 days","90 days in any 180-day period across the Schengen area. ETIAS online authorisation is expected from late 2026."),
 ("Russia","No, e-visa","Not yet visa-free (a mutual agreement is under negotiation). Malaysians can apply online for a 16-day e-visa; we supply the hotel confirmation but do not apply on your behalf."),
])}
  <h2>Flights from Malaysia</h2>
{ul([
 '<strong>Kuala Lumpur to Tashkent:</strong> AirAsia X nonstop three times a week (Monday, Wednesday, Friday) on an Airbus A330, about seven and a half hours.',
 '<strong>Kuala Lumpur to Almaty:</strong> AirAsia X nonstop, about seven and a half hours; alternatives with one stop via Istanbul, Dubai, Doha or Delhi.',
 '<strong>Almaty to Tashkent:</strong> under two hours by air, or an overnight sleeper train, which makes a combined Kazakhstan and Uzbekistan trip easy.',
 '<strong>China:</strong> many daily flights from KL to Guangzhou, Shanghai and Beijing; from Almaty, Air Astana and China Southern fly to Urumqi, Beijing and Guangzhou.',
 '<strong>Poland:</strong> one-stop connections via Doha, Dubai or Istanbul to Warsaw and Kraków.',
])}
  <h2>Halal food and prayer</h2>
  <p>Kazakhstan and Uzbekistan are Muslim-majority countries. Restaurants serve halal beshbarmak, plov, shashlik and samsa as standard, supermarkets label halal meat, and every city has central mosques with Friday prayer. In Almaty we also book Malaysian and Indonesian-style restaurants for groups who miss home cooking. In China we route groups through the Muslim quarters of Guangzhou, Xi'an and Beijing and book halal-certified restaurants in advance; see our <a href="{L['halal_cn']}">halal food in China</a> guide.</p>
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Almaty mountains and lakes, 4 to 5 nights:</strong> Medeu and Shymbulak by cable car, Big Almaty Lake, Charyn Canyon and Kolsai Lakes, with a free afternoon at the Green Bazaar. Based on our <a href="{L["almaty3"]}">Almaty in 3 days</a> programme.',
 f'<strong>Silk Road classic, 7 to 8 nights:</strong> Tashkent, Samarkand, Bukhara and Khiva by high-speed train, with Registan Square, the mausoleum of Imam al-Bukhari and the old-town madrasas. See <a href="{L["uz_islam"]}">Islamic heritage in Uzbekistan</a>.',
 f'<strong>Kazakhstan and Uzbekistan, 10 nights:</strong> fly into Almaty, out of Tashkent, as in our <a href="{L["kzuz10"]}">combined 10-day itinerary</a>.',
 f'<strong>Winter snow break, 4 nights:</strong> skiing or sledging on Shymbulak with instructors, hot springs and the ice rink at Medeu, December to March.',
 f'<strong>China trade and leisure, 5 to 6 nights:</strong> Guangzhou during the <a href="{L["canton"]}">Canton Fair</a> or Yiwu market, then <a href="{L["shanghai3"]}">Shanghai in 3 days</a>.',
])}
  {hotels_par}
  <h2>Practical notes for Malaysian travellers</h2>
{ul([
 '<strong>Currency:</strong> Kazakhstani tenge and Uzbek som; cards work in cities, and we recommend carrying some US dollars to exchange.',
 '<strong>Language:</strong> Kazakh, Uzbek and Russian; English is common in hotels and with our guides, limited elsewhere.',
 '<strong>Time zone:</strong> Almaty and Tashkent are three hours behind Kuala Lumpur, so jet lag is minimal.',
 '<strong>Weather:</strong> dry continental climate; summers are warm (30°C) and winters cold (down to -10°C in Almaty), so pack layers rather than tropical clothing.',
 '<strong>Insurance:</strong> travel insurance with medical cover is strongly recommended and required for Schengen.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>, <a href="{L["mice_uz"]}">Uzbekistan</a> and <a href="{L["mice_cn"]}">China</a>')}
{faq([
 ("Can Malaysians enter Kazakhstan without a visa?", "Yes. Malaysian citizens with an ordinary passport can stay up to 30 days per visit for tourism or business, within a limit of 90 days in any 180-day period."),
 ("Do Malaysians need a visa for Uzbekistan?", "No. Malaysia is on Uzbekistan's visa-free list for stays of up to 30 days."),
 ("Is China visa-free for Malaysians in 2026?", "Yes. Under the mutual visa exemption agreement in force since July 2025, Malaysians may stay up to 30 days per visit for tourism, business, family visits or transit."),
 ("Is Russia visa-free for Malaysians?", "Not yet. Malaysians apply online for a Russian e-visa valid for a 16-day stay. Arcadia does not process visas but provides the hotel confirmation your application needs."),
 ("Is it easy to find halal food in Kazakhstan?", "Very easy. Kazakhstan and Uzbekistan are Muslim-majority countries, and mainstream restaurants serve halal food by default."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Best things to do in Kazakhstan",L['kz_things']),("Best things to do in Uzbekistan",L['uz_things']),("Cost of a Kazakhstan trip",L['kz_cost']),("Cost of an Uzbekistan trip",L['uz_cost'])])}
{note()}
{cta("Plan your trip from Malaysia", "Private tours, family holidays and group trips with halal meals and English-speaking guides. Prices on request for any group size.", "Hello Arcadia, we are travelling from Malaysia and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Malaysia")}
</article>''')

# ---------------- SOUTH KOREA ----------------
pages['kr'] = dict(
 slug='south-korea', parent='hub',
 title='Visa-Free Travel for South Korean Citizens: Kazakhstan, Uzbekistan, Russia, Poland and China Without a Visa 2026',
 yoast_title='Kazakhstan & Uzbekistan for Koreans: Visa-Free 2026',
 yoast_desc='Korean passport holders enter Kazakhstan, Uzbekistan, Russia, Poland and China visa-free. Nonstop flights from Seoul, Koryo-saram heritage and itineraries.',
 focuskw='Kazakhstan visa-free for Koreans',
 body=f'''<article class="arcadia-market-kr-2026" lang="en" dir="ltr">
  <p>Holders of a <strong>South Korean passport</strong> can visit all five of Arcadia's destinations without a visa: <strong>30 days in Kazakhstan</strong>, <strong>30 days in Uzbekistan</strong>, <strong>30 days in China</strong> under the unilateral exemption extended to the end of 2026, <strong>90 days in Poland</strong> and <strong>60 days in Russia</strong>. Nonstop flights link Seoul with Almaty, Astana, Shymkent and Tashkent in around seven hours, and Central Asia has a special connection with Korea: the Koryo-saram communities of Almaty and Tashkent, each more than 100,000 strong, mean Korean restaurants, Korean churches and Korean-speaking locals are part of city life. Arcadia, a destination management company in Almaty, runs private tours, family holidays and corporate trips with English-speaking guides, and can arrange Korean-speaking guides on request.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for any of the five destinations. Flight time from Seoul to Almaty or Tashkent is about seven hours and the time difference is three hours. Best months: April to June and September to October; December to March for skiing on Shymbulak.</aside>
{cta("Get a proposal for your group from Korea", "Send your dates, number of travellers and the cities you have in mind. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from South Korea and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Korea", top=True)}
  <h2>Where Koreans travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Mutual visa-free agreement since 2014: up to 30 days per visit and 60 days in total in any 180-day period."),
 ("Uzbekistan","Yes, 30 days","Visa-free for stays of up to 30 days for tourism and business."),
 ("China","Yes, 30 days","Unilateral visa-free policy for Korean citizens, currently valid until 31 December 2026, for tourism, business, family visits, exchange and transit."),
 ("Poland (Schengen)","Yes, 90 days","90 days in any 180-day period. ETIAS online authorisation expected from late 2026."),
 ("Russia","Yes, 60 days","Mutual visa-free agreement: up to 60 days per visit and 90 days in any 180-day period."),
])}
  <h2>Flights from Korea</h2>
{ul([
 '<strong>Seoul to Almaty, Astana and Shymkent:</strong> nonstop flights several times a week, rising to around 20 weekly flights between Korea and Kazakhstan in summer; about seven hours.',
 '<strong>Seoul to Tashkent:</strong> nonstop flights by Uzbekistan Airways and Korean carriers, about seven and a half hours.',
 '<strong>Seoul to Warsaw:</strong> nonstop with LOT Polish Airlines, about eleven hours.',
 '<strong>China:</strong> dozens of daily flights from Incheon, Gimpo and Busan to Beijing, Shanghai and Guangzhou.',
 '<strong>Russia:</strong> no nonstop service at present; connections via Almaty, Tashkent or Istanbul to Moscow and Saint Petersburg.',
])}
  <h2>Korean heritage in Central Asia</h2>
  <p>Almaty and Tashkent are home to the largest Koryo-saram communities in the world. Visitors from Korea can see the Korean Theatre in Almaty, Korean markets with kimchi and morkovcha, and the memorials to the 1937 deportation. Many of our guests combine a heritage visit with the mountains: the Shymbulak ski resort and Medeu ice rink are 30 minutes from the city centre, and Charyn Canyon and the Kolsai Lakes make a two-day excursion.</p>
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Almaty highlights, 4 nights:</strong> city, Medeu and Shymbulak, Big Almaty Lake and Charyn Canyon, as in <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Astana and Burabay, 3 nights:</strong> the capital in two days plus the pine forests and lakes of <a href="{L["burabay"]}">Burabay</a>; see <a href="{L["astana2"]}">Astana in 2 days</a>.',
 f'<strong>Silk Road, 7 nights:</strong> Tashkent, Samarkand, Bukhara and Khiva by high-speed train; start with <a href="{L["tashkent2"]}">Tashkent in two days</a>.',
 f'<strong>Russia classic, 6 nights:</strong> <a href="{L["moscow3"]}">Moscow in 3 days</a> and <a href="{L["spb3"]}">Saint Petersburg in 3 days</a> by high-speed Sapsan train.',
 f'<strong>Poland, 5 nights:</strong> <a href="{L["warsaw3"]}">Warsaw</a>, Kraków and Zakopane in the Tatra mountains.',
 f'<strong>Ski week, 5 nights:</strong> Shymbulak with instructors, snowmobiles and hot springs, December to March; see <a href="{L["shymbulak"]}">Shymbulak and Medeu</a>.',
])}
  {hotels_par}
  <h2>Practical notes for Korean travellers</h2>
{ul([
 '<strong>Payment:</strong> Visa and Mastercard work in cities; Korean app payments do not. Carry some US dollars to exchange.',
 '<strong>Language:</strong> Russian and Kazakh or Uzbek; English in hotels and with our guides; Korean-speaking guides available on request in Almaty and Tashkent.',
 '<strong>Food:</strong> grilled meat, plov, noodles and bread; Korean restaurants in both Almaty and Tashkent.',
 '<strong>Weather:</strong> continental climate with hot summers and cold winters; spring and autumn are the most comfortable.',
 '<strong>Registration:</strong> hotels register foreign guests automatically in Kazakhstan, Uzbekistan and Russia.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>, <a href="{L["mice_uz"]}">Uzbekistan</a>, <a href="{L["mice_pl"]}">Poland</a> and <a href="{L["mice_cn"]}">China</a>')}
{faq([
 ("Do South Koreans need a visa for Kazakhstan?", "No. Korean citizens enter visa-free for up to 30 days per visit and 60 days in total within any 180-day period."),
 ("Is Uzbekistan visa-free for Koreans?", "Yes, for stays of up to 30 days."),
 ("Can Koreans visit China without a visa in 2026?", "Yes. China's unilateral visa-free policy for Korean citizens covers stays of up to 30 days and is currently valid until 31 December 2026."),
 ("Is Russia visa-free for Korean passport holders?", "Yes. The mutual agreement allows up to 60 days per visit and 90 days within any 180-day period."),
 ("Can you provide a Korean-speaking guide?", "Yes, on request in Almaty and Tashkent, subject to availability. Our standard guides speak English and Russian."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Tourism in Russia",L['ru']),("Tourism in Poland",L['pl']),("Best things to do in Russia",L['ru_things']),("Top attractions in Poland",L['pl_things'])])}
{note()}
{cta("Plan your trip from Korea", "Private tours, family holidays and corporate groups with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from South Korea and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Korea")}
</article>''')

# ---------------- SINGAPORE ----------------
pages['sg'] = dict(
 slug='singapore', parent='hub',
 title='Visa-Free Trips for Singaporeans: Kazakhstan, Uzbekistan, China and Poland Without a Visa 2026',
 yoast_title='Kazakhstan & Uzbekistan for Singaporeans: Visa-Free',
 yoast_desc='Singapore passport holders enter Kazakhstan, Uzbekistan, China and Poland visa-free. Flights via KL or Seoul, short breaks, halal options and hotels.',
 focuskw='Kazakhstan visa-free for Singaporeans',
 body=f'''<article class="arcadia-market-sg-2026" lang="en" dir="ltr">
  <p>The <strong>Singapore passport</strong> is one of the strongest in the world, and that includes Central Asia: <strong>30 days visa-free in Kazakhstan</strong>, <strong>30 days in Uzbekistan</strong>, <strong>30 days in China</strong> under the mutual exemption in force since February 2024, and <strong>90 days in Poland</strong> and the Schengen area. Only Russia still asks Singaporeans for an e-visa. For a traveller used to Bali, Bangkok and Tokyo, Almaty and Samarkand offer something different: snow-capped mountains next to a leafy city, Silk Road architecture, and prices well below Europe or Japan. Arcadia, a destination management company based in Almaty, plans and runs the trip from the airport to the airport.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan, Uzbekistan, China or Poland. One-stop flights via Kuala Lumpur or Seoul reach Almaty and Tashkent in ten to twelve hours door to door. Halal and vegetarian meals are easy to arrange. Best months: April to June and September to October; December to March for snow.</aside>
{cta("Get a proposal for your trip from Singapore", "Send your dates, number of travellers and interests. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from Singapore and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Singapore", top=True)}
  <h2>Where Singaporeans travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business, maximum 90 days in any 180-day period."),
 ("Uzbekistan","Yes, 30 days","Visa-free since 2018 for stays of up to 30 days."),
 ("China","Yes, 30 days","Mutual 30-day visa exemption between Singapore and China for ordinary passports, in force since 9 February 2024."),
 ("Poland (Schengen)","Yes, 90 days","90 days in any 180-day period. ETIAS online authorisation expected from late 2026."),
 ("Russia","No, e-visa","Singaporeans apply online for a 16-day e-visa. We supply the hotel confirmation but do not apply on your behalf."),
])}
  <h2>Flights from Singapore</h2>
{ul([
 '<strong>To Almaty:</strong> no nonstop service at present; one stop via Kuala Lumpur (AirAsia X), Seoul, Istanbul, Dubai, Doha or Delhi; ten to twelve hours in total.',
 '<strong>To Tashkent:</strong> one stop via Kuala Lumpur (AirAsia X nonstop from KL three times a week), Istanbul, Dubai or Seoul.',
 '<strong>To China:</strong> many daily nonstop flights to Guangzhou, Shanghai and Beijing; Guangzhou is under four hours.',
 '<strong>To Poland:</strong> one stop via Doha, Dubai, Istanbul or Frankfurt to Warsaw and Kraków.',
 '<strong>Between destinations:</strong> Almaty to Tashkent under two hours; Almaty to Urumqi, Beijing or Guangzhou nonstop.',
])}
  <h2>Why Central Asia from Singapore?</h2>
{ul([
 '<strong>Contrast:</strong> mountains at 3,000 metres, canyons and alpine lakes an hour from the city, and snow in winter.',
 '<strong>Value:</strong> four- and five-star hotels, private drivers and guides at a fraction of Japanese or European prices; see <a href="'+L['kz_cost']+'">what a Kazakhstan trip costs</a>.',
 '<strong>Food for everyone:</strong> halal by default in Kazakhstan and Uzbekistan; vegetarian options are easy to arrange with notice.',
 '<strong>Short breaks work:</strong> a four-night Almaty break or a five-night Uzbekistan loop fits a long weekend plus two days of leave.',
])}
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Almaty mountain break, 4 nights:</strong> Medeu and Shymbulak, Big Almaty Lake, Charyn Canyon and Kolsai Lakes; based on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Silk Road express, 5 to 6 nights:</strong> Tashkent, Samarkand and Bukhara by high-speed train; see <a href="{L["tashkent2"]}">Tashkent in two days</a> and <a href="{L["bukhara"]}">Bukhara</a>.',
 f'<strong>Kazakhstan and Uzbekistan, 10 nights:</strong> our <a href="{L["kzuz10"]}">combined itinerary</a> flying into Almaty and out of Tashkent.',
 f'<strong>China city break, 4 to 5 nights:</strong> <a href="{L["shanghai3"]}">Shanghai in 3 days</a> with a Hangzhou day trip, or Guangzhou during the Canton Fair.',
 f'<strong>Poland, 5 nights:</strong> <a href="{L["warsaw3"]}">Warsaw in 3 days</a> plus Kraków and the Wieliczka salt mine.',
])}
  {hotels_par}
  <h2>Practical notes for Singaporean travellers</h2>
{ul([
 '<strong>Time zone:</strong> Almaty and Tashkent are three hours behind Singapore.',
 '<strong>Money:</strong> cards accepted in cities; bring US dollars to exchange for markets and small towns.',
 '<strong>Language:</strong> English with our guides and in hotels; Russian and the local language elsewhere.',
 '<strong>Weather:</strong> dry and continental; pack layers, sunscreen and comfortable shoes. Winter in Almaty needs a proper coat.',
 '<strong>Connectivity:</strong> local SIM cards are cheap and available at the airport; we help on arrival.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>, <a href="{L["mice_uz"]}">Uzbekistan</a> and <a href="{L["mice_cn"]}">China</a>')}
{faq([
 ("Do Singaporeans need a visa for Kazakhstan?", "No. Singapore citizens enter visa-free for up to 30 days per visit, within 90 days in any 180-day period."),
 ("Is Uzbekistan visa-free for Singaporeans?", "Yes, for up to 30 days."),
 ("Is China visa-free for Singaporeans?", "Yes. The mutual visa exemption allows stays of up to 30 days per visit for tourism, business, family visits and transit."),
 ("What about Russia?", "Russia requires an e-visa for Singaporeans, applied for online and valid for a 16-day stay. Arcadia does not process visas but provides the hotel confirmation needed."),
 ("Is Kazakhstan safe for solo and family travellers?", "Yes. Almaty and Astana are calm, modern cities. Our tours use private vehicles and licensed guides throughout."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Tourism in China",L['cn']),("Best things to do in Kazakhstan",L['kz_things']),("Best time to visit Uzbekistan",L['uz_time'])])}
{note()}
{cta("Plan your trip from Singapore", "Private tours, family holidays and group trips with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from Singapore and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Singapore")}
</article>''')

# ---------------- AUSTRALIA / NZ ----------------
pages['au'] = dict(
 slug='australia-new-zealand', parent='hub',
 title='Visa-Free Travel for Australians and New Zealanders: Kazakhstan, Uzbekistan, China and Poland Without a Visa 2026',
 yoast_title='Kazakhstan & Uzbekistan for Australians: Visa-Free 2026',
 yoast_desc='Australian and New Zealand passports enter Kazakhstan, Uzbekistan, China and Poland visa-free in 2026. Silk Road and mountain itineraries and hotels.',
 focuskw='Kazakhstan visa-free for Australians',
 body=f'''<article class="arcadia-market-au-2026" lang="en" dir="ltr">
  <p>Travellers from <strong>Australia and New Zealand</strong> can explore Central Asia, China and Poland without a visa: <strong>30 days in Kazakhstan</strong>, <strong>30 days in Uzbekistan</strong>, <strong>30 days in China</strong> under the unilateral exemption extended to the end of 2026, and <strong>90 days in Poland</strong> and the Schengen area. Only Russia still requires a consular visa. For a long-haul traveller the region rewards time: two to three weeks that combine the Tian Shan mountains above Almaty, the Silk Road cities of Samarkand, Bukhara and Khiva, and a few days in Shanghai or Beijing on the way home. Arcadia, a destination management company based in Almaty, plans and runs the whole journey with private transport and licensed English-speaking guides.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan, Uzbekistan, China or Poland. Fly via Singapore, Kuala Lumpur, Dubai, Doha or Seoul; around 16 to 20 hours door to door. Best months: April to June and September to October. Winter brings skiing in Almaty.</aside>
{cta("Get a proposal for your trip from Australia or New Zealand", "Send your dates, number of travellers and interests. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from Australia/New Zealand and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Australia", top=True)}
  <h2>Where Australians and New Zealanders travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period."),
 ("Uzbekistan","Yes, 30 days","Both Australia and New Zealand are on Uzbekistan's visa-free list for stays of up to 30 days."),
 ("China","Yes, 30 days","Unilateral visa-free policy for Australian and New Zealand citizens, currently valid until 31 December 2026, for tourism, business, family visits, exchange and transit."),
 ("Poland (Schengen)","Yes, 90 days","90 days in any 180-day period. ETIAS online authorisation expected from late 2026."),
 ("Russia","No, visa required","Consular visa required; Australia and New Zealand are not on Russia's e-visa list. We supply the hotel confirmation and programme letter but do not apply on your behalf."),
])}
  <h2>Getting there</h2>
{ul([
 '<strong>To Almaty:</strong> one stop via Kuala Lumpur (AirAsia X nonstop to Almaty), Singapore, Dubai, Doha, Seoul or Istanbul; typically 16 to 20 hours including the connection.',
 '<strong>To Tashkent:</strong> one stop via Kuala Lumpur (AirAsia X three times a week), Dubai, Doha, Istanbul or Seoul.',
 '<strong>To China:</strong> nonstop from Sydney, Melbourne, Brisbane, Perth and Auckland to Shanghai, Guangzhou and Beijing; Guangzhou is a convenient gateway on to Almaty.',
 '<strong>Open-jaw works best:</strong> fly into Almaty and out of Tashkent (or vice versa) to avoid backtracking; the two cities are under two hours apart by air.',
])}
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Kazakhstan and Uzbekistan Silk Road, 14 nights:</strong> Almaty and its mountains, Charyn Canyon and Kolsai Lakes, then Tashkent, Samarkand, Bukhara and Khiva by train; built on our <a href="{L["kzuz10"]}">10-day combined itinerary</a> with extra nights in the mountains.',
 f'<strong>Mountains and steppe, 8 nights:</strong> Almaty, Shymbulak and Medeu, Big Almaty Lake, Charyn, Kolsai and Kaindy lakes, Altyn-Emel singing dunes; see <a href="{L["kz_things"]}">best things to do in Kazakhstan</a>.',
 f'<strong>Central Asia plus China, 18 to 21 nights:</strong> the Silk Road loop above, then Urumqi or a flight to <a href="{L["shanghai3"]}">Shanghai</a> and Beijing before flying home.',
 f'<strong>Uzbekistan in depth, 9 nights:</strong> Tashkent, the Fergana Valley crafts towns, Samarkand, Shahrisabz, <a href="{L["bukhara"]}">Bukhara</a> and Khiva.',
 f'<strong>Poland and the Tatras, 7 nights:</strong> <a href="{L["warsaw3"]}">Warsaw</a>, Kraków, Auschwitz memorial, Wieliczka and Zakopane.',
])}
  {hotels_par}
  <h2>Practical notes</h2>
{ul([
 '<strong>Seasons:</strong> Central Asian summers are hot (35°C in Samarkand) and winters cold; April to June and September to October are ideal. Autumn in Almaty brings golden poplars and apple harvests.',
 '<strong>Health:</strong> no special vaccinations required; travel insurance with medical cover is strongly recommended and required for Schengen.',
 '<strong>Money:</strong> cards work in cities; carry US dollars for exchange. Tipping is appreciated but not expected.',
 '<strong>Language:</strong> Russian, Kazakh and Uzbek; English with our guides and in hotels.',
 '<strong>Food:</strong> grilled meats, plov, dumplings, fresh bread and fruit; vegetarian and gluten-free requests are handled with notice.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>, <a href="{L["mice_uz"]}">Uzbekistan</a> and <a href="{L["mice_cn"]}">China</a>')}
{faq([
 ("Do Australians need a visa for Kazakhstan?", "No. Australian citizens enter visa-free for up to 30 days per visit, within 90 days in any 180-day period. The same applies to New Zealand citizens."),
 ("Is Uzbekistan visa-free for Australians and New Zealanders?", "Yes, both for stays of up to 30 days."),
 ("Can Australians and New Zealanders visit China without a visa in 2026?", "Yes. China's unilateral visa-free policy allows stays of up to 30 days and is currently valid until 31 December 2026."),
 ("What about Russia?", "Russia requires a consular visa for Australian and New Zealand passports. Arcadia does not process visas but can supply supporting documents for your own application."),
 ("How many days do I need for the Silk Road?", "A comfortable loop of Tashkent, Samarkand, Bukhara and Khiva takes seven to nine nights; add five to seven for Kazakhstan's mountains."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Tourism in China",L['cn']),("Best things to do in Uzbekistan",L['uz_things']),("Best time to visit Uzbekistan",L['uz_time']),("Cost of a Kazakhstan trip",L['kz_cost'])])}
{note()}
{cta("Plan your trip from Australia or New Zealand", "Private tours, small groups and corporate trips with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from Australia/New Zealand and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Australia")}
</article>''')

# ---------------- UK ----------------
pages['uk'] = dict(
 slug='united-kingdom', parent='hub',
 title='Visa-Free Travel for UK Citizens: Kazakhstan, Uzbekistan and Poland Without a Visa, Plus China Transit 2026',
 yoast_title='Kazakhstan & Uzbekistan for UK Travellers: Visa-Free',
 yoast_desc='British passport holders enter Kazakhstan and Uzbekistan visa-free for 30 days, with direct London flights to Almaty and Tashkent. Itineraries and hotels.',
 focuskw='Kazakhstan visa-free for UK citizens',
 body=f'''<article class="arcadia-market-uk-2026" lang="en" dir="ltr">
  <p>A <strong>British passport</strong> gives <strong>30 days visa-free in Kazakhstan</strong>, <strong>30 days in Uzbekistan</strong> and <strong>90 days in Poland</strong> and the Schengen area, and China allows a <strong>240-hour visa-free transit</strong> for travellers continuing to a third country. Direct flights from London reach Almaty and Tashkent in about seven and a half hours, which puts the Tian Shan mountains and the Silk Road cities closer than many Asian destinations. Arcadia, a destination management company based in Almaty, plans and runs private tours, family holidays, walking and photography trips and corporate programmes with licensed English-speaking guides.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan, Uzbekistan or Poland. Russia requires a consular visa. Direct London flights to Almaty (Air Astana) and Tashkent (Uzbekistan Airways). Best months: April to June and September to October; December to March for skiing above Almaty.</aside>
{cta("Get a proposal for your trip from the UK", "Send your dates, number of travellers and interests. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from the UK and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20the%20UK", top=True)}
  <h2>Where UK citizens travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period."),
 ("Uzbekistan","Yes, 30 days","Visa-free since 2019 for stays of up to 30 days."),
 ("Poland (Schengen)","Yes, 90 days","90 days in any 180-day period across the Schengen area. ETIAS online authorisation expected from late 2026."),
 ("China","Transit only, 240 hours","UK citizens can enter visa-free for up to 240 hours when transiting to a third country (for example Almaty to Shanghai to London). A full tourist visit requires a visa."),
 ("Russia","No, visa required","Consular visa required; the UK is not on Russia's e-visa list. We supply hotel confirmation and programme letters but do not apply on your behalf."),
])}
  <h2>Flights from the UK</h2>
{ul([
 '<strong>London to Almaty:</strong> Air Astana nonstop from Heathrow, about seven and a half hours; one-stop options via Istanbul, Dubai, Doha and Frankfurt from regional airports.',
 '<strong>London to Tashkent:</strong> Uzbekistan Airways nonstop, about seven hours; one-stop via Istanbul or Dubai.',
 '<strong>To Astana:</strong> one stop via Frankfurt, Istanbul or Almaty.',
 '<strong>To Warsaw and Kraków:</strong> nonstop from most UK airports with LOT, British Airways, Wizz Air and Ryanair, two and a half hours.',
 '<strong>Between destinations:</strong> Almaty to Tashkent under two hours by air or overnight by train; Tashkent to Samarkand two hours by high-speed train.',
])}
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Almaty and the mountains, 5 nights:</strong> city and bazaars, Medeu and Shymbulak, Big Almaty Lake, Charyn Canyon and the Kolsai and Kaindy lakes; built on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Silk Road classic, 8 nights:</strong> Tashkent, Samarkand, Bukhara and Khiva by train, with Registan Square, the Ark fortress and the walled old town of Khiva; see <a href="{L["uz_things"]}">best things to do in Uzbekistan</a>.',
 f'<strong>Kazakhstan and Uzbekistan, 12 to 14 nights:</strong> fly into Almaty and out of Tashkent, as in our <a href="{L["kzuz10"]}">combined itinerary</a>, with extra nights in the mountains and Khiva.',
 f'<strong>Astana and Burabay, 4 nights:</strong> the futuristic capital plus the lakes and granite cliffs of <a href="{L["burabay"]}">Burabay National Park</a>; see <a href="{L["astana2"]}">Astana in 2 days</a>.',
 f'<strong>Ski and snow, 5 nights:</strong> Shymbulak with instructors and rental gear, Medeu ice rink, hot springs and a winter visit to Kolsai; see <a href="{L["shymbulak"]}">Shymbulak and Medeu</a>.',
 f'<strong>Poland, 5 to 6 nights:</strong> <a href="{L["warsaw3"]}">Warsaw in 3 days</a> plus Kraków, Wieliczka and Zakopane.',
])}
  {hotels_par}
  <h2>Practical notes for British travellers</h2>
{ul([
 '<strong>Time zone:</strong> Almaty and Tashkent are four to five hours ahead of the UK depending on the season.',
 '<strong>Money:</strong> cards work in cities and hotels; bring US dollars or euros to exchange for markets and villages. ATMs are common in Almaty, Astana and Tashkent.',
 '<strong>Language:</strong> Russian, Kazakh and Uzbek; English in hotels and with our guides.',
 '<strong>Health and safety:</strong> no mandatory vaccinations; tap water is best avoided outside hotels; cities are calm and well policed. Take out travel insurance with medical cover.',
 '<strong>Driving:</strong> all our programmes use private vehicles with professional drivers; distances in Kazakhstan are long and roads vary.',
 '<strong>Dress:</strong> casual is fine; cover shoulders and knees at mosques and mausoleums in Uzbekistan.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>, <a href="{L["mice_uz"]}">Uzbekistan</a> and <a href="{L["mice_pl"]}">Poland</a>')}
{faq([
 ("Do British citizens need a visa for Kazakhstan?", "No. UK passport holders enter visa-free for up to 30 days per visit, within 90 days in any 180-day period."),
 ("Is Uzbekistan visa-free for UK citizens?", "Yes, for stays of up to 30 days."),
 ("Can UK citizens visit China without a visa?", "Only in transit: up to 240 hours when travelling on to a third country, which works well for a stopover in Shanghai, Beijing or Guangzhou between Central Asia and the UK. A dedicated China holiday still needs a visa."),
 ("What about Russia?", "Russia requires a consular visa for British passports and the UK is not on the e-visa list. Arcadia does not process visas; check the latest FCDO advice before planning."),
 ("Is Kazakhstan expensive?", "No. Four-star hotels, private drivers and guided excursions cost well below Western European prices; see our guide to the cost of a Kazakhstan trip."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Tourism in Poland",L['pl']),("Best things to do in Kazakhstan",L['kz_things']),("Cost of a Kazakhstan trip",L['kz_cost']),("Cost of an Uzbekistan trip",L['uz_cost'])])}
{note()}
{cta("Plan your trip from the UK", "Private tours, family holidays, walking and photography trips and corporate groups. Hotels, transport and guides under one contract; prices on request.", "Hello Arcadia, we are travelling from the UK and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20the%20UK")}
</article>''')


# ---------------- JAPAN ----------------
pages['jp'] = dict(
 slug='japan', parent='hub',
 title='Visa-Free Travel for Japanese Citizens: Kazakhstan, Uzbekistan, China and Poland Without a Visa 2026',
 yoast_title='Kazakhstan & Uzbekistan for Japanese: Visa-Free 2026',
 yoast_desc='Japanese passport holders enter Kazakhstan, Uzbekistan, China and Poland visa-free in 2026. Flights, Silk Road and mountain itineraries and hotels by Arcadia.',
 focuskw='Kazakhstan visa-free for Japanese',
 body=f"""<article class="arcadia-market-jp-2026" lang="en" dir="ltr">
  <p>Holders of a <strong>Japanese passport</strong> can visit most of Arcadia's destinations without a visa: <strong>30 days in Kazakhstan</strong>, <strong>30 days in Uzbekistan</strong>, <strong>30 days in China</strong> under the unilateral exemption restored in November 2024 and extended to the end of 2026, and <strong>90 days in Poland</strong> and the Schengen area. Only Russia asks Japanese citizens for an e-visa. Central Asia has long attracted travellers from Japan drawn to the Silk Road: the Registan in Samarkand, the mud-brick lanes of Bukhara and Khiva, and the Tian Shan mountains above Almaty. Arcadia, a destination management company based in Almaty, plans and runs private tours, small groups and corporate trips with licensed English-speaking guides, and can arrange Japanese-speaking guides in Uzbekistan on request.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan, Uzbekistan, China or Poland. Nonstop Tokyo to Tashkent flights with Uzbekistan Airways; Almaty via Seoul, Beijing or Istanbul. Best months: April to June and September to October; December to March for skiing above Almaty.</aside>
{cta("Get a proposal for your trip from Japan", "Send your dates, number of travellers and interests. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from Japan and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Japan", top=True)}
  <h2>Where Japanese citizens travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period."),
 ("Uzbekistan","Yes, 30 days","Visa-free for stays of up to 30 days."),
 ("China","Yes, 30 days","Unilateral visa-free policy for Japanese citizens, currently valid until 31 December 2026, for tourism, business, family visits, exchange and transit."),
 ("Poland (Schengen)","Yes, 90 days","90 days in any 180-day period. ETIAS online authorisation expected from late 2026."),
 ("Russia","No, e-visa","Japanese citizens apply online for a 16-day e-visa. We supply the hotel confirmation but do not apply on your behalf."),
])}
  <h2>Flights from Japan</h2>
{ul([
 '<strong>Tokyo to Tashkent:</strong> Uzbekistan Airways nonstop from Narita, about nine hours; also via Seoul or Istanbul.',
 '<strong>Tokyo or Osaka to Almaty and Astana:</strong> one stop via Seoul (nonstop Korea to Kazakhstan flights), Beijing, Istanbul or Dubai; eleven to thirteen hours in total.',
 '<strong>To China:</strong> many daily nonstop flights from Tokyo, Osaka, Nagoya and Fukuoka to Beijing, Shanghai and Guangzhou.',
 '<strong>To Poland:</strong> LOT Polish Airlines nonstop from Tokyo Narita to Warsaw.',
 '<strong>Between destinations:</strong> Almaty to Tashkent under two hours; Tashkent to Samarkand two hours by high-speed train.',
])}
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Silk Road classic, 7 to 8 nights:</strong> Tashkent, Samarkand, Bukhara and Khiva by train, with Registan Square, Shah-i-Zinda, the Ark fortress and Itchan Kala; see <a href="{L["uz_things"]}">best things to do in Uzbekistan</a>.',
 f'<strong>Almaty mountains, 4 to 5 nights:</strong> Medeu and Shymbulak, Big Almaty Lake, Charyn Canyon and the Kolsai Lakes; based on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Kazakhstan and Uzbekistan, 10 to 12 nights:</strong> our <a href="{L["kzuz10"]}">combined itinerary</a> flying into Almaty and out of Tashkent.',
 f'<strong>Astana and Burabay, 3 nights:</strong> <a href="{L["astana2"]}">Astana in 2 days</a> plus the lakes of <a href="{L["burabay"]}">Burabay</a>.',
 f'<strong>Poland, 5 nights:</strong> <a href="{L["warsaw3"]}">Warsaw in 3 days</a> plus Kraków and Zakopane.',
])}
  {hotels_par}
  <h2>Practical notes for Japanese travellers</h2>
{ul([
 '<strong>Time zone:</strong> Almaty and Tashkent are four hours behind Japan.',
 '<strong>Money:</strong> cards work in cities; carry US dollars to exchange. Cash is useful at bazaars.',
 '<strong>Language:</strong> Russian, Kazakh and Uzbek; English with our guides and in hotels; Japanese-speaking guides available in Samarkand and Bukhara on request.',
 '<strong>Food:</strong> plov, grilled meat, noodles, dumplings and fresh bread; mild spices. Vegetarian meals on request.',
 '<strong>Weather:</strong> dry continental climate; hot summers, cold winters. Spring and autumn are the most comfortable seasons.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>, <a href="{L["mice_uz"]}">Uzbekistan</a> and <a href="{L["mice_cn"]}">China</a>')}
{faq([
 ("Do Japanese citizens need a visa for Kazakhstan?", "No. Japanese passport holders enter visa-free for up to 30 days per visit, within 90 days in any 180-day period."),
 ("Is Uzbekistan visa-free for Japanese?", "Yes, for stays of up to 30 days."),
 ("Can Japanese visit China without a visa in 2026?", "Yes. China's unilateral visa-free policy for Japanese citizens allows stays of up to 30 days and is currently valid until 31 December 2026."),
 ("What about Russia?", "Russia requires an e-visa for Japanese citizens, applied for online and valid for a 16-day stay. Arcadia does not process visas."),
 ("Is Uzbekistan suitable for older travellers?", "Yes. High-speed trains, short transfers and comfortable hotels inside the old towns make it a relaxed trip; we adapt the walking pace to the group."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Tourism in China",L['cn']),("Best time to visit Uzbekistan",L['uz_time']),("Bukhara travel guide",L['bukhara'])])}
{note()}
{cta("Plan your trip from Japan", "Private tours, small groups and corporate trips with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from Japan and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Japan")}
</article>""")

# ---------------- INDONESIA ----------------
pages['id'] = dict(
 slug='indonesia', parent='hub',
 title='Visa-Free Holidays for Indonesian Travellers: Kazakhstan and Uzbekistan Without a Visa 2026',
 yoast_title='Kazakhstan & Uzbekistan for Indonesians: Visa-Free',
 yoast_desc='Indonesian passport holders enter Kazakhstan and Uzbekistan visa-free for 30 days. Halal food, Islamic heritage, flights via KL and itineraries by Arcadia.',
 focuskw='Kazakhstan visa-free for Indonesians',
 body=f"""<article class="arcadia-market-id-2026" lang="en" dir="ltr">
  <p>An <strong>Indonesian passport</strong> opens the two Muslim-majority countries at the heart of the Silk Road without a visa: <strong>30 days in Kazakhstan</strong> and <strong>30 days in Uzbekistan</strong>. For Indonesian families and pilgrimage-minded travellers, Uzbekistan is a special destination: the mausoleum of Imam al-Bukhari near Samarkand, the Uthman Quran in Tashkent and the madrasas of Bukhara, all with halal food as standard. Kazakhstan adds snow-capped mountains and alpine lakes 30 minutes from Almaty. With AirAsia X flying nonstop from Kuala Lumpur to Almaty and Tashkent, the journey from Jakarta is a single connection. Arcadia, a destination management company based in Almaty, plans and runs the trip with halal meals, prayer stops and English-speaking guides.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan or Uzbekistan. China allows Indonesians a 240-hour visa-free transit only; Poland and Russia require a visa, so we build Indonesian programmes around Central Asia. Best months: April to June and September to October; December to March for snow.</aside>
{cta("Get a proposal for your group from Indonesia", "Send your dates, number of travellers and the cities you have in mind. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from Indonesia and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Indonesia", top=True)}
  <h2>Where Indonesians travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period."),
 ("Uzbekistan","Yes, 30 days","Visa-free for stays of up to 30 days."),
 ("China","Transit only, 240 hours","Visa-free only when transiting to a third country within 240 hours; a dedicated China holiday requires a visa."),
 ("Poland (Schengen)","No, visa required","Schengen visa required. We supply hotel confirmation and programme letters but do not apply on your behalf."),
 ("Russia","No, visa required","Indonesia is not on Russia's e-visa list; a consular visa is required."),
])}
  <h2>Flights from Indonesia</h2>
{ul([
 '<strong>Jakarta to Almaty or Tashkent:</strong> one stop via Kuala Lumpur, where AirAsia X flies nonstop to both cities (Tashkent three times a week), or via Istanbul, Dubai or Doha; about eleven to thirteen hours in total.',
 '<strong>Almaty to Tashkent:</strong> under two hours by air or overnight by sleeper train.',
 '<strong>Tashkent to Samarkand and Bukhara:</strong> high-speed Afrosiyob train, two and four hours.',
])}
  <h2>Halal food, prayer and Islamic heritage</h2>
  <p>Kazakhstan and Uzbekistan are Muslim-majority countries: restaurants serve halal food by default, mosques are in every town and Friday prayer is part of the programme. Our Uzbekistan itineraries include the <a href="{L['uz_islam']}">Islamic heritage sites</a>: Imam al-Bukhari's mausoleum, the Hazrati Imam complex with the Uthman Quran, the Bahauddin Naqshband shrine near Bukhara and the Registan madrasas. In Almaty, the Central Mosque and halal restaurants serving beshbarmak, plov and shashlik are a short walk from our partner hotels.</p>
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Uzbekistan heritage, 7 nights:</strong> Tashkent, Samarkand, Bukhara and Khiva with the Islamic heritage sites, bazaars and craft workshops; start with <a href="{L["tashkent2"]}">Tashkent in two days</a> and <a href="{L["bukhara"]}">Bukhara</a>.',
 f'<strong>Almaty mountains and lakes, 4 to 5 nights:</strong> Medeu and Shymbulak, Big Almaty Lake, Charyn Canyon and the Kolsai Lakes; based on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Kazakhstan and Uzbekistan, 10 nights:</strong> our <a href="{L["kzuz10"]}">combined family itinerary</a> flying into Almaty and out of Tashkent.',
 f'<strong>Winter snow break, 4 nights:</strong> sledging and skiing on Shymbulak with instructors, the Medeu ice rink and hot springs, December to March; see <a href="{L["shymbulak"]}">Shymbulak and Medeu</a>.',
])}
  {hotels_par}
  <h2>Practical notes for Indonesian travellers</h2>
{ul([
 '<strong>Time zone:</strong> Almaty and Tashkent are one to two hours behind Jakarta depending on the season.',
 '<strong>Money:</strong> cards work in cities; carry US dollars to exchange. Prices are lower than in Japan or Europe; see <a href="'+L['uz_cost']+'">what an Uzbekistan trip costs</a>.',
 '<strong>Language:</strong> Russian, Kazakh and Uzbek; English with our guides and in hotels. Many Uzbek words are familiar from Arabic and Persian.',
 '<strong>Weather:</strong> dry continental climate; summers hot, winters cold. Pack layers, not tropical clothing.',
 '<strong>Group size:</strong> no minimum. Families, mosque and community groups and corporate teams are all welcome.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a> and <a href="{L["mice_uz"]}">Uzbekistan</a>')}
{faq([
 ("Do Indonesians need a visa for Kazakhstan?", "No. Indonesian passport holders enter visa-free for up to 30 days per visit, within 90 days in any 180-day period."),
 ("Is Uzbekistan visa-free for Indonesians?", "Yes, for stays of up to 30 days."),
 ("Can Indonesians visit China without a visa?", "Only in transit for up to 240 hours when travelling on to a third country. A full China holiday requires a visa, which we do not process."),
 ("Is all food halal?", "In Kazakhstan and Uzbekistan mainstream restaurants serve halal food by default, and we confirm halal certification for every restaurant on the programme."),
 ("Can you organise a group from a mosque or community?", "Yes. We organise groups of any size with prayer stops, Islamic heritage visits and a dedicated coordinator."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in Uzbekistan",L['uz']),("Islamic heritage in Uzbekistan",L['uz_islam']),("Best things to do in Uzbekistan",L['uz_things']),("Cost of a Kazakhstan trip",L['kz_cost'])])}
{note()}
{cta("Plan your trip from Indonesia", "Family holidays, community groups and corporate trips with halal meals, prayer stops and English-speaking guides. Prices on request.", "Hello Arcadia, we are travelling from Indonesia and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Indonesia")}
</article>""")


# ---------------- THAILAND ----------------
pages['th'] = dict(
 slug='thailand', parent='hub',
 title='Visa-Free Travel for Thai Citizens: Kazakhstan, China and Russia Without a Visa 2026',
 yoast_title='Kazakhstan for Thai Travellers: Visa-Free 2026',
 yoast_desc='Thai passport holders enter Kazakhstan, China and Russia visa-free for 30 days. Nonstop Bangkok and Phuket flights to Almaty, snow and mountain trips.',
 focuskw='Kazakhstan visa-free for Thai',
 body=f"""<article class="arcadia-market-th-2026" lang="en" dir="ltr">
  <p>A <strong>Thai passport</strong> enters three of Arcadia's destinations without a visa: <strong>30 days in Kazakhstan</strong>, <strong>30 days in China</strong> under the permanent mutual exemption in force since March 2024, and <strong>30 days in Russia</strong>. Kazakhstan is the natural first choice: Air Astana flies nonstop from both Bangkok and Phuket to Almaty, Thai AirAsia X adds more Bangkok departures, and the flight takes about seven hours. For travellers from a tropical climate, Almaty offers what Thailand cannot: snow from December to March, ski slopes 30 minutes from the city, alpine lakes and canyons in summer. Arcadia, a destination management company based in Almaty, plans and runs private tours, group holidays and corporate trips with English-speaking guides.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan, China or Russia. Uzbekistan and Poland require a visa, so Thai programmes are built around Kazakhstan, with China or Russia as a second country. Best months for snow: December to March; for lakes and mountains: May to October.</aside>
{cta("Get a proposal for your group from Thailand", "Send your dates, number of travellers and the type of trip. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from Thailand and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Thailand", top=True)}
  <h2>Where Thai citizens travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period."),
 ("China","Yes, 30 days","Permanent mutual visa exemption between Thailand and China since 1 March 2024, up to 30 days per visit and 90 days in 180."),
 ("Russia","Yes, 30 days","Mutual visa-free agreement for tourism, up to 30 days per visit."),
 ("Uzbekistan","No, visa required","Thai citizens apply for an Uzbekistan e-visa online. We supply hotel confirmation but do not apply on your behalf."),
 ("Poland (Schengen)","No, visa required","Schengen visa required."),
])}
  <h2>Flights from Thailand</h2>
{ul([
 '<strong>Bangkok to Almaty:</strong> Air Astana nonstop about six times a week and Thai AirAsia X three times a week; around seven hours.',
 '<strong>Phuket to Almaty:</strong> Air Astana nonstop daily in season.',
 '<strong>Bangkok to Astana:</strong> Air Astana plans a twice-weekly nonstop from December 2026; otherwise via Almaty (two hours).',
 '<strong>China and Russia:</strong> many daily flights from Bangkok to Guangzhou, Shanghai and Beijing; nonstop Bangkok and Phuket to Moscow with Aeroflot and others.',
])}
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Snow week in Almaty, 5 nights:</strong> skiing and sledging on Shymbulak with instructors and rental gear, the Medeu ice rink, hot springs and a snowy drive to the Kolsai Lakes; see <a href="{L["shymbulak"]}">Shymbulak and Medeu</a>.',
 f'<strong>Almaty mountains and lakes, 4 nights (summer):</strong> Big Almaty Lake, Charyn Canyon, Kolsai and Kaindy lakes; based on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Almaty and Astana, 6 nights:</strong> the mountain city plus the futuristic capital and <a href="{L["burabay"]}">Burabay</a>; see <a href="{L["astana2"]}">Astana in 2 days</a>.',
 f'<strong>Kazakhstan and China, 8 to 9 nights:</strong> Almaty, then nonstop to Urumqi or Guangzhou and <a href="{L["shanghai3"]}">Shanghai in 3 days</a>.',
 f'<strong>Kazakhstan and Russia, 9 nights:</strong> Almaty followed by <a href="{L["moscow3"]}">Moscow in 3 days</a> and <a href="{L["spb3"]}">Saint Petersburg</a>.',
])}
  {hotels_par}
  <h2>Practical notes for Thai travellers</h2>
{ul([
 '<strong>Time zone:</strong> Almaty is two hours behind Bangkok.',
 '<strong>Winter clothing:</strong> temperatures in Almaty drop to -10°C in January; we advise on gear and arrange rentals for ski days.',
 '<strong>Money:</strong> cards work in cities; carry US dollars to exchange.',
 '<strong>Food:</strong> grilled meat, plov, noodles and dumplings; halal by default; Thai, Korean and Chinese restaurants in Almaty.',
 '<strong>Language:</strong> Russian and Kazakh; English with our guides and in hotels.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a> and <a href="{L["mice_cn"]}">China</a>')}
{faq([
 ("Do Thai citizens need a visa for Kazakhstan?", "No. Thai passport holders enter visa-free for up to 30 days per visit, within 90 days in any 180-day period."),
 ("Is China visa-free for Thais?", "Yes. The permanent mutual exemption allows up to 30 days per visit and 90 days in any 180-day period."),
 ("Is Russia visa-free for Thai citizens?", "Yes, for tourism stays of up to 30 days."),
 ("Can I ski in Almaty without experience?", "Yes. Shymbulak has beginner slopes, English-speaking instructors and full rental equipment; non-skiers enjoy the cable car, sledging and the Medeu ice rink."),
 ("What about Uzbekistan?", "Thai citizens need an e-visa for Uzbekistan, which we do not process; most Thai groups combine Kazakhstan with China or Russia instead."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Tourism in China",L['cn']),("Tourism in Russia",L['ru']),("Best things to do in Kazakhstan",L['kz_things']),("Cost of a Kazakhstan trip",L['kz_cost'])])}
{note()}
{cta("Plan your trip from Thailand", "Snow weeks, mountain holidays, group trips and corporate programmes with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from Thailand and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20Thailand")}
</article>""")

# ---------------- PHILIPPINES ----------------
pages['ph'] = dict(
 slug='philippines', parent='hub',
 title='Visa-Free Travel for Filipino Citizens: Kazakhstan Without a Visa 2026',
 yoast_title='Kazakhstan for Filipino Travellers: Visa-Free 2026',
 yoast_desc='Filipino passport holders enter Kazakhstan visa-free for 30 days. Flights via Seoul, Bangkok or Dubai, snow and mountain itineraries and hotels by Arcadia.',
 focuskw='Kazakhstan visa-free for Filipinos',
 body=f"""<article class="arcadia-market-ph-2026" lang="en" dir="ltr">
  <p>Filipino travellers rarely get a visa-free destination with snow, mountains and a modern city in one trip. <strong>Kazakhstan</strong> is one: holders of a <strong>Philippine passport</strong> enter visa-free for <strong>30 days</strong>, no appointment, no fee and no show money beyond a return ticket and hotel booking. Almaty sits at the foot of the Tian Shan range, with a ski resort 30 minutes from the centre, alpine lakes and canyons for summer, and English-speaking guides from Arcadia, a destination management company based in the city. Flights from Manila connect once, via Seoul, Bangkok, Hong Kong, Dubai or Doha.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan. Uzbekistan, China, Poland and Russia require a visa for Filipinos, so we build Philippine programmes entirely in Kazakhstan: Almaty, Astana and the national parks. Best months: December to March for snow, May to October for lakes and mountains.</aside>
{cta("Get a proposal for your group from the Philippines", "Send your dates, number of travellers and the type of trip. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from the Philippines and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20the%20Philippines", top=True)}
  <h2>Where Filipinos travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 30 days","Visa-free for tourism and business; maximum 90 days in any 180-day period. Hotels register you automatically."),
 ("Uzbekistan","No, visa required","E-visa online; we supply hotel confirmation but do not apply on your behalf."),
 ("China","No, visa required","Consular visa required for a tourist visit."),
 ("Poland (Schengen)","No, visa required","Schengen visa required."),
 ("Russia","No, visa required","E-visa online for Filipino citizens; we do not process it."),
])}
  <h2>Flights from the Philippines</h2>
{ul([
 '<strong>Manila to Almaty:</strong> no nonstop service; one stop via Seoul (nonstop Korea to Almaty flights), Bangkok (Air Astana nonstop to Almaty), Hong Kong, Dubai or Doha; around 13 to 16 hours in total.',
 '<strong>Manila to Astana:</strong> via Seoul, Istanbul or Almaty.',
 '<strong>Within Kazakhstan:</strong> Almaty to Astana is a two-hour flight; the mountain parks are two to four hours by road from Almaty.',
])}
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Snow week, 5 nights:</strong> first skiing and sledging on Shymbulak with instructors and rental gear, the Medeu ice rink and hot springs; see <a href="{L["shymbulak"]}">Shymbulak and Medeu</a>.',
 f'<strong>Almaty mountains and lakes, 4 to 5 nights (summer):</strong> Big Almaty Lake, Charyn Canyon, Kolsai and Kaindy lakes, the Green Bazaar and Kok-Tobe; based on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Almaty and Astana, 6 to 7 nights:</strong> add the capital and the pine forests of <a href="{L["burabay"]}">Burabay</a>; see <a href="{L["astana2"]}">Astana in 2 days</a>.',
 f'<strong>Company outing or incentive, 4 nights:</strong> meetings in the hotel, team building in the mountains and a gala dinner; see <a href="{L["teambuild"]}">team-building activities in Kazakhstan</a>.',
])}
  {hotels_par}
  <h2>Practical notes for Filipino travellers</h2>
{ul([
 '<strong>Immigration on departure from Manila:</strong> carry your return ticket, hotel confirmation and our programme letter; we send all three with the booking.',
 '<strong>Time zone:</strong> Almaty is three hours behind Manila.',
 '<strong>Money:</strong> cards work in cities; carry US dollars to exchange.',
 '<strong>Food:</strong> grilled meat, rice dishes, noodles, bread and dumplings; Filipino groups usually enjoy plov and shashlik. Catholic churches exist in Almaty and Astana.',
 '<strong>Language:</strong> Russian and Kazakh; English with our guides and in hotels.',
 '<strong>Winter clothing:</strong> January temperatures reach -10°C; we advise on gear and arrange rentals.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>')}
{faq([
 ("Do Filipinos need a visa for Kazakhstan?", "No. Philippine passport holders enter visa-free for up to 30 days per visit, within 90 days in any 180-day period."),
 ("Is Kazakhstan safe for Filipino travellers?", "Yes. Almaty and Astana are calm, modern cities with low street crime. All our programmes use private vehicles and licensed guides."),
 ("Can we see snow in Almaty?", "Yes, reliably from December to March on Shymbulak and often in the city itself."),
 ("Can we add another country?", "Uzbekistan, China and Russia need a visa for Filipinos, which we do not process. Kazakhstan alone fills a week comfortably."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Best things to do in Kazakhstan",L['kz_things']),("Cost of a Kazakhstan trip",L['kz_cost']),("Best hotels in Almaty",L['hotels_almaty'])])}
{note()}
{cta("Plan your trip from the Philippines", "Snow weeks, mountain holidays, barkada and family trips and company outings with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from the Philippines and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20the%20Philippines")}
</article>""")

# ---------------- INDIA ----------------
pages['in'] = dict(
 slug='india', parent='hub',
 title='Visa-Free Travel for Indian Citizens: Kazakhstan Without a Visa for 14 Days 2026',
 yoast_title='Kazakhstan for Indian Travellers: Visa-Free 14 Days',
 yoast_desc='Indian passport holders enter Kazakhstan visa-free for 14 days. Nonstop Delhi and Mumbai flights to Almaty, vegetarian and Jain meals, itineraries and hotels.',
 focuskw='Kazakhstan visa-free for Indians',
 body=f"""<article class="arcadia-market-in-2026" lang="en" dir="ltr">
  <p>Kazakhstan has become one of the fastest-growing destinations for travellers from India, and the reason is simple: holders of an <strong>Indian passport</strong> enter <strong>visa-free for 14 days</strong>, nonstop flights from Delhi and Mumbai reach Almaty in about four hours, and the city sits at the foot of snow-capped mountains with a ski resort 30 minutes from the centre. Arcadia, a destination management company based in Almaty, runs private tours, family holidays, honeymoon trips and corporate offsites for Indian groups, with vegetarian and Jain meals arranged in advance and English-speaking guides throughout.</p>
  <aside style="margin:20px 0;padding:18px;background:#f5f9fd;border-left:4px solid #0b6bcb;border-radius:12px"><strong>In short:</strong> no visa for Kazakhstan for stays up to 14 days (42 days in any 180-day period). Uzbekistan, China, Poland and Russia require a visa for Indians, so we build Indian programmes in Kazakhstan: Almaty, Astana and the national parks. Best months: March to May and September to November; December to February for snow.</aside>
{cta("Get a proposal for your group from India", "Send your dates, number of travellers and the type of trip. We reply within 48 hours with a day-by-day programme and quote.", "Hello Arcadia, we are travelling from India and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20India", top=True)}
  <h2>Where Indian citizens travel without a visa</h2>
{table([
 ("Kazakhstan","Yes, 14 days","Visa-free for tourism and business, up to 14 days per visit and 42 days in any 180-day period. Hotels register you automatically."),
 ("Uzbekistan","No, e-visa","E-visa online; we supply hotel confirmation but do not apply on your behalf."),
 ("China","No, visa required","Consular visa required for a tourist visit."),
 ("Poland (Schengen)","No, visa required","Schengen visa required."),
 ("Russia","No, e-visa","E-visa online for Indian citizens; we do not process it."),
])}
  <h2>Flights from India</h2>
{ul([
 '<strong>Delhi to Almaty:</strong> Air Astana nonstop, about four hours; IndiGo has also operated the route (check current schedules).',
 '<strong>Mumbai to Almaty:</strong> IndiGo nonstop (launched September 2025), about five hours.',
 '<strong>To Astana:</strong> via Almaty (two hours) or one stop via Dubai, Abu Dhabi or Istanbul.',
 '<strong>Within Kazakhstan:</strong> the mountain parks are two to four hours by road from Almaty with our private vehicles.',
])}
  <h2>Food for Indian groups</h2>
  <p>Almaty has several Indian restaurants, and our partner hotels prepare vegetarian, Jain and no-onion-no-garlic meals with advance notice. Kazakh and Uzbek cuisine also offers vegetarian options: plov without meat, samsa with pumpkin, salads, breads and dairy. We confirm every meal on the itinerary before arrival.</p>
  <h2>Suggested itineraries</h2>
{ul([
 f'<strong>Almaty highlights, 4 nights:</strong> Medeu and Shymbulak by cable car, Big Almaty Lake, Kok-Tobe, the Green Bazaar and a Charyn Canyon day; based on <a href="{L["almaty3"]}">Almaty in 3 days</a>.',
 f'<strong>Lakes and canyons, 5 to 6 nights:</strong> Charyn Canyon, Kolsai and Kaindy lakes with a night in the mountains, plus Turgen waterfalls and Altyn-Emel; see <a href="{L["kz_things"]}">best things to do in Kazakhstan</a>.',
 f'<strong>Snow break, 4 nights:</strong> first skiing and sledging on Shymbulak with instructors and rental gear, the Medeu ice rink and hot springs; see <a href="{L["shymbulak"]}">Shymbulak and Medeu</a>.',
 f'<strong>Almaty and Astana, 6 to 7 nights:</strong> add the capital and <a href="{L["burabay"]}">Burabay</a>; see <a href="{L["astana2"]}">Astana in 2 days</a>.',
 f'<strong>Corporate offsite, 3 to 4 nights:</strong> meetings in a city hotel, team building in the mountains and a gala dinner; see <a href="{L["mice_kz"]}">corporate trips in Kazakhstan</a> and <a href="{L["teambuild"]}">team-building activities</a>.',
])}
  {hotels_par}
  <h2>Practical notes for Indian travellers</h2>
{ul([
 '<strong>Stay limit:</strong> 14 days per visit; a 15-night trip would need a visa, so we plan Indian itineraries at up to 13 nights.',
 '<strong>Time zone:</strong> Almaty is 30 minutes behind India.',
 '<strong>Money:</strong> cards work in cities; carry US dollars to exchange. Prices are lower than Europe or Dubai; see <a href="'+L['kz_cost']+'">what a Kazakhstan trip costs</a>.',
 '<strong>Language:</strong> Russian and Kazakh; English with our guides and in hotels. Hindi-speaking guides are available on request in Almaty.',
 '<strong>Weather:</strong> dry continental climate; summers warm, winters cold. Pack layers.',
])}
  {mice_par(f'<a href="{L["mice_kz"]}">Kazakhstan</a>')}
{faq([
 ("Do Indians need a visa for Kazakhstan?", "No, for stays of up to 14 days per visit and 42 days in total within any 180-day period. Longer stays require a visa, which we do not process."),
 ("Is Kazakhstan good for a honeymoon?", "Yes. Mountain hotels above Almaty, private cars, lake excursions and snow in winter make it a popular honeymoon destination from India."),
 ("Can you arrange vegetarian and Jain food?", "Yes, with advance notice at every hotel and restaurant on the programme, plus Indian restaurants in Almaty."),
 ("What about Uzbekistan?", "Indian citizens need an e-visa for Uzbekistan, which we do not process. Kazakhstan alone fills up to 13 nights comfortably."),
 ("Is there a Hindi-speaking guide?", "On request in Almaty, subject to availability; our standard guides speak English and Russian."),
])}
{readalso([("Visa-free travel hub",L['hub']),("Tourism in Kazakhstan",L['kz']),("Best things to do in Kazakhstan",L['kz_things']),("Cost of a Kazakhstan trip",L['kz_cost']),("Best hotels in Almaty",L['hotels_almaty']),("Corporate trips in Kazakhstan",L['mice_kz'])])}
{note()}
{cta("Plan your trip from India", "Family holidays, honeymoons, group tours and corporate offsites with hotels, transport and guides under one contract. Prices on request.", "Hello Arcadia, we are travelling from India and would like a proposal.{NL}Destination: {NL}Dates: {NL}Travellers: ", "Trip%20proposal%20request%20from%20India")}
</article>""")

for k,p in pages.items():
    assert len(p['yoast_title'])<=60, (k,len(p['yoast_title']))
    assert len(p['yoast_desc'])<=160, (k,len(p['yoast_desc']))
    open(os.path.join(OUT,f'{k}.html'),'w').write(p['body'])
    p2={kk:v for kk,v in p.items() if kk!='body'}; p2['words']=len(p['body'].split())
    print(k,p2['words'],p2['slug'])
json.dump({k:{kk:v for kk,v in p.items() if kk!='body'} for k,p in pages.items()}, open(os.path.join(OUT,'meta.json'),'w'), indent=1)
