"""Step 5: render static site from data/issue-*.json -> site/ (index.html = latest, archive/YYYY-MM-DD.html, archive/index.html)."""
import json,glob,os,html,collections
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));SITE=ROOT
os.makedirs(f'{SITE}/archive',exist_ok=True)
e=lambda s:html.escape(s or '',quote=True)
WD='一二三四五六日'
def page(issue,prefix):
    d=issue['date'];import datetime as dt;w=WD[dt.date.fromisoformat(d).weekday()]
    cats=collections.Counter(i['category'] for i in issue['items'])
    chips='<button class="chip on" data-f="all">全部 100</button><button class="chip" data-f="探索位">探索位</button>'+''.join(f'<button class="chip" data-f="{e(c)}">{e(c)} {n}</button>' for c,n in cats.most_common())
    cards=[]
    for it in issue['items']:
        exp='<span class="tag exp">探索位</span>' if it['explore'] else ''
        stars=('★'*it['stars']) if it['stars'] else ''
        also=''
        if it['also']:
            also='<details class="also"><summary>其他来源 '+str(len(it['also']))+'</summary>'+'<br>'.join(f'<a href="{e(a["link"])}" target="_blank" rel="noopener">{e(a["source"])}</a>：{e(a["title"])}' for a in it['also'])+'</details>'
        pub=(it['published'] or '')[:16].replace('T',' ')
        paras=''.join(f'<p>{e(p.strip())}</p>' for p in it['detail_zh'].split('\n\n') if p.strip())
        xc=' explore' if it['explore'] else ''
        xe=1 if it['explore'] else 0
        pubs=(' · 发布 '+e(pub)) if pub else ''
        cards.append(f'''<article class="item{xc}" data-id="{it['id']}" data-rank="{it['rank']}" data-cat="{e(it['category'])}" data-src="{e(it['source'])}" data-exp="{xe}">
<div class="row"><span class="dot"></span><button class="ttl" type="button"><span class="t"><span class="rank">{it['rank']}</span>{e(it['title_zh'])}</span><span class="m"><span class="tag">{e(it['category'])}</span>{exp}<span>{e(it['source'])}</span><span>{stars}</span></span></button><button class="noteb" type="button" title="备注" aria-label="备注">📝</button></div>
<textarea class="note" placeholder="可选备注：为什么感兴趣/不感兴趣，想看什么…"></textarea>
<div class="l1"><p class="sum">{e(it['summary_zh'])}</p><p class="why"><b>为什么值得看：</b>{e(it['why_zh'])}</p><button class="more" type="button">展开详细 ▾</button></div>
<div class="l2">{paras}<div class="src">来源：{e(it['source'])}<br><a class="orig" href="{e(it['link'])}" target="_blank" rel="noopener">阅读原文 ↗</a></div><div class="otitle">原标题：{e(it['orig_title'])}{pubs}</div>{also}</div>
</article>''')
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>每日简报 {d}</title>
<link rel="stylesheet" href="{prefix}assets/app.css"></head><body data-date="{d}"><header><h1>每日简报 · {d}（周{w}）</h1>
<div class="meta">共 {issue['count']} 条 · 按重要程度排序 · 中英韩多源汇编 · 生成于 {e(issue['generated_at'].replace('T',' '))}（UTC+9）</div>
<nav><a href="{prefix}index.html">今天</a><a href="{prefix}archive/index.html">往期</a><a href="#feedback">反馈汇总</a><span id="prog"></span></nav><div class="chips">{chips}</div></header>
<main><p class="hint">点标题看摘要 · 再点「展开详细」或摘要看长文和原文链接 · 没点开的视为不感兴趣 · 📝 可选备注</p>{''.join(cards)}
<section id="feedback"><h2>今日反馈汇总</h2><p id="fbcount"></p><p style="font-size:13px;color:var(--sub)">系统自动记录每条的阅读深度（0 未打开 / 1 看摘要 / 2 看详细）、是否点原文和备注，只保存在本机浏览器（localStorage）。复制下面的 JSON 发给简报员，我会据此调整明天的选题。</p>
<button class="btn" id="copy">一键复制反馈 JSON</button> <button class="btn ghost" id="clear">清空</button><pre id="fbjson"></pre></section></main>
<footer>摘要由简报员根据原文内容编写，请以原文为准。★ 表示重要程度；紫色左边框为「探索位」（你可能没关注过的方向）；蓝点=看过摘要，绿点=看过详细。</footer>
<script src="{prefix}assets/app.js"></script></body></html>'''
issues=sorted(glob.glob(f'{ROOT}/data/issue-*.json'))
allis=[json.load(open(p)) for p in issues]
for iss in allis:
    open(f"{SITE}/archive/{iss['date']}.html",'w').write(page(iss,'../'))
latest=allis[-1]
open(f'{SITE}/index.html','w').write(page(latest,''))
rows=''.join(f'<a href="{i["date"]}.html"><b>{i["date"]}</b> · {i["count"]} 条 · 头条：{e(i["items"][0]["title_zh"])}</a>' for i in reversed(allis))
open(f'{SITE}/archive/index.html','w').write(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>每日简报 · 往期</title><link rel="stylesheet" href="../assets/app.css"></head>
<body><header><h1>每日简报 · 往期</h1><nav><a href="../index.html">今天</a></nav></header><main class="arch">{rows}</main></body></html>''')
open(f'{SITE}/.nojekyll','w').write('')
print('rendered',len(allis),'issue(s); latest',latest['date'])
