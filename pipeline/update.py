"""6-hourly incremental 'latest updates' page.
Inputs : ../data/update-news.json (collect.py --hours 8 --end now --out ...), ../data/social/latest.json (social.py)
State  : ../data/updates-state.json (private): links already shown + last run time
Output : ../updates/YYYY-MM-DD-HH.html (public) + ../updates/index.html ; ../data/updates/YYYY-MM-DD-HH.json (private copy)
Only items NEW since the previous run are shown. Titles/snippets are the sources' own text (no machine summaries)."""
import json,os,re,html,datetime as dt,collections
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));KST=dt.timezone(dt.timedelta(hours=9));NOW=dt.datetime.now(KST)
e=lambda s:html.escape(s or '',quote=True)
SP=os.path.join(ROOT,'data','updates-state.json')
st=json.load(open(SP)) if os.path.exists(SP) else dict(seen=[],last=None,runs=[])
seen=set(st['seen']);last=dt.datetime.fromisoformat(st['last']) if st.get('last') else NOW-dt.timedelta(hours=6)
since=last-dt.timedelta(minutes=30)
def t(x):
    try: return dt.datetime.fromisoformat(x)
    except Exception: return None
news=[];soc=[]
np_=os.path.join(ROOT,'data','update-news.json')
if os.path.exists(np_):
    for c in json.load(open(np_))['candidates']:
        d=t(c.get('published'))
        if c['link'] in seen or not d or d<since: continue
        news.append(dict(kind='news',title=c['title'],source=c['source'],link=c['link'],time=c['published'],text=re.sub(r'\s+',' ',c.get('summary',''))[:280],
                         category=c.get('category'),score=c.get('score',0),coverage=c.get('coverage',1),origin=c.get('origin')))
news.sort(key=lambda x:-x['score']);news=news[:40]
sp=os.path.join(ROOT,'data','social','latest.json')
if os.path.exists(sp):
    for acc in json.load(open(sp))['accounts']:
        for p in acc['posts']:
            d=t(p.get('time'))
            if not p.get('link') or p['link'] in seen or not d or d<since or d>NOW+dt.timedelta(hours=1): continue
            soc.append(dict(kind='follow',title=p.get('title') or '(无标题)',source=acc['name'],platform=acc['platform'],link=p['link'],time=p['time'],text=(p.get('text') or '')[:280],approx=p.get('time_approx',False)))
soc.sort(key=lambda x:x['time'],reverse=True);soc=soc[:80]
slot=NOW.strftime('%Y-%m-%d-%H');os.makedirs(os.path.join(ROOT,'updates'),exist_ok=True);os.makedirs(os.path.join(ROOT,'data','updates'),exist_ok=True)
json.dump(dict(slot=slot,since=since.isoformat(timespec='minutes'),news=news,follow=soc),open(os.path.join(ROOT,'data','updates',slot+'.json'),'w'),ensure_ascii=False,indent=1)
PL={'youtube':'YouTube','bilibili':'B站','rss':'RSS','site':'网站','github':'GitHub','telegram':'Telegram','x':'X'}
def card(x):
    meta=f"{e(x['source'])}"+(f" · {PL.get(x.get('platform'),x.get('platform'))}" if x['kind']=='follow' else (f" · {e(x.get('category'))}" if x.get('category') else ''))
    tm=e((x['time'] or '')[5:16].replace('T',' '))+('（约）' if x.get('approx') else '')
    return f'<div class="ui"><a class="ut" href="{e(x["link"])}" target="_blank" rel="noopener">{e(x["title"])}</a><div class="um">{meta} · {tm}</div>'+(f'<p>{e(x["text"])}</p>' if x['text'] else '')+'</div>'
grp=collections.defaultdict(list)
for x in soc: grp[x['platform']].append(x)
soc_html=''.join(f'<h3>{PL.get(k,k)}（{len(v)}）</h3>'+''.join(card(x) for x in v) for k,v in sorted(grp.items(),key=lambda kv:-len(kv[1]))) or '<p class="hint">这段时间关注的账号没有新内容。</p>'
news_html=''.join(card(x) for x in news) or '<p class="hint">没有新的新闻。</p>'
page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>最新更新 {slot}</title><link rel="stylesheet" href="../assets/app.css?v=20261018a"></head>
<body><header><h1>最新更新 · {NOW:%Y-%m-%d %H:%M}（UTC+9）</h1><div class="meta">自 {since:%m-%d %H:%M} 以来的新内容 · 关注 {len(soc)} 条 · 新闻 {len(news)} 条 · 标题和摘录均为原文</div>
<nav><a href="../index.html">今日简报</a><a href="index.html">更新列表</a><a href="#follow">我的关注</a><a href="#news">新闻</a></nav></header>
<main class="upd"><section id="follow"><h2>我的关注</h2>{soc_html}</section><section id="news"><h2>新闻（按重要程度）</h2>{news_html}</section></main></body></html>'''
open(os.path.join(ROOT,'updates',slot+'.html'),'w').write(page)
import sys;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import panel;panel.retrofit(os.path.join(ROOT,'updates',slot+'.html'))   # feedback/fixed-topics panel + app.js
st['runs']=([dict(slot=slot,follow=len(soc),news=len(news))]+[r for r in st.get('runs',[]) if r['slot']!=slot])[:200]
rows=''.join(f'<a href="{r["slot"]}.html"><b>{r["slot"][:10]} {r["slot"][11:]}:00</b> · 关注 {r["follow"]} 条 · 新闻 {r["news"]} 条</a>' for r in st['runs'])
open(os.path.join(ROOT,'updates','index.html'),'w').write(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>最新更新</title><link rel="stylesheet" href="../assets/app.css?v=20261018a"></head>
<body><header><h1>最新更新（每6小时）</h1><nav><a href="../index.html">今日简报</a></nav></header><main class="arch">{rows}</main></body></html>''')
st['seen']=list((seen|{x['link'] for x in news+soc}))[-20000:];st['last']=NOW.isoformat(timespec='minutes')
json.dump(st,open(SP,'w'),ensure_ascii=False)
print('update',slot,'follow',len(soc),'news',len(news))
