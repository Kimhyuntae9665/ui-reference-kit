"""Build local reference documents from manifest.json and scenes.json (stdlib only).

Reference captures and individual concept SVG files are source assets: never written here.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BOOK_CSS = '''*{box-sizing:border-box}body{margin:0;background:#edf0f2;color:#27333c;font:15px/1.7 "Malgun Gothic",Segoe UI,sans-serif}header,main{max-width:1220px;margin:auto;padding:30px 24px}header{padding-bottom:14px}h1{font-size:30px;line-height:1.3;margin:7px 0 18px}.eyebrow,.number{color:#3b6b70;font-weight:700}.links,nav{display:flex;gap:12px;flex-wrap:wrap}a{color:#315e7a}nav{position:sticky;top:0;background:#edf0f2ed;padding:12px 0;z-index:1}button{border:1px solid #aab6bc;background:white;padding:8px 13px;cursor:pointer;color:#27333c}button[aria-pressed=true]{background:#284e55;color:white}#count{margin-left:auto}#cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:white;border:1px solid #aab6bc;padding:20px;scroll-margin-top:90px;min-width:0}.card-head{display:flex;gap:14px;align-items:flex-start}h2{margin:0;font-size:20px}.card-head p{font-size:12px;margin:4px 0 14px}.number{font-size:25px}.tag{font-size:11px;white-space:nowrap;margin-left:auto;background:#edf2f2;padding:4px 8px}.visual{border:1px solid #73848e;background:#f4f6f7;padding:8px}.visual img{width:100%;height:auto;display:block}.caption{font-size:12px;color:#536370;margin:7px 0 16px}dt{font-size:12px;font-weight:700;color:#536370;margin-top:11px}dd{margin:1px 0 0}details{border-top:1px solid #d6dfe2;padding-top:14px;margin-top:18px}summary{cursor:pointer;color:#315e7a}details .visual{margin-top:12px}.note{font-size:12px}.selected-summary{border-left:4px solid #527a79;background:white;padding:14px 20px}footer{padding:30px 0;font-size:12px}[hidden]{display:none!important}@media(max-width:850px){#cards{grid-template-columns:1fr}header,main{padding:20px 16px}h1{font-size:25px}}@media print{nav,.links{display:none}#cards{display:block}article{break-inside:avoid;margin-bottom:20px}}'''

BOOK_JS = '''const articles=[...document.querySelectorAll('#cards article')];
document.querySelectorAll('[data-filter]').forEach(button=>button.onclick=()=>{
  document.querySelectorAll('[data-filter]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
  let count=0;articles.forEach(article=>{
    const filter=button.dataset.filter;
    const show=filter==='all'||(filter==='selected'?article.dataset.selected==='true':filter==='new'?Number(article.dataset.id)>20:article.dataset.category===filter);
    article.hidden=!show;if(show)count++;
  });document.querySelector('#count').textContent=count+'개';document.querySelector('#empty').hidden=count>0;
});'''

BOARD_JS = r'''(() => {
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
})();'''


def escaped(value):
    return html.escape(str(value), quote=True)


def field_text(field, value):
    if field == 'interaction_verified' and isinstance(value, bool):
        return '조작 확인됨' if value else '조작 미확인'
    if field == 'reference_kind':
        return {'historical_documented_prototype': '공식 연구 개념도 · 문서에 기록된 프로토타입',
                'live_browser_screenshot': '브라우저에서 확인한 실제 화면'}.get(value, str(value))
    return str(value)


def reference_label(candidate):
    return '공식 연구 개념도' if candidate.get('reference_kind') == 'historical_documented_prototype' else '실제 참고 화면'


def write(relative, text):
    (ROOT / relative).write_text(text + '\n', encoding='utf-8')


def note(candidate, prefix=''):
    c = candidate
    ident = f"{c['id']:02d}"
    label = reference_label(c)
    lines = [f"# {ident} · {c['title_ko']}", '', f'## {label}', '',
             f"![{ident} {label}]({prefix}{c['local_reference_image']})", '',
             f"- 원작: {c['reference_name']}", f"- [원본 출처]({c['source_url']})",
             f"- 이미지 유형: {c.get('snapshot_type', 'browser_render_screenshot')} · {c.get('snapshot_date', '')} 보존."]
    for label, field in [('분류', 'category'), ('화면 설명', 'visual_description'), ('시각 원리', 'visual_principle'),
                         ('어울리는 업무', 'suitable_tasks'), ('재사용 기준', 'reuse_rule'),
                         ('기존 후보와의 차이', 'differentiation_from_existing'), ('방법 이름', 'methodology_name'),
                         ('조작 확인', 'interaction_verified'), ('참고 유형', 'reference_kind'),
                         ('발견 경로', 'discovery_path'), ('원본 확인 기록', 'evidence_status')]:
        if field in c and c[field] is not None and c[field] != '':
            lines.append(f"- {label}: {field_text(field, c[field])}")
    lines += ['', '## 프로젝트 적용 시안 — 미구현', '',
              f"![{ident} 적용 시안 · 미구현]({prefix}{c['local_concept_image']})", '',
              f"- 적용 방향: {c['matchroom_adaptation']}", f"- 조작 아이디어: {c['interaction_idea']}",
              f"- 선택 시 고려할 점: {c['tradeoff']}", '',
              '이 SVG는 합성 업무 예시를 비교하기 위한 구성 시안입니다. 실제 조작·계산이 가능한 구현 화면으로 인용하지 않습니다. '
              f"현재 구현 상태는 [DECISIONS.md]({prefix}DECISIONS.md)를 확인하세요."]
    return '\n'.join(lines)


def card(c, selected):
    ident = f"{c['id']:02d}"
    label = reference_label(c)
    badge = c['category'] + (' · ' + label if c.get('reference_kind') == 'historical_documented_prototype' else '')
    fields = [('화면 설명', 'visual_description'), ('시각 원리', 'visual_principle'), ('어울리는 업무', 'suitable_tasks'),
              ('재사용 기준', 'reuse_rule'), ('기존 후보와의 차이', 'differentiation_from_existing'),
              ('방법 이름', 'methodology_name'), ('조작 확인', 'interaction_verified'),
              ('참고 유형', 'reference_kind'), ('발견 경로', 'discovery_path'),
              ('프로젝트 적용', 'matchroom_adaptation'), ('조작 아이디어', 'interaction_idea'),
              ('주의점', 'tradeoff'), ('원본 확인 기록', 'evidence_status')]
    definitions = ''.join(f'<dt>{label}</dt><dd>{escaped(field_text(field, c[field]))}</dd>' for label, field in fields if field in c and c[field] is not None and c[field] != '')
    return f'''<article id="ui-{ident}" data-id="{c['id']}" data-category="{escaped(c['category'])}" data-selected="{str(c['id'] in selected).lower()}"><div class="card-head"><span class="number">{ident}</span><div><h2>{escaped(c['title_ko'])}</h2><p>{escaped(c['reference_name'])}</p></div><span class="tag">{escaped(badge)}</span></div><div class="visual"><a href="{escaped(c['local_reference_image'])}" target="_blank"><img src="{escaped(c['local_reference_image'])}" alt="{ident} {escaped(label)}" loading="lazy"></a></div><p class="caption">{escaped(label)} · {escaped(c.get('snapshot_date', ''))} / <a href="{escaped(c['source_url'])}" target="_blank" rel="noopener noreferrer">원본 출처 ↗</a></p><dl>{definitions}</dl><details><summary>프로젝트 적용 시안 보기 · 미구현</summary><div class="visual"><img src="{escaped(c['local_concept_image'])}" alt="{ident} 적용 시안 · 미구현" loading="lazy"></div><p class="caption">합성 업무 예시를 이용한 SVG 구성 시안. 실행 증거가 아닙니다.</p></details><a class="note" href="candidates/{ident}.md">후보 설명 Markdown</a></article>'''


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    scenes = json.loads((ROOT / 'scenes.json').read_text(encoding='utf-8'))
    candidates = sorted(manifest['candidates'], key=lambda c: c['id'])
    ids = [c['id'] for c in candidates]
    assert len(ids) == len(set(ids)), 'Duplicate candidate IDs'
    assert set(ids) == {int(scene['id']) for scene in scenes}, 'Candidate / scene ID mismatch'
    assert len(ids) == manifest['reference_count'] == manifest['concept_count'], 'Update manifest counts before building'
    selected = manifest['selected_ids']
    categories = list(dict.fromkeys(c['category'] for c in candidates))
    count, new_count = len(ids), sum(ident > 20 for ident in ids)
    for c in candidates:
        write(f"candidates/{c['id']:02d}.md", note(c, '../'))
    intro = f"{manifest['date']}. 디자인 선택 자료이며 지원용 포트폴리오가 아닙니다. 실제 화면·공식 연구 개념도·미구현 시안·최종 구현 화면을 구분합니다."
    write('CATALOG.md', f'# UI 참고 사례 {count}개 — 이미지와 설명\n\n{intro}\n\n---\n\n' + '\n\n---\n\n'.join(note(c) for c in candidates))
    source_lines = ['# 참고 사례의 원작과 출처', '', f"확인 기준일: {manifest['date']}. {count}개 후보의 확인 수준은 개별 문서에 기록합니다. 이미지 재사용 조건은 [NOTICE.md](NOTICE.md)를 함께 읽어주세요.", '', '| 번호 | 원작 | 원본 페이지 | 분석 |', '| --- | --- | --- | --- |']
    for c in candidates:
        source_lines.append(f"| {c['id']:02d} | {c['reference_name'].replace('|', '/')} | [원본]({c['source_url']}) | [사진·설명](candidates/{c['id']:02d}.md) |")
    write('SOURCES.md', '\n'.join(source_lines))
    buttons = [('all', '전체'), ('selected', f'기존 선택 {len(selected)}개'), ('new', f'추가 후보 {new_count}개')] + [(category, category) for category in categories]
    navigation = ''.join(f'<button {"id=new " if key == "new" else ""}data-filter="{escaped(key)}" aria-pressed="{str(key == "all").lower()}">{escaped(label)}</button>' for key, label in buttons)
    selected_text = ' · '.join(f'{ident:02d} {next(c["title_ko"] for c in candidates if c["id"] == ident)}' for ident in selected)
    write('index.html', f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UI Reference Kit · {count}개 참고 사례와 설명</title><style>{BOOK_CSS}</style></head><body><header><p class="eyebrow">UI REFERENCE KIT · {escaped(manifest['date'])}</p><h1>{count}개 참고 사례와 적용 시안</h1><p>{escaped(intro)}</p><p>시각 원리·어울리는 업무·주의점으로 방향을 비교하세요. 추가 후보 {new_count}개는 기존 선택 방향을 유지하며 확장했습니다.</p><p class="selected-summary">기존 선택: {escaped(selected_text)}</p><div class="links"><a href="OVERVIEW.html">사진 목차</a><a href="gallery/index.html">비교 보드 · 로컬 서버 필요</a><a href="CATALOG.md">전체 Markdown</a><a href="SOURCES.md">출처</a><a href="NOTICE.md">이미지 권리</a></div></header><main><nav aria-label="후보 필터">{navigation}<span id="count">{count}개</span></nav><p id="empty" hidden>이 필터에는 후보가 없습니다. 다른 분류를 선택하세요.</p><section id="cards">{''.join(card(c, selected) for c in candidates)}</section><footer>참고 원작의 권리는 각 제작자에게 있습니다. 이미지는 로컬 디자인 검토를 위한 캡처이며 재배포 라이선스를 부여하지 않습니다. 원본 출처와 확인 기록을 함께 유지하세요.</footer></main><script>{BOOK_JS}</script></body></html>''')
    overview_cards = ''.join(f'<a href="index.html#ui-{c["id"]:02d}" data-id="{c["id"]}" data-category="{escaped(c["category"])}" data-selected="{str(c["id"] in selected).lower()}"><img src="{escaped(c["local_reference_image"])}" alt="{c["id"]:02d} {escaped(reference_label(c))}" loading="lazy"><b>{c["id"]:02d} {escaped(c["title_ko"])}</b><small>{escaped(c["category"])} · {escaped(reference_label(c))}<br>{escaped(c["visual_principle"])}</small></a>' for c in candidates)
    overview_script = BOOK_JS.replace("#cards article", "#cards a") + "\nif(location.hash==='#new')document.querySelector('[data-filter=new]').click();"
    write('OVERVIEW.html', f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UI 참고 사례 {count}개 · 사진 목차</title><style>*{{box-sizing:border-box}}body{{margin:0;padding:20px;background:#edf0f2;color:#263d48;font:13px/1.5 "Malgun Gothic",sans-serif}}h1{{font-size:23px;margin:0 0 8px}}nav{{display:flex;gap:8px;flex-wrap:wrap;margin:15px 0}}button{{padding:7px 12px;border:1px solid #879ba6;cursor:pointer}}button[aria-pressed=true]{{background:#284e55;color:white}}section{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}}a{{display:block;background:white;padding:6px;border:1px solid #879ba6;color:#263d48;text-decoration:none;min-width:0}}img{{width:100%;height:110px;object-fit:contain;display:block;border:1px solid #879ba6}}b,small{{display:block;padding:7px 2px}}small{{font-size:10px}}[hidden]{{display:none!important}}@media(max-width:760px){{section{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}</style></head><body><h1>{count}개 참고 사례 · 사진 목차</h1><p>사진을 누르면 개별 설명으로 이동합니다. 기존 선택: {escaped(selected_text)} · 추가 후보 {new_count}개</p><nav aria-label="후보 필터">{navigation}<span id="count">{count}개</span></nav><p id="empty" hidden>이 필터에는 후보가 없습니다.</p><section id="cards">{overview_cards}</section><script>{overview_script}</script></body></html>''')
    refs = [{**c, 'image_url': '../' + c['local_reference_image']} for c in candidates]
    write('gallery/references.json', json.dumps(refs, ensure_ascii=False, indent=2))
    ordered_scenes = sorted(scenes, key=lambda scene: int(scene['id']))
    write('gallery/scenes.js', 'window.MATCHROOM_SCENES=' + json.dumps(ordered_scenes, ensure_ascii=False) + ';\nwindow.MATCHROOM_SELECTED_IDS=' + json.dumps(selected) + ';')
    write('gallery/board.js', BOARD_JS)
    options = '<option value="all">모든 분류</option>' + ''.join(f'<option value="{escaped(category)}">{escaped(category)}</option>' for category in categories)
    detail_fields = ''.join(f'<div id="{field}-block"><h3>{label}</h3><p id="{field}"></p></div>' for field, label in [('visual_principle', '시각 원리'), ('suitable_tasks', '어울리는 업무'), ('reuse_rule', '재사용 기준'), ('differentiation_from_existing', '기존 후보와의 차이'), ('methodology_name', '방법 이름'), ('interaction_verified', '조작 확인'), ('reference_kind', '참고 유형'), ('discovery_path', '발견 경로')])
    write('gallery/index.html', f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UI Reference Kit — {count}가지 화면 방향</title><link rel="stylesheet" href="./styles.css"></head><body>
<header class="masthead"><a class="wordmark" href="#all">UI REFERENCE KIT <span>시각 방향 탐색</span></a><span class="status" id="global-status">출처 참고 자료</span></header><main>
<section class="intro"><div><p class="eyebrow">VISUAL PRINCIPLE → TASK → INTERACTION → TRADEOFF</p><h1>업무가 보이는 화면, {count}가지 방향.</h1></div><div class="global-switch segmented" aria-label="전체 미리보기 종류"><button id="global-reference" aria-pressed="true">출처 참고 자료</button><button id="global-concept" aria-pressed="false">프로젝트 적용 구상</button></div></section>
<nav class="toolbar" aria-label="보기 방식"><div class="group"><a href="#all" data-view="all">{count}개 전체</a><a id="new" href="#new" data-view="new">추가 {new_count}개</a><label for="category-filter" class="nav-label">분류</label><select id="category-filter">{options}</select><span class="nav-label">5개씩 크게 보기</span><span id="sheet-links" class="group"></span></div><button id="favorites-view">선택한 방향 <span id="favorite-count">0</span>/3</button></nav>
<div class="sheet-context"><p id="view-caption">출처 참고 자료 · 전체</p><p id="view-note">원본 제품·프로젝트 화면 · 출처는 각 상세에서 확인</p></div><section id="gallery" aria-label="시각 방향 목록"></section><p id="empty" hidden></p><details id="github-baselines"><summary>내 GitHub 기준 화면 <span>실제 기존 프로젝트</span></summary><div id="baseline-grid"></div></details><footer>실제 화면·공식 연구 개념도와 프로젝트 적용 구상은 별도 보기입니다. 합성 업무 예시의 SVG 구상은 미구현이며 실행·운영 성과가 아닙니다. <a href="../index.html">오프라인 설명집</a> · <a href="../NOTICE.md">이미지 권리</a></footer></main>
<dialog id="detail" aria-labelledby="detail-title"><div class="detail-head"><div><span id="detail-id" class="eyebrow"></span><h2 id="detail-title"></h2></div><button id="close-detail" class="close" aria-label="상세 닫기">닫기 ×</button></div><div class="detail-actions"><div class="segmented"><button id="reference-tab" aria-pressed="true">출처 참고 자료</button><button id="concept-tab" aria-pressed="false">적용 구상 · 미구현</button></div><button id="choose-style">이 방향 선택</button></div><div id="detail-visual"></div><div class="detail-info">{detail_fields}<div><h3>프로젝트 적용</h3><p id="adaptation"></p></div><div><h3>조작 아이디어</h3><p id="interaction"></p></div><div><h3>선택할 때 고려할 점</h3><p id="tradeoff"></p></div></div><div class="source-strip"><span id="reference-name"></span><a id="source-link" target="_blank" rel="noopener noreferrer" hidden>원본 출처 열기 ↗</a></div><p id="evidence-note" class="evidence-note"></p></dialog><div id="toast" role="status" aria-live="polite"></div><script src="./scenes.js"></script><script src="./board.js"></script></body></html>''')
    print(f'Built {count} candidates, {new_count} additional, {len(categories)} categories, {(count + 4) // 5} sheets. Source images and SVG files untouched.')


if __name__ == '__main__':
    main()
