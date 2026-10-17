"""Fixed-topic ('固定关注') collector.
1) Load topic config: latest GitHub issue titled 'config: fixed-topics' authored by the repo owner (via GH_TOKEN),
   falling back to config/fixed_topics.json.
2) For each topic search recent news: Google News RSS (zh / ko / en), Naver News search (Korean), and
   known local outlets (e.g. 당진시대 RSS for 당진).
3) Resolve links, fetch article text (trafilatura), keep only items whose fetched text actually mentions a keyword.
Writes data/fixed-pack-DATE.json (private, gitignored) and data/fixed-config-DATE.json.
Usage: python fixed_topics.py 2026-10-17 [--hours 72]"""
import json,os,re,sys,html,argparse,datetime as dt,concurrent.futures as cf,urllib.parse as up
import requests,feedparser,trafilatura
from dateutil import parser as dp
from googlenewsdecoder import gnewsdecoder
ap=argparse.ArgumentParser();ap.add_argument('date');ap.add_argument('--hours',type=int,default=72);ap.add_argument('--per-topic',type=int,default=8);a=ap.parse_args()
KST=dt.timezone(dt.timedelta(hours=9));REPO='188083235/daily-brief';OWNER='188083235'
end=min(dt.datetime.now(KST),dt.datetime.fromisoformat(a.date).replace(hour=23,minute=59,tzinfo=KST));start=end-dt.timedelta(hours=a.hours)
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
def norm_topics(raw):
    out=[]
    for t in raw:
        if isinstance(t,str):
            parts=[p.strip() for p in re.split(r'[/／|,，]',t) if p.strip()]; t={'name':t.strip(),'keywords':parts}
        if not isinstance(t,dict) or not t.get('name'): continue
        kw=[k for k in (t.get('keywords') or re.split(r'[/／|,，]',t['name'])) if k.strip()]
        out.append(dict(name=t['name'].strip()[:40],keywords=[k.strip()[:40] for k in kw][:6],context_zh=t.get('context_zh',[])))
    return out[:12]
