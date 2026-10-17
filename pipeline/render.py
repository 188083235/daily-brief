"""Step 5: render static site from data/issue-*.json -> site/ (index.html = latest, archive/YYYY-MM-DD.html, archive/index.html)."""
import json,glob,os,html,collections
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));SITE=ROOT
os.makedirs(f'{SITE}/archive',exist_ok=True)
e=lambda s:html.escape(s or '',quote=True)
WD='一二三四五六日'
def _updl(prefix):
    import os,glob
    fs=sorted(f for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','updates','20*.html')))
    return f'<a class="updl" href="{prefix}updates/{os.path.basename(fs[-1])}">🕒 最新更新</a>' if fs else ''

def page(issue,prefix):
    updl=_updl(prefix)
    d=issue['date'];import datetime as dt;w=WD[dt.date.fromisoformat(issue.get('base_date',d)).weekday()];vlab=issue.get('version_label','')
    cats=collections.Counter(i['category'] for i in issue['items'])
    chips=f'<button class="chip on" data-f="all">全部 {issue["count"]+len(issue.get("follow_items",[]))}</button>'+('<button class="chip" data-f="我的关注">我的关注</button>' if issue.get('follow_items') else '')+'<button class="chip" data-f="探索位">探索位</button>'+''.join(f'<button class="chip" data-f="{e(c)}">{e(c)} {n}</button>' for c,n in cats.most_common())
    cards=[];fcards=[]
    for it in issue['items']+issue.get('follow_items',[]):
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
        (fcards if it['category']=='我的关注' else cards).append(f'''<article class="item{xc}" data-id="{it['id']}" data-rank="{it['rank']}" data-cat="{e(it['category'])}" data-src="{e(it['source'])}" data-exp="{xe}">
<div class="row"><span class="dot"></span><button class="ttl" type="button"><span class="t"><span class="rank">{it.get('rank_label',it['rank'])}</span><span class="tt">{e(it['title_zh'])}</span></span><span class="m"><span class="tag">{e(it['category'])}</span>{exp}<span>{e(it['source'])}</span><span>{stars}</span></span></button><button class="noteb" type="button" title="备注" aria-label="备注">📝</button></div>
<textarea class="note" placeholder="可选备注：为什么感兴趣/不感兴趣，想看什么…"></textarea>
<div class="l1"><p class="sum">{e(it['summary_zh'])}</p><p class="why"><b>为什么值得看：</b>{e(it['why_zh'])}</p><button class="more" type="button">展开详细 ▾</button></div>
<div class="l2">{paras}<div class="src">来源：{e(it['source'])}<br><a class="orig" href="{e(it['link'])}" target="_blank" rel="noopener">阅读原文 ↗</a></div><div class="otitle">原标题：{e(it['orig_title'])}{pubs}</div>{also}</div>
</article>''')
    fx=issue.get('fixed')
    fixed_html=''
    if fx:
        blocks=[]
        for tp in fx['topics']:
            its=''.join(f'''<div class="fi"><div class="ftl">{e(x['title_zh'])}</div><p>{e(x['summary_zh'])}</p><div class="src">{e(x['source'])}{(' · '+e(x['published'][:10])) if x.get('published') else ''} · <a href="{e(x['link'])}" target="_blank" rel="noopener">原文 ↗</a>{''.join(f' · <a href="{e(a["link"])}" target="_blank" rel="noopener">{e(a["source"])}</a>' for a in x['also'])}</div></div>''' for x in tp['items'])
            if not tp['items']: its='<p class="fnote">'+e(tp['note'] or '过去72小时没有找到新的相关报道。')+'</p>'
            else: its=('<p class="fnote">'+e(tp['note'])+'</p>' if tp['note'] else '')+its
            blocks.append(f'''<details class="ft" open><summary><b>{e(tp['name'])}</b> <span class="kw">{e(' / '.join(tp['keywords']))} · 找到 {tp['found']} 篇，精选 {len(tp['items'])} 条</span></summary>{its}</details>''')
        fw=fx['window'];fixed_html=f'''<section id="fixed"><h2>📌 固定关注 <a class="setb opensp" href="#panel">⚙ 设置</a></h2><p class="hint">检索范围：{e(fw[0][:16].replace('T',' '))} – {e(fw[1][:16].replace('T',' '))}（UTC+9）· 中/韩/英新闻搜索与当地媒体 · 只收录抓到正文且确实提到关键词的报道</p>{''.join(blocks)}</section>'''
        cfg=json.dumps(dict(topics=[dict(name=t['name'],keywords=t['keywords']) for t in fx['topics']]),ensure_ascii=False)
    else:
        cfg=json.dumps(dict(topics=[]),ensure_ascii=False)
    fo=issue.get('follow')
    follow_html=''
    if fo:
        st=' · '.join(f"{k} {v}" for k,v in fo['stats'].items())
        follow_html=f'''<section id="follow"><h2 class="sec">👤 我的关注（{len(fcards)}）</h2><p class="hint">来自你自己的 RSS/YouTube/Telegram/GitHub 等关注（{e(fo['window'][0][5:16].replace('T',' '))} – {e(fo['window'][1][5:16].replace('T',' '))}，UTC+9）。本次成功抓取的账号：{e(st)}。B站部分账号可匿名抓取（其余受风控限制）；抖音、头条、小红书暂未接入（需要登录信息）。YouTube 只有标题，发布时间为近似值。</p>{''.join(fcards)}</section>'''
    settings=f'''<script type="application/json" id="fixedcfg">{cfg.replace('</','<\\/')}</script>'''
    panel=f'''<section id="panel"><h2>⚙ 设置与反馈</h2>
<div class="pp"><h3>今日反馈</h3><p id="fbcount"></p><p class="hint">自动记录每条的阅读深度（0 未打开 / 1 看摘要 / 2 看详细）、是否点原文和备注，只存在本机浏览器。</p></div>
<div class="pp"><h3>固定关注</h3><p class="hint">别名/外文写法用 / 分隔，如「당진/唐津/Dangjin」。修改先存在本机，随下面的提交一起生效（下一期）。</p><ul id="toplist"></ul><div class="addrow"><input id="newtopic" placeholder="新主题，如：大连/Dalian/다롄"><button class="btn" type="button" id="addtopic">添加</button></div><p class="hint"><span id="cfgstate"></span> <button class="lnk" type="button" id="resetcfg">恢复为当前生效配置</button></p></div>
<div class="pp sub"><button class="btn" id="submitall" type="button">提交到 GitHub ↗</button><p class="hint">打开预填好的 issue「update: {d}」，含今日反馈（只含打开过的条目、备注和统计）以及固定关注的修改（如有），在 GitHub 上点 Submit 即可。</p><p id="substate" class="fbstate no">状态：未提交</p>
<div class="sprow"><button class="btn ghost" id="copy" type="button">复制完整 JSON</button> <button class="btn ghost" id="clear" type="button">清空今日记录</button></div>
<details class="json"><summary>查看 JSON</summary><pre id="fbjson"></pre></details></div></section>'''
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>每日简报 {d}</title>
<link rel="stylesheet" href="{prefix}assets/app.css"></head><body data-date="{d}" data-key="{e(issue.get('store_key',d))}"><header><h1>每日简报 · {issue.get('base_date',d)}（周{w}）{vlab}</h1>
<div class="meta">共 {issue['count']} 条 · 按重要程度排序 · 中英韩多源汇编 · 生成于 {e(issue['generated_at'].replace('T',' '))}（UTC+9）</div>
<nav><a href="{prefix}index.html">今天</a><a href="{prefix}archive/index.html">往期</a><a href="#fixed">固定关注</a><a href="#follow">我的关注</a><a class="opensp" href="#panel">⚙ 设置/反馈</a>{updl}<span id="prog"></span></nav><div class="chips">{chips}</div></header>
<main>{fixed_html}{follow_html}{settings}<h2 class="sec">今日 100 条</h2><p class="hint">点标题看摘要 · 再点「展开详细」或摘要看长文和原文链接 · 没点开的视为不感兴趣 · 📝 可选备注</p>{''.join(cards)}
{panel}</main>
<footer>摘要由简报员根据原文内容编写，请以原文为准。★ 表示重要程度；紫色左边框为「探索位」（你可能没关注过的方向）；蓝点=看过摘要，绿点=看过详细。</footer>
<script src="{prefix}assets/app.js"></script></body></html>'''
issues=sorted(glob.glob(f'{ROOT}/data/issue-*.json'))
allis=[json.load(open(p)) for p in issues]
for iss in allis:
    open(f"{SITE}/archive/{iss['date']}.html",'w').write(page(iss,'../'))
vers=[json.load(open(p)) for p in sorted(glob.glob(f'{ROOT}/data/versions/issue-*.json'))]
for iss in vers: open(f"{SITE}/archive/{iss['date']}.html",'w').write(page(iss,'../'))
latest=allis[-1]
open(f'{SITE}/index.html','w').write(page(latest,''))
rows=''.join(f'<a href="{i["date"]}.html"><b>{i.get("base_date",i["date"])}{e(i.get("version_label",""))}</b> · {i["count"]} 条 · 头条：{e(i["items"][0]["title_zh"])}</a>' for i in sorted(allis+vers,key=lambda i:(i.get('base_date',i['date']),'base_date' not in i),reverse=True))
open(f'{SITE}/archive/index.html','w').write(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>每日简报 · 往期</title><link rel="stylesheet" href="../assets/app.css"></head>
<body><header><h1>每日简报 · 往期</h1><nav><a href="../index.html">今天</a></nav></header><main class="arch">{rows}</main></body></html>''')
open(f'{SITE}/.nojekyll','w').write('')
print('rendered',len(allis),'issue(s); latest',latest['date'])
