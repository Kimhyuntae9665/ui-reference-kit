# 수정·새 후보 제안 안내

처음에는 잘못된 링크, 설명 오류, 번역, 실행 안내 개선처럼 작은 수정도 좋습니다. Issue에 후보 번호·문제·원본 출처를 적거나 브랜치를 만들어 Pull Request를 보내주세요.

## 기존 후보 수정

1. `candidates/NN.md`의 사진·원작·출처·화면 설명을 확인합니다.
2. `manifest.json`의 해당 ID도 함께 수정합니다. 주요 필드는 다음과 같습니다.

| 필드 | 의미 |
| --- | --- |
| `id`, `title_ko` | 후보 번호와 제목 |
| `source_url`, `reference_name` | 원작 출처와 이름 |
| `local_reference_image` | 실제 참고 JPG 경로 |
| `local_concept_image` | 자체 SVG 시안 경로 |
| `visual_description`, `visual_principle` | 실제 화면 설명과 가져올 원리 |
| `category`, `suitable_tasks`, `reuse_rule` | 분류·적합 업무·재사용 기준 |
| `matchroom_adaptation`, `interaction_idea`, `tradeoff` | 초기 예시에 대한 적용·조작·단점 |
| `evidence_status`, `snapshot_date`, `snapshot_type` | 확인 수준·기준일·캡처 유형 |

3. 집계 문서 `CATALOG.md`와 HTML 책자 `index.html`, 선택 갤러리 `gallery/references.json`의 같은 후보를 동기화합니다. 이미지 변경 시 `overview.jpg` 미리보기도 다시 캡처합니다.
4. `python scripts/validate.py`를 실행하고 브라우저에서 사진·설명·출처 연결을 확인합니다.

## 다른 프로젝트의 선택으로 바꾸기

`manifest.json`의 `selected_ids`·각 후보의 `selected`, `index.html`의 선택 요약, `DECISIONS.md`에 선택한 번호와 원리를 함께 기록합니다. 갤러리의 브라우저 선택은 문서와 자동 동기화되지 않으므로 번호를 따로 기록하세요.

## 새 후보 제안

기존20개와 표현 원리나 조작이 어떻게 다른지 먼저 설명합니다. 단순 색상 변경보다 실제 사용자에게 다른 이해·선택 방식을 제공하는 후보가 좋습니다.

- 공식 원작 링크와 실제 작업 화면을 제시합니다. 빈 캔버스·광고 배너보다 업무 대상과 조작이 드러난 화면을 고릅니다.
- 자체 제작 또는 공개 사용 조건이 확인된 이미지와 SVG를 우선합니다. 외부 캡처는 권리·출처·원본 표시를 확인하며 전체 제품이나 글을 무단 재배포하는 형태로 확장하지 않습니다.
- `candidates/NN.md`·`images/NN-reference.jpg`·`concepts/NN-concept.svg`와 메타데이터를 같은 ID로 묶습니다. 사진과 시안을 혼동하지 않습니다.
- SVG는 자체 제작하고 실제 구현이 아니면 미구현임을 표시합니다.
- 21개 이상으로 확장할 때는 `reference_count`, `concept_count`, README 목차, HTML 집계, `scenes.json`, `gallery/scenes.js`의 시안 정의를 업데이트합니다. 현재 선택 갤러리의4개 묶음·`sheet-1`–`sheet-4` UI와 관련 범위 처리도 늘려야 합니다.
- 추가한 실제 ID 수가 `reference_count`와 일치해야 합니다. 검수 스크립트는 메타데이터에 맞춰 개수를 검사합니다.

캡처에 이메일·토큰·실제 고객 문서·내부 시스템 정보가 없는지 확인합니다. 수치·성과·현재 기능은 직접 확인한 범위만 설명합니다. 참고 스타일을 특정 회사의 공식 요구나 제품 성능 보증으로 표현하지 않습니다.

코드 변경은 빌드 도구 없는 브라우저 JavaScript와 Python 표준 라이브러리를 유지하고, 불필요한 의존성·추적 스크립트·외부 데이터 전송을 추가하지 않습니다.
