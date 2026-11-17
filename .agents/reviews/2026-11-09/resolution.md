# 독립 검토 처리와 근거

이전 대화를 전달하지 않은 native subagent의 실제 반환 결과를 보존한다. 전체 EGM 설치·승인·5회 검토·2회 clean 수렴을 수행한 기록이 아니다. 현재 사용자 요청의 자율 개발 범위에서 EGM의 문맥 분리/원문-코드 대조와 Ponytail의 최소 완결 변경을 적용했다.

## 1차 결과

| ID | 역할·등급 | 발견 | 처리 | 근거 |
| --- | --- | --- | --- | --- |
| R1 | Readiness / Major | 문서 수정/참조·기록 파일 경계가 모호함 | 수락·명세 보완 | failure-feedback-plan에 확정 기록명, manifest 기반 원문 목록, 문서별 변경 범위 명시 |
| R2 | Readiness / Major | 무적·사망 화면 대기 때문에 실제 화면 재현 절차가 불완전함 | 수락·명세/미리보기 보완 | hp=1/invulnerable=0/공격 위치/패링 상태, 실제 피격, 66 tick과 dead/last_hit/폭 assert를 명시·실행 |
| R3 | Codebase / Blocker | 0.05초 프레임 상한이 시간 기반이라는 설명과 다름 | 수락·코드/문서 수정 | before-timing: 10fps에서 1초→0.5초. 상한을 core와 같은 0.25초로 맞춘 after-timing은 10/20/60fps 모두 1초→1초. 4fps 미만 제한은 명시 |
| R4 | Codebase / Blocker | F1은 보상 상태에서 조용히 무시됨 | 수락·입력/표시/검증 수정 | reward 상태·후보·포커스 보존, 도움말 뒤 카드 입력 차단, 닫기 후 선택. SDL UI 16경로 통과 |
| R5 | Codebase / Blocker | 육참골단 문구가 생존 증강 후 반격을 부정함 | 수락·문구와 실제 조합 검사 보완 | ‘살아남지 못하면 반격 불가’. 불굴/회생으로 살아남은 실제 counter 경로 검사 |

Blocker라는 등급은 원본 persona의 문서 모순 분류이며, 이 게임 전체가 고장 났다는 뜻으로 바꾸지 않는다. 처음 지적된 문서/코드와 처리 후 상태를 구분한다. 초기 보고서의 라인 번호는 수정 전 스냅샷 기준이다.

## 대화 분리 확인과 한계

- Turing: native ID 01a1bbe5-5d02-7d63-a5c9-6264a679936c / fork_context=false / 완료 / persona·standard·대상·소스를 읽었다는 실제 보고 수신 / 부모 전용 표식 UNKNOWN.
- Gibbs: native ID 01a1bbe5-5d58-7093-9eb7-6f60a829f7d6 / fork_context=false / 완료 / persona·standard·대상·소스를 읽었다는 실제 보고 수신 / 부모 전용 표식 UNKNOWN.
- 두 검토자 모두 호스트 AGENTS 지침이 있었다고 보고했다. 따라서 파일 시스템·호스트 지침·기본 메모리를 포함한 완전 격리를 주장하지 않는다. 부모 채팅/메모리 검색을 제공하지 않았으며 이 검토자들의 실제 결과는 goldfish-design-review.md와 goldfish-drift-review.md다.
- Halley의 사후 검토는 별도 fresh context로 요청했다. 완료되기 전에는 검토 완료/문제 없음으로 집계하지 않는다.
- Halley: native ID 01a1bbf2-3df0-7390-a8f9-f6cbb95b28ad / fork_context=false / 완료 / persona·standard·명세·코드·실행 근거를 읽었다는 보고 수신 / 부모 전용 표식 UNKNOWN. 보고 범위에서 중대 구현 결함은 발견하지 못했으나 모달 중 숫자/Enter의 직접 검증 누락을 지적했다. 이를 R6으로 수락해 native UI 검사에 추가했다. 코드가 이미 차단하는 동작의 검증 보완이며 미발견 오동작을 새 버그였다고 하지 않는다. raw 결과는 goldfish-post-review.md에 보존했다.

R6 후속: 도움말 중 숫자 2가 카드를 선택하지 않는지, Enter는 안내만 닫고 후보를 확정하지 않는지, 다시 안내를 연 뒤 ESC로 같은 화면에 복귀하는지 검사한다. 새 UI 경로는 총 18개다. 이 추가 검증의 성공은 아래 최신 실행 기록으로 확인한다. R3~R5를 재고쳤다는 이중 집계나 두 번 clean 수렴 주장은 하지 않는다.

## 실행 증거

- verification/feedback-20261109/before와 after: 같은 기존 ZIP의 코드/에셋과 현재 코드를 각각 사용한 실제 SDL 사유별 화면. 에셋은 바이트 대조 후 비교했다. 고정 피해 시나리오이며 사람 완주 장면이 아니다.
- after/hit-feedback.json: 뒤쪽/유효시간 종료/소모/육참골단/방어 없음/정보 없음의 6상태. 실제 피해 처리의 스냅샷과 표시를 대조했고 최대 문자열 폭 645px로 1120px 안에 든다.
- before-timing/timing.json, after-timing/timing.json: main·SDL 경로의 시계 주입 결과. 하드웨어 벤치마크나 4fps 미만 검증을 뜻하지 않는다.
- verification/polish/runs/20261109-011609/report.json: 69개 검사, 스타일 3종, 실제 무음 SDL 채널·기본 입력·메뉴·한 판·모션·빈 화면·음원 수치 통과.
- R6 보강 후 최종 결과는 verification/polish/runs/20261109-012111/report.json이다. 69개 검사와 메뉴 18경로를 포함한 모든 실행 항목이 통과했다. 독립 검토 3건은 실제 완료했으며, 사후 검토의 검증 누락 1건은 native 입력 검사로 보완했다.
- 신규 문구는 사망의 유일한 원인이나 플레이어 의도를 단정하지 않는다. 소리 청취·모션 자연스러움·재미·상업성은 이 검토의 합격 범위가 아니다.
