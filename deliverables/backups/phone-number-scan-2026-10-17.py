import re, json, html, time, urllib.request, urllib.parse as p, concurrent.futures as cf, collections

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126'}
A = 'https://arcadia-tour.com/'


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60)
    return r.status, r.read().decode('utf-8', 'replace')


# every published post and page (including noindex ones), via the public REST API
urls = []
for t in ('posts', 'pages'):
    pg = 1
    while True:
        try:
            st, b = get(f'{A}wp-json/wp/v2/{t}?per_page=100&page={pg}&_fields=link&cb={int(time.time())}')
        except Exception:
            break
        a = json.loads(b)
        if not a:
            break
        urls += [x['link'] for x in a]
        if len(a) < 100:
            break
        pg += 1
urls = list(dict.fromkeys(urls))
MAIN = '77064007561'
PHONE = re.compile(r'(?<![\d/])(?:\+|00)?\s?(?:7|380|48|86|966|971|974|965|973|968|90)[\s\-().]*\d(?:[\s\-().]*\d){7,11}(?!\d)')


def digits(s):
    return re.sub(r'\D', '', s)


def one(u):
    try:
        st, h = get(u)
    except Exception as e:
        return u, 'ERR', {}
    found = collections.defaultdict(set)
    for m in re.finditer(r'wa\.me/(\d{9,15})', h):
        found[m.group(1)].add('wa.me')
    for m in re.finditer(r'api\.whatsapp\.com/send/?\?phone=(\d{9,15})', h):
        found[m.group(1)].add('api.whatsapp')
    for m in re.finditer(r'href="tel:([^"]+)"', h):
        found[digits(m.group(1))].add('tel')
    for m in re.finditer(r'"telephone"\s*:\s*"([^"]+)"', h):
        found[digits(m.group(1))].add('schema')
    for m in re.finditer(r'wa\.me\\?/(\d{9,15})|phone["\']?\s*[:=]\s*["\']?\+?(\d{9,15})', h):
        n = m.group(1) or m.group(2)
        found[n].add('script')
    txt = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', h, flags=re.S))
    for m in PHONE.finditer(txt):
        d = digits(m.group(0))
        if d.startswith('00'):
            d = d[2:]
        if len(d) >= 10:
            found[d].add('text')
    return u, st, {k: sorted(v) for k, v in found.items()}


with cf.ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, urls))
tot = collections.Counter()
pages = collections.defaultdict(set)
for u, st, f in res:
    for n, kinds in f.items():
        tot[n] += 1
        pages[n].add(p.unquote(u)[24:70])
print('pages checked', len(urls), 'errors', sum(1 for r in res if r[1] == 'ERR'))
print('numbers found (pages):')
for n, c in tot.most_common():
    print(' ', n, c, 'pages', '| kinds:', sorted({k for u, st, f in res for k in f.get(n, [])}), '| e.g.', list(pages[n])[:4])
nowa = [p.unquote(u)[24:70] for u, st, f in res if st == 200 and MAIN not in f]
print('pages without the main number at all:', len(nowa), nowa[:20])
