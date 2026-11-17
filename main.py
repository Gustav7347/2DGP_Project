"""Run from any working directory: python path/to/main.py."""
from pathlib import Path
import argparse, json, time
from bladegame.core import Game, Controls
from bladegame import config as C


def main():
    parser=argparse.ArgumentParser(description='벼랑 아래 칼날')
    parser.add_argument('--gallery',action='store_true',help='주인공 모션 보기')
    parser.add_argument('--autoplay',action='store_true',help='일반 입력만 쓰는 전체 루프 검증')
    parser.add_argument('--fast',action='store_true',help='검증 모드만 고정 시간 간격으로 빠르게 실행')
    parser.add_argument('--frames',type=int,default=0,help='검증용 실행 프레임 제한')
    parser.add_argument('--capture-dir',type=Path,help='검증용 실제 화면 저장 위치')
    parser.add_argument('--report',type=Path,help='검증 결과 JSON')
    parser.add_argument('--input-check',action='store_true',help='SDL 키보드·마우스 입력 경로 검증')
    parser.add_argument('--ui-check',action='store_true',help='SDL 메뉴·설정·보상 입력 검증 (상태 고정 장면 포함)')
    parser.add_argument('--quiet-check',action='store_true',help='자동 검증만 숨김·음소거로 실행')
    args=parser.parse_args()
    if args.quiet_check and not (args.autoplay or args.input_check or args.ui_check):
        parser.error('--quiet-check는 --autoplay, --input-check 또는 --ui-check와 함께 사용합니다.')
    from pico2d import pico2d as p2
    from bladegame.render import Renderer, capture
    from bladegame import autoplay
    p2.open_canvas(C.WIDTH,C.HEIGHT,sync=not (args.autoplay and args.fast))
    if args.quiet_check: p2.SDL_HideWindow(p2.window)
    p2.print_fps=lambda: None
    p2.lattice_on=False
    p2.SDL_SetRenderDrawBlendMode(p2.renderer,p2.SDL_BLENDMODE_BLEND)
    p2.SDL_SetWindowTitle(p2.window,'벼랑 아래 칼날'.encode('utf-8'))
    renderer=Renderer()
    if args.quiet_check: renderer.muted=True
    from bladegame.preferences import Preferences
    preferences=Preferences() if not (args.autoplay or args.input_check or args.ui_check or args.gallery) else None
    if preferences:
        loaded_settings=preferences.load()
        for key,value in loaded_settings.items():setattr(renderer,key,value)
        renderer.set_volume(0)
        # set_volume deliberately unmutes changed volume; restore saved mute too.
        renderer.muted=loaded_settings['muted']
    saved_settings=Preferences.snapshot(renderer)
    ui=renderer.ui
    game=Game(104 if args.autoplay or args.input_check or args.ui_check else None)
    from bladegame.input_check import InputCheck
    input_check=InputCheck() if args.input_check else None
    from bladegame.ui_check import UICheck
    ui_check=UICheck() if args.ui_check else None
    held=set()
    left_held=False
    mouse=(0,0)
    running=True
    gallery=0 if args.gallery else None
    frame=0
    captured=set()
    reward_wait=0.
    finished_wait=0.
    if args.autoplay: game.start()
    previous=time.perf_counter()
    try:
        while running:
            now=time.perf_counter()
            dt=min(.25,now-previous)
            previous=now
            if (args.autoplay and args.fast) or input_check or ui_check: dt=1/60
            controls=Controls()
            if input_check: input_check.feed(frame,p2)
            if ui_check:ui_check.feed(frame,p2)
            for event in p2.get_events():
                if event.type==p2.SDL_QUIT: running=False
                elif event.type==p2.SDL_KEYDOWN:
                    was_held=event.key in held
                    held.add(event.key)
                    if was_held: continue
                    key=event.key
                    if gallery is not None:
                        if key==p2.SDLK_RIGHT: gallery=(gallery+1)%9; renderer.clock=0
                        elif key==p2.SDLK_LEFT: gallery=(gallery-1)%9; renderer.clock=0
                        elif key==p2.SDLK_RETURN: gallery=None; game.start(); held.clear()
                        elif key==p2.SDLK_ESCAPE: running=False
                        continue
                    if key==p2.SDLK_m: renderer.toggle_mute()
                    elif key==p2.SDLK_F7: renderer.set_volume(-.05)
                    elif key==p2.SDLK_F8: renderer.set_volume(.05)
                    elif key==p2.SDLK_F6: renderer.shake_enabled=not renderer.shake_enabled
                    elif key==p2.SDLK_F1 and (game.state!='dead' or game.result_visible): ui.open_help(game); held.clear(); left_held=False
                    elif key==p2.SDLK_ESCAPE:
                        if ui.page!='main':ui.back(game)
                        else:game.toggle_pause();ui.focus=0
                        held.clear();left_held=False
                    elif key==p2.SDLK_t and game.result_visible: game.state='title';ui.focus=0
                    elif key==p2.SDLK_r and game.state=='paused' and ui.page=='main': game.start(); held.clear();ui.focus=0
                    elif game.state=='reward' and ui.page=='main' and key in (p2.SDLK_1,p2.SDLK_2,p2.SDLK_3):
                        game.choose(key-p2.SDLK_1); held.clear();ui.reward_focus=0
                    elif game.state=='reward' and ui.page=='main' and key in (p2.SDLK_LEFT,p2.SDLK_RIGHT,p2.SDLK_a,p2.SDLK_d):
                        ui.reward_focus=(ui.reward_focus+(1 if key in (p2.SDLK_RIGHT,p2.SDLK_d) else -1))%len(game.choices)
                    elif game.state=='reward' and ui.page=='main' and key==p2.SDLK_RETURN:
                        game.choose(ui.reward_focus);held.clear();ui.reward_focus=0
                    elif ui.buttons(game):
                        if key in (p2.SDLK_UP,p2.SDLK_w,p2.SDLK_DOWN,p2.SDLK_s):
                            ui.focus=(ui.focus+(1 if key in (p2.SDLK_DOWN,p2.SDLK_s) else -1))%len(ui.buttons(game))
                        elif key==p2.SDLK_RETURN:running=ui.activate(game,renderer);held.clear()
                        elif ui.page=='settings' and ui.buttons(game)[ui.focus][0]!='back' and key in (p2.SDLK_LEFT,p2.SDLK_RIGHT,p2.SDLK_a,p2.SDLK_d):
                            ui.activate(game,renderer,adjust=1 if key in (p2.SDLK_RIGHT,p2.SDLK_d) else -1)
                    elif game.state=='playing':
                        if key==p2.SDLK_SPACE: controls.jump=True
                        elif key==p2.SDLK_q: controls.heal=True
                elif event.type==p2.SDL_KEYUP: held.discard(event.key)
                elif event.type==p2.SDL_MOUSEMOTION:
                    mouse=(event.x,C.HEIGHT-event.y);ui.hover(game,*mouse)
                elif event.type==p2.SDL_MOUSEBUTTONDOWN:
                    mouse=(event.x,C.HEIGHT-event.y)
                    if game.state=='reward' and ui.page=='main' and event.button==p2.SDL_BUTTON_LEFT:
                        game.choose(renderer.card_at(*mouse)); held.clear();ui.reward_focus=0
                    elif ui.buttons(game) and event.button==p2.SDL_BUTTON_LEFT:
                        index=ui.button_at(game,*mouse)
                        if index>=0:
                            ui.focus=index
                            running=ui.activate(game,renderer,index,adjust=-1 if mouse[0]<640 else 1)
                            held.clear();left_held=False
                    elif game.state=='playing':
                        if event.button==p2.SDL_BUTTON_LEFT: controls.attack=True; left_held=True
                        elif event.button==p2.SDL_BUTTON_RIGHT: controls.parry=True
                elif event.type==p2.SDL_MOUSEBUTTONUP:
                    if event.button==p2.SDL_BUTTON_LEFT: left_held=False
                elif event.type==p2.SDL_WINDOWEVENT:
                    # pico2d does not expose window-event details; keyboard focus is
                    # also checked below to clear movement on Alt-Tab.
                    pass
            if not (input_check or ui_check or args.autoplay) and not p2.SDL_GetWindowFlags(p2.window)&p2.SDL_WINDOW_INPUT_FOCUS:
                held.clear();left_held=False;ui.focus_lost(game)
            current_settings=Preferences.snapshot(renderer)
            if preferences and current_settings!=saved_settings:
                success=preferences.save(renderer)
                ui.settings_status='설정은 다음 실행에도 유지됩니다.' if success else '저장하지 못했습니다. 이번 실행에만 적용됩니다.'
                saved_settings=current_settings
            p2.SDL_SetWindowTitle(p2.window,'벼랑 아래 칼날'.encode('utf-8'))
            controls.move=int(bool({p2.SDLK_d,p2.SDLK_RIGHT}&held))-int(bool({p2.SDLK_a,p2.SDLK_LEFT}&held))
            controls.attack_held=left_held and game.state=='playing'
            if game.state!='playing': left_held=False
            if args.autoplay:
                controls=autoplay.control(game)
                if game.state=='reward':
                    reward_wait+=dt
                    if reward_wait>1.0:
                        game.choose(autoplay.choose(game)); reward_wait=0.
                if game.state in ('dead','clear'):
                    finished_wait+=dt
                    if finished_wait>1.5: running=False
            game.tick(dt,controls)
            if input_check: input_check.observe(frame,game)
            if ui_check:ui_check.observe(frame,game,renderer)
            if not args.quiet_check:renderer.sound(game)
            renderer.draw(game,dt,mouse,gallery)
            if args.capture_dir:
                name=None
                if gallery is not None and frame==30: name=f'motion-{gallery+1}'
                elif ui.page!='main':name=f'ui-{ui.page}'
                elif game.state in ('title','reward','dead','clear','paused'): name=f'{game.state}-{game.stage_index+1}'
                elif game.state=='playing' and game.stage_time>3:
                    name=f'stage-{game.stage_index+1}'
                    boss=next((e for e in game.living if e.boss and e.phase==2),None)
                    if boss: name='boss-phase-2'
                if name and name not in captured:
                    capture(args.capture_dir/f'{name}.png'); captured.add(name)
                for enemy in game.living:
                    if enemy.boss and enemy.state in ('windup','active','stunned'):
                        diagnostic=f'boss-{enemy.phase}-{enemy.current_attack}-{enemy.state}'
                        if diagnostic not in captured:
                            capture(args.capture_dir/f'{diagnostic}.png'); captured.add(diagnostic)
            p2.update_canvas()
            frame+=1
            if args.frames and frame>=args.frames: running=False
            if not (args.autoplay and args.fast):
                elapsed=time.perf_counter()-now
                if elapsed<1/120: p2.delay(1/120-elapsed)
        if args.report:
            report={'state':game.state,'simulation_seconds':round(game.time,2),'frames':frame,
                'hp':round(game.player.hp,2),'kills':game.player.kills,'parries':game.player.parries,
                'style':game.player.style,'augments':sorted(game.player.augments),'events':game.events,'milestones':game.milestones,'last_hit':game.last_hit}
            if input_check: report['input_check']=input_check.verify()
            if ui_check:report['ui_check']=ui_check.verify();report['purpose']='SDL menu input with staged reward/death fixtures; not combat validation'
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
            print(json.dumps({k:v for k,v in report.items() if k not in ('events','milestones')},ensure_ascii=False))
    finally:
        p2.close_canvas()


if __name__=='__main__': main()
