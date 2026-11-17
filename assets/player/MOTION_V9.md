# v9 — 가드와 횡 쳐내기, 교대 달리기

2026-11-12. 내장 이미지 생성 도구로 제작하고 원본 바이트를 그대로 복사했다. 생성 결과의 격자/자세를 읽어 별도 JSON으로 등록했다. Python/Pillow는 원화 픽셀 수정 없이 좌표·알파 경계 분석과 등록에만 사용했다.

## 채택/기각과 파일

- `parry-guard-sweep-v9.png`: 1536×1024, 3×2. 입력용 가드1/2, 접촉2, 성공3→4, 복귀5. 칼 각도는 가드−90°, 쳐내기0°. 별도 장검과 겹치는 손 픽셀을 등록한다. contact35ms→준비35ms→횡 쳐내기80ms→복귀70ms는 판정 창과 별도 표시 시간이다.
- `run-cycle-v9.png`: 1536×1024, 3×2. 밝은 근측 종아리와 어두운 원측 종아리를 유지한 서로 반대 접지/지지/발차기6자세.560ms주기, 실제 이동 거리 기반. 손 위치/발바닥/비행 높이를 개별 등록한다. 자연스러움이나 미세한 발 미끄러짐 해결을 검사 통과로 확정하지 않는다.
- `motion-registration-v9.json`: 활성 좌표/시간. `tools/register_motion_v9.py`로 재생성하며 `build_assets.py`도 v9 우선권을 보존한다.
- 첫 달리기 편집(4×2)은 이전 시트의 앞다리 반복을 충분히 해결하지 못해 기각했다. `verification/guard-v9/run-candidate-rejected.png`에 보존하며 배포에는 넣지 않는다.
- 패링 첫 생성 후 배경 제거를 별도 요청했다. 최종 파일의 빈 구역 알파0, 인체 불투명 픽셀과 경계를 확인했다. RGB의 갈색만 보고 불투명 배경으로 단정하지 않았다.
- 활성 원본: 생성 출력 `exec-024b605f-7520-46f9-ab5b-7d7d2b9020f2.png`(달리기), `exec-c1c7d1ba-9076-444a-83af-b7f57e926680.png`(패링). 이전 parry-guard-beat-v3/run-stride-v7는 보존한다.

## 적용한 도구

PixelFX 원본의 순수 효과 API와 PNG/JSON 출력기를 사용해 `tools/parry_contact_fx.mjs`를 작성했다. 큰 원형 방패 대신 백색 접점과 방향성 은색/금색 입자를 .28초 시트로 출력한다. 게임은 완성 PNG/JSON만 읽으며 Node/PixelFX/편집기를 요구하지 않는다. 원본 MIT/NOTICE는 assets/licenses에 있다. 제작 중 게임 화면에서 발견한 ‘패링 뒤 남는 적 베기 잔상’은 해당 적의 성공 시에만 정리한다. 일반 공격은 적의 공격을 취소시키지 않는다.

Pixelorama의 프레임 비교/앞뒤 자세 겹쳐보기 관점을 검수 기준에 반영했다. 프로그램 자체를 설치/사용한 것은 아니다. 음향도 기존 보존 CC0 소스의 제작 도구로 새 후보를 만들었으며 Audacity 조작으로 보고하지 않는다.

## 최종 달리기 생성 프롬프트

