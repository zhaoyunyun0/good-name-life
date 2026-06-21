const pages=[...document.querySelectorAll('.page')],navLinks=[...document.querySelectorAll('.nav-link')];
let lastScoreInput=null,lastNamingInput=null,generatedCandidates=new Map(),aiStatus={enabled:false,message:'AI 状态检查中'};
const compoundSurnames=['欧阳','司马','上官','诸葛','东方','皇甫','尉迟','公孙','慕容','司徒'];
const inferSurname=name=>compoundSurnames.includes(name.slice(0,2))?name.slice(0,2):name.slice(0,1);
const toNamingGender=value=>value==='男'?'boy':value==='女'?'girl':'neutral';
const toScoreGender=value=>value==='boy'?'男':value==='girl'?'女':'不限定';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const historyToggle=document.querySelector('#history-consent');
historyToggle.checked=localStorage.getItem('shiming-history-consent')==='true';
historyToggle.addEventListener('change',()=>localStorage.setItem('shiming-history-consent',String(historyToggle.checked)));

function showPage(id){pages.forEach(p=>p.classList.toggle('active',p.id===id));navLinks.forEach(n=>n.classList.toggle('active',n.dataset.page===id));scrollTo({top:0,behavior:'smooth'});history.replaceState(null,'',`#${id}`)}
document.addEventListener('click',e=>{const target=e.target.closest('[data-page],[data-go]');if(target)showPage(target.dataset.page||target.dataset.go)});
const hash=location.hash.slice(1);if(pages.some(p=>p.id===hash))showPage(hash);
fetch('/api/ai/status').then(r=>r.json()).then(r=>{if(r.ok){aiStatus=r.data;const banner=document.querySelector('#ai-status-banner');banner.className=`ai-status-banner ${aiStatus.enabled?'enabled':'disabled'}`;banner.textContent=aiStatus.enabled?`${aiStatus.provider} · ${aiStatus.model} · 服务可用`:aiStatus.message}}).catch(()=>{});

async function api(path,payload,button,extraHeaders={}){
  const old=button?.textContent;if(button){button.disabled=true;button.textContent='正在计算…'}
  try{
    const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Store-History':String(historyToggle.checked),...extraHeaders},body:JSON.stringify(payload)});
    const json=await response.json();if(!response.ok||!json.ok)throw new Error(json.error||'请求失败');return json.data;
  }catch(error){alert(error.message==='Failed to fetch'?'无法连接 Python 服务，请使用 python app.py 启动程序。':error.message);throw error}
  finally{if(button){button.disabled=false;button.textContent=old}}
}
const formObject=form=>Object.fromEntries(new FormData(form).entries());

document.querySelector('#score-form').addEventListener('submit',async e=>{
  e.preventDefault();const button=e.submitter;lastScoreInput=formObject(e.target);
  try{
    const d=await api('/api/score',lastScoreInput,button),metrics=Object.entries(d.metrics);
    const counts=Object.entries(d.bazi.counts).map(([k,v])=>`${k}${v}`).join(' · '),missing=d.bazi.missing.length?d.bazi.missing.join('、'):'无';
    const sources=Object.entries(d.calculation.character_sources).map(([char,source])=>`${char}：${source}`).join('；');
    const target=document.querySelector('#score-result');target.className='card result';target.innerHTML=`<div class="score-head"><div class="score-ring"><div><b>${d.score}</b><small>/ 100</small></div></div><div><p class="eyebrow">综合评价</p><h3>${esc(d.name)} · ${esc(d.grade)}</h3><p>${esc(d.summary)}</p></div></div><div class="bazi-panel"><b>四柱八字</b><span>${d.bazi.pillars.map(esc).join('　')}</span><small>${esc(d.bazi.lunar_date)} · 日主属${d.bazi.day_master}</small><small>五行计数：${counts}　缺失：${missing}</small><small>规则：${esc(d.bazi.rule)} · 评分版本：${esc(d.calculation.score_version)}</small><small>字库来源：${esc(sources)}</small></div><div class="metrics">${metrics.map(([name,value])=>`<div class="metric"><b>${value}</b><small>${name}</small></div>`).join('')}</div><p class="analysis"><b>周易卦象：</b>${esc(d.trigram.name)}（上卦${d.trigram.upper}、下卦${d.trigram.lower}）</p><p class="analysis"><b>综合建议：</b>${esc(d.advice)}</p><div class="result-actions"><button class="compare-button" data-action="to-naming">按此生辰智能起名 <span>→</span></button><button class="compare-button dark" data-action="to-ai-score">进入 AI 姓名顾问 <span>→</span></button></div>`;
  }catch(_){}
});

