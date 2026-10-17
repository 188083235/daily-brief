"""Freeze the user's follow posts for a daily issue: ../data/social/latest.json -> ../data/follow-pack-DATE.json (private).
Usage: python follow_pack.py DATE [--hours 30]   Each post gets a stable fid that editorial/DATE.py FOLLOW entries reference."""
import json,sys,os,argparse,datetime as dt
ap=argparse.ArgumentParser();ap.add_argument('date');ap.add_argument('--hours',type=int,default=30);a=ap.parse_args()
KST=dt.timezone(dt.timedelta(hours=9));end=dt.datetime.now(KST);start=end-dt.timedelta(hours=a.hours)
d=json.load(open('../data/social/latest.json'));items=[]
for acc in d['accounts']:
    for p in acc['posts']:
        if not p.get('time') or not (start.isoformat()<=p['time']<=end.isoformat()): continue
        items.append(dict(fid=len(items),platform=acc['platform'],account=acc['name'],category=acc.get('category'),**p))
json.dump(dict(date=a.date,window=[start.isoformat(timespec='minutes'),end.isoformat(timespec='minutes')],collected_at=d['collected_at'],summary=d['summary'],items=items),
          open(f'../data/follow-pack-{a.date}.json','w'),ensure_ascii=False,indent=1)
print('follow-pack',len(items),'posts')
