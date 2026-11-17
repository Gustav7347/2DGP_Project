# v10 미술 제작·연결 기록

2026-11-12. ART_DIRECTION.md의 D36 기준에 따라 기존 검사1명의 패링 반응과 전경 지지 원화를 추가했다. 내장 이미지 생성 도구를 사용했고 PNG 원본을 바꾸지 않고 복사했다. tools/register_art_v10.py와 build_assets.py는 좌표/알파 경계만 읽는다.

## 파일과 역할

- enemies/sword-parried-v10.png / .json: 3×2,6자세. 접촉→위로 밀림→몸 반동→기절 자세 정리. 칼이 없는 몸과 별도 장검을 합성해 최초 접촉을 주인공의 그 순간 칼날에 맞춘다. 손 픽셀을 자루 앞에 다시 그린다. .22초 표시는 실제 기절/피해 판정을 지연하지 않는다.
- environment/supports-v10.png / .json: 2×2,돌기둥·목재기둥·목재브래킷·석재받침. 산길은 돌 지지, 도장 앞은 목재 지지로 렌더링한다. 접지/발판 윗면과 충돌은 그대로다.
- 최초 지지 시안은 바닥면 아래와 지지대 상단 사이가 시각적으로 벌어져 배치 높이를 수정했다. 최종 기둥 상단은 기존 발판 면 뒤로 들어가며, 캐릭터가 지나는 뒤 레이어임을 명도로 구분한다.
- 다른 적/보스의 전면 원화 교체는 하지 않았다. 검사 장면이 이번 표준 장면이다. 창병/보스까지 같은 접촉 보정이 전부 끝났다고 보고하지 않는다.
- 생성 출력: exec-253f03d3-7e6a-4438-bf46-40a407f9b49a.png(검사), exec-7afeff34-304d-44a3-9570-106070cb61af.png(지지). 원본 크기/좌표는 JSON을 기준으로 한다.

## 검사 생성 요청 전문

Production asset for an existing mature Eastern swordsman pixel-art side scroller. Edit ONLY the same maroon-robed enemy swordsman in this reference into a PARRIED REACTION BODY sprite sheet. Keep his exact adult proportions, tied dark hair, short beard, muted burgundy tunic, charcoal trousers, bandaged calves and boots. EXACT six equal cells, 3 columns x 2 rows, full bodies, facing RIGHT in every cell, constant scale and ground line. IMPORTANT REMOVE ALL WEAPONS: no blade, no scabbard, no visible hilt. The game draws the sword separately; both hands grip the SAME invisible short handle, touching/stacked, never two disconnected hands. Frame1 top-left: clash contact, sword hand(s) around chest height reaching FORWARD to the right, elbows slightly bent, torso braced leaning forward, eyes facing right. Frame2 top-middle: his hands are knocked upward/outward toward his RIGHT at face height, shoulders recoil back left, knees braced. Frame3 top-right: followthrough knocked away, hands still together above/right of head, torso leans slightly BACK left, feet grounded. Frame4 bottom-left: stagger settles, both hands descend toward sternum, elbows bending, knees soft. Frame5 bottom-middle: lower hands toward waist, torso folds forward slightly in stunned reaction. Frame6 bottom-right: match the reference's hunched hurt pose (bottom middle) but without sword: one hand holds stomach, weapon hand low near hip. No new outfit, no extra arm/hand, no background/glow/floor shadow, no attack trails, no text or grid lines, true transparent background. Clean restrained pixel clusters, two arms/two legs, clear shoulders-to-wrists chain and knee support. Do not put the sword into the bitmap. This is six key poses of one reaction, not six new characters.

참조: assets/enemies/sword.png. 내장 도구, transparent_background=true.

## 지지 원화 생성 요청 전문

Create a production PIXEL ART environment SUPPORT atlas for this existing serious Eastern swordsman side-scrolling game. Use reference only for restrained grey stone and weathered timber texture/pixel density, do not copy its floating platform shapes. Exactly FOUR separate objects in a regular 2x2 equal-cell grid. Top-left: a straight narrow ancient grey stone pier, front/side view, flat top/bottom, weathered stones with muted moss in cracks, about 1:4 width to height. Top-right: a straight narrow aged dark timber support post with a small horizontal beam at top and iron bands, about 1:4 width to height. Bottom-left: a triangular diagonal wooden corbel/brace, horizontal upper beam and diagonal under-brace, attached to a short vertical beam on left, front/side view. Bottom-right: a tapered broken stone buttress/rock support, wide flat upper surface and narrower cracked vertical stone foot, front/side view. These are BACK supports placed behind playable ledges; keep dark muted values, never white outline/glow. Every object fully contained inside its own cell with generous transparent margins, no scenery/floor/contact shadows, genuine alpha transparency outside all four silhouettes. No characters, text, borders, grid lines, grass floating islands, 3D perspective blocks, UI or effects. Crisp limited-palette pixel clusters, muted cold grey stone and dark desaturated brown timber. Objects remain distinct and easy to crop/export.

참조: assets/environment/terrain.png. 내장 도구, transparent_background=true.

## 채택/검수

게임의 실제 좌우 반전/접촉/후속 동작/전경·보상·도움말을 확인한다. 새 성공 반응이 손/칼을 과도하게 가리거나 바닥선을 튀게 하면 보정한다. 원화만 봤다는 것과 게임에서 봤다는 것을 구별한다. 실제 화면 표본과 영상 내보내기는 verification/art-direction-v10에 있고 최종 실행 검사는 verification/polish/latest를 기준으로 한다. 전체 시간의 영상 시청, 실제 음향 청취, 사용자 미감/난이도 평가는 따로 남긴다.

