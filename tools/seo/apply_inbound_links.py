import json,sys,re,subprocess,os
A={
 "A1":("السياحة في أستانا 2026: دليل العائلات العربية","https://arcadia-tour.com/astana-family-guide-2026/"),
 "A2":("ألماتي مع الأطفال: أفضل 10 أنشطة عائلية","https://arcadia-tour.com/almaty-with-kids-family-activities/"),
 "A3":("رحلة كازاخستان وأوزبكستان 10 أيام","https://arcadia-tour.com/kazakhstan-uzbekistan-10-days-trip/"),
 "A4":("موسكو مع الأطفال: أفضل 10 أنشطة عائلية","https://arcadia-tour.com/moscow-with-kids-family-activities/"),
 "A5":("السياحة في كازان: دليل العائلات العربية","https://arcadia-tour.com/kazan-tourism-guide/"),
 "A6":("طشقند في يومين: برنامج سياحي كامل","https://arcadia-tour.com/tashkent-2-days-itinerary/"),
 "A7":("بكين مع الأطفال: أفضل 10 أنشطة عائلية","https://arcadia-tour.com/beijing-with-kids-family-guide/"),
 "A8":("سانت بطرسبرغ مع الأطفال: أفضل 10 أنشطة عائلية","https://arcadia-tour.com/st-petersburg-with-kids-family-activities/"),
 "A9":("برنامج الصين 10 أيام للعائلات","https://arcadia-tour.com/china-family-10-days-itinerary/"),
 "B1":("أفضل وقت لزيارة كازاخستان 2026","https://arcadia-tour.com/best-time-visit-kazakhstan-2026/"),
 "B2":("أفضل وقت لزيارة أوزبكستان 2026","https://arcadia-tour.com/best-time-visit-uzbekistan-2026/"),
 "B3":("أفضل وقت لزيارة الصين 2026","https://arcadia-tour.com/best-time-visit-china-2026/"),
 "B4":("أفضل وقت لزيارة بولندا 2026","https://arcadia-tour.com/best-time-visit-poland-2026/"),
 "C1":("السياحة في كازاخستان للسعوديين 2026","https://arcadia-tour.com/kazakhstan-for-saudis-2026/"),
 "C2":("السياحة في روسيا للسعوديين 2026","https://arcadia-tour.com/russia-for-saudis-2026/"),
 "C3":("السياحة في أوزبكستان للسعوديين 2026","https://arcadia-tour.com/uzbekistan-for-saudis-2026/"),
 "C4":("السياحة في بولندا للسعوديين 2026","https://arcadia-tour.com/poland-for-saudis-2026/"),
 "D1":("مطاعم ألماتي الحلال والعربية","https://arcadia-tour.com/almaty-halal-restaurants-guide/"),
 "D2":("شيمبولاك وميديو: دليل التلفريك والتزلج","https://arcadia-tour.com/shymbulak-medeu-almaty-guide/"),
 "D3":("السياحة في سوتشي للعائلات","https://arcadia-tour.com/sochi-russia-family-guide-2026/"),
 "D4":("شهر العسل في كازاخستان","https://arcadia-tour.com/kazakhstan-honeymoon-guide-2026/"),
 "E1":("مطاعم حلال في موسكو","https://arcadia-tour.com/moscow-halal-restaurants-guide/"),
 "E2":("برنامج كازاخستان 5 أيام","https://arcadia-tour.com/kazakhstan-5-days-itinerary/"),
 "E3":("ألماتي أم أستانا؟ المقارنة الكاملة","https://arcadia-tour.com/almaty-vs-astana-comparison/"),
 "E4":("أوزبكستان مع الأطفال: أفضل 10 أنشطة","https://arcadia-tour.com/uzbekistan-with-kids-family-guide/"),
 "F1":("أفضل فنادق موسكو للعائلات 2026","https://arcadia-tour.com/best-hotels-moscow-families-2026/"),
 "F2":("أفضل فنادق أستانا 2026","https://arcadia-tour.com/best-hotels-astana-2026/"),
 "F3":("أفضل فنادق سمرقند وبخارى 2026","https://arcadia-tour.com/best-hotels-samarkand-bukhara-2026/"),
 "G1":("تركستان: مقام الخوجة أحمد يسوي وأوترار","https://arcadia-tour.com/turkistan-kazakhstan-yasawi-guide/"),
 "G2":("بوروفوي: بحيرات شمال كازاخستان","https://arcadia-tour.com/burabay-borovoe-kazakhstan-guide/"),
 "G3":("أفضل فنادق طشقند 2026","https://arcadia-tour.com/best-hotels-tashkent-2026/"),
 "G4":("أفضل فنادق سانت بطرسبرغ للعائلات 2026","https://arcadia-tour.com/best-hotels-st-petersburg-families-2026/"),
 "H1":("مطاعم حلال في كراكوف","https://arcadia-tour.com/krakow-halal-restaurants-guide/"),
 "H2":("أفضل فنادق بكين وشنغهاي للعائلات 2026","https://arcadia-tour.com/best-hotels-beijing-shanghai-families-2026/"),
 "H3":("أفضل فنادق وارسو وكراكوف للعائلات 2026","https://arcadia-tour.com/best-hotels-warsaw-krakow-families-2026/"),
 "D5":("السياحة الدينية في أوزبكستان","https://arcadia-tour.com/uzbekistan-islamic-religious-tourism-guide/"),
}
PLAN=json.load(open(sys.argv[1]))
BK="deliverables/backups/inbound-links-before-2026-10-02"; os.makedirs(BK,exist_ok=True)
CTA=re.compile(r'اطلب|احجز|تواصل|رتب|لم تحسم|احصل')
FAQ=re.compile(r'أسئلة شائعة|الأسئلة الشائعة')
def block(keys):
    links=[f'<a href="{A[k][1]}">{A[k][0]}</a>' for k in keys]
    return '<p class="arcadia-read-also"><strong>اقرأ أيضاً:</strong> '+' | '.join(links)+'</p>'
