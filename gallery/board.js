(() => {
  'use strict';
  const scenes=window.MATCHROOM_SCENES||[];
  const $=id=>document.getElementById(id);
  const gallery=$('gallery'), detail=$('detail');
  let references=[], selected=null, imageMode='reference', detailMode='reference', toastTimer;
  let favorites=[];
  try { favorites=JSON.parse(localStorage.getItem('matchroom-style-favorites')||'[]').filter(id=>scenes.some(s=>s.id===id)).slice(0,3); } catch {}
  const refFor=id=>references.find(item=>String(item.id).padStart(2,'0')===id)||{};
  const safeURL=value=>{try{const url=new URL(value,location.href);return /^https?:$/.test(url.protocol)?url.href:null;}catch{return null;}};
  const make=(tag,cls,text)=>{const element=document.createElement(tag);if(cls)element.className=cls;if(text!==undefined)element.textContent=text;return element;};
  function unavailable(title,description,cls='image-unavailable'){const wrap=make('div',cls);wrap.append(make('strong','',title),make('span','',description));return wrap;}
  function imageFor(ref,eager=false){
    const url=ref.image_url && safeURL(ref.image_url);
    if(!url)return unavailable('참고 화면 준비 중','실제 참고 이미지는 출처 확인 후 표시됩니다.');
    const img=make('img');img.src=url;img.alt=`실제 참고 화면 — ${ref.reference_name||ref.title_ko||'원본 출처'}`;img.loading=eager?'eager':'lazy';img.referrerPolicy='no-referrer';
    img.addEventListener('error',()=>img.replaceWith(unavailable('참고 이미지에 접근할 수 없습니다','상세에서 원본 출처를 열어 확인하세요.')),{once:true});
    return img;
  }
  function toast(message){$('toast').textContent=message;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2500);}
  function render(){
    const hash=location.hash.slice(1)||'all';
    const sheet=Number(/^sheet-([1-4])$/.exec(hash)?.[1]||0);
    document.body.classList.toggle('sheet-mode',!!sheet);
    document.querySelectorAll('[data-view]').forEach(a=>a.classList.toggle('active',a.dataset.view===hash||(hash==='favorites'&&a.dataset.view==='none')));
    $('favorites-view').classList.toggle('active',hash==='favorites');
    $('favorite-count').textContent=favorites.length;
    const prefix=imageMode==='reference'?'실제 참고 화면':'프로젝트 적용 구상 · 미구현';
    $('view-caption').textContent=`${prefix} · ${sheet?`${String((sheet-1)*5+1).padStart(2,'0')}–${String(sheet*5).padStart(2,'0')}`:hash==='favorites'?'선택한 방향':'전체'}`;
    $('view-note').textContent=imageMode==='reference'?'원본 제품·프로젝트 화면 · 출처는 각 상세에서 확인':'동일한 예시 · 수량 100 / 80 / 100 · 단가 10,000 / 10,800원';
    $('global-status').textContent=imageMode==='reference'?'실제 출처 화면':'스타일 구상 · 미구현';
    $('global-reference').setAttribute('aria-pressed',String(imageMode==='reference'));
    $('global-concept').setAttribute('aria-pressed',String(imageMode==='concept'));
    gallery.replaceChildren();
    const subset=sheet?scenes.slice((sheet-1)*5,sheet*5):hash==='favorites'?scenes.filter(s=>favorites.includes(s.id)):scenes;
    $('empty').hidden=subset.length>0;
    subset.forEach(scene=>{
      const ref=refFor(scene.id), card=make('article',`style-card ${imageMode==='reference'?'reference-card':''}`),button=make('button','open-card'),frame=make('div','scene-frame');
      const cardTitle=imageMode==='reference'?ref.title_ko||scene.title:scene.title;
      button.type='button';button.setAttribute('aria-label',`${scene.id} ${cardTitle} 상세 보기`);
      if(imageMode==='concept')frame.innerHTML=scene.svg;else frame.append(imageFor(ref,!!sheet));
      const caption=make('div','card-caption'), title=make('span','card-title');title.append(make('span','card-number',scene.id),make('span','',cardTitle));caption.append(title,make('span','card-status',imageMode==='reference'?'실제 출처':'구상 · 미구현'));
      button.append(frame,caption,make('p','card-reference',imageMode==='reference'?ref.reference_name||'원본 출처 확인 중':`Matchroom · ${scene.title}`));
      button.addEventListener('click',()=>openDetail(scene));card.append(button);
      if(favorites.includes(scene.id))card.append(make('span','favorite-badge','선택한 방향'));
      gallery.append(card);
    });
  }
  function renderDetail(){
    if(!selected)return;
    const ref=refFor(selected.id);
    $('detail-id').textContent=`DIRECTION ${selected.id} / ${detailMode==='concept'?'스타일 구상 · 미구현':'실제 참고 화면'}`;
    $('detail-title').textContent=detailMode==='reference'?ref.title_ko||selected.title:selected.title;
    $('concept-tab').setAttribute('aria-pressed',String(detailMode==='concept'));
    $('reference-tab').setAttribute('aria-pressed',String(detailMode==='reference'));
    const visual=$('detail-visual');visual.replaceChildren();
    if(detailMode==='concept')visual.innerHTML=selected.svg;else visual.append(imageFor(ref,true));
    $('adaptation').textContent=ref.matchroom_adaptation||selected.adaptation;
    $('interaction').textContent=ref.interaction_idea||selected.interaction;
    $('tradeoff').textContent=ref.tradeoff||selected.tradeoff;
    $('reference-name').textContent=ref.reference_name?`원본 참고작 · ${ref.reference_name}`:'원본 참고 정보 준비 중';
    const link=safeURL(ref.source_url||'');$('source-link').hidden=!ref.source_url||!link;if(link)$('source-link').href=link;
    $('evidence-note').textContent=detailMode==='concept'?'이 화면은 원본 참고작을 복제한 것이 아닌 Matchroom 적용 구상입니다. 제안한 조작·계산·업무는 아직 구현되지 않았습니다.':`원본 화면은 해당 제작자·프로젝트에 귀속됩니다. ${ref.evidence_status||'출처 정보 확인 중'}${ref.visual_description?' · '+ref.visual_description:''}`;
    $('choose-style').classList.toggle('chosen',favorites.includes(selected.id));$('choose-style').textContent=favorites.includes(selected.id)?'선택 해제':'이 방향 선택';
  }
  function openDetail(scene){selected=scene;detailMode=imageMode;renderDetail();detail.showModal();}
  $('close-detail').addEventListener('click',()=>detail.close());
  detail.addEventListener('click',e=>{if(e.target===detail){const rect=detail.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)detail.close();}});
  $('concept-tab').addEventListener('click',()=>{detailMode='concept';renderDetail();});
  $('reference-tab').addEventListener('click',()=>{detailMode='reference';renderDetail();});
  $('global-reference').addEventListener('click',()=>{imageMode='reference';render();});
  $('global-concept').addEventListener('click',()=>{imageMode='concept';render();});
  $('favorites-view').addEventListener('click',()=>{location.hash='favorites';});
  $('choose-style').addEventListener('click',()=>{
    if(!selected)return;
    if(favorites.includes(selected.id))favorites=favorites.filter(id=>id!==selected.id);
    else if(favorites.length>=3){toast('최대 3개까지 선택할 수 있습니다. 한 방향을 해제한 후 선택하세요.');return;}
    else favorites.push(selected.id);
    try{localStorage.setItem('matchroom-style-favorites',JSON.stringify(favorites));}catch{}
    render();renderDetail();
  });
  addEventListener('hashchange',()=>{render();window.scrollTo({top:0,behavior:'instant'});});
  render();
  fetch('./references.json',{cache:'no-store'}).then(res=>{if(!res.ok)throw new Error('metadata unavailable');return res.json();}).then(data=>{references=Array.isArray(data)?data:[];render();renderDetail();}).catch(()=>{references=[];render();});
  fetch('./github-baselines.json',{cache:'no-store'}).then(res=>{if(!res.ok)throw new Error('baselines unavailable');return res.json();}).then(data=>{
    if(!Array.isArray(data)||!data.length){$('github-baselines').hidden=true;return;}
    data.forEach(item=>{const card=make('article','baseline'),img=imageFor({...item,reference_name:item.title},false);card.append(img,make('h3','',item.title),make('p','',item.description));if(item.repo_url&&safeURL(item.repo_url)){const link=make('a','', 'GitHub 원본 열기 ↗');link.href=safeURL(item.repo_url);link.target='_blank';link.rel='noopener noreferrer';card.append(link);}$('baseline-grid').append(card);});
  }).catch(()=>{$('github-baselines').hidden=true;});
})();
