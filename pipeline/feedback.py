"""Reader feedback store (private: data/feedback/ is gitignored).

  python feedback.py fetch                 # pull owner-authored 'update: YYYY-MM-DD' (and legacy 'feedback:') issues via GH_TOKEN -> data/feedback/YYYY-MM-DD.json
  python feedback.py import FILE [--note T] # store a pasted export (full or compact JSON) -> data/feedback/DATE.json
  python feedback.py propose [--days 14]   # aggregate -> data/feedback/prefs-proposed.json (NOT applied to ranking)
  python feedback.py approve               # copy proposed -> prefs-approved.json; run ONLY after the user approves the proposal
  python feedback.py weekly [END_DATE]     # 7-day report -> data/feedback/weekly-END.md

collect.py applies only data/feedback/prefs-approved.json (category score deltas, clamped to ±0.5).
"""
import json,os,re,sys,glob,datetime as dt,collections,requests
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));FB=os.path.join(ROOT,'data','feedback')
REPO='188083235/daily-brief';OWNER='188083235';KST=dt.timezone(dt.timedelta(hours=9))
os.makedirs(FB,exist_ok=True)

def issue_meta(date):
    p=os.path.join(ROOT,'data',f'issue-{date}.json')
    if not os.path.exists(p): p=os.path.join(ROOT,'data','versions',f'issue-{date}.json')
    if not os.path.exists(p): return {}
    return {str(it['id']):it for it in json.load(open(p))['items']}

def normalize(j,origin,extra=None):
    """Accept the page's full export (items[rank,id,depth,link_clicked,note...]) or compact (items[r,id,c,d,l,n,t])."""
    date=j['date'];meta=issue_meta(date);items=[]
    for o in j.get('items',[]):
        if 'r' in o: x=dict(rank=o['r'],id=str(o['id']),category=o.get('c'),depth=o.get('d',0),link_clicked=bool(o.get('l')),note=o.get('n',''),title=o.get('t',''),explore=bool(o.get('e')))
        else: x=dict(rank=o.get('rank'),id=str(o.get('id')),category=o.get('category'),depth=o.get('depth',0),link_clicked=bool(o.get('link_clicked')),note=o.get('note',''),title=o.get('title',''),explore=bool(o.get('explore')))
        m=meta.get(x['id'])
        if m:  # fill from the public issue when the payload was trimmed
            x['category']=x['category'] or m.get('category'); x['title']=x['title'] or m.get('title_zh',''); x['source']=m.get('source'); x['explore']=x['explore'] or bool(m.get('explore'))
        if x['depth'] or x['note'] or x['link_clicked']: items.append(x)
    shown=collections.Counter(m.get('category') for m in meta.values()) if meta else None
    if not shown and isinstance(j.get('by_category'),dict):
        shown={k:(v[0] if isinstance(v,list) else v.get('n',0)) for k,v in j['by_category'].items()}
    return dict(date=date,origin=origin,saved_at=dt.datetime.now(KST).isoformat(timespec='seconds'),summary=j.get('summary'),
                trimmed=j.get('trimmed'),shown_by_category=dict(shown or {}),items=sorted(items,key=lambda x:x['rank'] or 999),**(extra or {}))

def save(rec):
    p=os.path.join(FB,f"{rec['date']}.json");json.dump(rec,open(p,'w'),ensure_ascii=False,indent=1);return p

def fetch():
    tok=os.environ.get('GH_TOKEN')
    if not tok: sys.exit('GH_TOKEN not set')
    r=requests.get(f'https://api.github.com/repos/{REPO}/issues',params=dict(state='all',per_page=100,sort='created',direction='asc'),
                   headers={'Authorization':f'Bearer {tok}','Accept':'application/vnd.github+json'},timeout=20); r.raise_for_status()
    n=0
    for iss in r.json():   # oldest first, so the newest submission for a date wins
        ttl=iss.get('title','').lower()
        if 'pull_request' in iss or not (ttl.startswith('feedback:') or ttl.startswith('update:')): continue
        if iss.get('user',{}).get('login')!=OWNER: continue          # only the owner's feedback counts
        m=re.search(r'\{.*\}',iss.get('body') or '',re.S)
        try: j=json.loads(m.group(0)) if m else None
        except Exception: j=None
        if j and isinstance(j.get('feedback'),dict): j=dict(j['feedback'],date=j.get('date'))   # 'update:' issue (feedback + fixed_topics)
        elif j and ttl.startswith('update:'): j=None
        if not j or not re.fullmatch(r'\d{4}-\d\d-\d\d(-v\d+)?',str(j.get('date',''))): print('skip issue without feedback',iss['number']); continue
        print('saved',save(normalize(j,'github-issue',dict(issue=iss['number'],issue_created_at=iss['created_at'])))); n+=1
    print(f'{n} feedback issue(s) stored')