def inject(c,b):
    pos=c.rfind("<h2")
    if pos==-1: return c.rstrip()+"\n"+b+"\n"
    h2=c[pos:c.find("</h2>",pos)]
    if CTA.search(h2) or FAQ.search(h2):
        k=c.rfind("<section",0,pos)
        if k!=-1 and pos-k<700: pos=k
        return c[:pos]+b+"\n"+c[pos:]
    m=re.search(r'\s*<!-- /wp:html -->\s*$',c)
    if m: return c[:m.start()]+"\n"+b+c[m.start():]
    return c.rstrip()+"\n"+b+"\n"
for item in PLAN:
    t,i,keys=item["type"],item["id"],item["links"]
    r=subprocess.run(["curl",f"https://arcadia-tour.com/wp-json/wp/v2/{t}/{i}?context=edit&_fields=id,link,content","-sS","-n"],capture_output=True,text=True)
    d=json.loads(r.stdout); c=d["content"]["raw"]
    open(f"{BK}/{t}-{i}.html","w",encoding="utf-8").write(c)
    if 'class="arcadia-read-also"' in c:
        add=' | '+' | '.join(f'<a href="{A[k][1]}">{A[k][0]}</a>' for k in keys if A[k][1] not in c)
        if add==' | ': print(i,"SKIP already linked"); continue
        new=c.replace('</p>',add+'</p>',1) if False else re.sub(r'(class="arcadia-read-also">.*?)(</p>)',lambda m:m.group(1)+add+m.group(2),c,count=1,flags=re.S)
    else:
        new=inject(c,block(keys))
    assert new!=c
    json.dump({"content":new},open(f"inbound/{t}-{i}.payload.json","w",encoding="utf-8"),ensure_ascii=False)
    r=subprocess.run(["curl",f"https://arcadia-tour.com/wp-json/wp/v2/{t}/{i}","-sS","-n","-X","POST","-H","Content-Type: application/json","--data-binary",f"@inbound/{t}-{i}.payload.json"],capture_output=True,text=True)
    try:
        res=json.loads(r.stdout); raw=res["content"]["raw"]
        ok=all(A[k][1] in raw for k in keys)
        at=raw.find('class="arcadia-read-also"'); ctx=re.sub(r'<[^>]+>',' ',raw[at:at+400]); ctx=re.sub(r'\s+',' ',ctx)[:110]
        print(i,t,"OK" if ok else "FAIL",keys,"|",ctx)
    except Exception as e: print("ERR",i,r.stdout[:300])
