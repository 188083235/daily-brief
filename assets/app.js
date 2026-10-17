(function(){
const D=document.body.dataset.date, KEY='daily-brief:v2:'+D;
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
let render=function(){const j=build(),s=j.summary;
  document.getElementById('fbjson').textContent=JSON.stringify(j,null,1);
  const t=`已读 ${s.interested+s.very_interested}/${s.total}（摘要 ${s.interested} · 详细 ${s.very_interested} · 点原文 ${s.link_clicked} · 备注 ${s.notes}）`;
  document.getElementById('fbcount').textContent=t; const p=document.getElementById('prog'); if(p)p.textContent=`已读 ${s.interested+s.very_interested}/${s.total}`;}
document.getElementById('copy').addEventListener('click',async()=>{const t=document.getElementById('fbjson').textContent;
  try{await navigator.clipboard.writeText(t)}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove()}
  const b=document.getElementById('copy');b.textContent='已复制 ✓';setTimeout(()=>b.textContent='一键复制反馈 JSON',1500)});
// ---- 提交反馈到 GitHub ----
const SUBKEY='daily-brief:fb-submitted:'+D, MAXURL=7800, FB_BASE='https://github.com/188083235/daily-brief/issues/new?labels=feedback&title='+encodeURIComponent('feedback: '+D)+'&body=';
function compact(){const j=build(),its=j.items.filter(x=>x.depth>0||x.note||x.link_clicked);
  return {v:1,date:D,at:now(),schema:'d: 1=摘要 2=详细; l=点了原文; n=备注; 未列出的条目=未打开(depth 0)',summary:j.summary,
    by_category:Object.fromEntries(Object.entries(j.by_category).map(([k,b])=>[k,[b.n,b.d1,b.d2]])),
    items:its.map(x=>{const o={r:x.rank,id:x.id,c:x.category,d:x.depth,t:x.title.slice(0,40)};if(x.link_clicked)o.l=1;if(x.note)o.n=x.note;if(x.explore)o.e=1;return o;})};}
const fbUrl=b=>FB_BASE+encodeURIComponent('请直接点「Submit new issue」提交，简报流水线会读取这条反馈。\n\n```json\n'+JSON.stringify(b)+'\n```\n');
function payload(){const b=compact(),notes=[];let u=fbUrl(b);
  if(u.length>MAXURL){b.items.forEach(o=>delete o.t);notes.push('去掉了标题');u=fbUrl(b);}
  if(u.length>MAXURL){delete b.by_category;notes.push('去掉了分类统计');b.trimmed=notes.join('、');u=fbUrl(b);}
  if(u.length>MAXURL){b.items.forEach(o=>{if(o.n&&o.n.length>120)o.n=o.n.slice(0,120)+'…'});notes.push('备注截断到120字');b.trimmed=notes.join('、');u=fbUrl(b);}
  let dropped=0;while(u.length>MAXURL&&b.items.length){b.items.sort((a,c)=>(c.d+(c.n?2:0))-(a.d+(a.n?2:0)));b.items.pop();dropped++;b.trimmed=notes.concat('省略了 '+dropped+' 条最浅的记录（完整版请用复制按钮）').join('、');u=fbUrl(b);}
  if(notes.length&&!b.trimmed)b.trimmed=notes.join('、');if(b.trimmed)u=fbUrl(b);
  return {b,u,sig:JSON.stringify(b.items)+JSON.stringify(b.summary)};}
function fbStatus(){const el=document.getElementById('fbstate');if(!el)return;let sub;try{sub=JSON.parse(localStorage.getItem(SUBKEY))}catch(e){}
  const p=payload();el.className='fbstate';
  if(!sub){el.textContent='状态：未提交';el.classList.add('no');}
  else if(sub.sig!==p.sig){el.textContent='状态：'+new Date(sub.at).toLocaleString('zh-CN',{hour12:false})+' 打开过提交页，之后有新的阅读记录未提交';el.classList.add('chg');}
  else {el.textContent='状态：已打开提交页 ✓（'+new Date(sub.at).toLocaleString('zh-CN',{hour12:false})+'，需在 GitHub 点 Submit 才算提交）';el.classList.add('ok');}
  if(p.b.trimmed)el.textContent+=' · 内容较长，提交时'+p.b.trimmed;}
const _r=render; render=function(){_r();fbStatus();};
document.getElementById('submitfb').addEventListener('click',()=>{const p=payload();
  localStorage.setItem(SUBKEY,JSON.stringify({at:now(),sig:p.sig,len:p.u.length}));document.body.dataset.lastFbUrl=p.u;
  window.open(p.u,'_blank','noopener');fbStatus();});
document.getElementById('clear').addEventListener('click',()=>{if(confirm('清空今天的全部阅读记录和备注？')){st={};save();location.reload()}});
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));c.classList.add('on');const v=c.dataset.f;
  document.querySelectorAll('.item').forEach(el=>{el.style.display=(v==='all'||el.dataset.cat===v||(v==='探索位'&&el.dataset.exp==='1'))?'':'none'})}));
