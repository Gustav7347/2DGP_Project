"""Ink, red cord and pixel lettering. Presentation never owns combat input."""
from pathlib import Path
import math
from pico2d import pico2d as p2
from . import config as C
from .interface import choice_detail,combat_status,reward_sections

PALE=(235,231,211);GOLD=(211,183,126);MUTED=(179,187,188)
RED=(170,57,64);TEAL=(120,193,181);DARK=(12,18,24)
GLYPHS={'blood':'bloody-sword','moon':'moon','chain':'crossed-swords','counter':'blade-bite',
        'echo':'crossed-slashes','bleed':'bleeding-wound','insight':'eye-shield',
        'unyielding':'ninja-mask','revive':'ankh'}


def rect(x,y,w,h,color,alpha=255):
    p2.draw_rectangle(x,y,x+w,y+h,*color,alpha,filled=True)


class GameUI:
    def __init__(self,renderer):
        self.r=renderer
        root=Path(__file__).resolve().parents[1]/'assets/ui'
        self.images={p.stem:p2.load_image(str(p)) for p in root.glob('*.png')}

    def frame(self,name,x,y,w,h,alpha=1.):
        if name=='vignette':
            image=self.images[name];image.opacify(alpha);image.draw(x+w/2,y+h/2,w,h);image.opacify(1.)
            return
        rect(x,y,w,h,DARK,round(239*alpha))
        edge=(91,86,70)
        rect(x+12,y+h-2,w-24,1,edge,round(190*alpha))
        rect(x,y+12,1,h-24,edge,round(150*alpha))
        rect(x+w-1,y+12,1,h-24,edge,round(150*alpha))
        for sx,sy,sign in ((x,y+h,1),(x+w,y+h,-1),(x,y,1),(x+w,y,-1)):
            rect(sx if sign==1 else sx-12,sy-2 if sy==y+h else sy,12,2,GOLD,round(150*alpha))
        rect(x+5,y+h-24,3,16,RED,round(255*alpha))

    def icon(self,name,x,y,size,color=PALE,alpha=1.):
        image=self.images[name];image.opacify(alpha)
        p2.SDL_SetTextureColorMod(image.texture,*color);image.draw(x,y,size,size)
        p2.SDL_SetTextureColorMod(image.texture,255,255,255);image.opacify(1.)

    def seal(self,key,x,y,size=48,color=GOLD,alpha=1.):
        half=size/2;rect(x-half,y-half,size,size,DARK,round(210*alpha))
        p2.draw_rectangle(x-half,y-half,x+half,y+half,*color,round(110*alpha))
        if key in ('pointy-sword','eye-shield'):self.action_glyph(key,x,y,size*.65,color)
        else:self.icon(GLYPHS.get(key,key),x,y,size*.65,color,alpha)

    def action_glyph(self,key,x,y,size,color):
        scale=size/28
        lines=([(-8,-9,9,10),(-6,-2,0,-8),(-10,-12,-5,-7)] if key=='pointy-sword' else
               [(0,-9,0,12),(-6,-4,6,-4),(0,-13,0,-6),(-12,10,9,0),(-8,10,-12,4)])
        for x0,y0,x1,y1 in lines:
            for ox,oy in ((0,0),(1,0),(0,1)):
                p2.draw_line(x+x0*scale+ox,y+y0*scale+oy,x+x1*scale+ox,y+y1*scale+oy,*color,255)

    def key(self,label,x,y,width=38):
        width=max(width,self.r.text_width(label,20)+14)
        rect(x-width/2,y-13,width,28,(29,38,44));rect(x-width/2,y-13,width,2,(92,109,113))
        self.r.text(label,x,y,20,PALE,True)

    def bar(self,x,y,w,h,value,trail=None):
        rect(x-2,y-2,w+4,h+4,(7,10,15));rect(x,y,w,h,(55,29,35))
        if trail is not None:rect(x,y,w*max(0,min(1,trail)),h,GOLD,180)
        width=w*max(0,min(1,value))
        if width:rect(x,y,width,h,RED);rect(x,y+h-3,width,3,(220,109,105))

    def block(self,text,x,y,width,size=20,color=PALE,display=False):
        for line in self.r.wrap_text(text,size,width,display):
            self.r.text(line,x,y,size,color,display=display);y-=26
        return y

    def toast(self,text,x,y,width=330,alpha=1.):
        x=max(width/2+8,min(C.WIDTH-width/2-8,x))
        self.frame('band',x-width/2,y-17,width,43,alpha);self.r.text(text,x,y+2,20,PALE,True)

    def enemy_cue(self,e,x):
        y=e.y+(206 if e.boss else 187)
        if e.state=='arriving':self.seal('crossed-swords',x,y,28,MUTED,.65)
        if e.bleed_left>0:self.icon('bleeding-wound',x+35,e.y+164,19,RED)
        if e.state=='stunned':
            for n in range(3):
                angle=self.r.clock*3+n*math.tau/3;rect(x+math.cos(angle)*20-2,y+math.sin(angle)*5,4,4,TEAL)
        if e.state!='windup':return
        color=PALE if e.timer<=.18 else GOLD
        self.icon('pointy-sword' if e.current_attack=='thrust' else 'crossed-swords',x,y,25,color)
        progress=1-e.timer/max(.001,e.windup_total)
        for n in range(max(0,min(24,round(progress*24)))):
            a=math.pi/2-n*math.tau/24;b=a-math.tau/24
            p2.draw_line(x+math.cos(a)*21,y+math.sin(a)*21,x+math.cos(b)*21,y+math.sin(b)*21,*color,255)
        if e.pattern in ('combo','chain'):self.icon('crossed-slashes' if e.pattern=='combo' else 'pointy-sword',x+28,y+11,17,color)

    def hud(self,g,camera,mouse):
        r=self.r;p=g.player
        # The swordsman's portrait anchors the vitality strip.
        self.frame('panel',22,16,480,78)
        image=r.hero['idle']
        image.clip_draw(79,image.h-275,185,185,64,56,76,76)
        p2.draw_line(101,18,101,91,*GOLD,210)
        p2.draw_line(105,91,406,91,*GOLD,155)
        style=C.STYLES[p.style][0] if p.style else '검객'
        detail=f'  {p.stacks}중첩' if p.style=='chain' else f'  ×{p.multiplier:.2f}' if p.style=='blood' else ''
        r.text(style+detail,108,84,24,PALE,display=True)
        self.bar(108,52,252,15,p.hp/C.MAX_HP,r.hp_trail/C.MAX_HP)
        r.text(f'{math.ceil(p.hp)}',392,58,24,PALE,True,display=True)
        keys=[k for k in C.AUGMENTS if k in p.augments]
        for i,key in enumerate(keys):
            x=120+i*146;spent=(key=='revive' and p.revive_used) or (key=='unyielding' and p.unyielding_used)
            self.icon(GLYPHS[key],x,25,20,MUTED if spent else GOLD,.45 if spent else 1.)
            r.text(C.AUGMENTS[key][0],x+20,25,20,MUTED if spent else PALE)
            if abs(mouse[0]-(x+47))<68 and 12<mouse[1]<40:self.tooltip(key,p,x+80,129,spent)
        if not keys:
            for slot in (122,151):
                p2.draw_line(slot-6,29,slot,35,*GOLD,150)
                p2.draw_line(slot,35,slot+6,29,*GOLD,150)
                p2.draw_line(slot+6,29,slot,23,*GOLD,150)
                p2.draw_line(slot,23,slot-6,29,*GOLD,150)
        available=g.can_heal()
        color=TEAL if available else MUTED
        self.icon('potion-ball',457,72,28,color,1. if available else .5)
        r.text(str(p.heals),482,72,20,color,True)
        label='Q 회복' if available else '회복 중' if p.action=='heal' else '소진' if not p.heals else '최대' if p.hp>=C.MAX_HP else '대기'
        r.text(label,457,30,18,color,True)
        if any(effect['kind']=='heal_interrupted' for effect in g.effects):
            self.toast('회복 중단 · 약은 남아 있음',272,126,330)
        if p.unyielding_left>0 or p.insight or p.counter_ready:
            self.frame('band',530,18,350,50);r.text(combat_status(p),550,43,20,TEAL)
        self.frame('panel',1010,636,248,68);r.text(g.stage['name'],1029,684,24,PALE,display=True)
        r.text(f'전투 {g.wave_index+1}/{len(g.stage["waves"])}',1205,684,18,MUTED,True)
        r.text(f'전체 {g.stage_index+1}/4',1029,654,15,MUTED)
        for i in range(4):rect(1144+i*24,652,17,5,RED if i==g.stage_index else TEAL if i<g.stage_index else (65,78,84))
        for x,key,label,enabled in ((1110,'pointy-sword','좌클릭',True),(1210,'eye-shield','우클릭',p.parry_cooldown<=0)):
            active=key=='eye-shield' and (p.parry_ready or p.parry_feedback>0)
            self.seal(key,x,91,42,TEAL if active else PALE if enabled else MUTED,1. if enabled or active else .45)
            self.key(label,x,43,76)
            if key=='eye-shield' and not enabled:
                rect(x-21,64,42,3,(39,48,53));rect(x-21,64,42*(1-p.parry_cooldown/C.PARRY_COOLDOWN),3,TEAL)
        r.text('F1 안내',961,31,20,MUTED,True)
        boss=next((e for e in g.enemies if e.boss and e.alive),None)
        if boss:
            self.frame('panel',392,633,496,72);r.text('도장주',640,681,24,PALE,True,display=True)
            r.text('2페이즈' if boss.phase==2 else '1페이즈',849,681,20,MUTED,True);self.bar(412,644,456,13,boss.hp/boss.max_hp)
            if p.style=='moon':
                for i in range(3):rect(617+i*18,624,10,5,TEAL if i<boss.parry_count else (51,66,73))
            if boss.state=='stunned':self.toast('공격 기회',640,591,170)
        if g.state!='playing':return
        next_area=g.next_encounter
        if next_area:
            x=max(90,min(1190,next_area['trigger']-camera));y=C.GROUND+60
            p2.draw_line(x-7,y-5,x+7,y,*GOLD,255);p2.draw_line(x+7,y,x-7,y+5,*GOLD,255);r.text('다음 전투',x,y+35,20,PALE,True)
        elif not boss:r.text(f'남은 적 {len(g.living)}',1134,617,20,MUTED,True)
        if r.hints_enabled and g.stage_index==0 and g.transition_banner<=0:
            lesson=None
            threat=next((e for e in g.living if e.state=='windup' and
                         abs(e.x-p.x)<=C.ENEMIES[e.kind]['reach']+50),None)
            if threat and 'parry' not in g.practiced:
                lesson=('우클릭','적이 베기 직전에 패링')
            elif any(e.state=='stunned' for e in g.living):
                lesson=('좌클릭','열린 틈에 반격')
            elif p.action=='idle' and not any(e.state=='active' for e in g.living):
                lessons=(('move','← / →','이동 · A / D도 가능'),('attack','좌클릭','클릭마다 검격 · 연타로 연격'),
                         ('jump','SPACE','점프'))
                lesson=next(((key,label) for action,key,label in lessons
                             if action not in g.practiced and (action!='jump' or not g.living)),None)
            if lesson:
                key,label=lesson;self.frame('band',28,560,400,48);self.key(key,85,584,88);r.text(label,143,584,20,PALE)
        for direction in (-1,1):
            if any((e.x-camera<35 if direction<0 else e.x-camera>1245) for e in g.living):
                x=24 if direction<0 else 1256;y=255;self.icon('crossed-swords',x,y,25,RED)
                p2.draw_line(x,y-24,x+direction*9,y-15,*RED,230);p2.draw_line(x+direction*9,y-15,x,y-6,*RED,230)
        if g.notices and not boss:self.toast(g.notices[-1][0],640,531,600)
        if g.transition_banner>0:
            r.text(g.stage['name'],640,449,48,PALE,True,display=True);r.text(g.stage['subtitle'],640,394,20,MUTED,True)

    def tooltip(self,key,player,x,y,spent=False):
        x=max(225,min(1055,x));self.frame('card',x-205,y,410,170)
        self.r.text(C.AUGMENTS[key][0]+(' · 소모' if spent else ''),x-180,y+135,24,GOLD,display=True)
        top=y+98
        for line in choice_detail(key,player):top=self.block(line,x-180,top,360,20,PALE)

    def reward(self,g):
        r=self.r;rect(0,0,1280,720,DARK,239)
        r.text('전투 스타일' if g.stage_index==0 else '증강 선택',100,630,48,PALE,display=True)
        r.text('전투 스타일을 하나 고른다' if g.stage_index==0 else '다음 전투에 가져갈 증강을 고른다',103,574,20,MUTED)
        catalog=C.STYLES if g.stage_index==0 else C.AUGMENTS
        for i,key in enumerate(g.choices):
            x=100+i*370;selected=i==r.ui.reward_focus;self.frame('card',x,180,340,320)
            if selected:
                rect(x,180,7,320,RED);p2.draw_rectangle(x,180,x+340,500,*PALE,255);rect(x,490,340,10,RED)
            r.text(str(i+1),x+28,462,24,PALE if selected else MUTED,display=True)
            # Each lesson pairs a drawn stance with its small school seal.
            pose,frame={'blood':('attack',4),'moon':('attack2',3),'chain':('attack3',4),
                        'counter':('parry',3),'echo':('attack2',4),'bleed':('attack',3),
                        'insight':('parry',1),'unyielding':('idle',2),'revive':('jump',4)}[key]
            ink=TEAL if key in ('moon','echo','revive') else RED if key in ('blood','counter','bleed') else GOLD
            rect(x+17,389,306,2,ink,130)
            if key=='echo':r.draw_hero(pose,0,x+214,397,1,76,frame=2,alpha=.32)
            frames=r.hero_data['animations'][pose]['frames']
            beat=sum(f['durationMs'] for f in frames[:frame])/1000
            r.draw_hero(pose,beat,x+238,397,1,76,frame=frame)
            self.seal(key,x+303,467,30,ink)
            r.text(catalog[key][0],x+23,416,36,PALE,display=True)
            y=372
            for j,(label,text) in enumerate(reward_sections(key,g.player)):
                r.text(label,x+28,y,15,(145,133,106))
                y=self.block(text,x+28,y-26,284,24 if j==0 else 20,PALE if j==0 else MUTED,display=j==0)-10
        current=g.choices[r.ui.reward_focus];rect(100,88,1080,2,(64,79,84))
        r.text('현재 선택  '+catalog[current][0],104,130,24,PALE,display=True)
        r.text('← → 선택 · 클릭/ENTER 확정',665,130,20,MUTED)
        r.text('F1 설명',1174-r.text_width('F1 설명',20),130,20,MUTED)
        r.text('체력 유지 / 회복약 충전',104,51,20,TEAL)
        r.text('1~3 바로 확정',1174-r.text_width('1~3 바로 확정',20),51,20,MUTED)

    def button(self,label,x,y,w,h,selected,value=''):
        if selected:
            rect(x,y,w,h,(33,42,48));rect(x,y,6,h,RED);rect(x+w-13,y+8,5,h-16,RED)
        else:rect(x,y,w,h,DARK,100)
        self.r.text(label,x+26,y+h/2,24,PALE if selected else MUTED,display=selected)
        if value:self.r.text(value,x+w-110,y+h/2,20,TEAL if selected else MUTED)

    def title(self):
        r=self.r;r.backgrounds['mountain'].draw(640,360,1280,720);self.frame('vignette',0,0,1280,720)
        rect(60,0,558,720,DARK,210);rect(60,450,6,182,RED);rect(66,449,48,5,RED)
        r.text('벼랑 아래',100,581,48,PALE,display=True);r.text('칼날',99,493,96,PALE,display=True)
        r.text('빼앗긴 도장으로 돌아간다.',103,409,20,MUTED);r.draw_hero('idle',r.clock,940,128,1,370)
        r.text('↑ ↓ 선택    ENTER 확인',103,51,20,MUTED)
