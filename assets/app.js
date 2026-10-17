(function(){
const D=document.body.dataset.date, KEY='daily-brief:fb:'+D;
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY))||{}}catch(e){return{}}};
let fb=load();const save=()=>{localStorage.setItem(KEY,JSON.stringify(fb));render()};
document.querySelectorAll('.item').forEach(el=>{
  const id=el.dataset.id;const st=fb[id]||{};const ta=el.querySelector('textarea.note');
  const sync=()=>{const s=fb[id]||{};el.querySelectorAll('.fb button').forEach(b=>{const k=b.dataset.k;b.classList.toggle('on',k==='note'?!!s.note:!!s[k])});ta.value=s.note||'';if(s.note)ta.classList.add('show')};
  el.querySelectorAll('.fb button').forEach(b=>b.addEventListener('click',()=>{
    const k=b.dataset.k;const s=fb[id]||(fb[id]={});
    if(k==='note'){ta.classList.toggle('show');if(ta.classList.contains('show'))ta.focus();return}
    s[k]=!s[k]; if(k==='useful'&&s.useful)s.useless=false; if(k==='useless'&&s.useless){s.useful=false;s.more=false} if(k==='more'&&s.more)s.useless=false;
    if(!s.useful&&!s.useless&&!s.more&&!s.note)delete fb[id]; save();sync();}));
  ta.addEventListener('input',()=>{const s=fb[id]||(fb[id]={});s.note=ta.value.trim();if(!s.useful&&!s.useless&&!s.more&&!s.note)delete fb[id];save();sync()});
  sync();
});
function render(){
  const out=[];document.querySelectorAll('.item').forEach(el=>{const s=fb[el.dataset.id];if(!s)return;
    out.push({id:el.dataset.id,rank:+el.dataset.rank,category:el.dataset.cat,source:el.dataset.src,explore:el.dataset.exp==='1',title:el.querySelector('h2').textContent,
      useful:!!s.useful,useless:!!s.useless,more:!!s.more,note:s.note||''})});
  out.sort((a,b)=>a.rank-b.rank);
  const sum={useful:out.filter(x=>x.useful).length,useless:out.filter(x=>x.useless).length,more:out.filter(x=>x.more).length,notes:out.filter(x=>x.note).length};
  const j={date:D,exported_at:new Date().toISOString(),summary:sum,items:out};
  document.getElementById('fbjson').textContent=JSON.stringify(j,null,1);
  document.getElementById('fbcount').textContent=`已反馈 ${out.length} 条（有用 ${sum.useful} / 没用 ${sum.useless} / 多来点 ${sum.more} / 备注 ${sum.notes}）`;
}
document.getElementById('copy').addEventListener('click',async()=>{const t=document.getElementById('fbjson').textContent;
  try{await navigator.clipboard.writeText(t)}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove()}
  const b=document.getElementById('copy');b.textContent='已复制 ✓';setTimeout(()=>b.textContent='一键复制反馈 JSON',1500)});
document.getElementById('clear').addEventListener('click',()=>{if(confirm('清空今天的全部反馈？')){fb={};save();location.reload()}});
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));c.classList.add('on');const v=c.dataset.f;
  document.querySelectorAll('.item').forEach(el=>{el.style.display=(v==='all'||el.dataset.cat===v||(v==='探索位'&&el.dataset.exp==='1'))?'':'none'})}));
render();
})();
