"""Step 2: choose candidates per category quota + exploration slots, resolve Google News links,
fetch article text (trafilatura) for grounding, keep only grounded items, write data/pack-DATE.json."""
import json,sys,re,collections,concurrent.futures as cf,requests,trafilatura
from googlenewsdecoder import gnewsdecoder
date=sys.argv[1]
d=json.load(open(f'../data/candidates-{date}.json'))
C=d['candidates']
MAP={'时政/新闻':'时政','综合新闻':'时政','科技/数码':'科技','军事':'国际','技术博客':'科技'}
for c in C:
    c['bucket']=MAP.get(c['category'],c['category'])
    if c['language'].startswith('zh') and c['bucket']=='时政': c['bucket']='中国'
    if c['bucket']=='时政': c['bucket']='国际'
QUOTA={'国际':15,'中国':8,'韩国':10,'财经':10,'AI':7,'科技':9,'科学':6,'健康':5,'气候环境':4,'日本':4,'欧洲':5,'中东':5,'非洲':3,'体育':5,'网络安全':1}
JUNK=re.compile(r'PRNewswire|Top headlines in major|\[포토\]|\[사진\]|\[속보\]|부고|인사\]|Pictured|live$|– live|as it happened|Quiz|crossword',re.I)
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
pool=[];cnt=collections.Counter()
for c in C:
    b=c['bucket']
    if JUNK.search(c['title']): continue
    if b in QUOTA and cnt[b]<QUOTA[b]*2+2: pool.append(c);cnt[b]+=1
exp=[c for c in C if c not in pool and not JUNK.search(c['title']) and (c['category'] in {'技术博客','历史/文化','趣闻','网络安全','AI','科学'} or c['tier']==1)][:24]
for c in exp: c['explore']=True
pool+=exp
def text(c):
    url=c['link']
    try:
        if c['gnews']:
            r=gnewsdecoder(url,interval=0.5); url=r.get('decoded_url') or None
            c['link_resolved']=url
        if url:
            r=requests.get(url,headers=UA,timeout=12)
            t=trafilatura.extract(r.text,include_comments=False) or ''
            c['article']=re.sub(r'\s+',' ',t)[:2000]
    except Exception as e: c['article_err']=str(e)[:80]
    return c
with cf.ThreadPoolExecutor(8) as ex: pool=list(ex.map(text,pool))
def grounded(c): return len(c.get('article',''))>=300 or (not c['gnews'] and len(c['summary'])>=150)
final=[];cnt=collections.Counter();ecnt=0
for c in pool:
    if not grounded(c): continue
    if c.get('explore'):
        if ecnt<14: final.append(c);ecnt+=1
    elif cnt[c['bucket']]<int(QUOTA[c['bucket']]*1.4)+1: final.append(c);cnt[c['bucket']]+=1
for i,c in enumerate(final):
    c['cid']=i
    if c.get('link_resolved'): c['link']=c['link_resolved']
json.dump(final,open(f'../data/pack-{date}.json','w'),ensure_ascii=False,indent=1)
print(len(pool),len(final),dict(cnt),ecnt)
