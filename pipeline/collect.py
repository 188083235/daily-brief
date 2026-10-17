"""Step 1: fetch all rankable feeds from sources/channels.json, keep items from the last N hours,
dedupe/cluster across sources, score, and write data/candidates-YYYY-MM-DD.json.
Usage: python collect.py 2026-10-17 [--hours 30]"""
import json,sys,re,time,html,datetime as dt,concurrent.futures as cf,argparse,collections
import feedparser,requests
from dateutil import parser as dp
ap=argparse.ArgumentParser();ap.add_argument('date');ap.add_argument('--hours',type=int,default=30);a=ap.parse_args()
KST=dt.timezone(dt.timedelta(hours=9))
end=dt.datetime.fromisoformat(a.date).replace(hour=10,tzinfo=KST)
start=end-dt.timedelta(hours=a.hours)
ch=json.load(open('../sources/channels.json'))['channels']
SKIP_CAT={'软件','影视','软件更新','影视/娱乐','游戏/电竞','生活/兴趣','热榜'}
feeds=[c for c in ch if c.get('feed_url_if_known') and c.get('feed_status')=='ok' and not c.get('duplicate_of')
       and not c.get('exclude_from_ranking') and c['type'] in ('rss','site','x') and c['category'] not in SKIP_CAT]
# source tier: wire/global majors 3, national majors 2, others 1
T3=['Reuters','AP News','Bloomberg','BBC','Guardian','NPR','Nature','Science News','纽约时报','BBC','新华社','人民日报','Yonhap','연합뉴스','Al Jazeera','Financial','CNBC','Nikkei','NHK','DW','KBS']
T2=['Ars','Verge','TechCrunch','MIT','Hacker News','Euronews','POLITICO','Japan Times','Times of Israel','AllAfrica','STAT','Carbon','Inside Climate','NASA','조선','동아','한겨레','경향','매일경제','Korea Herald','法广','联合早报','澎湃','南方周末','财联社','经济日报','界面','虎嗅','Solidot','IT 之家','cnBeta','iDaily','知乎','竹新社','hankyoreh','德国之声','共同网','求是','ESPN','WHO','arXiv','光明','中国日报','韩联社','凤凰','KBS WORLD','Trump']
def tier(n):
    if any(k in n for k in T3): return 3
    if any(k in n for k in T2): return 2
    return 1
UA={'User-Agent':'Mozilla/5.0 daily-brief/1.0 (+https://github.com/188083235/daily-brief)'}
def clean(s): 
    s=re.sub(r'<[^>]+>',' ',html.unescape(s or ''));return re.sub(r'\s+',' ',s).strip()
def fetch(c):
    try:
        r=requests.get(c['feed_url_if_known'],headers=UA,timeout=15)
        f=feedparser.parse(r.content)
    except Exception as e: return c,[],str(e)
    out=[]
    for e in f.entries:
        d=None
        for k in ('published','updated','created'):
            if e.get(k):
                try: d=dp.parse(e[k],fuzzy=True); break
                except Exception: pass
        if d and d.tzinfo is None: d=d.replace(tzinfo=dt.timezone(dt.timedelta(hours=8)))
        title=clean(e.get('title'));
        if not title: continue
        src=c['name']
        if 'news.google.com' in c['feed_url_if_known']:
            m=re.match(r'(.*) - ([^-]+)$',title)
            if m: title,src2=m.group(1).strip(),m.group(2).strip(); src=f"{src2}"
        out.append(dict(title=title,link=e.get('link'),published=d.isoformat() if d else None,
            summary=clean(e.get('summary') or e.get('description'))[:1500],source=src,channel=c['name'],
            language=c['language'],category=c['category'],tier=tier(c['name']),origin=('added' if c.get('source')=='supplement' else 'user'),gnews='news.google.com' in c['feed_url_if_known']))
    return c,out,None
with cf.ThreadPoolExecutor(20) as ex: res=list(ex.map(fetch,feeds))
items=[];stats={}
for c,out,err in res:
    keep=[i for i in out if i['published'] and start<=dt.datetime.fromisoformat(i['published'])<=end+dt.timedelta(hours=1)]
    if 'arXiv' in c['name']: keep=keep[:15]
    stats[c['name']]=dict(fetched=len(out),in_window=len(keep),error=err)
    items+=keep
# dedupe by link and normalized title, cluster by token overlap
def toks(t):
    t=t.lower()
    w=re.findall(r'[a-z0-9]{3,}',t)+[t[i:i+2] for i in range(len(t)-1) if re.match(r'[\u4e00-\u9fff\uac00-\ud7a3]{2}',t[i:i+2])]
    stop={'the','and','for','with','that','from','says','after','over','into','new','what','how','why','will','has','have','are','was','its','his','her','this'}
    return {x for x in w if x not in stop}
seen=set();uniq=[]
for i in sorted(items,key=lambda x:(-x['tier'],x['gnews'],-len(x['summary']))):
    k=(i['link'] or '').split('?')[0]; nt=re.sub(r'\W','',i['title'].lower())
    if k in seen or nt in seen: continue
    seen|={k,nt}; i['tokens']=toks(i['title']); uniq.append(i)
clusters=[]
for i in uniq:
    for cl in clusters:
        h=cl[0]
        inter=len(i['tokens']&h['tokens']); 
        if inter>=4 and inter/max(1,min(len(i['tokens']),len(h['tokens'])))>=0.5: cl.append(i); break
    else: clusters.append([i])
CATW={'国际':1.3,'时政':1.1,'综合新闻':1.1,'财经':1.2,'AI':1.25,'科技':1.1,'科学':1.1,'健康':1.0,'气候环境':1.0,'韩国':1.15,'日本':1.0,'欧洲':1.0,'中东':1.1,'非洲':0.95,'体育':0.85,'军事':0.9,'网络安全':0.9,'技术博客':0.7,'历史/文化':0.7,'趣闻':0.6,'科技/数码':0.9,'时政/新闻':1.0}
cands=[]
for cl in clusters:
    head=max(cl,key=lambda x:(x['tier'],not x['gnews'],len(x['summary'])))
    srcs=sorted({x['source'] for x in cl})
    age=(end-dt.datetime.fromisoformat(head['published'])).total_seconds()/3600
    # modest boost for the user's own feeds (bookmarks / RSS / follows); category quotas in select_items keep breadth
    user_boost=0.6 if head.get('origin')=='user' else (0.3 if any(x.get('origin')=='user' for x in cl) else 0)
    score=head['tier']*1.0+min(len(srcs),6)*0.8+max(0,1.5-age/20)+CATW.get(head['category'],0.8)+(0.3 if len(head['summary'])>200 else 0)+user_boost
    cands.append(dict({k:v for k,v in head.items() if k!='tokens'},score=round(score,2),coverage=len(srcs),user_in_cluster=any(x.get('origin')=='user' for x in cl),also=[dict(source=x['source'],title=x['title'],link=x['link']) for x in cl if x is not head][:6]))
cands.sort(key=lambda x:-x['score'])
json.dump(dict(date=a.date,window=[start.isoformat(),end.isoformat()],feed_stats=stats,candidates=cands),open(f'../data/candidates-{a.date}.json','w'),ensure_ascii=False,indent=1)
print('feeds',len(feeds),'items',len(items),'uniq',len(uniq),'clusters',len(cands))
print(collections.Counter(c['category'] for c in cands[:300]).most_common())
