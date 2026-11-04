import json,re,sys,html,subprocess,os,time
ids=[int(x) for x in sys.argv[1:]]
pat=re.compile(r'^\s*(?:<p>)?<strong>(.*?)</strong>\s*(?:</p>)?\s*$',re.S)
def conv(raw):
    out=[];n=0
    for line in raw.split('\n'):
        m=pat.match(line)
        if m:
            inner=m.group(1).strip()
            txt=html.unescape(re.sub('<[^>]+>','',inner)).strip()
            words=len(txt.split())
            if ('<img' not in inner and 'fr-img' not in inner and 'style=' not in inner
                and 2<=words<=15 and len(txt)<=120 and not txt.endswith(('.', '!', ':', '،', ',')) ):
                line=f'<h2>{inner}</h2>'; n+=1
        out.append(line)
    return '\n'.join(out),n
bk='deliverables/backups/h2-structure-before-2026-10-02'; os.makedirs(bk,exist_ok=True)
for pid in ids:
    p=json.load(open(f"{pid}.json")); raw=p['content']['raw']
    json.dump({'id':pid,'title':p['title']['raw'],'content':raw},open(f'{bk}/{pid}.json','w'),ensure_ascii=False)
    new,n=conv(raw)
    if n==0: print(pid,'nothing to convert'); continue
    json.dump({'content':new},open(f'payload_{pid}.json','w'),ensure_ascii=False)
    for a in range(3):
        r=subprocess.run(["curl","-sS","-n","-m","120",f"https://arcadia-tour.com/wp-json/wp/v2/posts/{pid}","-X","POST","-H","Content-Type: application/json","--data-binary",f"@payload_{pid}.json"],capture_output=True,text=True).stdout
        try:
            j=json.loads(r); print(pid,'saved, h2 converted',n,'| h2 in saved:',len(re.findall(r'<h2[\s>]',j['content']['raw']))); break
        except Exception: time.sleep(2)
    else: print(pid,'FAILED',r[:200])
