import json,subprocess,sys,time
ids=json.load(open("comments_open.json")); b=int(sys.argv[1]); batch=ids[(b-1)*10:b*10]
for i in batch:
    for attempt in range(4):
        out=subprocess.run(["curl",f"https://arcadia-tour.com/wp-json/wp/v2/posts/{i}","-sS","-n","-m","60","--retry","2","-X","POST","-H","Content-Type: application/json","-d",'{"comment_status":"closed","ping_status":"closed"}'],capture_output=True,text=True).stdout
        try:
            r=json.loads(out); print(i,r.get("comment_status")); break
        except Exception:
            time.sleep(2)
    else:
        print(i,"FAILED")
