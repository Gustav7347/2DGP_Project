"""Hidden native art probes. Geometry/layout evidence is not aesthetic approval."""
from pathlib import Path
import argparse,json,math,sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    out=parser.parse_args().out.resolve();out.mkdir(parents=True,exist_ok=True)
    from pico2d import pico2d as p2
    from bladegame.core import Game,Controls,Enemy
    from bladegame.render import Renderer,capture,box
    from bladegame import motion,config as C
    p2.open_canvas(1280,720);p2.SDL_HideWindow(p2.window);p2.lattice_on=False
    p2.SDL_SetRenderDrawBlendMode(p2.renderer,p2.SDL_BLENDMODE_BLEND)
    r=Renderer();r.muted=True;r.shake_enabled=False;rows=[];cards=[]
    try:
        for face in (1,-1):
            for air in (False,True):
                g=Game(41);g.start();g.stage_index=3;g.transition_banner=0;g.notices=[]
                p=g.player;p.x=620;p.facing=face;p.invulnerable=0;p.hp=50
                if air:p.y=168;p.grounded=False
                g.enemies=[Enemy(i,'sword',620+face*(85+i-90),facing=-face,hp=500,max_hp=500,state='recovery',timer=99) for i in (91,92)]
                g.tick(1/120,Controls(parry=True));g._enemy_strike(g.enemies[0]);start=g.time
                for label,elapsed in (('contact',0.),('sweep',.10),('settle',.18)):
                    while g.time-start<elapsed-1e-8:g.tick(1/120)
                    if label=='sweep':g._enemy_strike(g.enemies[1])
                    r.draw(g,1/60);p2.update_canvas()
                    capture(out/f'{face}-{int(air)}-{label}.png')
                    if label=='sweep':
                        fx=next(e for e in reversed(g.effects) if e['kind']=='parry')
                        spark=r.contact_point(fx,(fx['x'],fx['y']))
                        anim=r.hero_data['animations']['parry'];seconds=motion.parry_pose_time(anim,p.action_time,p.parry_feedback)
                        a,b=motion.blade_edge(anim,r.hero_data['weapon'],seconds,p.x,p.y,face,148,continuous=False)
                        dx,dy=b[0]-a[0],b[1]-a[1]
                        distance=abs((spark[0]-a[0])*dy-(spark[1]-a[1])*dx)/math.hypot(dx,dy)
                        assert distance<1e-6,(face,air,distance)
                        rows.append(dict(facing=face,airborne=air,second_contact_distance=distance))
        original=r.text
        for stage,keys in ((0,list(C.STYLES)),(1,list(C.AUGMENTS)[:3]),(1,list(C.AUGMENTS)[3:])):
            g=Game(41);g.start();g.stage_index=stage;g.state='reward';g.choices=keys;r.ui.reward_focus=1
            drawn=[]
            def text(*args,**kwargs):
                if args[1] in (128,498,868) and 180<=args[2]<=385:
                    size=args[3] if len(args)>3 else 18
                    width=r.text_width(args[0],size,kwargs.get('display',False))
                    assert width<=284,(args[0],width)
                    assert args[2]>=190,(args[0],args[2])
                    drawn.append(dict(text=args[0],y=args[2],width=width))
                return original(*args,**kwargs)
            r.text=text;r.draw(g,1/60);p2.update_canvas();capture(out/f'cards-{stage}-{keys[0]}.png');r.text=original
            assert len(drawn)>=18,drawn
            cards.append(dict(keys=keys,min_baseline=min(v['y'] for v in drawn),lines=len(drawn)))
    finally:p2.close_canvas()
    (out/'report.json').write_text(json.dumps(dict(contacts=rows,cards=cards,listened=False,human_aesthetic_approval=False),indent=2),encoding='utf8')
    print(json.dumps(dict(contacts=len(rows),cards=sum(len(c['keys']) for c in cards),status='passed')))

if __name__=='__main__':main()
