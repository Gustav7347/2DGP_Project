# 에셋 출처

## D29 글꼴과 UI

현재 글꼴은 [Galmuri / quiple](https://github.com/quiple/galmuri)의 v2.40.4 배포본이다. Galmuri9.ttf·Galmuri11.ttf·Galmuri11-Bold.ttf를 수정 없이 포함했다. [SIL Open Font License 1.1](fonts/Galmuri-OFL.txt), 원본 주소/개별 SHA256은 [글꼴 출처](fonts/SOURCE.json)에 있다. 본문은 갈무리9의20px, 일반 정보는 갈무리11의24px, 제목/강조는 갈무리11 Bold의24/36/48/72/96px을 사용한다. OS 기본 글꼴을 게임 자산으로 복사하지 않았다.

현재 먹색 패널·검붉은 선택선·키 표시는 코드로 제작한 자체 도형이다. 기존 Lorc/Game-icons의 아이콘과 자체 비네트/인물 문장은 계속 사용하며 아래 출처 고지를 유지한다. D24의 금속 프레임 PNG는 과거 시안 자산이고 현재 패널 출력에는 사용하지 않는다. 비교용 다른 서체와 Steam 참고 스크린샷은 검증 폴더에만 두며 게임에 재배포하지 않는다.

## 현재 D24 화면·동작·음향

2026-11-09: 현재 달리기는 이 프로젝트용 AI 생성 `player/run-authored-v6.png`의 전신8프레임이다. [Martial Hero / LuizMelo](https://luizmelo.itch.io/martial-hero)의 CC0 동작을 참고했으며 원본 캐릭터 스프라이트는 배포하지 않는다. 이전 분리 리그는 보존한 시안이며 활성 동작이 아니다. 제작·보류 이유는 [달리기 제작 기록](player/RUN_GENERATION.md)에 있다.

UI 아이콘은 **Lorc / [Game-icons.net](https://game-icons.net)**, [CC BY3.0](https://creativecommons.org/licenses/by/3.0/)다. 출처SVG·개별 blobID·수정 내용·원문 고지는 [UI 출처](ui/ATTRIBUTION.md), ui/sources.json, licenses/game-icons-license.txt에 포함했다. 배경 사각형 제거·색 통일·PNG 내보내기를 적용했으며 F1 도움말에도 저자를 표시한다. 철제/먹색 프레임·인장·삿갓 문장은 프로젝트용으로 코드로 만든 SVG/PNG이며 Kenney의 UI 그림을 가져온 것이 아니다. 바탕·맑은고딕은 설치된 Windows 글꼴을 읽고 재배포하지 않는다.

현재 새 효과음14개(휘두름/적중/패링 각3,선택1,발소리2,점프1,착지1)는 rubberduck의 [80 CC0 RPG SFX](https://opengameart.org/content/80-cc0-rpg-sfx)와 Kenney의 [RPG Audio](https://kenney.nl/assets/rpg-audio), [Impact Sounds](https://kenney.nl/assets/impact-sounds), [Interface Sounds](https://kenney.nl/assets/interface-sounds)에서 실제 선택한 소스를 편집했다. 모두 CC0이며 원본ZIP/OGG·라이선스·게시자 페이지·재생성 해시는 assets/licenses/presentation-v2와 source-presentation-v2 파일에 보존했다. 상세 선택과 가공은 [새 음향 고지](licenses/presentation-v2/NOTICE.md)와 tools/prepare_presentation_audio.py를 따른다. 기존 G 원음을 새 세트에 재사용하지 않았고 피격 hurt는 기존의 짧은 몸 타격음을 유지한다. 측정·무음 믹서 연결과 실제 청취는 구분한다.

아래 D21~D23 및 이전 음원 목록은 제작 이력이다. 현재 재생 파일은 bladegame/config.py의 SOUND_FILES가 기준이다.

2026-11-08 보완: 보스의 찌르기·기절·2페이즈 추가 자세와 돌/목재 바닥·발판도 이 프로젝트용 AI 생성 에셋이다. 실제로 쓰지 않는 셀은 좌표 목록에서 제외하고, 찌르기는 단독 스프라이트로 분리해 인접 셀의 칼이 잘리지 않도록 했다. 원본 PNG를 보존하고 런타임 클리핑용 좌표만 작성한다.

## 캐릭터·배경

2026-11-09 D23 당시: `player/run-rig-v1.png`는 기존 주인공을 참고해 내장 imagegen으로 생성한 달리기 분리 원화였다. D24에서 전신 시트로 교체했으며 이전 원본은 보존한다.

2026-11-08 제품 흐름 보완: `backgrounds/mountain-trail-v1.png`와 `backgrounds/dojo-courtyard-v1.png`는 기존 배경을 스타일 참고로 내장 image_gen에서 별도 생성했다. 원본 산 배경을 보존했고 새 파일을 각각 산길·도장 앞에 연결했다. 최종 요청문은 [배경 생성 기록](backgrounds/GENERATION.md)에 보존했다. 게임에서 비·색조를 별도 렌더링하며 새 배경 PNG 자체를 재편집하지 않았다.

주인공(삿갓·남색 무복·적색 허리띠), 검사, 창병, 도장주, 산과 도장 배경은 이 프로젝트용으로 AI 이미지 생성 도구에서 제작했다. 주인공은 몸과 공통 장검을 나누어 사용한다. 프레임 좌표·손 위치·칼 각도·타이밍은 게임의 JSON 데이터로 지정한다. 원본 PNG를 자동 보정하거나 배경 제거 필터로 다시 가공하지 않았다.

기존 1타 공격 제작 때 [Martial Hero / LuizMelo](https://luizmelo.itch.io/martial-hero)의 공개 동작 영상을 준비·회전·회수의 참고로 사용했다. 해당 게임 캐릭터 이미지나 스프라이트 파일은 배포물에 넣지 않았다.

## PixelFX

[patch-gg/pixelfx](https://github.com/patch-gg/pixelfx), MIT License.

- 사용 효과: `melee/sword-slash`, `melee/thrust`, `impacts/parry`, `impacts/hit-spark`.
- PNG·JSON 시트로 내보냈으며 검격 팔레트를 게임의 회색·백색 계열로 조정했다.
- 라이선스 원문: `licenses/pixelfx-MIT.txt`, 고지: `licenses/pixelfx-NOTICE.md`.
- 일부 효과 원작: Hugo Duprez / Sprite Fusion, MIT. 포함된 원문 고지를 유지한다.
- PixelFX의 기본 캐릭터·전용 글꼴은 사용하지 않는다.

## 녹음 효과음

### 현재 검격 적중·패링 구성

2026-11-08 D21: 새로운 검격 원음을 내려받거나 다시 합성하지 않았다. 기존 `game-impact-3-soft.wav`를 육참골단 반격 역할에도 연결하고, 잔영은 별도 채널의 낮은 게인으로 혼합한다. 패링의 남은 칼바람 정리와 같은 반격의 중복 피격음 정리는 런타임 처리다. 음색의 사용자 채택이나 청취 합격으로 해석하지 않는다.

- [Sword Hit / qubodup](https://freesound.org/people/qubodup/sounds/442769/), CC0. 제작자는 FreeDink의 sword1.wav 대체를 목표로 구성한 소리라고 설명한다. 실제 배포 게임에서 채택됐다는 뜻으로 쓰지 않는다. `source-game-sword.mp3`와 변환 PCM 사본을 보존했다.
- [Slash - Rpg / colorsCrimsonTears](https://freesound.org/people/colorsCrimsonTears/sounds/580307/), CC0. 클래식 RPG에서 적을 베는 소리를 목표로 제작한 완성형 절삭음이다. `source-game-rpg-slash.mp3`와 PCM 사본을 보존했다.
- [Meat Slime Hit Layer 1](https://freesound.org/people/qubodup/sounds/877025/), [2](https://freesound.org/people/qubodup/sounds/877026/), [3](https://freesound.org/people/qubodup/sounds/877027/), qubodup, CC0. 제작자는 Netherspire 트레일러용 베기 적중을 보강하기 위해 구성했다고 설명한다. `source-game-cut-1/2/3.mp3`와 PCM 사본을 보존했다.
- 위 파일은 로그인 없이 공개된 Freesound 고품질 MP3 미리보기를 내려받아 사용했다. 원본 WAV/FLAC 마스터나 무손실 다운로드라고 부르지 않는다. PCM 사본은 SDL_mixer로 44.1kHz mono로 변환하고 25% 게인을 적용했다. 편집 시 층별 음량을 다시 맞췄다.
- `game-impact-1/2/3-soft.wav`: 완성형 검격·절삭·베기 대상 소리를 겹친 0.29/0.32/0.38초 적중음. `game-parry-1/2/3-soft.wav`: 기존 StarNinjas 금속 반응에 짧은 검격층을 겹치고 0.21초로 정리했다. 제작용 `tools/prepare_game_audio.py`로 재현하며 numpy는 제작 시에만 필요하다.
- 현재 게임은 휘두름에 기존 칼바람, 적중에 새 검격 합성, 피격에 기존 몸 타격, 패링에 새 짧은 금속 반응을 사용한다. 합성은 소리 층을 섞는다는 의미이며 생성형 모델로 만든 음원이라는 뜻이 아니다. 전투 기본 음량 15%와 채널 제한은 유지한다.

### 기존 소스와 보존한 이전 구성

- [Swishes Sound Pack / artisticdude](https://opengameart.org/content/swishes-sound-pack), CC0. `swish-1.wav`, `swish-7.wav`, `swish-9.wav`를 검격 바람 소리로 사용.
- [20 Sword Sound Effects / StarNinjas](https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes), CC0. `sword.4.ogg`, `sword_clash.3.ogg`, `sword_clash.5.ogg`, `sword_clash.8.ogg`, `sword_clash.10.ogg`를 적중·패링·선택에 사용. [작가 페이지](https://opengameart.org/users/starninjas).
- [37 hits/punches / Independent.nu](https://opengameart.org/node/2558), qubodup 게시, CC0. `hit09.mp3.flac`, `hit10.mp3.flac`, `hit18.mp3.flac`를 각각 `body-1.flac`, `body-2.flac`, `body-3.flac`로 보존했다. 이 녹음과 소량의 기존 칼 적중음을 혼합해 1·2·3타의 `impact-*-soft.wav`를 만들었다. 몸 타격음은 0.20/0.24/0.30초, 2.2kHz 저역 통과, 피크 0.30/0.32/0.36으로 제한했다. 합성 발진음은 추가하지 않았다.
- 런타임에는 원본에서 고음·DC 성분·앞뒤 클릭을 줄이고 피크를 제한한 `*-soft.wav` 파일을 사용한다. 패링 금속음은 0.48초·2.1kHz·피크 0.34로 줄였다. 기본 재생 음량 15%, 칼바람 채널은 그중 65%, 일반 적중 85%, 잔영검 42.5%. 원본 녹음 파일도 함께 보존한다. 수치는 장치별 청취 평가를 대신하지 않는다.
- CC0 원문: <https://creativecommons.org/publicdomain/zero/1.0/>.

Windows 맑은 고딕은 설치된 시스템 글꼴을 읽으며 게임 폴더에 재배포하지 않는다.

v26 주인공 질주(run-v26.png)와 제동 자세(brake-v26.png)는 기존 주인공 복장을 참조한 내장 imagegen 생성물이다. 질주 후보 8칸에서 7자세를 선택하고 발·손·칼 기준점을 개별 등록했다.
