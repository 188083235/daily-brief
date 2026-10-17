"""Step 4: merge editorial (Chinese title/summary/why, written from pack text) with pack metadata -> data/issue-DATE.json.
Refuses to build if any editorial item has no matching grounded source item (no fabrication)."""
import json,sys,importlib.util,datetime as dt
date=sys.argv[1]
pack={c['cid']:c for c in json.load(open(f'../data/pack-{date}.json'))}
sp=importlib.util.spec_from_file_location('ed',f'../editorial/{date}.py');ed=importlib.util.module_from_spec(sp);sp.loader.exec_module(ed)
DET=getattr(ed,'DETAIL',{})
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
    detail=it.get('detail') or DET.get(it['cid'])
    assert detail and len(detail)>=100, f"cid {it['cid']} missing detail"
    stars=5 if rank<=10 else 4 if rank<=30 else 3 if rank<=60 else 2
    if it.get('explore'): stars=None
    items.append(dict(id=f"{date}-{rank:03d}",rank=rank,category=it['cat'],explore=bool(it.get('explore')),stars=stars,
        title_zh=it['t'],summary_zh=it['s'],why_zh=it['w'],detail_zh=detail,source=c['source'],orig_title=c['title'],
        link=c['link'],published=c['published'],language=c['language'],coverage=c.get('coverage',1),also=also[:5]))
# ---- 固定关注 ----
import os
fixed=None
fp=f'../data/fixed-pack-{date}.json'
if os.path.exists(fp):
    fpk=json.load(open(fp)); FX=getattr(ed,'FIXED',{}); byfid={str(c['fid']):c for c in fpk['items']}
    topics=[]
    for tp in fpk['topics']:
        got=[c for c in fpk['items'] if c['topic']==tp['name']]; ent=FX.get(tp['name'])
        items_out=[]
        if ent:
            for x in ent['items']:
                c=byfid[str(x['fid'])]; assert c['topic']==tp['name'] and len(c.get('article',''))>=200, f"fixed fid {x['fid']} not grounded"
                also=[dict(source=byfid[str(m)]['source'],title=byfid[str(m)]['title'],link=byfid[str(m)]['link']) for m in x.get('merge',[])]
                items_out.append(dict(title_zh=x['t'],summary_zh=x['s'],source=c['source'],link=c['link'],orig_title=c['title'],published=c['published'],also=also))
        note=(ent or {}).get('note') or ('过去72小时没有找到新的相关报道。' if not got else '')
        if not got: note='过去72小时没有找到新的相关报道。'
        topics.append(dict(name=tp['name'],keywords=tp['keywords'],note=note,items=items_out,found=len(got)))
    fixed=dict(window=fpk['window'],config_source=fpk['config_source'],topics=topics)
# ---- private: how many items came from the user's own feeds (never written to the public issue) ----
try:
    ch=json.load(open('../sources/channels.json'))['channels']; org={c['name']:('added' if c.get('source')=='supplement' else 'user') for c in ch}
    import collections as _c
    cnt=_c.Counter(org.get(pack[it['cid']]['channel'],pack[it['cid']].get('origin','?')) for it in ed.ITEMS)
    json.dump(dict(date=date,main_items=dict(cnt)),open(f'../data/origin-stats-{date}.json','w'),ensure_ascii=False)
    print('origin',dict(cnt))
except FileNotFoundError: pass
import glob as _g
_v=_g.glob(f'../data/versions/issue-{date}-v*.json')
issue=dict(date=date,**(dict(store_key=f'{date}-v{len(_v)+1}',version_label=f' · 第{len(_v)+1}版') if _v else {}),fixed=fixed,generated_at=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec='minutes'),count=len(items),items=items)
json.dump(issue,open(f'../data/issue-{date}.json','w'),ensure_ascii=False,indent=1)
print(len(items),'items')
