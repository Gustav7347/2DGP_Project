"""Scripted training capture for before/after comparison, not a difficulty test."""
from pathlib import Path
import argparse, array, ctypes, json, sys, wave


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--scenario',choices=('contact','movement','camera','ledge','timing','approach','gait','links'),default='contact')
    parser.add_argument('--augments',nargs='*',default=[])
    parser.add_argument('--enemy',choices=('sword','spear','boss'),default='sword')
    parser.add_argument('--phase',type=int,choices=(1,2),default=1)
    parser.add_argument('--clean',action='store_true',help='Omit diagnostic overlay from the image; keep fixture disclosure in JSON.')
    args=parser.parse_args(); root=args.project.resolve(); out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root))
    from pico2d import pico2d as p2
    from bladegame.core import Game,Controls,Enemy
    from bladegame.render import Renderer,capture
    p2.open_canvas(1280,720)
    p2.SDL_HideWindow(p2.window);p2.lattice_on=False
    p2.SDL_SetRenderDrawBlendMode(p2.renderer,p2.SDL_BLENDMODE_BLEND)
    renderer=Renderer();renderer.shake_enabled=True
    game=Game(11);game.start();game.stage_index=3;game.transition_banner=0;game.notices=[]
    game.player.x=440;game.player.style='moon';game.player.invulnerable=0
    game.player.augments.update(args.augments)
    target=Enemy(501,args.enemy,730,hp=260,max_hp=260,state='recovery',timer=99,
                 phase=args.phase,transitioned=args.enemy=='boss')
    if args.enemy=='boss':game.stage_index=3
    game.enemies=[target]; audio_events=[];frame=0
    if args.scenario=='gait':
        game.player.x=290;target.x=970;target.state='approach'
    if args.scenario=='movement':
        game.player.x=300;target.x=1900
    elif args.scenario=='camera':
        game.stage_index=1;game.player.x=900;target.x=2200
    elif args.scenario=='ledge':
        game.stage_index=1;game.player.x=600;game.player.y=205;target.x=750
    renderer.play_sound=lambda name:audio_events.append({'time':frame/60,'name':name})
    renderer.stop_sound=lambda channel:audio_events.append({'time':frame/60,'stop':channel})
    decoded={};state_samples=[]
    try:
        for frame in range(420):
            c=Controls()
            if args.scenario=='gait':
                c.move=1 if frame<84 else -1 if 152<=frame<212 else 0
            elif args.scenario=='links':
                c.move=1 if frame<155 else -1 if frame<200 else 1 if frame<276 else 0
                if frame in (36,52,71,250):c.attack=True
                if frame==219:c.parry=True
                if frame==194:
                    target.x=game.player.x+100;target.facing=-1
                    target.state='windup';target.timer=target.windup_total=.47
                    target.strike_spent=False;game.attack_owner=target.uid
            elif args.scenario=='approach':
                if frame<54:c.move=1
                if frame==27:
                    target.state='windup';target.facing=-1
                    target.timer=target.windup_total=.55
                    target.strike_spent=False;game.attack_owner=target.uid
                if frame==54:c.parry=True
                if frame==90:c.attack=True
            elif args.scenario=='timing':
                if frame==60:
                    game.player.x=560;game.player.facing=1;game.player.invulnerable=0
                    game._begin_attack();game.player.action_time=.206
                    target.x=645;target.state='windup';target.timer=.004;target.strike_spent=False
                    target.facing=-1;game.attack_owner=target.uid
                if frame==210:
                    game.hit_stop=0;game.effects=[]
                    game.player.x=560;game.player.hp=100;game.player.invulnerable=0
                    game.player.recoil_left=0
                    game._begin_attack(2);game.player.action_time=.54
                    game.player.attack_fired=game.player.attack_sounded=True
                    target.x=645;target.state='recovery';target.timer=99;target.recoil_left=0
                    c.attack=True
            elif args.scenario in ('movement','camera'):
                if frame<112:c.move=1
                elif 135<=frame<247:c.move=-1
                if frame in (60,180):c.jump=True
            else:
                if frame<24:c.move=1
                if frame in (48,66,85,207,367):c.attack=True
                if 168<=frame<195:c.move=-1
            if frame==300 and args.scenario=='contact':
                game.player.x=560;game.player.facing=1;game.player.action='idle'
                target.x=655;target.hp=max(90,target.hp);target.state='windup';target.facing=-1
                target.timer=target.windup_total=.55;target.strike_spent=False
                game.attack_owner=target.uid
            if frame==326 and args.scenario=='contact': c.parry=True
            if args.scenario!='timing':game.tick(1/60,c)
            elif frame%6==0:
                game.tick(.1,c)
                state_samples.append({'frame':frame,'action':game.player.action,'combo':game.player.combo_index+1,
                                'action_time':game.player.action_time,'hp':game.player.hp,'enemy_state':target.state})
            renderer.sound(game);renderer.draw(game,1/60)
            if not args.clean:renderer.text('Scripted training / fixed setup / not a playthrough',640,584,18,(222,180,108),True)
            if args.scenario=='timing':
                renderer.text('10fps 진단 · 동시 적중: 접촉 후 상대 공격' if frame<210 else '10fps 진단 · 마무리 회수 중 클릭 1회',640,535,21,(91,205,193),True)
            if frame%2==0: capture(out/f'frame-{frame//2:04d}.png')
            p2.update_canvas()
        for name,sound in renderer.sounds.items():
            chunk=sound.wav.contents
            samples=array.array('h',ctypes.string_at(chunk.abuf,chunk.alen))
            if sys.byteorder!='little':samples.byteswap()
            decoded[name]=[(samples[i]+samples[i+1])*.5 for i in range(0,len(samples)-1,2)]
    finally:p2.close_canvas()
    count=max(Renderer.sound_channel(name)[0] for name in decoded)+1
    length=7*44100; channels=[array.array('i',[0])*length for _ in range(count)]; ends=[0]*count
    for event in audio_events:
        if 'stop' in event:
            channel=event['stop'];start=round(event['time']*44100)
            for i in range(start,min(length,ends[channel])):channels[channel][i]=0
            ends[channel]=start
            continue
        name=event['name']; data=decoded.get(name,[])
        if hasattr(Renderer,'sound_channel'):channel,level=Renderer.sound_channel(name)
        else:
            channel=0 if name.startswith('swing') else 2 if name.startswith('parry') else 3 if name=='reward' else 1
            level=.45 if channel==3 else .85 if channel==1 else 1.
        start=round(event['time']*44100); gain=renderer.volume*level
        end=min(length,start+len(data))
        for i in range(start,min(length,ends[channel])):channels[channel][i]=0
        for i in range(start,end):channels[channel][i]=round(data[i-start]*gain)
        ends[channel]=end
    mixed=array.array('h',(max(-32768,min(32767,sum(c[i] for c in channels))) for i in range(length)))
    if sys.byteorder!='little':mixed.byteswap()
    with wave.open(str(out/'audio.wav'),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(44100);wav.writeframes(mixed.tobytes())
    report={'purpose':'Scripted training comparison; fixed initial positions and target health. No claim of human difficulty.',
            'project':str(root),'scenario':args.scenario,'fps':30,'duration':7,'frames':210,'audio_events':audio_events,
            'events':game.events,'final_hp':game.player.hp,'target_hp':target.hp,'samples':state_samples}
    (out/'preview.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(out)


if __name__=='__main__':main()