render();
// ---- 固定关注设置 ----
const CFGKEY='daily-brief:fixed-topics',REPO='188083235/daily-brief';
const live=JSON.parse(document.getElementById('fixedcfg').textContent||'{"topics":[]}');
let cfg;try{cfg=JSON.parse(localStorage.getItem(CFGKEY))}catch(e){} if(!cfg||!Array.isArray(cfg.topics))cfg=JSON.parse(JSON.stringify(live));
const panel=document.getElementById('setpanel'),ul=document.getElementById('toplist'),stx=document.getElementById('cfgstate');
const same=()=>JSON.stringify(cfg.topics)===JSON.stringify(live.topics);
function draw(){ul.innerHTML='';cfg.topics.forEach((t,i)=>{const li=document.createElement('li');
  const sp=document.createElement('span');sp.textContent=t.name+(t.keywords&&t.keywords.length?'  ['+t.keywords.join(' / ')+']':'');
  const x=document.createElement('button');x.type='button';x.className='rm';x.textContent='✕';x.title='删除';x.onclick=()=>{cfg.topics.splice(i,1);store();};
  li.append(sp,x);ul.append(li);});
  stx.textContent=same()?'当前与已生效配置一致。':'本机有未提交的修改（已保存在本机），提交后下一期生效。';}
function store(){localStorage.setItem(CFGKEY,JSON.stringify(cfg));draw();}
function parseTopic(v){const parts=v.split(/[\/／|,，]/).map(x=>x.trim()).filter(Boolean);if(!parts.length)return null;return {name:v.trim().slice(0,40),keywords:parts.slice(0,6)};}
document.getElementById('addtopic').onclick=()=>{const inp=document.getElementById('newtopic'),t=parseTopic(inp.value);if(!t)return;
  if(cfg.topics.length>=12){alert('最多 12 个主题');return}cfg.topics.push(t);inp.value='';store();};
document.getElementById('newtopic').addEventListener('keydown',e=>{if(e.key==='Enter')document.getElementById('addtopic').click()});
document.getElementById('resetcfg').onclick=()=>{cfg=JSON.parse(JSON.stringify(live));localStorage.removeItem(CFGKEY);draw();};
const open=()=>{panel.hidden=false;draw();panel.scrollIntoView({behavior:'smooth',block:'start'})};
document.querySelectorAll('#openset,#navset').forEach(b=>b.addEventListener('click',open));
document.getElementById('closeset').onclick=()=>{panel.hidden=true};
document.getElementById('submitcfg').onclick=()=>{
  const body={version:1,submitted_at:new Date().toISOString(),topics:cfg.topics};
  const md='请直接点「Submit new issue」提交。下一次生成简报时，流水线会读取仓库主人提交的最新一条 `config: fixed-topics` issue。\n\n```json\n'+JSON.stringify(body,null,1)+'\n```\n';
  const url='https://github.com/'+REPO+'/issues/new?labels=config&title='+encodeURIComponent('config: fixed-topics')+'&body='+encodeURIComponent(md);
  localStorage.setItem(CFGKEY,JSON.stringify(cfg)); window.open(url,'_blank','noopener'); stx.textContent='已在新标签页打开预填 issue；确认提交后下一期生效。';
  document.body.dataset.lastSubmitUrl=url;};
})();