def load_all(days=None,end=None):
    recs=[json.load(open(p)) for p in sorted(glob.glob(os.path.join(FB,'20??-??-??.json')))]
    if end: recs=[r for r in recs if r['date']<=end]
    if days and end:
        lo=(dt.date.fromisoformat(end)-dt.timedelta(days=days-1)).isoformat(); recs=[r for r in recs if r['date']>=lo]
    return recs

def aggregate(recs):
    shown=collections.Counter();opened=collections.Counter();deep=collections.Counter();src=collections.Counter()
    for r in recs:
        shown.update(r.get('shown_by_category',{}))
        for x in r['items']:
            if x['depth']>=1: opened[x['category']]+=1
            if x['depth']>=2: deep[x['category']]+=1
            if x.get('source'): src[x['source']]+=x['depth']
    return shown,opened,deep,src

def propose(days=14):
    end=dt.datetime.now(KST).date().isoformat();recs=load_all(days,end)
    shown,opened,deep,src=aggregate(recs);tot_s=sum(shown.values()) or 1;tot_o=sum(opened.values())+sum(deep.values())
    base=tot_o/tot_s;deltas={}
    for c,n in shown.items():
        rate=(opened[c]+deep[c])/n if n else 0
        # need at least 3 days and ~30 opened signals before suggesting anything; changes are small and clamped
        if len(recs)>=3 and tot_o>=30 and n>=10: deltas[c]=round(max(-0.5,min(0.5,(rate-base)/max(base,1e-6)*0.2)),2)
    prop=dict(generated_at=dt.datetime.now(KST).isoformat(timespec='seconds'),days=len(recs),window_days=days,approved=False,
              category_delta=deltas,evidence={c:dict(shown=shown[c],opened=opened[c],detail=deep[c]) for c in shown},
              note='Not applied until the user approves it (python feedback.py approve).' if deltas else f'Not enough feedback yet ({len(recs)} day(s), {tot_o} signal(s)); no changes proposed.')
    p=os.path.join(FB,'prefs-proposed.json');json.dump(prop,open(p,'w'),ensure_ascii=False,indent=1);print(json.dumps(prop,ensure_ascii=False,indent=1));print('->',p)

def approve():
    p=os.path.join(FB,'prefs-proposed.json');prop=json.load(open(p));prop['approved']=True;prop['approved_at']=dt.datetime.now(KST).isoformat(timespec='seconds')
    json.dump(prop,open(os.path.join(FB,'prefs-approved.json'),'w'),ensure_ascii=False,indent=1);print('approved',prop['category_delta'])

def weekly(end=None):
    end=end or dt.datetime.now(KST).date().isoformat();recs=load_all(7,end);shown,opened,deep,src=aggregate(recs)
    L=[f'# 每周反馈小结（截至 {end}，共 {len(recs)} 天有反馈）','']
    for r in recs:
        s=r.get('summary') or {};L.append(f"- {r['date']}（{r['origin']}{'，issue #'+str(r['issue']) if r.get('issue') else ''}）：打开 {len([x for x in r['items'] if x['depth']>=1])} 条，看详细 {len([x for x in r['items'] if x['depth']>=2])} 条，备注 {len([x for x in r['items'] if x['note']])} 条"+(f"；提交时{r['trimmed']}" if r.get('trimmed') else ''))
    L+=['','## 分类','| 分类 | 展示 | 打开 | 详细 |','|---|---|---|---|']+[f'| {c} | {shown[c]} | {opened[c]} | {deep[c]} |' for c in sorted(shown,key=lambda c:-(opened[c]+deep[c]))]
    L+=['','## 看过的条目']+[f"- {r['date']} #{x['rank']} [{x['category']}] {x['title']}（深度 {x['depth']}{'，点了原文' if x['link_clicked'] else ''}）"+(f"\n  - 备注：{x['note']}" if x['note'] else '') for r in recs for x in r['items']]
    p=os.path.join(FB,f'weekly-{end}.md');open(p,'w').write('\n'.join(L)+'\n');print('\n'.join(L));print('->',p)

if __name__=='__main__':
    a=sys.argv[1:] or ['fetch']
    if a[0]=='fetch': fetch()
    elif a[0]=='import':
        j=json.load(sys.stdin if a[1]=='-' else open(a[1])); note=a[a.index('--note')+1] if '--note' in a else None
        print('saved',save(normalize(j,'pasted',dict(note=note) if note else None)))
    elif a[0]=='propose': propose(int(a[a.index('--days')+1]) if '--days' in a else 14)
    elif a[0]=='approve': approve()
    elif a[0]=='weekly': weekly(a[1] if len(a)>1 else None)
    else: sys.exit(__doc__)