Generate a NEW technically accurate RUN CYCLE using this image ONLY as character design reference. Do not copy its poses. Production sprite sheet: EXACT 3 columns x 2 rows, SIX frames, consistent cell sizes, full bodies, all facing RIGHT in side view, true transparent background. Straw conical hat hiding face, navy clothes, crimson waist sash, short dark cape; mature restrained pixel art. Establish two visibly distinguishable legs: NEAR LEG has light ivory calf wraps and a navy trouser, FAR LEG is dark slate including dark calf wraps. Keep this distinction consistently in ALL six frames, do not swap colors halfway. Frame1 top-left: near LIGHT leg extended forward, heel touches ground; far DARK leg stretched backward, toe departing. Frame2 top-middle: near LIGHT leg supports vertical under hips with knee flexed; far DARK leg bent, knee passing forward. Frame3 top-right: near LIGHT leg stretched BEHIND hips in push-off; far DARK thigh reaches FORWARD with knee raised, foot tucked under knee. Frame4 bottom-left: far DARK leg extended FORWARD, heel touches ground; near LIGHT leg stretched BACKWARD with toe departing. Frame5 bottom-middle: far DARK leg supports vertical UNDER hips with knee flexed; near LIGHT knee passes FORWARD. Frame6 bottom-right: far DARK leg extended BEHIND in push-off; near LIGHT thigh reaches FORWARD, foot tucked. MUST show these opposite contact poses frame1 vs frame4, opposite passing poses frame2 vs frame5, opposite push-off poses frame3 vs frame6. This alternation is more important than costume detail. Arms: only two, one hand near waist gripping an invisible sword hilt, no blade as the game renders it; far elbow follows leg cycle. Modest forward torso lean, pelvis centered at same horizontal location within each cell, modest rise/fall, hat scale stable. Clean crisp small pixel clusters; no smoke, glows, sparks, multiple limbs, trails, background, text or grid lines. Clear separation of feet; don't simply repeat same front leg in every frame.

## 패링 생성 프롬프트

Edit into a coherent PARRY body animation sheet for the same side-scrolling game. Preserve exact character design, straw conical hat hiding face, navy outfit, muted crimson sash, charcoal cape, adult proportions, serious pixel art, face RIGHT throughout. EXACT regular 3-column x 2-row grid, 6 full-body poses, transparent background with NO glow/shadows/background, no text. Runtime draws a LONG SWORD separately, so draw NO blade, NO sword scabbard: only both hands gripping the same invisible short hilt, hands touching or stacked together without separation. Keep both hands around lower chest height. Pose1 quiet neutral with hands near hip. Pose2 upright guard, hilt around sternum in front of the body, elbows bent low; knees flex slightly. Pose3 same guard taking contact, slight backward weight transfer, hands firmly together, DO NOT extend arms. Pose4 start horizontal deflection: hips rotate right, hands sweep from chest toward right, slightly separated stance, weapon still omitted. Pose5 horizontal sweep followthrough: rotate shoulders, both hands together reach modestly to right at CHEST HEIGHT, elbows still slightly bent, knees support weight, cape lags left. DO NOT aim hands downward toward knee as source pose5 does. Pose6 hands return to neutral hip matching pose1, weight returns centered. Full body never cropped, hat and feet same scale in each cell, ground line consistent. Exactly two arms two hands two legs; rear arm darker, no duplicate hands, no fists floating detached. Maintain high-quality crisp pixel clusters and restrained palette, simplify folds for animation consistency. This is production game sprite animation, not an illustrated poster.

배경 후속: Background removal ONLY. Preserve the exact 1536x1024 3x2 sprite grid, every character pose, position, silhouette and all character pixels. Remove ALL brown/grey/black background gradients, all ambient glow and all floor/contact shadows. Every pixel outside the six character silhouettes must be truly alpha=0 transparent. This is a game spritesheet cutout, not illustration. Do not change hands, hat, boots or clothing. Crisp alpha edge around each separate full-body character. No extra content.

## 확인 범위

게임의 고정 입력 접촉/이동/육참골단 장면을 숨김 창으로 캡처했고, 선택한 시점의 실제 화면을 직접 확인했다. 실제 시간 영상과 전후 같은 입력 비교본은 verification/guard-v9에 보존한다. 이 문서의 ‘캡처/내보내기’는 영상 전체 시청·음향 실제 청취·사람의 재미/선호 합격을 뜻하지 않는다. 적 원화 속 칼날과의 정확한 교차, 정지/점프/모든 취소 연결의 미세한 미술 보정은 남아 있다.
