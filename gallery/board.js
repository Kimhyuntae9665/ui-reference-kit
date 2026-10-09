(() => {
  'use strict';
  const scenes=window.MATCHROOM_SCENES||[], defaults=window.MATCHROOM_SELECTED_IDS||[];
  const $=id=>document.getElementById(id), gallery=$('gallery'), detail=$('detail');
  const idFor=id=>String(id).padStart(2,'0');
  let references=[], selected=null, imageMode='reference', detailMode='reference', category='all', toastTimer, metadataError=false;
  let favorites=defaults.map(idFor);
  try { const saved=JSON.parse(localStorage.getItem('matchroom-style-favorites'));if(Array.isArray(saved))favorites=saved.map(idFor); } catch {}
  favorites=[...new Set(favorites)].filter(id=>scenes.some(scene=>idFor(scene.id)===id)).slice(0,3);
  const refFor=id=>references.find(item=>idFor(item.id)===idFor(id))||{};
  const referenceLabel=ref=>ref.reference_kind==='historical_documented_prototype'?'공식 연구 개념도':'실제 참고 화면';
  const referenceKindLabel=value=>({historical_documented_prototype:'공식 연구 개념도 · 문서에 기록된 프로토타입',live_browser_screenshot:'브라우저에서 확인한 실제 화면'})[value]||value;
  const safeURL=value=>{try{const url=new URL(value,location.href);return /^(https?:|file:)$/.test(url.protocol)?url.href:null;}catch{return null;}};
  const make=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
  function unavailable(title,description,cls='image-unavailable'){const wrap=make('div',cls);wrap.append(make('strong','',title),make('span','',description));return wrap;}
  function imageFor(ref,eager=false){
    const url=ref.image_url&&safeURL(ref.image_url);
    if(!url)return unavailable('참고 화면을 표시할 수 없습니다',metadataError?'로컬 서버에서 갤러리를 열고 메타데이터 파일을 확인하세요.':'출처 메타데이터를 불러오는 중입니다.');
    const img=make('img');img.src=url;img.alt=`${referenceLabel(ref)} — ${ref.reference_name||ref.title_ko||'원본 출처'}`;img.loading=eager?'eager':'lazy';img.referrerPolicy='no-referrer';
    img.addEventListener('error',()=>img.replaceWith(unavailable('참고 이미지에 접근할 수 없습니다','상세에서 원본 출처를 확인하세요.')),{once:true});return img;
  }
  function toast(message){$('toast').textContent=message;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2500);}
  function filtered(){return scenes.filter(scene=>category==='all'||refFor(scene.id).category===category);}
  function navigation(items,newScope){
    const pages=Math.ceil(items.length/5), nav=$('sheet-links');nav.replaceChildren();
    for(let page=1;page<=pages;page++){const start=items[(page-1)*5],end=items[Math.min(page*5,items.length)-1],view=`${newScope?'new-':''}sheet-${page}`;const link=make('a','',`${idFor(start.id)}–${idFor(end.id)}`);link.href=`#${view}`;link.dataset.view=view;nav.append(link);}
  }
  function render(){
    const hash=location.hash.slice(1)||'all', sheet=Number(/^(?:new-)?sheet-(\d+)$/.exec(hash)?.[1]||0), newScope=hash==='new'||/^new-sheet-\d+$/.test(hash), items=filtered().filter(scene=>!newScope||Number(scene.id)>20);
    navigation(items,newScope);
    document.body.classList.toggle('sheet-mode',sheet>0);
    document.querySelectorAll('[data-view]').forEach(link=>link.classList.toggle('active',link.dataset.view===hash||(newScope&&link.dataset.view==='new')));
    $('favorites-view').classList.toggle('active',hash==='favorites');$('favorite-count').textContent=favorites.length;
    const subset=sheet?items.slice((sheet-1)*5,sheet*5):hash==='favorites'?items.filter(scene=>favorites.includes(idFor(scene.id))):hash==='new'||hash==='all'?items:[];
    const prefix=imageMode==='reference'?'출처 참고 자료':'프로젝트 적용 구상 · 미구현';
    const scope=sheet?(subset.length?`${idFor(subset[0].id)}–${idFor(subset[subset.length-1].id)} / ${newScope?'추가 ':''}${items.length}`:'비어 있는 묶음'):hash==='favorites'?'선택한 방향':hash==='new'?'추가 후보':'전체';
    $('view-caption').textContent=`${prefix} · ${scope} · ${subset.length}개`;
    $('view-note').textContent=metadataError?'메타데이터를 불러오지 못했습니다. 로컬 서버 실행 경로를 확인하세요.':imageMode==='reference'?'원본 제품·프로젝트 화면 · 출처는 각 상세에서 확인':'합성 업무 예시로 만든 구성 시안 · 조작·계산 미구현';
    $('global-status').textContent=imageMode==='reference'?'출처 참고 자료':'스타일 구상 · 미구현';
    $('global-reference').setAttribute('aria-pressed',String(imageMode==='reference'));$('global-concept').setAttribute('aria-pressed',String(imageMode==='concept'));
    gallery.replaceChildren();$('empty').hidden=subset.length>0;
    $('empty').textContent=hash==='favorites'?'선택한 방향이 없습니다. 상세에서 최대 3개를 선택하세요.':'이 보기에는 후보가 없습니다. 전체 또는 다른 분류를 선택하세요.';
    subset.forEach(scene=>{
      const ref=refFor(scene.id), id=idFor(scene.id), card=make('article',`style-card ${imageMode==='reference'?'reference-card':''}`), button=make('button','open-card'), frame=make('div','scene-frame');
      const title=imageMode==='reference'?ref.title_ko||scene.title:scene.title;button.type='button';button.setAttribute('aria-label',`${id} ${title} 상세 보기`);
      if(imageMode==='concept')frame.innerHTML=scene.svg;else frame.append(imageFor(ref,sheet>0));
      const caption=make('div','card-caption'), name=make('span','card-title');name.append(make('span','card-number',id),make('span','',title));caption.append(name,make('span','card-status',imageMode==='reference'?referenceLabel(ref):'구상 · 미구현'));
      button.append(frame,caption,make('p','card-reference',imageMode==='reference'?ref.reference_name||'출처 불러오는 중':`적용 구상 · ${scene.title}`));button.addEventListener('click',()=>{selected=scene;detailMode=imageMode;renderDetail();detail.showModal();});card.append(button);
      if(favorites.includes(id))card.append(make('span','favorite-badge','선택한 방향'));gallery.append(card);
    });
  }
  function renderDetail(){
    if(!selected)return;const ref=refFor(selected.id), id=idFor(selected.id);
    $('detail-id').textContent=`DIRECTION ${id} / ${detailMode==='concept'?'스타일 구상 · 미구현':referenceLabel(ref)}`;$('detail-title').textContent=detailMode==='reference'?ref.title_ko||selected.title:selected.title;
    $('reference-tab').textContent=referenceLabel(ref)+' 보기';
    $('concept-tab').setAttribute('aria-pressed',String(detailMode==='concept'));$('reference-tab').setAttribute('aria-pressed',String(detailMode==='reference'));
    $('detail-visual').replaceChildren();if(detailMode==='concept')$('detail-visual').innerHTML=selected.svg;else $('detail-visual').append(imageFor(ref,true));
    ['visual_principle','suitable_tasks','reuse_rule','differentiation_from_existing','methodology_name','interaction_verified','reference_kind','discovery_path'].forEach(field=>{
      const value=ref[field], present=value!==undefined&&value!==null&&value!=='';
      $(field).textContent=field==='reference_kind'?referenceKindLabel(value):field==='interaction_verified'&&typeof value==='boolean'?(value?'조작 확인됨':'조작 미확인'):value||'';$(field+'-block').hidden=!present;
    });
    $('adaptation').textContent=ref.matchroom_adaptation||selected.adaptation||'';$('interaction').textContent=ref.interaction_idea||selected.interaction||'';$('tradeoff').textContent=ref.tradeoff||selected.tradeoff||'';
    $('reference-name').textContent=ref.reference_name?`원본 참고작 · ${ref.reference_name}`:'원본 참고 정보 준비 중';
    const link=safeURL(ref.source_url||'');$('source-link').hidden=!ref.source_url||!link;if(link)$('source-link').href=link;
    $('evidence-note').textContent=detailMode==='concept'?'합성 업무 예시를 이용한 미구현 적용 구상입니다. 제안한 조작·계산·업무는 실행 증거가 아닙니다.':`원본 화면은 해당 제작자·프로젝트에 귀속됩니다. ${ref.evidence_status||'출처 정보 확인 중'} · ${ref.visual_description||''}`;
    $('choose-style').classList.toggle('chosen',favorites.includes(id));$('choose-style').textContent=favorites.includes(id)?'선택 해제':'이 방향 선택';
  }
  $('close-detail').addEventListener('click',()=>detail.close());
  detail.addEventListener('click',event=>{if(event.target===detail){const rect=detail.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)detail.close();}});
  $('concept-tab').addEventListener('click',()=>{detailMode='concept';renderDetail();});$('reference-tab').addEventListener('click',()=>{detailMode='reference';renderDetail();});
  $('global-reference').addEventListener('click',()=>{imageMode='reference';render();});$('global-concept').addEventListener('click',()=>{imageMode='concept';render();});
  $('favorites-view').addEventListener('click',()=>{location.hash='favorites';});
  $('category-filter').addEventListener('change',event=>{category=event.target.value;location.hash='all';render();});
  $('choose-style').addEventListener('click',()=>{
    if(!selected)return;const id=idFor(selected.id);
    if(favorites.includes(id))favorites=favorites.filter(value=>value!==id);else if(favorites.length>=3){toast('최대 3개까지 선택할 수 있습니다. 한 방향을 해제한 후 선택하세요.');return;}else favorites.push(id);
    try{localStorage.setItem('matchroom-style-favorites',JSON.stringify(favorites));}catch{toast('선택은 현재 창에서 유지됩니다. 브라우저 저장소를 사용할 수 없습니다.');}render();renderDetail();
  });
  addEventListener('hashchange',()=>{render();window.scrollTo({top:0,behavior:'instant'});});render();
  fetch('./references.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('metadata unavailable');return response.json();}).then(data=>{if(!Array.isArray(data)||data.length!==scenes.length)throw new Error('metadata mismatch');references=data;render();renderDetail();}).catch(()=>{metadataError=true;render();renderDetail();});
  fetch('./github-baselines.json',{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('baselines unavailable');return response.json();}).then(data=>{
    if(!Array.isArray(data)||!data.length){$('github-baselines').hidden=true;return;}data.forEach(item=>{const card=make('article','baseline');card.append(imageFor({...item,reference_name:item.title}),make('h3','',item.title),make('p','',item.description));if(item.repo_url&&safeURL(item.repo_url)){const link=make('a','','GitHub 원본 열기 ↗');link.href=safeURL(item.repo_url);link.target='_blank';link.rel='noopener noreferrer';card.append(link);}$('baseline-grid').append(card);});
  }).catch(()=>{$('github-baselines').hidden=true;});
})();
