import json,sys
sys.path.insert(0,'.')
from supplement_sources import S
P='../sources/channels.json'
d=json.load(open(P))
res={x['name']:x for x in json.load(open('/tmp/supp_res.json'))}
d['channels']=[c for c in d['channels'] if c.get('source')!='supplement']
for n,l,cat,site,feed in S:
    r=res.get(n,{})
    d['channels'].append(dict(name=n,type='rss',url_or_handle=site,language=l,category=cat,feed_url_if_known=feed,source='supplement',
        feed_status='ok' if r.get('status')=='ok' else 'dead',feed_latest_item=r.get('latest'),feed_checked_items=r.get('items'),
        feed_note=('Google News site search (headline+source only)' if 'news.google.com' in feed else None)))
BLOCK=['6v电影','艾旦影视','free347','不死鸟','ahhhhfs','bilibili - 热门全站榜']
for c in d['channels']:
    if any(b in c['name'] for b in BLOCK):
        c['exclude_from_ranking']=True; c['exclude_reason']='pirate/free-resource or non-news aggregator'
    if c['name']=='WHO News': c['feed_status']='stale'
json.dump(d,open(P,'w'),ensure_ascii=False,indent=1)
print(len(d['channels']),sum(1 for c in d['channels'] if c.get('exclude_from_ranking')))
