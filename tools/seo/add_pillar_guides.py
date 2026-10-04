import json,subprocess,os,sys,re,time
ADD={
 155:[("https://arcadia-tour.com/krakow-halal-restaurants-guide/","مطاعم حلال في كراكوف 2026"),("https://arcadia-tour.com/best-hotels-warsaw-krakow-families-2026/","أفضل فنادق وارسو وكراكوف للعائلات 2026")],
 3359:[("https://arcadia-tour.com/best-hotels-beijing-shanghai-families-2026/","أفضل فنادق بكين وشنغهاي للعائلات 2026")],
}
BK='deliverables/backups/pillars-newguides-before-2026-10-02e'; os.makedirs(BK,exist_ok=True)
def addbox(html,items):
    i=html.find('arcadia-new-guides'); assert i>=0
    j=html.find('</ul></div>',i); assert j>=0
    lis=''.join(f'<li><a href="{u}">{t}</a></li>' for u,t in items if u not in html)
    return html[:j]+lis+html[j:], lis!=''
for pid,items in ADD.items():
    d=json.load(open(f'pillars/el_{pid}.json'))
    json.dump(d,open(f'{BK}/{pid}.json','w'),ensure_ascii=False)
    el=json.loads(d['meta']['_elementor_data']); c=d['content']['raw']; n=0
    def walk(nodes):
        global n
        for nd in nodes:
            st=nd.get("settings") or {}
            if not isinstance(st,dict): st={}
            for key in ('editor','html'):
                v=st.get(key)
                if isinstance(v,str) and 'arcadia-new-guides' in v:
                    nv,ch=addbox(v,items); st[key]=nv; n+=ch
            walk(nd.get('elements',[]))
    walk(el)
    c2,ch=addbox(c,items)
    payload={'content':c2,'meta':{'_elementor_data':json.dumps(el,ensure_ascii=False,separators=(',',':'))}}
    json.dump(payload,open(f'pillars/payload2_{pid}.json','w'),ensure_ascii=False)
    for a in range(3):
        r=subprocess.run(['curl','-sS','-n','-m','120',f'https://arcadia-tour.com/wp-json/wp/v2/pages/{pid}','-X','POST','-H','Content-Type: application/json','--data-binary',f'@pillars/payload2_{pid}.json'],capture_output=True,text=True).stdout
        try:
            j=json.loads(r); el2=j['meta']['_elementor_data']
            print(pid,'saved; widgets changed',n,'content changed',ch,'| links in el:',all(u in el2.replace('\\/','/') for u,_ in items)); break
        except Exception: time.sleep(3)
    else: print(pid,'FAILED',r[:200])
