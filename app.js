const pages=[...document.querySelectorAll('.page')],navLinks=[...document.querySelectorAll('.nav-link')];
let lastScoreInput=null,lastNamingInput=null;
const compoundSurnames=['欧阳','司马','上官','诸葛','东方','皇甫','尉迟','公孙','慕容','司徒'];
const inferSurname=name=>compoundSurnames.includes(name.slice(0,2))?name.slice(0,2):name.slice(0,1);
const toNamingGender=value=>value==='男'?'boy':value==='女'?'girl':'neutral';
const toScoreGender=value=>value==='boy'?'男':value==='girl'?'女':'不限定';
function showPage(id){pages.forEach(p=>p.classList.toggle('active',p.id===id));navLinks.forEach(n=>n.classList.toggle('active',n.dataset.page===id));scrollTo({top:0,behavior:'smooth'});history.replaceState(null,'',`#${id}`)}
document.addEventListener('click',e=>{const target=e.target.closest('[data-page],[data-go]');if(target)showPage(target.dataset.page||target.dataset.go)});
const hash=location.hash.slice(1);if(pages.some(p=>p.id===hash))showPage(hash);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(path,payload,button){
  const old=button?.textContent;if(button){button.disabled=true;button.textContent='正在计算…'}
  try{
    const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const json=await response.json();if(!response.ok||!json.ok)throw new Error(json.error||'请求失败');return json.data;
  }catch(error){alert(error.message==='Failed to fetch'?'无法连接 Python 服务，请使用 python app.py 启动程序。':error.message);throw error}
  finally{if(button){button.disabled=false;button.textContent=old}}
}
function formObject(form){return Object.fromEntries(new FormData(form).entries())}

document.querySelector('#score-form').addEventListener('submit',async e=>{
  e.preventDefault();const button=e.submitter;lastScoreInput=formObject(e.target);
  try{const d=await api('/api/score',lastScoreInput,button),metrics=Object.entries(d.metrics);
    const counts=Object.entries(d.bazi.counts).map(([k,v])=>`${k}${v}`).join(' · '),missing=d.bazi.missing.length?d.bazi.missing.join('、'):'无';const target=document.querySelector('#score-result');target.className='card result';target.innerHTML=`<div class="score-head"><div class="score-ring"><div><b>${d.score}</b><small>/ 100</small></div></div><div><p class="eyebrow">综合评价</p><h3>${esc(d.name)} · ${esc(d.grade)}</h3><p>${esc(d.summary)}</p></div></div><div class="bazi-panel"><b>四柱八字</b><span>${d.bazi.pillars.map(esc).join('　')}</span><small>${esc(d.bazi.lunar_date)} · 日主属${d.bazi.day_master}</small><small>五行计数：${counts}　缺失：${missing}　规则：${esc(d.bazi.rule)}</small><small>姓名用字：${d.name_elements.join('、')}　数据源：${esc(d.bazi.calendar_source)}</small></div><div class="metrics">${metrics.map(([name,value])=>`<div class="metric"><b>${value}</b><small>${name}</small></div>`).join('')}</div><p class="analysis"><b>周易卦象：</b>${esc(d.trigram.name)}（上卦${d.trigram.upper}、下卦${d.trigram.lower}）</p><p class="analysis"><b>综合建议：</b>${esc(d.advice)}</p><button class="compare-button" data-action="to-naming">按此生辰智能起名 <span>→</span></button>`;
  }catch(_){}}
);

document.querySelector('#naming-form').addEventListener('submit',async e=>{
  e.preventDefault();lastNamingInput=formObject(e.target);try{const payload={...lastNamingInput,nonce:Date.now().toString()};const d=await api('/api/names',payload,e.submitter),target=document.querySelector('#naming-result');target.className='card result';const missing=d.bazi.missing.length?d.bazi.missing.join('、'):'无',counts=Object.entries(d.bazi.counts).map(([k,v])=>`<span><i>${k}</i><b>${v}</b></span>`).join('');target.innerHTML=`<div class="naming-analysis"><p class="eyebrow">生辰八字与五行分析</p><h3>${d.bazi.pillars.map(esc).join('　')}</h3><p class="lunar-date">${esc(d.bazi.lunar_date)} · 日主属${d.bazi.day_master} · 月令属${d.bazi.seasonal}</p><div class="element-counts">${counts}</div><div class="analysis-copy"><b>分析结论：五行缺失 ${missing}</b><p>${esc(d.strategy.analysis)}</p><small>起名规则：必补 ${d.strategy.required.length?d.strategy.required.join('、'):'无'} · 优先 ${d.strategy.recommended.join('、')} · 相生辅助 ${d.strategy.supporting.length?d.strategy.supporting.join('、'):'无'}</small></div></div><p class="eyebrow name-list-title">结合以上分析推荐十组名字</p><div class="name-grid">${d.names.map(n=>`<div class="name-item"><b>${esc(n.name)}</b><span>${n.score}</span><p>${esc(n.meaning)}</p><small>用字五行：${n.elements.join('、')} · ${esc(n.trigram)}</small><button class="name-score-link" data-action="score-name" data-score-name="${esc(n.name)}">查看评分 →</button></div>`).join('')}</div>`}catch(_){}
});

document.addEventListener('click',e=>{
  const action=e.target.closest('[data-action]');if(!action)return;
  if(action.dataset.action==='to-naming'&&lastScoreInput){
    const form=document.querySelector('#naming-form');form.elements.surname.value=inferSurname(lastScoreInput.name);form.elements.birth.value=lastScoreInput.birth;form.elements.birth_time.value=lastScoreInput.birth_time;form.elements.gender.value=toNamingGender(lastScoreInput.gender);showPage('naming');setTimeout(()=>form.requestSubmit(),80);
  }
  if(action.dataset.action==='score-name'&&lastNamingInput){
    const form=document.querySelector('#score-form');form.elements.name.value=action.dataset.scoreName;form.elements.birth.value=lastNamingInput.birth;form.elements.birth_time.value=lastNamingInput.birth_time;form.elements.gender.value=toScoreGender(lastNamingInput.gender);showPage('score');setTimeout(()=>form.requestSubmit(),80);
  }
});

document.querySelector('#population-form').addEventListener('submit',async e=>{
  e.preventDefault();try{const d=await api('/api/population',formObject(e.target),e.submitter);document.querySelector('#population-result').innerHTML=`<div class="risk-card card"><div class="risk-score ${d.level}"><b>${d.score}</b><small>/ 100</small></div><div class="risk-summary"><p class="eyebrow">“${esc(d.name)}”的重名风险</p><h3>${esc(d.label)}</h3><p>模型置信度：${esc(d.confidence)} · ${esc(d.method)}</p></div><div class="risk-signals">${d.signals.map(s=>`<p><span>✓</span>${esc(s)}</p>`).join('')}</div><small class="risk-disclaimer">${esc(d.disclaimer)}</small></div>`}catch(_){}
});