def load_config():
    tok=os.environ.get('GH_TOKEN')
    if tok:
        try:
            r=requests.get(f'https://api.github.com/repos/{REPO}/issues',params=dict(state='all',per_page=50,sort='created',direction='desc'),
                           headers={'Authorization':f'Bearer {tok}','Accept':'application/vnd.github+json'},timeout=15)
            for iss in r.json():
                ttl=iss.get('title','').lower()
                if 'pull_request' in iss or not (ttl.startswith('config: fixed-topics') or ttl.startswith('update:')): continue
                if iss.get('user',{}).get('login')!=OWNER: continue        # only the owner may change config
                m=re.search(r'\{.*\}',iss.get('body') or '',re.S)
                if not m: continue
                try: cfg=json.loads(m.group(0))
                except Exception: continue
                if ttl.startswith('update:'):          # combined issue: only counts if it carries fixed_topics
                    if not isinstance(cfg.get('fixed_topics'),dict): continue
                    cfg=cfg['fixed_topics']
                tp=norm_topics(cfg.get('topics',[]))
                if tp:
                    try:   # keep repo-side search hints (context_zh) for topics that also exist in config/fixed_topics.json
                        dflt={t['name']:t for t in norm_topics(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','config','fixed_topics.json')))['topics'])}
                        for t in tp:
                            if not t.get('context_zh') and dflt.get(t['name'],{}).get('context_zh'): t['context_zh']=dflt[t['name']]['context_zh']
                    except Exception: pass
                    return tp,f"issue #{iss['number']} ({iss['created_at']})"
        except Exception as e: print('config issue lookup failed:',e)
    cfg=json.load(open('../config/fixed_topics.json'));return norm_topics(cfg['topics']),'config/fixed_topics.json'
LOCAL={'당진':['https://www.djtimes.co.kr/rss/allArticle.xml']}   # local outlets with RSS, keyed by keyword
def gnews(q,hl,gl,ceid):
    u='https://news.google.com/rss/search?q='+up.quote(q+' when:3d')+f'&hl={hl}&gl={gl}&ceid={ceid}'
    out=[]
    try: f=feedparser.parse(requests.get(u,headers=UA,timeout=15).content)
    except Exception: return out
    for e in f.entries[:40]:
        t=html.unescape(e.get('title',''));src=''
        m=re.match(r'(.*) - ([^-]+)$',t)
        if m: t,src=m.group(1).strip(),m.group(2).strip()
        out.append(dict(title=t,link=e.link,published=e.get('published'),source=src or 'Google News',via='google-news',gnews=True))
    return out
def naver(q):
    """Naver News via the official Search API (needs NAVER_CLIENT_ID / NAVER_CLIENT_SECRET from developers.naver.com).
    The HTML search page answers 403 to scripts, so without keys Naver is skipped."""
    cid,sec=os.environ.get('NAVER_CLIENT_ID'),os.environ.get('NAVER_CLIENT_SECRET')
    if not (cid and sec): return []
    out=[]
    try:
        r=requests.get('https://openapi.naver.com/v1/search/news.json',params=dict(query=q,display=30,sort='date'),
                       headers={'X-Naver-Client-Id':cid,'X-Naver-Client-Secret':sec},timeout=15).json()
        for e in r.get('items',[]):
            out.append(dict(title=html.unescape(re.sub(r'<[^>]+>','',e.get('title',''))),link=e.get('originallink') or e.get('link'),
                            published=e.get('pubDate'),source='Naver 뉴스',via='naver',gnews=False))
    except Exception as e: print('naver api failed',e)
    return out
def local(url):
    out=[]
    try: f=feedparser.parse(requests.get(url,headers=UA,timeout=15).content)
    except Exception: return out
    name=f.feed.get('title','local')
    for e in f.entries: out.append(dict(title=html.unescape(e.get('title','')),link=e.link,published=e.get('published'),source=name,via='local-rss',gnews=False))
    return out
def fetch(it):
    url=it['link']
    try:
        if it['gnews']: url=gnewsdecoder(url,interval=0.3).get('decoded_url') or None
        if not url: return it
        it['link']=url
        r=requests.get(url,headers=UA,timeout=12); r.encoding=r.apparent_encoding if not r.encoding or r.encoding.lower()=='iso-8859-1' else r.encoding
        md=trafilatura.extract_metadata(r.text)
        it['article']=re.sub(r'\s+',' ',trafilatura.extract(r.text,include_comments=False) or '')[:2500]
        if md:
            it['title']=it['title'] or (md.title or '')
            if not it['published'] and md.date: it['published']=md.date
            if it['source'] in ('Naver 뉴스',) and md.sitename: it['source']=f"{md.sitename}（Naver）"
        if not it['published']:
            m=re.search(r'data-date-time="([\d\- :]+)"',r.text)
            if m: it['published']=m.group(1)+' +0900'
    except Exception as e: it['err']=str(e)[:80]
    return it
def when(s):
    try:
        d=dp.parse(s,fuzzy=True)
        return d if d.tzinfo else d.replace(tzinfo=KST)
    except Exception: return None
topics,cfg_src=load_config()
pack=[]
for tp in topics:
    cands=[]
    for k in tp['keywords']:
        qk=f'"{k}"' if ' ' in k else k          # multi-word keywords are searched as exact phrases
        if re.search(r'[\uac00-\ud7a3]',k): cands+=gnews(qk,'ko','KR','KR:ko')+naver(k)
        elif re.search(r'[\u4e00-\u9fff]',k):
            q=qk if not tp.get('context_zh') else f"{qk} ({' OR '.join(tp['context_zh'])})"
            cands+=gnews(q,'zh-CN','CN','CN:zh-Hans')+gnews(q,'zh-TW','TW','TW:zh-Hant')
        else: cands+=gnews(qk,'en-US','US','US:en')
        for u in LOCAL.get(k,[]): cands+=[c for c in local(u)]
    seen=set();pre=[]
    for c in cands:
        d=when(c['published']) if c['published'] else None
        if d and not (start<=d<=end+dt.timedelta(hours=1)): continue
        key=re.sub(r'\W','',c['title'].lower())[:40] or c['link']
        if key in seen or c['link'] in seen: continue
        seen|={key,c['link']};pre.append(c)
    # interleave sources so Naver / local outlets are not crowded out by Google News
    byvia={}
    for c in pre: byvia.setdefault(c['via'],[]).append(c)
    pre=[];i=0
    while len(pre)<60 and any(i<len(v) for v in byvia.values()):
        for v in byvia.values():
            if i<len(v): pre.append(v[i])
        i+=1
    with cf.ThreadPoolExecutor(8) as ex: got=list(ex.map(fetch,pre))
    keep=[]
    for c in got:
        d=when(c['published']) if c.get('published') else None
        if not d or not (start<=d<=end+dt.timedelta(hours=1)): continue
        txt=c.get('article','')
        if len(txt)<200: continue
        if not any(re.search(re.escape(k.lower())+(r'(?![\d.])' if k[-1].isdigit() else ''),txt.lower()) for k in tp['keywords']): continue   # fetched body must really mention the topic ('iPad mini 8' must not match 'iPad mini 8.3-inch')   # fetched body must really mention the topic
        if re.search(r'security service to protect|Cloudflare Ray ID|新浪首页 新闻 体育',txt): continue   # bot walls / nav-only pages
        if '唐津' in tp['keywords'] and '唐津' in txt and not any(x in txt for x in ['당진','韩国','忠清','Dangjin']) and not any(k in txt for k in tp['keywords'] if k!='唐津'): continue  # avoid Karatsu (Japan)
        c['published']=d.isoformat();c['topic']=tp['name'];keep.append(c)
    dd=set();fin=[]
    for c in sorted(keep,key=lambda x:x['published'],reverse=True):
        k=re.sub(r'\W','',c['title'])[:18]
        if k in dd: continue
        dd.add(k);fin.append(c)
    for i,c in enumerate(fin[:a.per_topic]): c['fid']=f"{len(pack)}";pack.append(c)
    print(tp['name'],'candidates',len(cands),'fetched',len(pre),'relevant',len(keep),'kept',min(len(fin),a.per_topic))
json.dump(dict(date=a.date,window=[start.isoformat(),end.isoformat()],config_source=cfg_src,topics=topics,items=pack),open(f'../data/fixed-pack-{a.date}.json','w'),ensure_ascii=False,indent=1)
json.dump(dict(config_source=cfg_src,topics=topics),open(f'../data/fixed-config-{a.date}.json','w'),ensure_ascii=False,indent=1)
print('config from',cfg_src,'total kept',len(pack))
