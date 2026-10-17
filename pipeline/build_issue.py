"""Step 4: merge editorial (Chinese title/summary/why, written from pack text) with pack metadata -> data/issue-DATE.json.
Refuses to build if any editorial item has no matching grounded source item (no fabrication)."""
import json,sys,importlib.util,datetime as dt
date=sys.argv[1]
pack={c['cid']:c for c in json.load(open(f'../data/pack-{date}.json'))}
sp=importlib.util.spec_from_file_location('ed',f'../editorial/{date}.py');ed=importlib.util.module_from_spec(sp);sp.loader.exec_module(ed)
main=[i for i in ed.ITEMS if not i.get('explore')];exp=[i for i in ed.ITEMS if i.get('explore')]
order=[];ei=0
for i,it in enumerate(main):
    order.append(it)
    if (len(order)+1)%10==0 and ei<len(exp): order.append(exp[ei]);ei+=1
order+=exp[ei:]
items=[]
for rank,it in enumerate(order,1):
    c=pack.get(it['cid']); assert c, f"cid {it['cid']} missing from pack"
    assert len(c.get('article','')+c['summary'])>=150, f"cid {it['cid']} not grounded"
    also=[]
    for m in it.get('merge',[]):
        o=pack[m]; also.append(dict(source=o['source'],title=o['title'],link=o['link']))
    for x in c.get('also',[])[:3]:
        if x['link'] and all(x['link']!=a['link'] for a in also) and 'news.google.com' not in x['link']: also.append(x)
    for n,u in it.get('x',[]): also.append(dict(source=n,title='X 上的相关讨论',link=u))
    stars=5 if rank<=10 else 4 if rank<=30 else 3 if rank<=60 else 2
    if it.get('explore'): stars=None
    items.append(dict(id=f"{date}-{rank:03d}",rank=rank,category=it['cat'],explore=bool(it.get('explore')),stars=stars,
        title_zh=it['t'],summary_zh=it['s'],why_zh=it['w'],source=c['source'],orig_title=c['title'],
        link=c['link'],published=c['published'],language=c['language'],coverage=c.get('coverage',1),also=also[:5]))
issue=dict(date=date,generated_at=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec='minutes'),count=len(items),items=items)
json.dump(issue,open(f'../data/issue-{date}.json','w'),ensure_ascii=False,indent=1)
print(len(items),'items')
