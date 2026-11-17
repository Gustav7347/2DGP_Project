# 마지막 피격의 사실과 재도전 안내

상태: 구현 전 설계. 아래 `last_hit`와 새 테스트는 만들 예정이며 현재 존재한다고 주장하지 않는다. 기반은 현재 PRD의 검격·방향 패링·육참골단·3+1 스테이지다. 새 전투 규칙·성장·조작은 추가하지 않는다.

## 문제와 목적

사망 결과 화면은 처치/패링/시간/조합만 보여 준다. 플레이어가 다음 도전에서 무엇을 바꿀지 판단하기 어렵다. 실제 피해가 수락된 순간의 상태만 기록해 마지막 피격의 출처·패링 상태와 짧은 대응 안내를 보여 준다. 플레이어의 의도나 사망의 유일한 원인을 추측하지 않는다. 화면 명칭은 ‘마지막 피격’이다.

## 선택과 대안

- 선택: Game에 마지막 피격 한 건만 보관하고 기존 `_hurt_player` 경로에서 갱신한다. 결과 문구는 기존 interface/render에 추가한다. 현재 이벤트 꼬리는 300개로 제한되므로 이를 결과 화면에서 다시 추론하지 않는다.
- 전체 전투 리플레이/통계 프레임워크: 이번 안내에 필요 없고 저장/입력 동기화 범위가 커져 제외한다.
- 결과 화면에서 적의 현재 위치로 원인 추정: 피격 뒤의 이동/상태 변경 때문에 당시 상황을 보장할 수 없어 제외한다.
- ‘패링을 늦게 눌렀음’ 같은 의도 추정: 키를 누르지 않은 경우와 구분할 근거가 없어 제외한다.

## 변경 범위

Modify `bladegame/core.py`, `bladegame/interface.py`, `bladegame/render.py`, `tools/product_preview.py`, `main.py`, `PRD.md`, `README.md`, `DECISIONS.md`, `DEVLOG.md`, `QUALITY_REVIEW.md`, `IMPLEMENTATION_STATUS.md`, `PRODUCT_REVIEW.md`, `AGENTS.md`, `prompts/polish-pass.md`.
Create `tests/test_hit_feedback.py`, `.agents/reviews/2026-11-09/`의 설계/검토/처리 기록, `.agents/references/`의 참조 원문/라이선스/출처 기록, `prompts/evidence-review.md`.
Generated output: `verification/feedback-20261109/`, 반복 검증 폴더, 상위 `output/`의 실행 ZIP과 미리보기. 다른 사용자 변경은 보존한다.

비생성 기록의 확정 파일명은 `.agents/reviews/2026-11-09/failure-feedback-plan.md`, `goldfish-design-review.md`, `goldfish-drift-review.md`, `goldfish-post-review.md`, `resolution.md`다. 참조 원문은 `.agents/references/manifest.json`의 9개 파일만 추가하며 도구/훅은 설치하지 않는다. AGENTS와 polish-pass에는 evidence-review 링크를 추가한다. PRD/README에는 마지막 피격의 관측 범위와 알려지지 않은 출처의 중립 표시를 추가한다. DECISIONS에는 최신 사용자 원문을 D22로 기록한다. DEVLOG에는 검토·발견·수정·검증을, QUALITY_REVIEW/PRODUCT_REVIEW/구현 현황에는 현재 개선과 미검증 경계를 연결한다. 그 외 구조 변경은 하지 않는다.

## 데이터·분기

1. `Game.last_hit`: 새 Game과 `start()`에서 None. 스테이지 이동 때는 유지한다. 한 판의 마지막 관측이므로 새 피해가 수락되면 덮어쓴다.
2. `_hurt_player`에 선택적 keyword-only `enemy=None`, `reason='unblocked'`를 추가한다. 기존 `ignore_invulnerability`, `direction`과 모든 직접 호출은 호환한다. 상태가 playing이 아니거나 무적 시간 때문에 거부되면 갱신하지 않는다.
3. 수락 직후 체력/생존 분기보다 먼저 마지막 피격 dict를 만든다. 스키마: `enemy_kind`(str 또는 None), `attack`('slash'/'thrust' 또는 None), `reason`(아래 enum), `stage`(1-based int). 적 객체 자체를 저장하지 않는다. 직접 호출에서 enemy가 없으면 `reason='unknown'`으로 기록한다. 기존 player_hit/player_died 이벤트도 이 내용을 `hit` 필드로 포함한다. 기존 이벤트 키와 의미는 유지한다.
4. 정상 패링 성공은 마지막 피격을 갱신하지 않는다. 육참골단은 기존처럼 실제 피해를 처리할 때 enemy와 `reason='counter_cost'`를 전달한다. 치명상도 기록한다. 반월 회복/반격/불굴·회생의 순서는 그대로다.
5. 일반 실패 분기는 현재 방향 판정을 재사용해 다음 순서로 reason을 선택한다: 적이 허용 방향 밖이면 `behind`; 아니고 action이 parry이며 action_time > PARRY_WINDOW이면 `window_ended`; 아니고 action이 parry이며 parry_ready가 False이면 `spent`; 그 외 `unblocked`. 경계 `== PARRY_WINDOW`는 기존 성공 조건을 유지한다. 여러 조건이 동시에 참일 때 선택한 한 관측을 보여 줄 뿐 이를 유일한 실패 원인으로 주장하지 않는다.
6. 판정 밖 공격, 무적 시간의 무효 타격은 기록을 바꾸지 않는다. 생존 증강이 피해를 처리해 살아남은 경우도 ‘피격’ 기록으로 남는다. 이 기록은 피해 수락/방어 상태이며 실제 체력 감소량을 주장하지 않는다.

