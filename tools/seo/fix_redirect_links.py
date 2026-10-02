import json,subprocess,os,sys,re,time,urllib.parse
BK='deliverables/backups/redirect-links-fix-before-2026-10-02'; os.makedirs(BK,exist_ok=True)
# (type,id): list of (old_href, new_href) exact href values (unencoded); applied to raw & percent-encoded & JSON-escaped variants
R={
 ('pages',151):[('/السياحة-في-كازاخستان/تأشيرة-كازاخستان','/السياحة-في-كازاخستان/تأشيرة-كازاخستان/'),('/السياحة-في-كازاخستان/المدن-في-كازاخستان-تعرف-على-أهم-9-مدن-سي','/السياحة-في-كازاخستان/المدن-في-كازاخستان-تعرف-على-أهم-9-مدن-سي/'),('/الدراسة-في-كازاخستان-دليلك-الشامل-لأف','/الدراسة-في-كازاخستان-دليلك-الشامل-لأف/'),('/السياحة-في-كازاخستان/السياحة-في-كازاخستان-في-الشتاء-مع-أجوا','/السياحة-في-كازاخستان/السياحة-في-كازاخستان-في-الشتاء-مع-أجوا/')],
 ('pages',153):[('/العروض-والحجوزات/رحله-سياحيه-6-أيام-5-أيام-في-سان-بطرسبرج','/offers-bookings/'),('/العروض-والحجوزات/برنامج-سياحي-في-روسيا-8-ايام-7-ليالي','/offers-bookings/'),('/العروض-والحجوزات/رحله-سياحيه-روسيا-6-أيام-موسكو-وسانت-بطرسبرغ','/offers-bookings/'),('/العروض-والحجوزات','/offers-bookings/')],
 ('pages',155):[('/السياحة-في-بولندا-1/','/السياحة-في-بولندا/'),('/العروض-والحجوزات','/offers-bookings/')],
 ('pages',157):[('/السياحة-في-أوزبكستان-1/why-travel-to-uzbekistan','/why-travel-to-uzbekistan/'),('/السياحة-في-أوزبكستان-1/uzbekistan','/السياحة-في-أوزبكستان/uzbekistan/'),('/السياحة-في-أوزبكستان-1/أهم-المدن-السياحية-في-أوزبكستان','/السياحة-في-أوزبكستان/أهم-المدن-السياحية-في-أوزبكستان/'),('/العروض-والحجوزات','/offers-bookings/')],
 ('pages',576):[('https://arcadia-tour.com/السياحة-في-روسيا/russia-info"','https://arcadia-tour.com/السياحة-في-روسيا/russia-info/"')],
 ('pages',577):[('https://www.arcadia-tour.com/السياحة-في-روسيا/المدن-في-روسيا"','https://arcadia-tour.com/السياحة-في-روسيا/المدن-في-روسيا/"')],
 ('pages',579):[('/en/tourism-in-moscow-10-places-to-visit-in-moscow/','/en/learn-about-the-10-best-tourist-places-in-moscow-russia/')],
 ('posts',2214):[('"/russia-7-days/"','"https://arcadia-tour.com/السياحة-في-روسيا/russia-7-days/"')],
 ('posts',2670):[('"/russia-7-days/"','"https://arcadia-tour.com/السياحة-في-روسيا/russia-7-days/"')],
 ('posts',3890):[('/en/why-choose-tourism-in-uzbekistan-en/','/en/why-choose-tourism-in-uzbekistan/')],
 ('posts',3889):[('/en/entering-russia-without-a-visa-to-the-gulf-countries-what-you-need-to-know/','/en/entering-russia-without-a-visa-to-the-gulf-countries-what-you-need-to-know-befor/')],
}
def variants(s):
    out={s}
    enc=urllib.parse.quote(s,safe='/:?=&"'); out.add(enc); out.add(enc.lower())
    return out
only=[int(x) for x in sys.argv[1:]]
for (t,i),reps in R.items():
    if only and i not in only: continue
    d=json.load(open(f'redfix/{t}-{i}.json')); c=d['content']['raw']; el=(d.get('meta') or {}).get('_elementor_data') or ''
    open(f'{BK}/{t}-{i}.json','w',encoding='utf-8').write(json.dumps({'content':c,'_elementor_data':el},ensure_ascii=False))
    n=0
    for old,new in reps:
        # trailing-slash-add rule: when old lacks slash and new is old+'/', only replace href="old" exactly (avoid double slash)
        if new==old+'/':
            for ov in variants(old):
                for q in ('"','\\"','\\\\"'):
                    k=c.count('href='+q+ov+q); c=c.replace('href='+q+ov+q,'href='+q+ov+'/'+q); n+=k
                    ov2=ov.replace('/','\\/'); k=el.count('href='+q+ov2+q); el=el.replace('href='+q+ov2+q,'href='+q+ov2+'\\/'+q); n+=k
            continue
        for ov in variants(old):
            nv=new if ov==old else urllib.parse.quote(new,safe='/:?=&"')
            k=c.count(ov); c=c.replace(ov,nv); n+=k
            ov2=ov.replace('/','\\/'); nv2=nv.replace('/','\\/'); k=el.count(ov2); el=el.replace(ov2,nv2); n+=k
    if el: json.loads(el)
    payload={'content':c}
    if el: payload['meta']={'_elementor_data':el}
    json.dump(payload,open(f'redfix/payload-{t}-{i}.json','w'),ensure_ascii=False)
    for a in range(3):
        r=subprocess.run(['curl','-sS','-n','-m','120',f'https://arcadia-tour.com/wp-json/wp/v2/{t}/{i}','-X','POST','-H','Content-Type: application/json','--data-binary',f'@redfix/payload-{t}-{i}.json'],capture_output=True,text=True).stdout
        try: j=json.loads(r); print(t,i,'saved, replacements:',n); break
        except Exception: time.sleep(3)
    else: print(t,i,'FAILED',r[:200])
