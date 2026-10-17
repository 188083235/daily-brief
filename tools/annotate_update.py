"""Add Chinese titles/summaries to an updates/SLOT.html page.
Input: data/updates/SLOT.zh.json = {link: {"t": 中文标题, "s": 1-2句中文摘要}} written only from the fetched text.
Keeps the original title (as 原题) and original excerpt (folded). Idempotent: re-renders from the page's original cards.
Usage: python3 tools/annotate_update.py 2026-10-17-18"""
import sys,json,re,html,os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));slot=sys.argv[1]
P=os.path.join(ROOT,'updates',slot+'.html');Z=json.load(open(os.path.join(ROOT,'data','updates',slot+'.zh.json')))
s=open(P).read()
if 'class="uz"' in s: print('already annotated');sys.exit(0)
e=lambda x:html.escape(x,quote=True)
def rep(m):
    href,orig,meta,rest=m.group(1),m.group(2),m.group(3),m.group(4)
    z=Z.get(html.unescape(href))
    if not z: return m.group(0)
    ex=re.match(r'<p>(.*?)</p>',rest,re.S)
    exc=f'<details class="uox"><summary>原文摘录</summary><p>{ex.group(1)}</p></details>' if ex else ''
    return (f'<div class="ui"><a class="ut" href="{href}" target="_blank" rel="noopener">{e(z["t"])}</a>'
            f'<div class="uo">原题：{orig}</div><div class="um">{meta}</div><p class="uz">{e(z["s"])}</p>{exc}</div>')
s,n=re.subn(r'<div class="ui"><a class="ut" href="([^"]*)" target="_blank" rel="noopener">(.*?)</a><div class="um">(.*?)</div>((?:<p>.*?</p>)?)</div>',rep,s,flags=re.S)
s=s.replace('标题和摘录均为原文','中文标题和摘要据抓取到的原文编写，原题与原文摘录保留')
s=s.replace('</head>','<style>.uo{font-size:.8em;color:#888;margin:2px 0}.uz{margin:4px 0}.uox summary{font-size:.8em;color:#888;cursor:pointer}</style></head>',1)
open(P,'w').write(s);print('annotated',n,'cards')
