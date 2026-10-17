"""Collect the user's own follows (RSS/OPML feeds, YouTube, Bilibili, X, Telegram, ...) -> data/social/ (private, gitignored).

  python social.py [--platforms rss,youtube,bilibili,x] [--per-account 5] [--bili-max 67]

Methods (legitimate only; no bot-protection bypass, no borrowed cookies):
  rss/site/github/telegram : the feed URL; RSSHub URLs on the user's remote instance are rewritten to the local RSSHub (127.0.0.1:1200)
  youtube   : local RSSHub /youtube/channel/<id> (YouTube's native feeds 404 from this box); fallback yt-dlp --flat-playlist (approximate dates)
  bilibili  : local RSSHub /bilibili/user/video/<uid>, paced; stops after 3 consecutive risk-control (-352) refusals
  x         : the feed URL the user already had (rss.app)
  douyin / toutiao / xiaohongshu : not collected (anonymous access blocked / needs login, or profile ids missing)
"""
import os,re,sys,json,time,html,argparse,subprocess,datetime as dt,concurrent.futures as cf
import requests,feedparser
from dateutil import parser as dp
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'data','social');os.makedirs(OUT,exist_ok=True)
KST=dt.timezone(dt.timedelta(hours=9));NOW=dt.datetime.now(KST)
LOCAL=os.environ.get('RSSHUB_LOCAL','http://127.0.0.1:1200');REMOTE_HOSTS=('rsshub.188083235.xyz',)
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141 Safari/537.36'}
ap=argparse.ArgumentParser();ap.add_argument('--platforms',default='rss,site,github,telegram,x,youtube,bilibili')
ap.add_argument('--per-account',type=int,default=5);ap.add_argument('--bili-max',type=int,default=999);ap.add_argument('--bili-gap',type=float,default=12);ap.add_argument('--yt-desc-hours',type=int,default=36);ap.add_argument('--yt-desc-max',type=int,default=30)
a=ap.parse_args();PLAT=set(a.platforms.split(','))
YTDLP=os.path.join(ROOT,'.venv','bin','yt-dlp')

def clean(s,n=700):
    s=re.sub(r'<(script|style|iframe)[^>]*>.*?</\1>','',s or '',flags=re.S|re.I);s=re.sub(r'<br\s*/?>|</p>','\n',s,flags=re.I)
    s=html.unescape(re.sub(r'<[^>]+>','',s));s=re.sub(r'[ \t\u3000]+',' ',s);s=re.sub(r'\n\s*\n+','\n',s).strip()
    return s[:n]
def iso(x):
    if not x: return None
    try:
        d=dp.parse(x) if isinstance(x,str) else dt.datetime(*x[:6],tzinfo=dt.timezone.utc)
        if d.tzinfo is None: d=d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(KST).isoformat(timespec='minutes')
    except Exception: return None
def local_route(url):
    m=re.match(r'https?://([^/]+)(/.*)',url or '')
    return m.group(2) if m and m.group(1) in REMOTE_HOSTS else None
def rsshub(route,timeout=90):
    r=requests.get(LOCAL+route,timeout=timeout);d=r.json()
    if 'error' in d: raise RuntimeError(str(d['error'].get('message') if isinstance(d['error'],dict) else d['error'])[:200])
    return [dict(title=clean(i.get('title'),200),time=iso(i.get('pubDate')),link=i.get('link'),text=clean(i.get('description'))) for i in d.get('item',[])]
def feed(url):
    r=requests.get(url,headers=UA,timeout=20);r.raise_for_status();f=feedparser.parse(r.content)
    if not f.entries and f.bozo: raise RuntimeError('not a feed')
    return [dict(title=clean(e.get('title'),200),time=iso(e.get('published') or e.get('updated') or e.get('published_parsed')),link=e.get('link'),
                 text=clean((e.get('content') or [{}])[0].get('value') or e.get('summary'))) for e in f.entries]
def ytdlp(cid):
    p=subprocess.run([YTDLP,'--flat-playlist','-j','--playlist-end','8','--extractor-args','youtubetab:approximate_date',f'https://www.youtube.com/channel/{cid}/videos'],capture_output=True,text=True,timeout=120)
    out=[]
    for l in p.stdout.splitlines():
        d=json.loads(l);ts=d.get('timestamp')
        out.append(dict(title=d.get('title'),time=dt.datetime.fromtimestamp(ts,KST).isoformat(timespec='minutes') if ts else None,link=d.get('url'),text='',time_approx=True))
    if not out: raise RuntimeError((p.stderr or 'no entries')[-200:])
    return out

