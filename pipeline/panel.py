"""Shared '⚙ 设置与反馈' panel for the 6-hourly update pages (same element ids as the daily page, so assets/app.js drives both).
Feedback from an update page is submitted as the issue 'update: YYYY-MM-DD-HH' (feedback.py stores it under data/feedback/updates/)."""
import json,os,re,html
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
def live_topics():
    """Currently active fixed topics = what the latest daily page embeds (falls back to config/fixed_topics.json)."""
    try:
        m=re.search(r'<script type="application/json" id="fixedcfg">(.*?)</script>',open(os.path.join(ROOT,'index.html')).read(),re.S)
        j=json.loads(m.group(1).replace('<\\/','</'))
        if j.get('topics'): return j
    except Exception: pass
    try: return dict(topics=[dict(name=t['name'],keywords=t.get('keywords',[])) for t in json.load(open(os.path.join(ROOT,'config','fixed_topics.json')))['topics']])
    except Exception: return dict(topics=[])
def update_panel(slot):
    cfg=json.dumps(live_topics(),ensure_ascii=False).replace('</','<\\/')
    return f'''<script type="application/json" id="fixedcfg">{cfg}</script><section id="panel"><h2>⚙ 设置与反馈</h2>
<div class="pp"><h3>本期反馈</h3><p id="fbcount"></p><p class="hint">自动记录：展开「原文摘录」= 感兴趣，点开原文 = 很感兴趣，📝 可写备注。只存在本机浏览器，点下面的按钮提交。</p></div>
<div class="pp"><h3>固定关注</h3><p class="hint">别名/外文写法用 / 分隔，如「당진/唐津/Dangjin」。修改先存在本机，随下面的提交一起生效（下一期日报）。</p><ul id="toplist"></ul><div class="addrow"><input id="newtopic" placeholder="新主题，如：大连/Dalian/다롄"><button class="btn" type="button" id="addtopic">添加</button></div><p class="hint"><span id="cfgstate"></span> <button class="lnk" type="button" id="resetcfg">恢复为当前生效配置</button></p></div>
<div class="pp sub"><button class="btn" id="submitall" type="button">提交到 GitHub ↗</button><p class="hint">打开预填好的 issue「update: {html.escape(slot)}」，含本期反馈以及固定关注的修改（如有），在 GitHub 上点 Submit 即可。</p><p id="substate" class="fbstate no">状态：未提交</p>
<div class="sprow"><button class="btn ghost" id="copy" type="button">复制完整 JSON</button> <button class="btn ghost" id="clear" type="button">清空本期记录</button></div>
<details class="json"><summary>查看 JSON</summary><pre id="fbjson"></pre></details></div></section>'''
def retrofit(path):
    """Add data attributes, the panel and app.js to an already generated updates/SLOT.html (idempotent)."""
    s=open(path).read();slot=os.path.basename(path)[:-5]
    if 'id="submitall"' in s: return False
    n={'follow':0,'news':0}
    def sect(m):
        kind=m.group(1);body=m.group(2);plat=['']
        def card(c):
            if c.group(0).startswith('<h3>'): plat[0]=re.sub(r'（\d+）$','',c.group(1));return c.group(0)
            i=n[kind];n[kind]+=1
            return f'<div class="ui" data-id="{kind[0]}{i}" data-cat="{html.escape(("关注·"+plat[0]) if kind=="follow" else "新闻")}">'
        return f'<section id="{kind}">'+re.sub(r'<h3>(.*?)</h3>|<div class="ui">',card,body)+'</section>'
    s=re.sub(r'<section id="(follow|news)">(.*?)</section>',sect,s,flags=re.S)
    s=s.replace('<body>',f'<body data-kind="update" data-date="{slot[:10]}" data-key="upd:{slot}" data-slot="{slot}">',1)
    s=s.replace('<a href="#news">新闻</a></nav>','<a href="#news">新闻</a><a class="opensp" href="#panel">⚙ 设置/反馈</a><span id="prog"></span></nav>',1)
    s=s.replace('</main>',update_panel(slot)+'</main><script src="../assets/app.js?v=20261018a"></script>',1)
    open(path,'w').write(s);return True
if __name__=='__main__':
    import sys,glob
    for p in sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT,'updates','20*.html'))): print(p,'retrofitted' if retrofit(p) else 'already has panel')
