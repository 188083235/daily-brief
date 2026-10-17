(function(){
const D=document.body.dataset.date, KEY='daily-brief:v2:'+(document.body.dataset.key||D);
let st;try{st=JSON.parse(localStorage.getItem(KEY))||{}}catch(e){st={}}
const now=()=>new Date().toISOString();
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}render()};
const rec=id=>st[id]||(st[id]={depth:0});
function setDepth(el,d){const id=el.dataset.id,s=rec(id);
  if(d>=1&&!s.t1)s.t1=now(); if(d>=2&&!s.t2)s.t2=now();
  if(d>(s.depth||0))s.depth=d; s.last=now(); el.dataset.depth=s.depth; save();}
document.querySelectorAll('.item').forEach(el=>{
  const id=el.dataset.id, s=st[id]||{}; el.dataset.depth=s.depth||0;
  const ta=el.querySelector('textarea.note'), nb=el.querySelector('.noteb');
  if(s.note){ta.value=s.note;nb.classList.add('has')}
  el.querySelector('.ttl').addEventListener('click',()=>{
    if(el.classList.contains('open1')){el.classList.remove('open1','open2');return}
    el.classList.add('open1'); setDepth(el,1);});
  const go2=()=>{el.classList.add('open1','open2'); setDepth(el,2);};
  el.querySelector('.more').addEventListener('click',go2);
  el.querySelector('.sum').addEventListener('click',go2);
  el.querySelectorAll('a.orig,details.also a').forEach(a=>a.addEventListener('click',()=>{const r=rec(id);r.link_clicked=true;if(!r.tl)r.tl=now();save();}));
  nb.addEventListener('click',e=>{e.stopPropagation();ta.classList.toggle('show');if(ta.classList.contains('show'))ta.focus();});
  ta.addEventListener('input',()=>{const r=rec(id);r.note=ta.value.trim();if(r.note&&!r.tn)r.tn=now();nb.classList.toggle('has',!!r.note);save();});
});
function build(){
  const items=[],sum={total:0,unopened:0,interested:0,very_interested:0,link_clicked:0,notes:0},bycat={};
  document.querySelectorAll('.item').forEach(el=>{const s=st[el.dataset.id]||{},d=s.depth||0,c=el.dataset.cat;
    sum.total++; if(d===0)sum.unopened++; else if(d===1)sum.interested++; else sum.very_interested++;
    if(s.link_clicked)sum.link_clicked++; if(s.note)sum.notes++;
    const b=bycat[c]||(bycat[c]={n:0,d1:0,d2:0}); b.n++; if(d===1)b.d1++; if(d>=2)b.d2++;
    const o={rank:+el.dataset.rank,id:el.dataset.id,title:el.querySelector('.tt').textContent,category:c,source:el.dataset.src,explore:el.dataset.exp==='1',depth:d,link_clicked:!!s.link_clicked,note:s.note||''};
    if(s.t1)o.opened_at=s.t1; if(s.t2)o.detail_at=s.t2; if(s.tl)o.link_at=s.tl;
    items.push(o);});
  sum.explore_opened=items.filter(x=>x.explore&&x.depth>0).length;
  return {date:D,exported_at:now(),schema:'depth: 0=未打开(不感兴趣) 1=看了摘要(感兴趣) 2=看了详细(很感兴趣)',summary:sum,by_category:bycat,items};
}
// ---- 固定关注（本机草稿） ----
const CFGKEY='daily-brief:fixed-topics',REPO='188083235/daily-brief',SUBKEY='daily-brief:submitted:'+(document.body.dataset.key||D),MAXURL=7800;
const live=JSON.parse(document.getElementById('fixedcfg').textContent||'{"topics":[]}');
let cfg;try{cfg=JSON.parse(localStorage.getItem(CFGKEY))}catch(e){} if(!cfg||!Array.isArray(cfg.topics))cfg=JSON.parse(JSON.stringify(live));
const ul=document.getElementById('toplist'),cst=document.getElementById('cfgstate');
const cfgChanged=()=>JSON.stringify(cfg.topics)!==JSON.stringify(live.topics);
function draw(){ul.innerHTML='';cfg.topics.forEach((t,i)=>{const li=document.createElement('li');
  const sp=document.createElement('span');sp.textContent=t.name+(t.keywords&&t.keywords.length?'  ['+t.keywords.join(' / ')+']':'');
  const x=document.createElement('button');x.type='button';x.className='rm';x.textContent='✕';x.title='删除';x.onclick=()=>{cfg.topics.splice(i,1);store();};
  li.append(sp,x);ul.append(li);});
  cst.textContent=cfgChanged()?'有修改（已保存在本机），提交后下一期生效。':'与当前生效的配置一致。';}
function store(){localStorage.setItem(CFGKEY,JSON.stringify(cfg));draw();render();}
function parseTopic(v){const parts=v.split(/[\/／|,，]/).map(x=>x.trim()).filter(Boolean);if(!parts.length)return null;return {name:v.trim().slice(0,40),keywords:parts.slice(0,6)};}
document.getElementById('addtopic').onclick=()=>{const inp=document.getElementById('newtopic'),t=parseTopic(inp.value);if(!t)return;
  if(cfg.topics.length>=12){alert('最多 12 个主题');return}cfg.topics.push(t);inp.value='';store();};
