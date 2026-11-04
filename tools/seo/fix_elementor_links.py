import json,subprocess,sys,os
pid=int(sys.argv[1]); typ=sys.argv[2]
reps=json.loads(sys.argv[3])
d=json.loads(subprocess.run(["curl","-sS","-n","-m","90",f"https://arcadia-tour.com/wp-json/wp/v2/{typ}/{pid}?context=edit"],capture_output=True,text=True).stdout)
os.makedirs("elfix2/backup",exist_ok=True)
json.dump({"id":pid,"content":d["content"]["raw"],"_elementor_data":d["meta"]["_elementor_data"]},open(f"elfix2/backup/{pid}.json","w"),ensure_ascii=False)
el=d["meta"]["_elementor_data"]; c=d["content"]["raw"]; n=0
for old,new in reps.items():
    for o,nw in ((old,new),(old.replace('/','\\/'),new.replace('/','\\/'))):
        n+=el.count(o); el=el.replace(o,nw)
    c=c.replace(old,new)
print("replacements in elementor data:",n)
json.loads(el)  # validate
payload={"content":c,"meta":{"_elementor_data":el}}
json.dump(payload,open(f"elfix2/payload_{pid}.json","w"),ensure_ascii=False)
r=subprocess.run(["curl","-sS","-n","-m","120",f"https://arcadia-tour.com/wp-json/wp/v2/{typ}/{pid}","-X","POST","-H","Content-Type: application/json","--data-binary",f"@elfix2/payload_{pid}.json"],capture_output=True,text=True).stdout
try:
    j=json.loads(r); el2=j["meta"]["_elementor_data"]
    print("saved id",j["id"],"remaining old:",sum(el2.count(o)+el2.count(o.replace('/','\\/')) for o in reps))
except Exception as e: print("ERR",r[:300])
