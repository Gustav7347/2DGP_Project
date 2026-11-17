"""Capture real SDL screens for product-flow review, not difficulty evidence."""
from pathlib import Path
import argparse, ctypes, json, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--project',type=Path,default=ROOT)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(args.project.resolve()))
    from pico2d import pico2d as p2
    from bladegame.core import Game,Enemy
    from bladegame import config as C
    from bladegame.render import Renderer,capture
    p2.open_canvas(1280,720);p2.SDL_HideWindow(p2.window);p2.lattice_on=False
    p2.SDL_SetRenderDrawBlendMode(p2.renderer,p2.SDL_BLENDMODE_BLEND)
    names=[]
    try:
        renderer=Renderer();renderer.muted=True;renderer.shake_enabled=False
        labels=[];original_text=renderer.text;feedback=[]
        def observe(text,x,y,size=18,*rest,**kwargs):
            if str(text).startswith('마지막 피격'):
                width,height=ctypes.c_int(),ctypes.c_int()
                p2.TTF_SizeUTF8(renderer.fonts[size].font,str(text).encode('utf-8'),ctypes.byref(width),ctypes.byref(height))
                labels.append({'text':text,'width':width.value})
            return original_text(text,x,y,size,*rest,**kwargs)
        renderer.text=observe
        def save(name,game,mouse=(0,0)):
            if hasattr(renderer,'ui'):renderer.ui.hover(game,*mouse)
            labels.clear()
            renderer.clock=1.2;renderer.draw(game,0,mouse);capture(args.out/f'{name}.png')
            p2.update_canvas();names.append(name)
        game=Game(104);save('title',game)
        if hasattr(renderer,'ui'):
            for page in ('help','settings'):
                renderer.ui.page=page;save(page,game)
            renderer.ui.page='main'
        for index in range(4):
            game.start();game._enter_stage(index);game.transition_banner=0;game.notices=[]
            game.player.style=None if index==0 else 'moon'
            game.player.augments=set() if index<2 else {'insight'} if index==2 else {'insight','bleed'}
            save(f'stage-{index+1}',game)
        game.start();game.player.x=800;game.camera=288;game.enemies=[];game.transition_banner=0;game.notices=[]
        save('route',game)
        game._enter_stage(2);game.player.style='chain';game.player.augments={'echo'}
        game.player.x=850;game.camera=338;game.enemies=[];game.wave_index=1;game.notices=[];game._spawn_wave()
        game.transition_banner=0;save('flanking-entry',game)
        game.start();game.state='reward';game.choices=['blood','moon','chain'];save('reward-style',game,(630,350))
        game._enter_stage(1);game.player.style='moon';game.state='reward'
        game.choices=['counter','insight','revive'];save('reward-augment',game,(630,350))
        if hasattr(renderer,'ui'):
            renderer.ui.open_help(game);save('reward-help',game);renderer.ui.back(game)
        game.state='paused';save('pause',game)
        game.state='dead';game.player.action='death';game.player.action_time=1.5;save('dead',game)
        game._enter_stage(3);game.state='clear';save('clear',game)
        for reason in ('behind','window_ended','spent','counter_cost','unblocked','unknown'):
            game.start();game._enter_stage(3);game.transition_banner=0;game.notices=[]
            p=game.player;p.hp=1;p.invulnerable=0;p.style='moon'
            enemy=Enemy(501,'boss',p.x+85,hp=420,max_hp=420,state='active',facing=-1)
            game.enemies=[enemy]
            if reason=='behind':enemy.x=p.x-85;enemy.facing=1
            if reason in ('window_ended','spent','counter_cost'):
                p.action='parry';p.action_time=C.PARRY_WINDOW+.001 if reason=='window_ended' else .1
                p.parry_ready=reason!='spent'
            if reason=='counter_cost':p.augments={'counter'}
            if reason=='unknown':game._hurt_player(9999)
            else:game._enemy_strike(enemy)
            assert game.state=='dead',reason
            hit=getattr(game,'last_hit',None)
            if hasattr(game,'last_hit'):
                expected={'enemy_kind':None if reason=='unknown' else 'boss','attack':None if reason=='unknown' else 'slash','reason':reason,'stage':4}
                assert hit==expected,(reason,hit)
            for _ in range(66):game.tick(1/60)
            assert game.player.action_time>.85
            save('hit-'+reason,game)
            if hasattr(game,'last_hit'):assert len(labels)==1 and labels[0]['width']<=1120,(reason,labels)
            feedback.append({'reason':reason,'last_hit':hit,'tracking_available':hasattr(game,'last_hit'),'labels':list(labels)})
        (args.out/'screens.json').write_text(json.dumps({'screens':names,'purpose':'staged UI review; not a human playthrough'},indent=2),'utf-8')
        (args.out/'hit-feedback.json').write_text(json.dumps(feedback,ensure_ascii=False,indent=2),'utf-8')
    finally:p2.close_canvas()
    print(args.out)


if __name__=='__main__':main()
