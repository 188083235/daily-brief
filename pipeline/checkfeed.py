import sys,json,concurrent.futures as cf,requests,re,time
requests.packages.urllib3.disable_warnings()
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 daily-brief-feedcheck'}
from dateutil import parser as dp
import datetime as dt
def newest(body):
    best=None
    for m in re.finditer(r'<(pubDate|updated|published|dc:date)>\s*(?:<!\[CDATA\[)?([^<\]]+)',body):
        try:
            d=dp.parse(m.group(2).strip(),fuzzy=True)
            if d.tzinfo is None: d=d.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
            if d.year>2000 and (best is None or d>best): best=d
        except Exception: pass
    return best.isoformat() if best else None
def check(url):
    t=time.time()
    try:
        r=requests.get(url,headers=UA,timeout=10,verify=False,allow_redirects=True)
        body=r.text[:200000]
        isfeed=bool(re.search(r'<(rss|feed|rdf:RDF)[\s>]',body[:5000],re.I))
        items=len(re.findall(r'<(item|entry)[\s>]',body,re.I))
        last=newest(body)
        st='ok' if (r.status_code==200 and isfeed and items>0) else ('empty' if r.status_code==200 and isfeed else ('not_feed' if r.status_code==200 else f'http_{r.status_code}'))
        return dict(url=url,status=st,http=r.status_code,items=items,latest=last,secs=round(time.time()-t,1),final_url=r.url)
    except Exception as e:
        return dict(url=url,status='error',error=type(e).__name__+': '+str(e)[:120],secs=round(time.time()-t,1))
if __name__=='__main__':
    urls=json.load(open(sys.argv[1]))
    with cf.ThreadPoolExecutor(24) as ex: res=list(ex.map(check,urls))
    json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