## 표시와 입력

- `interface.last_hit_text(hit)`는 dict/None을 받아 설명 문자열 하나를 돌려준다. 적 이름은 검사/창병/도장주, 공격은 베기/찌르기. None·출처 없는 직접 피해에는 적 이름을 발명하지 않고 ‘마지막 피격 정보 없음’을 쓴다.
- behind: ‘뒤쪽 적에게 피격 · 적을 바라보고 패링’.
- window_ended: ‘패링 유효시간이 지난 뒤 피격 · 타격 직전에 입력’.
- spent: ‘이번 패링을 이미 사용한 뒤 피격 · 다음 타격의 예고 확인’.
- counter_cost: ‘육참골단은 패링해도 피해를 받음 · 남은 체력 확인’.
- unblocked: ‘패링 방어가 없는 상태로 피격 · 예고와 회복약 확인’.
- 문구 앞에 ‘마지막 피격  {적 이름} · {공격} / ’를 붙인다. 사망 결과에만 y=274, 가운데 x=640, 18px로 한 줄 표시한다. 조합 y=298과 버튼 상단 y=255 사이에 배치하며 키/클릭 좌표는 유지한다. 클리어 화면에는 사망 안내를 표시하지 않는다. 최초 y=264 시안은 실제 화면에서 버튼과 간격이 좁아 10px 위로 조정했다.
- main.py 검증 JSON에 `last_hit`를 추가한다. 사람이 플레이한 기록이라고 주장하지 않는다.
- product_preview.py는 각 사유를 실제 `_enemy_strike`/`_hurt_player`로 발생시킨 고정 상태 화면을 만들고, 맑은 고딕 실측 폭을 기록한다. 1120px 안에 맞지 않으면 문구를 짧게 고친다. 기존 미리보기는 유지한다.

미리보기 재현값: seed=104, `_enter_stage(3)`, 플레이어 x=160/y=GROUND/hp=1/invulnerable=0/기본 facing=1. uid=501 도장주는 x=245, facing=-1, state=active, hp/max_hp=420, pattern=slash다. behind는 적 x=75/facing=1로 변경한다. window_ended는 player.action=parry/action_time=PARRY_WINDOW+.001/parry_ready=True, spent는 parry/.1/False, counter_cost는 parry/.1/True와 augments={'counter'}, unblocked는 idle이다. unknown은 enemy 없이 `_hurt_player(9999)`를 호출한다. 다른 사유는 `_enemy_strike`를 호출하고 dead 및 기대 last_hit dict 전체 값을 즉시 assert한다. 이후 dead 상태에서 66×1/60초 tick해 action_time>.85를 assert한 뒤 저장한다. 그림을 얻으려고 기록을 직접 주입하지 않는다. `hit-feedback.json`에 실제 사유·표시 문자열·폭을 기록하고 최대 1120px/사망 상태/출처 일치가 합격 기준이다. 겹친 실패 조건은 behind 우선, 스테이지 이동 보존과 이벤트 hit 복사도 검증한다.

## 검증과 위험 제한

독립 대조에서 추가 확인한 범위: main.py의 프레임 경과 상한을 0.05→0.25초로 맞춘다. core의 기존 0.25초 보호 상한은 유지하고 4fps 미만의 느려짐은 PRD에 명시한다. 실제 main/SDL 경로 시계 주입으로 10/20/60fps에서 1초 진행을 비교한다. 보상 중 F1 도움말은 reward 상태·후보·선택 포커스를 보존하며, 모달 중 숫자/화살표/클릭이 카드를 선택하지 않도록 main.py 입력 분기와 Interface.hover를 제한한다. 기존 ui_check.py에 보상 도움말·차단·복귀를 추가한다. 육참골단 보상 문구는 ‘살아남지 못하면 반격 불가’로 고쳐 생존 증강의 우선 처리를 반영한다. Modify allowlist에 bladegame/ui_check.py, tests/test_product_flow.py, tests/test_planned_scope.py를 추가한다. tests/test_hit_feedback.py에 생존 증강 후 반격·보상 도움말 상태 보존·중첩 실패 우선순위를 추가한다. 시계 주입 probe는 verification/feedback-20261109/의 생성 검증물이다.

Phase 1: 문서/코드의 현재 상태를 fresh reviewer가 확인. 검토 실패는 미실행으로 기록하고 의견별 수락·반박·보류를 구분한다.
Phase 2: 원인 스냅샷·표시·검증 보고 경로를 구현. 회귀 검사: 뒤쪽/유효시간 종료/1회 소모/방어 없음/육참골단 치명상, 방향/타이밍 경계 성공, 무적/범위 밖 미갱신, 새 판 초기화, 이후 적 이동에도 기록 유지, 출처 없음의 중립 문구, 기존 생존 처리 순서와 입력 유지.
Phase 3: 실제 SDL 사유별 결과 화면과 글자 폭, 전체 unittest와 `tools/polish_check.py --runtime`, 실행 ZIP 내용 대조. 수정 후 독립 검토에서 허위 설명·분기 누락·기존 입력 회귀를 확인한다.

네트워크·새 라이브러리·개인 데이터 수집은 없다. 한 건의 작은 dict만 유지한다. EGM의 분리 검토와 Ponytail의 최소 완결 변경 원칙을 적용하지만 환각 방지 보증이나 상업 품질 인증으로 쓰지 않는다. 전체 EGM 승인/다회 수렴 루프를 실행했다고 주장하지 않는다. 현재 요청의 자율 개발 권한 안에서 설계·검토·구현·재검증을 이어 진행한다.
