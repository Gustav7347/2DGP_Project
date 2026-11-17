# 방어 자세 → 성공 시 칼 쳐내기 — 2026-11-10

사용자 원문: “우클할때 방어자세, 패링성공시 쳐내는 이미지로 해주셈”.

내장 imagegen으로 기존 외형을 참고하여 몸 시트를 새로 생성했다. 활성 파일은 `parry-guard-beat-v3.png`(1536×1024,3×2)이며 원본 PNG를 픽셀 후처리 없이 복사했다. 양손을 같은 자루에 모은 방어와 상체를 돌려 바깥으로 미는 성공 후속 자세를 구분한다. 장검은 기존 공통 무기를 손 위치에 따로 조합한다.

0번은 낮은 준비,1·2번은 가슴 앞 방어,3번은 성공 시 쳐내기 시작,4번은 칼을 바깥/아래로 쳐낸 후속,5번은 낮은 준비 복귀다. 성공 후 표시 시간은 시작35ms→후속115ms→복귀70ms다. 기존75ms 적중 정지 동안에는 첫 성공 자세가 보존된다. 실패에는3·4번이 나오지 않는다. 우클릭을 계속 누르면 상시 방어하는 기능을 추가한 것이 아니며 기존 타이밍 패링 판정/공중 사용을 유지한다.

등록값은 `animations.json`과 공통 `motion-registration-v7.json`의 parry 항목이다. 달리기의 등록값은 유지한다. 양손의 앞쪽 손을 칼 회전 중심으로 사용한다. 방어 칼 각도 -55도, 성공 시작 -38도, 쳐낸 후속 +30도다. 실제 화면에서는 좌우 방향으로 반전한다.

생성 요청과 다른 결과/한계: 프레임1·2의 방어 몸 그림은 거의 같다. 이번에는 유지하는 방어 자세이므로 그대로 사용했다. 성공 두 자세의 팔·몸통·망토는 구분된다. 두 손이 모인 낮은 준비 자세는 기존 한 손 대기와 완전히 같지는 않으므로 복귀 연결의 미감은 후속 검수 항목이다. 격자/검사 통과를 사용자 선호나 모션 완성 판정으로 쓰지 않는다.

## 생성 요청

참조1: 기존 parry-braced-v2.png는 교체할 시안. 참조2: idle.png는 캐릭터 외형/화풍. 투명 배경을 요청했다. 최종 요청 전문:

```text
Use case: identity-preserve. Asset: production BODY animation sprites for a 2D swordsman. Image1 is the old inadequate parry sheet: its raised-fist boxing stance and backward flinch must be replaced. Image2 is exact character identity and shaded pixel-art style reference. Create a NEW exactly SIX-sprite sheet in 3 columns x 2 rows on genuine transparent background. Each cell equal roomy size, all full-body characters face RIGHT in fixed side/three-quarter gameplay view. Keep the adult lean character, broad straw conical hat hiding entire face, navy blue martial tunic and loose pants, charcoal grey short cape, muted red sash, cream wrist/shin wraps, black boots. Preserve same scale, proportions, hat size and feet registration across all cells. EXACTLY TWO arms and TWO legs per character. No extra hands. BODY ONLY, no sword blade, no scabbard, no effects, no floor, no shadows, no text. The sword will be rendered separately onto the hand. Both hands should be CLOSE TOGETHER gripping a short horizontal/diagonal hilt stub as a Japanese/Korean swordsman would; one closed leading hand at the chest-to-waist height, second hand immediately behind/below on that SAME shared grip, NOT separated boxing fists. Frame1 top-left: neutral stance, dominant sword hand lowered beside hip, matching identity ref. Frame2 top-middle: DEFENSIVE GUARD, knees slightly flexed, elbows close, both hands gathered in front of lower chest, ready to support an upright diagonal blade; feet planted. Frame3 top-right: HOLD DEFENSIVE GUARD, same hand area and balanced stance, shoulders steady; do not punch or extend an empty fist at head height. Frame4 bottom-left: SUCCESSFUL PARRY / BEAT START, proactively rotate hips and shoulders toward right, move the two joined hands outward-forward away from torso at chest height, front foot plants, rear heel pushes; a forceful deflection, NOT taking a hit or crouching backward. Frame5 bottom-middle: FOLLOW-THROUGH OF KNOCKING THE ENEMY BLADE AWAY, arms extend diagonally down-and-forward toward RIGHT, joined hands ahead of front hip, torso slightly opens, cape and red sash trail opposite the sharp turn; front knee supports weight, rear leg follows, sword would sweep outward in a short arc. A DISTINCT silhouette from the guard, not just changing fist height. Frame6 bottom-right: return to neutral stance matching frame1. This is guard then quick outward sword beat, NOT an offensive full slash, not blocking a punch, not recoiling from injury, no crouch-only success. Crisp pixel edges, consistent dark outline and adult proportions matching identity reference. Keep full hat and both boots clear within every cell, grounded stance, no chibi, no high-knee pose, no duplicated bodies, no painted background or halo.
```

생성 원본 경로·SHA256과 복사 일치는 verification/guard-beat-20261110/asset.json, 현재 실행 결과와 캡처는 같은 폴더에 기록한다. source/PPT/기존 실행 사본은 변경하지 않는다.