document.querySelector('#naming-form').addEventListener('submit',async e=>{
  e.preventDefault();lastNamingInput=formObject(e.target);
  try{
    const payload={...lastNamingInput,nonce:Date.now().toString()},d=await api('/api/names',payload,e.submitter),target=document.querySelector('#naming-result');
    generatedCandidates=new Map(d.names.map(item=>[item.name,item]));target.className='card result';
    const missing=d.bazi.missing.length?d.bazi.missing.join('、'):'无',counts=Object.entries(d.bazi.counts).map(([k,v])=>`<span><i>${k}</i><b>${v}</b></span>`).join('');
    target.innerHTML=`<div class="naming-analysis"><p class="eyebrow">生辰八字与五行分析</p><h3>${d.bazi.pillars.map(esc).join('　')}</h3><p class="lunar-date">${esc(d.bazi.lunar_date)} · 日主属${d.bazi.day_master} · 月令属${d.bazi.seasonal}</p><div class="element-counts">${counts}</div><div class="analysis-copy"><b>分析结论：五行缺失 ${missing}</b><p>${esc(d.strategy.analysis)}</p><small>规则：${esc(d.bazi.rule)} · 评分：${esc(d.strategy.score_version)} · 优先：${d.strategy.recommended.join('、')}</small><small class="source-line">姓名语料：${esc(d.strategy.corpus_source)}</small></div></div><p class="eyebrow name-list-title">结合以上分析推荐十组名字</p><div class="name-grid">${d.names.map(n=>`<div class="name-item"><b>${esc(n.name)}</b><span>${n.score}</span><p>${esc(n.meaning)}</p><small>用字五行：${n.elements.join('、')} · ${esc(n.trigram)}</small>${n.ambiguity_warnings.length?`<small class="warning-line">歧义提示：${n.ambiguity_warnings.map(esc).join('、')}</small>`:''}<div class="name-actions"><button class="name-score-link" data-action="score-name" data-score-name="${esc(n.name)}">查看评分 →</button><button class="name-score-link" data-action="favorite-name" data-score-name="${esc(n.name)}">＋ 收藏</button><button class="name-score-link" data-action="to-ai-candidate" data-score-name="${esc(n.name)}">AI 顾问 →</button></div></div>`).join('')}</div>`;
  }catch(_){}
});

document.querySelector('#ai-form').addEventListener('submit',async e=>{
  e.preventDefault();const input=formObject(e.target),target=document.querySelector('#ai-page-result');target.classList.remove('empty');await runAiAnalysis(input.name,input,e.submitter,target);
});

function getFavorites(){try{return JSON.parse(localStorage.getItem('shiming-favorites')||'[]')}catch(_){return[]}}
function setFavorites(items){localStorage.setItem('shiming-favorites',JSON.stringify(items));renderFavorites()}
function renderFavorites(){
  const items=getFavorites(),target=document.querySelector('#favorites-grid');
  if(!items.length){target.innerHTML='<p class="favorites-empty">尚未收藏候选名字。</p>';return}
  target.innerHTML=items.map(item=>`<article><b>${esc(item.name)}</b><span>${item.score}分</span><p>${esc(item.meaning)}</p><small>${item.elements.join('、')} · ${esc(item.input.birth)} · ${esc(item.input.birth_time)}</small><button data-action="remove-favorite" data-favorite-id="${esc(item.id)}">移除</button></article>`).join('');
}
renderFavorites();

function ensureAiConsent(){
  if(localStorage.getItem('shiming-ai-consent')==='true')return true;
  const accepted=confirm('AI 语义体检会把当前姓名、四柱、五行计数和评分发送给模型服务。不会发送公历生日原值和精确出生时间。AI 结果仅供语言与文化语境参考。是否继续？');
  if(accepted)localStorage.setItem('shiming-ai-consent','true');return accepted;
}
function renderAiAnalysis(target,d){
  const a=d.analysis,riskLabel={low:'低',medium:'中',high:'高'}[a.risk_level]||a.risk_level;
  target.innerHTML=`<div class="ai-analysis-head"><b>${esc(d.name)} · AI 辅助分析</b><span class="ai-risk ${a.risk_level}">歧义风险 ${riskLabel}</span></div><p class="ai-summary">${esc(a.summary)}</p><div class="ai-analysis-grid"><article><b>整体语义</b><p>${esc(a.semantic_analysis)}</p></article><article><b>文化意象</b><p>${esc(a.cultural_imagery)}</p></article><article><b>读音体验</b><p>${esc(a.pronunciation_review)}</p></article><article><b>气质与时代感</b><p>${a.style_tags.map(esc).join(' · ')}；${esc(a.era_impression)}</p></article></div>${a.risk_items.length?`<div class="ai-warnings"><b>谐音与歧义提示</b>${a.risk_items.map(item=>`<p>${esc(item.description)} <small>置信度：${esc(item.confidence)}</small></p>`).join('')}</div>`:'<p class="ai-safe">未发现需要特别提示的常见谐音歧义。</p>'}${a.source_notes.length?`<p class="ai-notes">来源说明：${a.source_notes.map(esc).join('；')}</p>`:''}${a.warnings.length?`<p class="ai-notes">注意：${a.warnings.map(esc).join('；')}</p>`:''}<small class="ai-disclaimer">${esc(d.disclaimer)} · ${esc(d.meta.provider)} · ${esc(d.meta.model)}</small>`;
}
async function runAiAnalysis(name,input,button,target){
  if(!aiStatus.enabled){alert(aiStatus.message);return}
  if(!ensureAiConsent())return;
  try{target.classList.remove('empty');target.innerHTML='<p class="ai-loading">AI 正在分析语义与常见语境…</p>';const d=await api('/api/ai/analyze',{...input,name},button,{'X-AI-Consent':'true'});renderAiAnalysis(target,d)}catch(_){target.innerHTML='<p class="ai-loading">分析未完成，请检查 AI 配置后重试。</p>'}
}