document.getElementById('newtopic').addEventListener('keydown',e=>{if(e.key==='Enter')document.getElementById('addtopic').click()});
document.getElementById('resetcfg').onclick=()=>{cfg=JSON.parse(JSON.stringify(live));localStorage.removeItem(CFGKEY);draw();render();};
// ---- 合并提交：update: DATE（feedback + 有修改时的 fixed_topics） ----
function compactFb(){const j=build(),its=j.items.filter(x=>x.depth>0||x.note||x.link_clicked);
  return {schema:'d: 1=摘要 2=详细; l=点了原文; n=备注; 未列出的条目=未打开(depth 0)',summary:j.summary,
    by_category:Object.fromEntries(Object.entries(j.by_category).map(([k,b])=>[k,[b.n,b.d1,b.d2]])),
    items:its.map(x=>{const o={r:x.rank,id:x.id,c:x.category,d:x.depth,t:x.title.slice(0,40)};if(x.link_clicked)o.l=1;if(x.note)o.n=x.note;if(x.explore)o.e=1;return o;})};}
const BASE='https://github.com/'+REPO+'/issues/new?labels=update&title='+encodeURIComponent('update: '+D)+'&body=';
const mkUrl=b=>BASE+encodeURIComponent('请直接点「Submit new issue」提交。简报流水线会读取这条更新（今日反馈'+(b.fixed_topics?' + 固定关注设置':'')+'）。\n\n```json\n'+JSON.stringify(b)+'\n```\n');
function payload(){const f=compactFb(),b={v:2,type:'update',date:D,at:now(),feedback:f};if(cfgChanged())b.fixed_topics={topics:cfg.topics};
  const notes=[],mark=()=>{f.trimmed=notes.join('、')};let u=mkUrl(b);
  if(u.length>MAXURL){f.items.forEach(o=>delete o.t);notes.push('去掉了标题');mark();u=mkUrl(b);}
  if(u.length>MAXURL){delete f.by_category;notes.push('去掉了分类统计');mark();u=mkUrl(b);}
  if(u.length>MAXURL){f.items.forEach(o=>{if(o.n&&o.n.length>120)o.n=o.n.slice(0,120)+'…'});notes.push('备注截断到120字');mark();u=mkUrl(b);}
  let dropped=0;while(u.length>MAXURL&&f.items.length){f.items.sort((a,c)=>(c.d+(c.n?2:0))-(a.d+(a.n?2:0)));f.items.pop();dropped++;f.trimmed=notes.concat('省略了 '+dropped+' 条最浅的记录（完整版请用复制按钮）').join('、');u=mkUrl(b);}
  return {b,u,sig:JSON.stringify(f.items)+JSON.stringify(f.summary)+JSON.stringify(b.fixed_topics||null)};}
function full(){return {date:D,exported_at:now(),feedback:build(),fixed_topics:{changed:cfgChanged(),topics:cfg.topics}};}
function status(p){const el=document.getElementById('substate');let sub;try{sub=JSON.parse(localStorage.getItem(SUBKEY))}catch(e){}
  el.className='fbstate';const t=x=>new Date(x).toLocaleString('zh-CN',{hour12:false});
  if(!sub){el.textContent='状态：未提交';el.classList.add('no');}
  else if(sub.sig!==p.sig){el.textContent='状态：'+t(sub.at)+' 打开过提交页，之后有新的记录或设置未提交';el.classList.add('chg');}
  else {el.textContent='状态：已打开提交页 ✓（'+t(sub.at)+'，需在 GitHub 点 Submit 才算提交）';el.classList.add('ok');}
  const inc=['今日反馈'];if(p.b.fixed_topics)inc.push('固定关注修改');el.textContent+=' · 本次将提交：'+inc.join(' + ');
  if(p.b.feedback.trimmed)el.textContent+=' · 内容较长，提交时'+p.b.feedback.trimmed;}
let render=function(){const j=build(),s=j.summary;
  document.getElementById('fbjson').textContent=JSON.stringify(full(),null,1);
  document.getElementById('fbcount').textContent=`已读 ${s.interested+s.very_interested}/${s.total}（摘要 ${s.interested} · 详细 ${s.very_interested} · 点原文 ${s.link_clicked} · 备注 ${s.notes}）`;
  const pr=document.getElementById('prog'); if(pr)pr.textContent=`已读 ${s.interested+s.very_interested}/${s.total}`; status(payload());};
document.getElementById('submitall').addEventListener('click',()=>{const p=payload();
  localStorage.setItem(SUBKEY,JSON.stringify({at:now(),sig:p.sig,len:p.u.length}));document.body.dataset.lastSubmitUrl=p.u;
  window.open(p.u,'_blank','noopener');status(p);});
document.getElementById('copy').addEventListener('click',async()=>{const t=JSON.stringify(full(),null,1);
  try{await navigator.clipboard.writeText(t)}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove()}
  const b=document.getElementById('copy');b.textContent='已复制 ✓';setTimeout(()=>b.textContent='复制完整 JSON',1500)});
document.getElementById('clear').addEventListener('click',()=>{if(confirm('清空今天的全部阅读记录和备注？')){st={};save();location.reload()}});
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));c.classList.add('on');const v=c.dataset.f;
  document.querySelectorAll('.item').forEach(el=>{el.style.display=(v==='all'||el.dataset.cat===v||(v==='探索位'&&el.dataset.exp==='1'))?'':'none'})}));
draw();render();
})();
