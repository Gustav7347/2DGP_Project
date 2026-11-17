"""Fixed native before/after fixtures. Not a human difficulty/listening test."""
from pathlib import Path
import argparse,json,sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.project.resolve()))
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    from pico2d import pico2d as p2
    from bladegame.core import Game,Controls,Enemy
    from bladegame.render import Renderer,capture
    p2.open_canvas(1280,720);p2.SDL_HideWindow(p2.window);p2.lattice_on=False
    p2.SDL_SetRenderDrawBlendMode(p2.renderer,p2.SDL_BLENDMODE_BLEND)
    r=Renderer();r.muted=True;r.shake_enabled=False;rows=[]
    try:
        for kind,phase in (('sword',1),('spear',1),('boss',1),('boss',2)):
            for face,air in ((1,False),(-1,False),(1,True),(-1,True)):
                g=Game(41);g.start();g.stage_index=3;g.transition_banner=0;g.notices=[]
                p=g.player;p.x=620;p.facing=face;p.invulnerable=0;p.hp=50;p.style='moon'
                if air:p.y=168;p.grounded=False
                e=Enemy(91,kind,620+face*95,facing=-face,hp=500,max_hp=500,
                        state='recovery',timer=99,phase=phase)
                g.enemies=[e];g.tick(1/120,Controls(parry=True));g._enemy_strike(e)
                start=g.time;prefix=f'{kind}-{phase}-{face}-{int(air)}'
                for label,elapsed in (('contact',0.),('sweep',.10),('settle',.18),('recover',.30)):
                    while g.time-start<elapsed-1e-8:g.tick(1/120)
                    r.draw(g,1/60);p2.update_canvas();capture(out/f'{prefix}-{label}.png')
                    rows.append(dict(kind=kind,phase=phase,facing=face,airborne=air,
                                     label=label,asset=r.enemy_pose(e),state=e.state))
        # Third successful moon parry: brief contact followed by actual stun.
        for phase in (1,2):
            g=Game(41);g.start();g.stage_index=3;g.transition_banner=0;g.notices=[]
            p=g.player;p.x=620;p.facing=1;p.style='moon';p.invulnerable=0
            e=Enemy(91,'boss',715,facing=-1,hp=500,max_hp=500,state='recovery',timer=99,
                    phase=phase,parry_count=2);g.enemies=[e]
            g.tick(1/120,Controls(parry=True));g._enemy_strike(e);start=g.time
            while g.time-start<.1:g.tick(1/120)
            assert e.state=='stunned' and r.enemy_pose(e)==('boss-extra',1)
            r.draw(g,1/60);p2.update_canvas();capture(out/f'boss-{phase}-third-stun.png')
    finally:p2.close_canvas()
    report=dict(project=str(args.project.resolve()),fixtures=rows,listened=False,
                human_motion_approval=False,description='Fixed one-enemy parry; simulation and hidden muted SDL.')
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(f'{len(rows)} samples and two third-parry stun probes written to {out}')


if __name__=='__main__':main()