def collect(c):
    pf=c.get('platform') or c['type'];base=dict(platform=pf,name=c['name'],account=c.get('url_or_handle'),category=c.get('category'),language=c.get('language'))
    try:
        if pf=='youtube':
            cid=c.get('channel_id')
            if not cid: return dict(base,status='no_channel_id',posts=[])
            try: posts=[dict(x,time_approx=True) for x in rsshub(f'/youtube/channel/{cid}')];method='rsshub-local'   # RSSHub dates come from 'N hours ago' -> approximate
            except Exception as e:
                posts=ytdlp(cid);method='yt-dlp'
        elif pf=='bilibili':
            uid=re.search(r'space\.bilibili\.com/(\d+)',c['url_or_handle']).group(1);posts=rsshub(f'/bilibili/user/video/{uid}',timeout=120);method='rsshub-local'
        else:
            url=c.get('feed_url_if_known')
            if not url: return dict(base,status='no_feed',posts=[])
            lr=local_route(url)
            if lr:
                try: posts=rsshub(lr);method='rsshub-local'
                except Exception: posts=feed(url);method='feed(remote rsshub fallback)'
            else: posts=feed(url);method='feed'
        posts=[p for p in posts if p.get('title') or p.get('text')]
        posts.sort(key=lambda p:p.get('time') or '',reverse=True)
        return dict(base,status='ok' if posts else 'empty',method=method,posts=posts[:a.per_account])
    except Exception as e:
        return dict(base,status='error',error=str(e)[:200],posts=[])

ch=json.load(open(os.path.join(ROOT,'sources','channels.json')))['channels']
user=[c for c in ch if c.get('source')!='supplement' and not c.get('duplicate_of')]
res=[]
NOT={'douyin':'needs_login','toutiao':'needs_login','xiaohongshu':'unresolved_id+needs_login'}
for c in user:
    pf=c.get('platform') or c['type']
    if pf in NOT: res.append(dict(platform=pf,name=c['name'],account=c.get('url_or_handle'),category=c.get('category'),status=NOT[pf],posts=[]))
feeds=[c for c in user if (c.get('platform') or c['type']) in PLAT-{'youtube','bilibili'} and (c.get('platform') or c['type']) not in NOT]
yts=[c for c in user if c['type']=='youtube'] if 'youtube' in PLAT else []
bili=[c for c in user if c.get('platform')=='bilibili' and not c.get('dead')] if 'bilibili' in PLAT else []
if 'bilibili' not in PLAT: res+=[dict(platform='bilibili',name=c['name'],account=c['url_or_handle'],category=c.get('category'),status='not_run',posts=[]) for c in user if c.get('platform')=='bilibili' and not c.get('dead')]
t0=time.time()
with cf.ThreadPoolExecutor(16) as ex: res+=list(ex.map(collect,feeds))
print('feeds',len(feeds),round(time.time()-t0),'s',flush=True)
with cf.ThreadPoolExecutor(3) as ex: res+=list(ex.map(collect,yts))
print('youtube',len(yts),round(time.time()-t0),'s',flush=True)
fails=0
for i,c in enumerate(bili):
    if i>=a.bili_max or fails>=6:
        res.append(dict(platform='bilibili',name=c['name'],account=c['url_or_handle'],category=c.get('category'),status='skipped_after_risk_control' if fails>=6 else 'skipped',posts=[]));continue
    r=collect(c);res.append(r)
    fails=fails+1 if r['status']=='error' else 0
    time.sleep(a.bili_gap)
print('bilibili',len(bili),round(time.time()-t0),'s',flush=True)
for c in [c for c in user if c.get('platform')=='bilibili' and c.get('dead')]: res.append(dict(platform='bilibili',name=c['name'],account=c['url_or_handle'],status='dead_account',posts=[]))
# enrich recent YouTube posts (title-only from the channel listing) with the video description via yt-dlp metadata
BOT={'hit':False}
def ytdesc(p):
    if BOT['hit']: return
    try:
        r=subprocess.run([YTDLP,'-j','--skip-download','--no-warnings',p['link']],capture_output=True,text=True,timeout=90)
        if 'confirm you' in r.stderr: BOT['hit']=True; return   # YouTube bot check: stop, do not work around it
        d=json.loads(r.stdout.splitlines()[0]);p['text']=clean(d.get('description'),900);p['title']=d.get('title') or p['title']
        if d.get('timestamp'): p['time']=dt.datetime.fromtimestamp(d['timestamp'],KST).isoformat(timespec='minutes');p.pop('time_approx',None)
    except Exception: pass
recent=[p for r in res if r['platform']=='youtube' for p in r['posts'] if p.get('time') and p['time']>=(NOW-dt.timedelta(hours=a.yt_desc_hours)).isoformat()]
recent.sort(key=lambda p:p['time'],reverse=True)
with cf.ThreadPoolExecutor(2) as ex: list(ex.map(ytdesc,recent[:a.yt_desc_max]))
if BOT['hit']: print('youtube bot check hit; stopped description lookups',flush=True)
print('youtube descriptions',min(len(recent),a.yt_desc_max),'of',len(recent),flush=True)
day=NOW.date().isoformat()
summary={}
for r in res:
    s=summary.setdefault(r['platform'],{});s[r['status']]=s.get(r['status'],0)+1
out=dict(collected_at=NOW.isoformat(timespec='minutes'),summary=summary,accounts=res)
json.dump(out,open(os.path.join(OUT,f'social-{day}-{NOW:%H}.json'),'w'),ensure_ascii=False,indent=1)
json.dump(out,open(os.path.join(OUT,'latest.json'),'w'),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False,indent=1))
print('posts',sum(len(r['posts']) for r in res))