document.addEventListener('click',e=>{
  const action=e.target.closest('[data-action]');if(!action)return;
  if(action.dataset.action==='to-naming'&&lastScoreInput){
    const form=document.querySelector('#naming-form');form.elements.surname.value=inferSurname(lastScoreInput.name);form.elements.birth.value=lastScoreInput.birth;form.elements.birth_time.value=lastScoreInput.birth_time;form.elements.gender.value=toNamingGender(lastScoreInput.gender);form.elements.rule_version.value=lastScoreInput.rule_version;form.elements.score_version.value=lastScoreInput.score_version;showPage('naming');setTimeout(()=>form.requestSubmit(),80);
  }
  if(action.dataset.action==='score-name'&&lastNamingInput){
    const form=document.querySelector('#score-form');form.elements.name.value=action.dataset.scoreName;form.elements.birth.value=lastNamingInput.birth;form.elements.birth_time.value=lastNamingInput.birth_time;form.elements.gender.value=toScoreGender(lastNamingInput.gender);form.elements.rule_version.value=lastNamingInput.rule_version;form.elements.score_version.value=lastNamingInput.score_version;showPage('score');setTimeout(()=>form.requestSubmit(),80);
  }
  if(action.dataset.action==='favorite-name'&&lastNamingInput){
    const item=generatedCandidates.get(action.dataset.scoreName);if(!item)return;const items=getFavorites(),id=[item.name,lastNamingInput.birth,lastNamingInput.birth_time,lastNamingInput.rule_version,lastNamingInput.score_version].join('|');if(!items.some(x=>x.id===id))items.push({...item,id,input:lastNamingInput});setFavorites(items);action.textContent='✓ 已收藏';
  }
  if(action.dataset.action==='remove-favorite')setFavorites(getFavorites().filter(item=>item.id!==action.dataset.favoriteId));
  if(action.dataset.action==='export-favorites'){
    const blob=new Blob([JSON.stringify({product:'拾名',exported_at:new Date().toISOString(),candidates:getFavorites()},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='拾名候选报告.json';a.click();URL.revokeObjectURL(url);
  }
  if(action.dataset.action==='print-report')window.print();
  if(action.dataset.action==='to-ai-score'&&lastScoreInput){const form=document.querySelector('#ai-form');form.elements.name.value=lastScoreInput.name;form.elements.birth.value=lastScoreInput.birth;form.elements.birth_time.value=lastScoreInput.birth_time;form.elements.gender.value=lastScoreInput.gender;form.elements.rule_version.value=lastScoreInput.rule_version;form.elements.score_version.value=lastScoreInput.score_version;showPage('ai');if(aiStatus.enabled)setTimeout(()=>form.requestSubmit(),80)}
  if(action.dataset.action==='to-ai-candidate'&&lastNamingInput){const form=document.querySelector('#ai-form');form.elements.name.value=action.dataset.scoreName;form.elements.birth.value=lastNamingInput.birth;form.elements.birth_time.value=lastNamingInput.birth_time;form.elements.gender.value=toScoreGender(lastNamingInput.gender);form.elements.rule_version.value=lastNamingInput.rule_version;form.elements.score_version.value=lastNamingInput.score_version;showPage('ai');if(aiStatus.enabled)setTimeout(()=>form.requestSubmit(),80)}
});

document.querySelector('#population-form').addEventListener('submit',async e=>{
  e.preventDefault();try{
    const d=await api('/api/population',formObject(e.target),e.submitter),target=document.querySelector('#population-result');
    if(d.mode==='official')target.innerHTML=`<div class="risk-card card"><div class="risk-score low"><b>${d.total.toLocaleString()}</b><small>真实同名人数</small></div><div class="risk-summary"><p class="eyebrow">授权数据查询</p><h3>${esc(d.name)}</h3><p>男 ${d.male.toLocaleString()} · 女 ${d.female.toLocaleString()}</p></div><small class="risk-disclaimer">来源：${esc(d.source)} · 查询时间：${esc(d.queried_at)}</small></div>`;
    else target.innerHTML=`<div class="risk-card card"><div class="risk-score ${d.level}"><b>${d.score}</b><small>/ 100</small></div><div class="risk-summary"><p class="eyebrow">“${esc(d.name)}”的重名风险</p><h3>${esc(d.label)}</h3><p>模型置信度：${esc(d.confidence)} · ${esc(d.method)}</p></div><div class="risk-signals">${d.signals.map(s=>`<p><span>✓</span>${esc(s)}</p>`).join('')}</div><small class="risk-disclaimer">${esc(d.disclaimer)}</small></div>`;
  }catch(_){}
});
