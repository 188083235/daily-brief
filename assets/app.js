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
    const o={rank:+el.dataset.rank,id:el.dataset.id,title:el.querySelector('.t').textContent,category:c,source:el.dataset.src,explore:el.dataset.exp==='1',depth:d,link_clicked:!!s.link_clicked,note:s.note||''};
    if(s.t1)o.opened_at=s.t1; if(s.t2)o.detail_at=s.t2; if(s.tl)o.link_at=s.tl;
    items.push(o);});
  sum.explore_opened=items.filter(x=>x.explore&&x.depth>0).length;
  return {date:D,exported_at:now(),schema:'depth: 0=未打开(不感兴趣) 1=看了摘要(感兴趣) 2=看了详细(很感兴趣)',summary:sum,by_category:bycat,items};
}
function render(){const j=build(),s=j.summary;
  document.getElementById('fbjson').textContent=JSON.stringify(j,null,1);
  const t=`已读 ${s.interested+s.very_interested}/${s.total}（摘要 ${s.interested} · 详细 ${s.very_interested} · 点原文 ${s.link_clicked} · 备注 ${s.notes}）`;
  document.getElementById('fbcount').textContent=t; const p=document.getElementById('prog'); if(p)p.textContent=`已读 ${s.interested+s.very_interested}/${s.total}`;}
document.getElementById('copy').addEventListener('click',async()=>{const t=document.getElementById('fbjson').textContent;
  try{await navigator.clipboard.writeText(t)}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove()}
  const b=document.getElementById('copy');b.textContent='已复制 ✓';setTimeout(()=>b.textContent='一键复制反馈 JSON',1500)});
document.getElementById('clear').addEventListener('click',()=>{if(confirm('清空今天的全部阅读记录和备注？')){st={};save();location.reload()}});
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));c.classList.add('on');const v=c.dataset.f;
  document.querySelectorAll('.item').forEach(el=>{el.style.display=(v==='all'||el.dataset.cat===v||(v==='探索位'&&el.dataset.exp==='1'))?'':'none'})}));
render();
})();
