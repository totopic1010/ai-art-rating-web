/* AI Art Rating — plain JavaScript to keep the project beginner-friendly. */
const $ = id => document.getElementById(id);
const storageKey = 'ai-art-rating-web-v6';
const session = JSON.parse(localStorage.getItem(storageKey) || '{}');
if (!session.participant) session.participant = crypto.randomUUID();
if (!session.ratings) session.ratings = {};
if (!session.pairs) session.pairs = {};
const persist = () => localStorage.setItem(storageKey, JSON.stringify(session));
persist();
let works = [], index = 0, shownAt = performance.now(), pairIds = [], summary = null;
const reasons = ['色彩', '構図', '独創性', '感情', '技術', 'その他'];
const average = values => values.length ? values.reduce((a,b) => a+b,0)/values.length : null;
const show = (id, state) => $(id).classList.toggle('hidden', !state);
const setStatus = (message) => { $('status').textContent = message; };
const getJSON = async url => { const r = await fetch(url); if(!r.ok) throw Error('取得に失敗しました'); return r.json(); };
async function send(path, body) {
  const response = await fetch(path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if (!response.ok) {
    let data={}; try {data=await response.json();}catch {}
    throw Error(data.detail || '送信できませんでした');
  }
  return response.json();
}
function renderRuler(){
  $('rulerLines').replaceChildren();
  for(let i=0;i<9;i++){const el=document.createElement('div'); if (Math.round(index/Math.max(works.length-1,1)*8)===i) el.classList.add('active');$('rulerLines').append(el);}
}
function renderArtwork(){
  if(!works.length)return;
  const art = works[index];
  $('artImage').src = art.image_url;
  $('artImage').alt = `${art.title}（AI生成画像）`;
  $('artTitle').textContent = art.title;
  $('artGenre').textContent = art.genre;
  $('counter').textContent = `${String(index+1).padStart(2,'0')} / ${String(works.length).padStart(2,'0')}`;
  $('previous').disabled = index === 0;
  $('next').disabled = index === works.length-1;
  $('score').value = 50;
  $('scoreText').textContent = '50';
  $('reason').value='';
  show('reasonArea',false);
  $('reasonBtn').setAttribute('aria-expanded','false');
  const saved=session.ratings[art.id];
  $('rateBtn').disabled = !!saved;
  $('rateBtn').textContent = saved ? '評価済み' : 'この評価を確定 →';
  $('ratedState').textContent = saved ? `あなたの評価 ${saved.score}点` : '';
  setStatus(saved ? 'この作品はすでに評価済みです。' : '点数を選び、評価を確定してください。');
  renderRuler();
  shownAt=performance.now();
}
function jump(n){index=Math.min(Math.max(n,0),works.length-1);renderArtwork();}
function nextUnrated(){
  let i=index+1;
  while(i<works.length && session.ratings[works[i].id]) i++;
  if(i<works.length)jump(i); else if(index<works.length-1)jump(index+1);
  else setStatus('すべての作品を確認しました。「結果」から傾向を見られます。');
}
function openReveal(){
  if(session.ratings[works[index].id])return;
  $('revisedScore').value=$('score').value;
  $('revisedText').textContent=$('score').value;
  $('revealDialog').showModal();
}
async function saveRating(withRecheck){
  const art=works[index];
  const body={artwork_id:art.id,participant_id:session.participant,score:Number($('score').value),
      reason:$('reason').value,duration_seconds:Math.min(Math.round((performance.now()-shownAt)/100)/10,3600),
      revised_score:withRecheck ? Number($('revisedScore').value) : null,info_shown:withRecheck};
  $('rateBtn').disabled=true;
  try{
    await send('/api/ratings',body);
    session.ratings[art.id]={...body,title:art.title,genre:art.genre};persist();
    $('revealDialog').close();
    nextUnrated();
  }catch(err){$('revealDialog').close();$('rateBtn').disabled=false;setStatus(err.message);}
}
function pickPair(){
  if(works.length<2)return;
  const a=Math.floor(Math.random()*works.length);
  let b=Math.floor(Math.random()*(works.length-1));if(b>=a)b++;
  pairIds=[works[a].id,works[b].id];
  $('pairImgA').src=works[a].image_url;$('pairImgB').src=works[b].image_url;
  $('pairStatus').textContent='直感的に美しいと思う方を選んでください。';
}
async function votePair(i){
  const [l,r]=pairIds;
  const sorted=[l,r].sort().join('|');
  if(session.pairs[sorted]){$('pairStatus').textContent='この組み合わせはすでに評価済みです。別の組み合わせを選んでください。';return;}
  $('pairA').disabled=$('pairB').disabled=true;
  try{
    await send('/api/pair',{participant_id:session.participant,left_id:l,right_id:r,winner_id:pairIds[i]});
    session.pairs[sorted]=pairIds[i];persist();
    pickPair();$('pairStatus').textContent='比較結果を保存しました。次の2作品を表示しています。';
  }catch(err){$('pairStatus').textContent=err.message;}
  finally{$('pairA').disabled=$('pairB').disabled=false;}
}
function bar(container,label,value,max,display){
  const wrap=document.createElement('div');wrap.className='bar-line';
  const l=document.createElement('span');l.textContent=label;
  const track=document.createElement('div');track.className='bar-track';
  const fill=document.createElement('div');fill.className='bar-fill';fill.style.width=`${Math.max(0,Math.min(100,max?value/max*100:0))}%`;
  track.append(fill);
  const number=document.createElement('span');number.textContent=display;
  wrap.append(l,track,number);container.append(wrap);
}
function renderSummary(stats){
  const mine=Object.values(session.ratings);
  const mineAvg=average(mine.map(r=>r.score));
  $('myCount').textContent=mine.length;
  $('myAverage').textContent=mineAvg===null?'—':mineAvg.toFixed(1);
  $('allAverage').textContent=stats.average===null?'—':Number(stats.average).toFixed(1);
  $('shiftAverage').textContent=stats.avg_shift==null?'—':`${Number(stats.avg_shift)>0?'+':''}${Number(stats.avg_shift).toFixed(1)}`;
  const distribution=$('distribution');distribution.replaceChildren();
  for(const [key,label] of [['0','0–19'],['20','20–39'],['40','40–59'],['60','60–79'],['80','80–100']]){
    const val=Number(stats.distribution?.[key]||0);
    bar(distribution,label,val,Math.max(1,...Object.values(stats.distribution||{}).map(Number)),String(val));
  }
  const genres=$('genres');genres.replaceChildren();
  for(const row of (stats.genres||[]).sort((a,b)=>b.average-a.average)) bar(genres,row.genre,Number(row.average),100,Number(row.average).toFixed(1));
  if(!stats.genres?.length)genres.textContent='評価が集まると表示されます。';
  const reasonContainer=$('reasons');reasonContainer.replaceChildren();
  const items=Object.entries(stats.reasons||{}).sort((a,b)=>b[1]-a[1]);
  items.forEach(([reason,count])=>bar(reasonContainer,reason,Number(count),Math.max(1,...items.map(v=>Number(v[1]))),String(count)));
  if(!items.length)reasonContainer.textContent='評価理由はまだありません。';
  const comp=$('personalComparison');comp.replaceChildren();
  if(mineAvg!==null && stats.average!==null){
    bar(comp,'あなた',mineAvg,100,mineAvg.toFixed(1));
    bar(comp,'全体',Number(stats.average),100,Number(stats.average).toFixed(1));
  }else comp.textContent='採点すると比較できます。';
}
async function updateStats(){
  try{summary=await getJSON('/api/stats');renderSummary(summary);}
  catch(e){$('allAverage').textContent='—';$('personalComparison').textContent='集計を取得できません。';}
}
function exportCSV(){
  const headers=['artwork_id','title','genre','score','reason','duration_seconds','revised_score','info_shown'];
  const rows=Object.values(session.ratings).map(r=>headers.map(h=>String(r[h]??'').replaceAll('"','""')));
  const content='\ufeff'+[headers,...rows].map(row=>row.map(x=>'"'+x+'"').join(',')).join('\r\n');
  const blob=new Blob([content],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download='my_art_ratings.csv';a.click();URL.revokeObjectURL(url);
}
function activate(view){
  for(const key of ['gallery','pair','results'])show(key,key===view);
  document.querySelectorAll('.nav').forEach(btn=>btn.classList.toggle('active',btn.dataset.view===view));
  if(view==='results')updateStats();
  if(view==='pair')pickPair();
}
async function init(){
  try{
    works=await getJSON('/api/artworks');
    const health=await getJSON('/api/health');
    $('storageStatus').textContent=health.mode==='supabase'?'共有データベースに接続':health.mode==='local'?'ローカル保存モード':'データベース設定が必要です';
    if(health.mode==='unconfigured')setStatus('Supabaseの設定が必要です。採点データは保存されません。');
    renderArtwork();
  }catch(err){setStatus(`起動に失敗しました：${err.message}`);}
}
$('score').addEventListener('input',e=>{$('scoreText').textContent=e.target.value;});
$('revisedScore').addEventListener('input',e=>{$('revisedText').textContent=e.target.value;});
$('previous').addEventListener('click',()=>jump(index-1));
$('next').addEventListener('click',()=>jump(index+1));
$('reasonBtn').addEventListener('click',()=>{let open=$('reasonArea').classList.contains('hidden');show('reasonArea',open);$('reasonBtn').setAttribute('aria-expanded',String(open));});
$('rateBtn').addEventListener('click',openReveal);
$('skipReveal').addEventListener('click',()=>saveRating(false));
$('confirmReveal').addEventListener('click',()=>saveRating(true));
$('pairA').addEventListener('click',()=>votePair(0));
$('pairB').addEventListener('click',()=>votePair(1));
$('anotherPair').addEventListener('click',pickPair);
$('exportBtn').addEventListener('click',exportCSV);
$('homeBtn').addEventListener('click',()=>activate('gallery'));
document.querySelectorAll('.nav').forEach(btn=>btn.addEventListener('click',()=>activate(btn.dataset.view)));
init();
