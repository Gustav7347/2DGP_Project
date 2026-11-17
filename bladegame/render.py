"""pico2d presentation. Simulation never depends on rendering."""
from pathlib import Path
import ctypes, json, math, os, struct, zlib
from pico2d import pico2d as p2
from . import config as C
from .motion import blade_edge,run_weight,grip_travel,sample_frame,blade_angle,blade_ribbon,attack_pose_time,counter_pose_time,parry_pose_time,parry_contact,deflect_frame,held_blade_angle
from .interface import Interface,choice_detail,combat_status,last_hit_text
from .presentation import GameUI

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'
INK=(224,226,222)
MUTED=(157,173,182)
GOLD=(222,180,108)
RED=(185,66,65)
TEAL=(91,205,193)


def box(x,y,w,h,color,alpha=255,outline=False):
    p2.draw_rectangle(x,y,x+w,y+h,*color,alpha,filled=not outline)


class Renderer:
    def __init__(self):
        font_root=ASSETS/'fonts'
        sizes={15:20,18:20,20:20,21:24,24:24,25:24,32:36,36:36,44:48,48:48,62:72,72:72,96:96}
        self.fonts={size:p2.load_font(str(font_root/'Galmuri11.ttf'),actual) for size,actual in sizes.items()}
        self.display_fonts={size:p2.load_font(str(font_root/'Galmuri11-Bold.ttf'),actual if actual!=20 else 24) for size,actual in sizes.items()}
        self.hero_data=json.loads((ASSETS/'player'/'animations.json').read_text('utf-8'))
        self.enemy_deflected_sword=p2.load_image(str(ASSETS/'player'/'sword.png'))
        hero_images={v['file'] for v in self.hero_data['animations'].values()}
        sheets={file:p2.load_image(str(ASSETS/'player'/file)) for file in hero_images}
        self.hero={name:sheets[a['file']] for name,a in self.hero_data['animations'].items()}
        self.enemy_data=json.loads((ASSETS/'enemies'/'animations.json').read_text('utf-8'))
        enemy_images={name:p2.load_image(str(ASSETS/'enemies'/name)) for name in {v['file'] for v in self.enemy_data.values()}}
        self.enemies={k:enemy_images[v['file']] for k,v in self.enemy_data.items()}
        self.enemy_weapons=json.loads((ASSETS/'enemies'/'weapons-v11.json').read_text('utf8'))
        self.enemy_weapon_image=p2.load_image(str(ASSETS/'enemies'/self.enemy_weapons['file']))
        self.backgrounds={k:p2.load_image(str(ASSETS/'backgrounds'/f'{k}.png')) for k in ('mountain','dojo','mountain-trail-v1','dojo-courtyard-v1')}
        self.terrain=p2.load_image(str(ASSETS/'environment'/'terrain.png'))
        self.terrain_data=json.loads((ASSETS/'environment'/'terrain.json').read_text('utf-8'))
        self.support_data=json.loads((ASSETS/'environment'/'supports-v10.json').read_text('utf8'))
        self.supports=p2.load_image(str(ASSETS/'environment'/self.support_data['file']))
        self.fx_data={k:json.loads((ASSETS/'fx'/f'{k}.json').read_text('utf-8')) for k in ('sword-slash','thrust','parry','hit-spark')}
        self.fx_images={k:p2.load_image(str(ASSETS/'fx'/f'{k}.png')) for k in self.fx_data}
        self.clock=0.
        self.last_hero_pose=None
        self.pose_link=None
        self.hover=-1
        self.muted=False
        self.shake_enabled=True
        self.hints_enabled=True
        self.ui=Interface()
        self.skin=GameUI(self)
        self.geometry_supported=hasattr(p2,'SDL_RenderGeometry')
        self.audio_counter=0
        self.volume=.15
        self.channel_levels=[.65,.85,1.,.45,.25,.28]
        self.last_step=None
        self.step_interval=sum(f['durationMs'] for f in self.hero_data['animations']['run']['frames'])/2000
        self.hp_trail=C.MAX_HP
        self.hp_seen=C.MAX_HP
        self.hp_delay=0.
        self.sounds={}
        if p2.audio_on:
            p2.Mix_AllocateChannels(max(6,p2.Mix_AllocateChannels(-1)))
            for k,file in C.SOUND_FILES.items():
                self.sounds[k]=p2.load_wav(str(ASSETS/'audio'/file))
                self.sounds[k].set_volume(128)
        self.last_event=None
        self.last_state=None

    def text(self, text, x, y, size=18, color=INK, center=False, display=False):
        text=str(text)
        font=(self.display_fonts if display else self.fonts)[size]
        if center:
            width,height=ctypes.c_int(),ctypes.c_int()
            p2.TTF_SizeUTF8(font.font,text.encode('utf-8'),ctypes.byref(width),ctypes.byref(height))
            x-=width.value/2
        if display:font.draw(round(x)+2,round(y)-2,text,(8,11,16))
        font.draw(round(x),round(y),text,color)

    def text_width(self,text,size=20,display=False):
        font=(self.display_fonts if display else self.fonts)[size]
        width,height=ctypes.c_int(),ctypes.c_int()
        p2.TTF_SizeUTF8(font.font,str(text).encode('utf-8'),ctypes.byref(width),ctypes.byref(height))
        return width.value

    def wrap_text(self,text,size,width,display=False):
        if width<=0:raise ValueError('Text width must be positive')
        lines=[];line=''
        for word in str(text).split():
            candidate=(line+' '+word).strip()
            if self.text_width(candidate,size,display)<=width:line=candidate;continue
            if line:lines.append(line);line=''
            for char in word:
                if line and self.text_width(line+char,size,display)>width:
                    lines.append(line);line=''
                line+=char
        if line:lines.append(line)
        return lines

    def sound(self, game):
        player=getattr(game,'player',None);step=None
        if player and game.state=='playing' and player.grounded and player.moving and player.action=='idle':
            beat=int(player.run_time/getattr(self,'step_interval',.28))
            marker=(getattr(game,'stage_index',0),beat)
            if marker!=getattr(self,'last_step',None):step=f'footstep{1+beat%2}'
            self.last_step=marker
        else:self.last_step=None
        if self.muted:
            self.last_event=game.events[-1] if game.events else None
            self.last_state=game.state
            return
        fresh=[]
        for event in reversed(game.events):
            if event is self.last_event: break
            fresh.append(event)
        names={'player_hit':'hurt','reward_selected':'reward','jumped':'jump','landed':'land'}
        parried=any(event['kind']=='parry' for event in fresh)
        countered=any(event['kind']=='counter' for event in fresh)
        if parried:self.stop_sound(0)
        played=set()
        if step in self.sounds and not any(e['kind'] in ('jumped','landed') for e in fresh):
            self.play_sound(step);played.add(step)
        for event in reversed(fresh):
            k=names.get(event['kind'])
            if event['kind']=='swing': k=f'swing{event.get("combo",1)}'
            elif event['kind']=='enemy_hit':
                k=event['impact'] if event.get('impact') in ('echo','counter') else f'impact{min(3,max(1,event.get("combo",1)))}'
            elif event['kind']=='parry':
                self.audio_counter+=1
                k=f'parry{1+self.audio_counter%3}'
            if (countered or (parried and event.get('hit',{}).get('reason')=='counter_cost')) and k=='hurt':continue
            if k in self.sounds and k not in played:
                self.play_sound(k); played.add(k)
        if game.state=='reward' and self.last_state!='reward' and 'reward' in self.sounds:
            self.play_sound('reward')
        self.last_event=game.events[-1] if game.events else None
        self.last_state=game.state

    @staticmethod
    def sound_channel(name):
        if name.startswith('footstep') or name in ('jump','land'):
            return 5,{'jump':.23,'land':.35}.get(name,.28)
        channel=0 if name.startswith('swing') else 2 if name.startswith('parry') else 3 if name=='reward' else 4 if name=='echo' else 1
        level=.65 if channel==0 or name=='counter' else .45 if channel==3 else .25 if channel==4 else .85 if channel==1 else 1.
        return channel,level

    def play_sound(self, name):
        channel,level=self.sound_channel(name)
        self.channel_levels[channel]=level
        p2.Mix_Volume(channel,int(128*self.volume*level))
        p2.Mix_PlayChannel(channel,self.sounds[name].wav,0)

    def stop_sound(self,channel):
        if p2.audio_on:p2.Mix_HaltChannel(channel)

    def set_volume(self, delta):
        self.volume=max(0.,min(.5,self.volume+delta))
        if self.volume>0: self.muted=False
        if p2.audio_on:
            for channel,level in enumerate(getattr(self,'channel_levels',(.65,.85,1.,.45,.25,.28))):
                p2.Mix_Volume(channel,int(128*self.volume*level))

    def toggle_mute(self):
        self.muted=not self.muted
        if self.muted and p2.audio_on: p2.Mix_HaltChannel(-1)

    @staticmethod
    def frame_at(animation, seconds):
        return sample_frame(animation,seconds)[0]

    def link_hand(self,player,name,facing,grip,angle,dt,allow):
        """Release the previous guard or recovery into the next pose before contact."""
        previous=self.last_hero_pose
        valid=previous and previous[0] is player and previous[2]==facing
        if not valid or not allow:
            self.pose_link=None
        elif previous[1]!=name:
            duration=.033 if name=='parry' else .060
            dx=previous[3][0]-grip[0];dy=previous[3][1]-grip[1]
            gain=min(1.,12/max(1.,math.hypot(dx,dy)))
            turn=(previous[4]-angle+180)%360-180
            self.pose_link=(dx*gain,dy*gain,turn,duration,0.)
        dx=dy=0.
        if self.pose_link:
            sx,sy,turn,duration,elapsed=self.pose_link
            elapsed=min(duration,elapsed+dt)
            t=elapsed/duration
            remaining=1-t*t*(3-2*t)
            dx,dy=sx*remaining,sy*remaining
            angle+=turn*remaining
            self.pose_link=(sx,sy,turn,duration,elapsed) if elapsed<duration else None
        self.last_hero_pose=(player,name,facing,(grip[0]+dx,grip[1]+dy),angle)
        return dx,dy,angle

    def draw_hero(self, name, seconds, x, y, facing=1, height=148, frame=None, alpha=1., weapon=True, player=None, dt=0.):
        anim=self.hero_data['animations'][name]
        i=self.frame_at(anim,seconds) if frame is None else frame
        f=anim['frames'][i]
        image=self.hero[name]
        scale=height/anim['referenceBodyHeight']
        left,top,w,h=f['rect']; ax,ay=f['anchor']
        image.opacify(alpha)
        image.clip_composite_draw(left,image.h-top-h,w,h,0,'h' if facing<0 else '',
            x+facing*(w/2-ax)*scale,y+(ay-h/2)*scale,w*scale,h*scale)
        image.opacify(1.)

    def draw_planted_run(self,image,anim,index,seconds,x,y,facing,height,alpha,lx,ly):
        f=anim['frames'][index]
        leg=f['supportLeg']; ax,ay=f['anchor']
        scale=height/anim['referenceBodyHeight']
        _,phase=sample_frame(anim,seconds)
        contact=max(c['frame'] for c in anim['footContacts'] if c['frame']<=index)
        elapsed=(sum(p['durationMs'] for p in anim['frames'][contact:index])+phase*f['durationMs'])/1000
        # The planted sole stays on the same stone while the pelvis advances.
        shift=46*height/148-C.MOVE_SPEED*elapsed*height/148-(leg['sole']-ax)*scale
        next_contact=next((c['frame'] for c in anim['footContacts'] if c['frame']>index),len(anim['frames']))
        step_time=sum(p['durationMs'] for p in anim['frames'][contact:next_contact])/1000
        step=elapsed/step_time
        dx,dy,lift=(v*height/148 for v in run_weight(step))
        travel_x,travel_y=grip_travel(anim,index,phase,scale)
        dx+=lx+travel_x;dy+=ly+travel_y
        if step>.72:
            flight=(step-.72)/.28
            shift*=1-flight*flight*(3-2*flight)
        self.draw_planted_pose(image,f,x,y+lift,facing,scale,shift,anim['referenceBodyHeight'],alpha,
                               torso_x=dx,torso_y=dy-lift)
        grip_weight=min(1.,max(0.,(ay-30*anim['referenceBodyHeight']/355-f['grip'][1])/(146*anim['referenceBodyHeight']/355)))
        return dx*grip_weight,lift+(dy-lift)*grip_weight

    def draw_planted_pose(self,image,f,x,y,facing,scale,shift,body_height,alpha,torso_x=0.,torso_y=0.):
        left,top,w,h=f['rect']; ax,ay=f['anchor'];leg=f['supportLeg']
        ratio=body_height/355
        # Weights follow only the support leg. The shoe translates as a single
        # piece, the knee shares the load, and the free leg passes independently.
        rows=[(0,leg['hip'],0),(ay-round(176*ratio),leg['hip'],0),
              (ay-round(127*ratio),leg['knee'],.18),(ay-round(87*ratio),leg['knee'],.48),
              (ay-round(40*ratio),leg['sole'],.82),(ay-round(26*ratio),leg['sole'],1),
              (ay,leg['sole'],1),(h,leg['sole'],1)]
        outer,inner=round(112*ratio),round(49*ratio)
        def columns(center):
            return (0,max(0,center-outer),max(0,center-inner),min(w,center+inner),min(w,center+outer),w)
        def torso(v):
            return max(0.,min(1.,(ay-30*ratio-v)/(146*ratio)))
        points=[];indices=[]
        for row,(v,center,load) in enumerate(rows):
            cuts=columns(center)
            for col,(u,influence) in enumerate(zip(cuts,(0,0,1,1,0,0))):
                px=x+facing*((u-ax)*scale+shift*load*influence+torso_x*torso(v))
                py=C.HEIGHT-y-(ay-v)*scale-torso_y*torso(v)
                points.append((px,py,(left+u)/image.w,(top+v)/image.h))
                if row and col:
                    n=len(points)-1
                    indices.extend((n-7,n-6,n,n-7,n,n-1))
        if self.geometry_supported:
            vertices=(p2.SDL_Vertex*len(points))(*(p2.SDL_Vertex((px,py),(255,255,255,round(255*alpha)),(u,v))
                                                   for px,py,u,v in points))
            triangles=(ctypes.c_int*len(indices))(*indices)
            if p2.SDL_RenderGeometry(p2.renderer,image.texture,vertices,len(points),triangles,len(indices))==0:
                return True
        # Older SDL renderers use the same weights on narrow scan bands.
        for (v0,c0,l0),(v1,c1,l1) in zip(rows,rows[1:]):
            for v in range(v0,v1,8):
                stop=min(v1,v+8);t=((v+stop)/2-v0)/(v1-v0)
                center=round(c0+(c1-c0)*t);load=l0+(l1-l0)*t
                cuts=columns(center)
                edges=[round(x+facing*((u-ax)*scale+shift*load*j+torso_x*torso((v+stop)/2))) for u,j in zip(cuts,(0,0,1,1,0,0))]
                upper=round(y+(ay-v)*scale+torso_y*torso(v));lower=round(y+(ay-stop)*scale+torso_y*torso(stop))
                for col,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
                    a,b=edges[col:col+2]
                    if hi>lo and a!=b and upper>lower:
                        image.clip_composite_draw(left+lo,image.h-top-stop,hi-lo,stop-v,0,'h' if facing<0 else '',
                                                  (a+b)/2,(upper+lower)/2,abs(b-a),upper-lower)
        return True

    @staticmethod
    def draw_weighted_pose(image,frame,x,y,facing,scale,dx,dy,shoe_shift,hinge):
        left,top,w,h=frame['rect'];ax,ay=frame['anchor']
        hinge=int(min(ay-1,hinge))
        edges=[0,*range(hinge,int(ay),10),int(ay)]
        if h>ay:edges.append(h)
        def weight(row):
            return min(1.,max(0.,(ay-row)/(ay-hinge)))
        def screen_y(row):
            return round(y+(ay-row)*scale+dy*weight(row))
        for a,b in zip(edges,edges[1:]):
            upper,lower=screen_y(a),screen_y(b)
            if upper<=lower:continue
            t=weight((a+b)/2)
            center=x+facing*((w/2-ax)*scale+dx*t+shoe_shift*(1-t))
            image.clip_composite_draw(left,image.h-top-b,w,b-a,0,'h' if facing<0 else '',
                                      center,(upper+lower)/2,w*scale,upper-lower)

    @staticmethod
    def enemy_weight(enemy):
        if enemy.state=='windup':
            t=max(0.,min(1.,1-enemy.timer/ enemy.windup_total))
            load=math.sin(t*math.pi/2)
            return -7*load,-5*load,0.
        if enemy.state=='active':
            t=max(0.,min(1.,1-enemy.timer/C.ENEMY_ACTIVE))
            push=1-(1-t)**3
            return -7+18*push,-5+3*push,0.
        if enemy.state=='recovery' and enemy.elapsed<.20:
            release=max(0.,1-enemy.elapsed/.20)
            return 11*release,-2*release,0.
        return 0.,0.,0.

    def mesh(self,points,indices):
        if not self.geometry_supported:return False
        vertices=(p2.SDL_Vertex*len(points))(*(p2.SDL_Vertex((x,C.HEIGHT-y),color) for x,y,color in points))
        triangles=(ctypes.c_int*len(indices))(*indices)
        if p2.SDL_RenderGeometry(p2.renderer,None,vertices,len(vertices),triangles,len(triangles))<0:
            self.geometry_supported=False
            return False
        return True

    def shadow(self,actor,game,camera):
        ground=max([C.GROUND]+[top for x,top,width in game.stage['platforms'] if x-15<actor.x<x+width+15 and top<=actor.y+.1])
        distance=max(0.,actor.y-ground)
        opacity=round(95*max(.15,1-distance/380))
        radius=(47 if actor is game.player else 53 if actor.boss else 40)*max(.55,1-distance/600)
        x=actor.x-camera;y=ground+2
        points=[(x,y,(3,5,8,opacity))]+[(x+math.cos(n*math.tau/24)*radius,y+math.sin(n*math.tau/24)*9,(3,5,8,0)) for n in range(24)]
        indices=[j for n in range(24) for j in (0,n+1,(n+1)%24+1)]
        self.mesh(points,indices)

    @staticmethod
    def enemy_pose(enemy):
        if (enemy.kind=='sword' and enemy.alive and enemy.deflect_context
                and enemy.state in ('active','recovery','stunned')
                and enemy.deflect_left<=.105):
            settling=enemy.state in ('stunned','recovery') and enemy.timer<.46
            return 'sword-parried',4 if settling else 3
        if enemy.alive and enemy.state!='transition' and enemy.deflect_left>0:
            if not (enemy.boss and enemy.state=='stunned' and enemy.deflect_left<=.15):
                return enemy.kind+'-parried',deflect_frame(enemy.deflect_left)
        if enemy.boss and enemy.alive:
            if enemy.state=='stunned': return 'boss-extra',1
            if enemy.state=='transition': return 'boss-extra',2
            if enemy.state=='windup' and enemy.current_attack=='thrust': return 'boss-extra',0
            if enemy.state=='active' and enemy.current_attack=='thrust': return 'boss-thrust',0
            if enemy.phase==2 and enemy.state in ('windup','active','recovery'):
                return 'boss-extra',{'windup':3,'active':4,'recovery':2}[enemy.state]
        if not enemy.alive: i=5
        elif enemy.state=='stunned': i=4
        elif enemy.state=='windup': i=2
        elif enemy.state=='active': i=3
        elif enemy.hurt>0: i=4
        elif enemy.state=='recovery' and enemy.kind=='sword' and enemy.strike_spent and enemy.elapsed<.085: i=3
        elif enemy.state=='approach' and enemy.moving:
            distance=enemy.walk_time*C.ENEMIES[enemy.kind]['speed']
            stride=144 if enemy.boss else 110
            return enemy.kind+'-gait',math.floor(distance*6/stride)%6
        else: i=0
        return enemy.kind,i

    def draw_enemy(self, enemy, camera):
        asset,i=self.enemy_pose(enemy)
        data=self.enemy_data[asset]
        image=self.enemies[asset]
        f=data['frames'][i]
        left,top,w,h=f['rect']; ax,ay=f['anchor']
        scale=(182 if enemy.boss else 144)/data['referenceBodyHeight']
        alpha=max(.12,1-enemy.elapsed/.9) if not enemy.alive else 1.
        if not enemy.alive and enemy.elapsed>1.: return
        image.opacify(alpha)
        x=enemy.x-camera
        dx,dy,shoe=self.enemy_weight(enemy) if enemy.alive and enemy.deflect_left<=0 and not asset.endswith('-parried') else (0.,0.,0.)
        def draw_body(opacity):
            if asset.endswith('-gait'):
                stride=144 if enemy.boss else 110
                distance=enemy.walk_time*C.ENEMIES[enemy.kind]['speed']
                shift=stride*.32-distance%(stride/2)-(f['supportLeg']['sole']-ax)*scale
                self.draw_planted_pose(image,f,x,enemy.y,enemy.facing,scale,shift,data['referenceBodyHeight'],opacity)
            elif dx or dy or shoe:
                self.draw_weighted_pose(image,f,x,enemy.y,enemy.facing,scale,dx,dy,shoe,ay-data['referenceBodyHeight']*.28)
            else:
                image.clip_composite_draw(left,image.h-top-h,w,h,0,'h' if enemy.facing<0 else '',
                    x+enemy.facing*(w/2-ax)*scale,enemy.y+(ay-h/2)*scale,w*scale,h*scale)
        draw_body(alpha)
        if asset.endswith('-parried'):
            self.deflected_weapon(enemy,f,data,camera)
        if enemy.alive and enemy.hurt>enemy.hurt_duration*.67:
            p2.SDL_SetTextureBlendMode(image.texture,p2.SDL_BLENDMODE_ADD)
            image.opacify(.48)
            draw_body(.48)
            p2.SDL_SetTextureBlendMode(image.texture,p2.SDL_BLENDMODE_BLEND)
        image.opacify(1.)
        if not enemy.alive: return
        if not enemy.boss:
            box(x-27,enemy.y+155,54,5,(15,19,25))
            box(x-26,enemy.y+156,52*enemy.hp/enemy.max_hp,3,RED)
        self.skin.enemy_cue(enemy,x)

    def contact_point(self,context,hint):
        return parry_contact(self.hero_data['animations']['parry'],self.hero_data['weapon'],
                             *context['origin'],context['facing'],hint,
                             seconds=context.get('pose_time',0.),feedback=context.get('pose_feedback',.22))

    def deflected_weapon(self,enemy,frame,data,camera):
        scale=(182 if enemy.boss else 144)/data['referenceBodyHeight'];ax,ay=frame['anchor'];hx,hy=frame['grip']
        gx=enemy.x+enemy.facing*(hx-ax)*scale;gy=enemy.y+(ay-hy)*scale
        contact=self.contact_point(enemy.deflect_context,enemy.deflect_context['hint'])
        elapsed=.22-enemy.deflect_left;u=max(0.,min(1.,(elapsed-.035)/.09));u=u*u*(3-2*u)
        # Boss keeps a compact forward guard; lifting behind its head silhouettes
        # the blade across the face instead of showing a controlled brace.
        raised_x=gx+enemy.facing*20 if enemy.boss else enemy.x-enemy.facing*80
        if enemy.kind=='sword' and enemy.deflect_left<=.105 and enemy.state in ('stunned','recovery'):
            # The grip follows the shoulder drawing. Let the tip turn outward as balance returns.
            recovery=max(0.,min(1.,(.62-enemy.timer)/.45))
            raised_x-=enemy.facing*85*recovery
        tx=contact[0]*(1-u)+raised_x*u
        ty=contact[1]*(1-u)+(enemy.y+(225 if enemy.boss else 200))*u
        settle=0. if enemy.kind=='sword' else max(0.,min(1.,(elapsed-.16)/.06))
        tx=tx*(1-settle)+(gx+enemy.facing*100)*settle
        ty=ty*(1-settle)+(gy-45)*settle
        angle=math.atan2(ty-gy,tx-gx)
        if enemy.kind=='sword':
            weapon=self.hero_data['weapon'];image=self.enemy_deflected_sword
            rect=[0,0,image.w,image.h];ws=112/weapon['bladeLength']
        else:
            weapon=self.enemy_weapons[enemy.kind];image=self.enemy_weapon_image
            rect=weapon['rect'];ws=weapon['forwardLength']/(weapon['tip'][0]-weapon['grip'][0])
        left,top,w,h=rect
        dx=(w/2-weapon['grip'][0])*ws;dy=(weapon['grip'][1]-h/2)*ws
        image.clip_composite_draw(left,image.h-top-h,w,h,angle,'',
                                  gx-camera+dx*math.cos(angle)-dy*math.sin(angle),
                                  gy+dx*math.sin(angle)+dy*math.cos(angle),w*ws,h*ws)
        # Keep the original hand pixels in front of the handle.
        image=self.enemies[enemy.kind+'-parried'];left,top,_,_=frame['rect'];ox,oy,ow,oh=frame['handOverlay']
        image.clip_composite_draw(left+ox,image.h-(top+oy+oh),ow,oh,0,'h' if enemy.facing<0 else '',
            enemy.x-camera+enemy.facing*(ox+ow/2-ax)*scale,enemy.y+(ay-oy-oh/2)*scale,ow*scale,oh*scale)

    def environment(self, game, camera):
        boss=game.stage_index==3
        bg=self.backgrounds[('mountain','mountain-trail-v1','dojo-courtyard-v1','dojo')[game.stage_index]]
        if boss: bg.draw(640,360,C.WIDTH,C.HEIGHT)
        else:
            bg.draw(640-camera*.10,390,1500,845)
            if camera>900: bg.draw(2140-camera*.10,390,1500,845)
        tint=[(17,26,39),(16,34,37),(35,22,29),(13,20,28)][game.stage_index]
        box(0,0,C.WIDTH,C.HEIGHT,tint,55 if not boss else 45)
        if not boss:
            if game.stage_index==1:
                for n in range(44):
                    x=(n*137-self.clock*72-camera*.18)%C.WIDTH
                    y=130+(n*83-self.clock*275)%440
                    p2.draw_line(x,y,x-4,y-17,111,143,148,60)
        for x,top,w in game.stage['platforms']:
            self.platform_supports(game.stage_index,x-camera,top,w)
        # Collision surfaces and their top edges use exactly the simulation coordinates.
        box(0,0,C.WIDTH,C.GROUND,(29,32,40))
        tile=2 if boss else 0
        rect=self.terrain_data['frames'][tile]['rect']
        width=int(C.GROUND*rect[2]/rect[3])
        offset=int(camera)%width
        for x in range(-offset,C.WIDTH,width): self.draw_terrain(tile,x,0,width,C.GROUND)
        for x,top,w in game.stage['platforms']:
            sx=x-camera
            self.draw_terrain(3 if game.stage_index==2 else 1,sx,top-38,w,38)
        for n in range(12):
            x=(n*137+self.clock*(12+n%4*5)-camera*.18)%C.WIDTH
            y=155+(n*71)%360+math.sin(self.clock+n)*12
            box(x,y,3,2,(167,91,70),95)

    def draw_terrain(self, index, x, y, width, height):
        left,top,w,h=self.terrain_data['frames'][index]['rect']
        self.terrain.clip_draw(left,self.terrain.h-top-h,w,h,x+width/2,y+height/2,width,height)

    def support_piece(self,index,x,y,width,height,alpha=.65,flip=False):
        left,top,w,h=self.support_data['frames'][index]['rect'];image=self.supports
        image.opacify(alpha)
        image.clip_composite_draw(left,image.h-top-h,w,h,0,'h' if flip else '',x+width/2,y+height/2,width,height)
        image.opacify(1.)

    def platform_supports(self,stage,x,top,width):
        # Back structures share no collision; their narrow, subdued posts stay behind actors.
        if x+width<0 or x>C.WIDTH:return
        height=max(12.,top-16-C.GROUND)
        if stage==2:
            beam_y=top-49
            self.draw_terrain(2,x+5,beam_y,width-10,19)
            for sx,flip in ((x+16,False),(x+width-62,True)):
                self.support_piece(1,sx,C.GROUND+18,46,height-20,.9)
                self.support_piece(2,sx if not flip else sx-28,beam_y-34,74,48,.9,flip)
                self.draw_terrain(3,sx-5,C.GROUND,56,22)
            self.draw_terrain(2,x+28,C.GROUND+32,width-56,12)
        else:
            for sx in (x+20,x+width-44):self.support_piece(0,sx,C.GROUND,24,height,.42)
            self.support_piece(3,x+width*.28,top-74,width*.44,62,.48)

    def effects(self, game, camera):
        for e in game.effects:
            x=e['x']-camera; y=e['y']; t=1-e['life']/e['max_life']
            a=round((1-t)*235)
            if e['kind']=='slash':
                if self.geometry_supported and not e.get('echo') and 'combo' in e:continue
                face=e.get('facing',1)
                scale=e.get('reach',165)/61
                tail=1-max(0.,t-.55)/.45
                if e.get('enhanced'):
                    self.draw_fx('sword-slash',.045+t*.54,x,y,scale*1.035,face,
                                 reverse=e.get('combo',0)==1,alpha=.28*tail,color=GOLD)
                self.draw_fx('sword-slash',.045+t*.54,x,y,scale,face,
                             reverse=e.get('combo',0)==1,alpha=(.42 if e.get('echo') else .90)*tail,
                             color=TEAL if e.get('echo') else None)
            elif e['kind']=='number':
                self.text(e['text'],x,y+t*32,21 if e.get('finisher') else 18,RED if e.get('bleed') else GOLD,True)
            elif e['kind']=='parry':
                if 'origin' in e:
                    contact=self.contact_point(e,(e['x'],e['y']))
                    x,y=contact[0]-camera,contact[1]
                self.draw_fx('parry',t*.28,x,y,1.,e.get('facing',1))
            elif e['kind']=='heal':
                p2.draw_circle(int(x),int(y),int(25+t*30),*TEAL,a)
                self.text('+ 회복',x,y+35+t*40,18,TEAL,True)
            elif e['kind'] in ('hit','hurt'):
                self.draw_fx('hit-spark',t*.48,x,y,1.55 if e.get('finisher') else 1.15 if e['kind']=='hit' else 1.)
                color=RED if e['kind']=='hurt' else GOLD
                facing=e.get('facing',1)
                if e['kind']=='hit' and t<.4:
                    strength=1-t/.4;dx=facing*(57 if e.get('finisher') else 39)*(.6+.4*strength)
                    dy=(26 if e.get('combo')==1 else -26)*(.6+.4*strength)
                    points=[(x-dx,y-dy-7,(222,164,85,0)),(x+dx,y+dy-7,(222,164,85,0)),
                            (x-dx,y-dy,(250,235,196,round(220*strength))),(x+dx,y+dy,(250,235,196,round(220*strength))),
                            (x-dx,y-dy+7,(222,164,85,0)),(x+dx,y+dy+7,(222,164,85,0))]
                    self.mesh(points,[0,1,2,1,3,2,2,3,4,3,5,4])
                for i in range(5):
                    angle=(i-2)*.34;distance=t*(32+i*5)
                    sx=x+facing*math.cos(angle)*distance;sy=y+math.sin(angle)*distance
                    p2.draw_line(int(sx),int(sy),int(sx+facing*(3+(1-t)*4)),int(sy+math.sin(angle)*3),*color,a)
            elif e['kind']=='land':
                for sign in (-1,1):
                    for i in range(3):
                        spread=6+i*4+t*(18+i*9)*e['power']
                        box(x+sign*spread,y+math.sin(t*math.pi)*(3+i),3,2,MUTED,int(a*.46))
            elif e['kind']=='combat_label':
                self.skin.toast(e['text'],x,y+t*14,130)
            elif e['kind']=='enemy_slash':
                self.draw_fx('thrust' if e.get('thrust') else 'sword-slash',t*.7,x,y,2.3,e.get('facing',1),alpha=.65)

    def draw_fx(self, name, seconds, x, y, scale, facing=1, reverse=False, alpha=1., color=None):
        data=self.fx_data[name]; image=self.fx_images[name]
        meta=data['meta']['pixelfx']
        i=min(len(data['frames'])-1,int(max(0,seconds)*meta['fps']))
        f=data['frames'][i]['frame']
        px,py=meta['pivot']
        # Pin the visible centre of the effect, not the stock actor's feet.
        py-=20 if name in ('hit-spark','thrust') else 26 if name=='sword-slash' else 0
        if name=='sword-slash': px+=6
        dx=(f['w']/2-px)*scale*facing
        dy=(py-f['h']/2)*scale*(-1 if reverse else 1)
        flip=('h' if facing<0 else '')+('v' if reverse else '')
        image.opacify(alpha)
        if color is not None:p2.SDL_SetTextureColorMod(image.texture,*color)
        image.clip_composite_draw(f['x'],image.h-f['y']-f['h'],f['w'],f['h'],0,flip,x+dx,y+dy,f['w']*scale,f['h']*scale)
        if color is not None:p2.SDL_SetTextureColorMod(image.texture,255,255,255)
        image.opacify(1.)

    def hud(self,game,camera,mouse=(0,0)):
        self.skin.hud(game,camera,mouse)

    @staticmethod
    def card_at(x,y):
        return Interface.card_at(x,y)

    def reward(self,game,mouse):
        self.hover=self.ui.reward_focus
        self.skin.reward(game)

    def title(self):
        self.skin.title()

    def menu(self,game,mouse):
        ui=self.ui
        if ui.page!='main':
            box(0,0,1280,720,(7,13,21),246)
            self.skin.frame('card',100,24,1080,666)
            self.text('조작과 전투' if ui.page=='help' else '설정',640,640,44,INK,True,display=True)
            if ui.page=='help':
                rows=[('A D / ← →','좌우 이동 · 보는 방향으로 검격'),('SPACE','점프 · 공중 검격/패링 가능'),
                      ('좌클릭','클릭마다 검격 · 추가 클릭으로 연격'),('우클릭','적 타격 직전에 정면에서 패링'),
                      ('Q','제자리 회복 · 완료 시 소모 · 돌파마다 충전')]
                for i,(key,desc) in enumerate(rows):
                    y=550-i*59;self.text(key,145,y,21,TEAL);self.text(desc,310,y,18,INK)
                self.text('검사: 짧은 베기 · 창병: 긴 찌르기',145,232,18,GOLD)
                self.text('도장주: 2페이즈 · 사망 시 처음부터',145,202,18,INK)
                self.text('1곳: 스타일 / 2·3곳: 증강 선택',145,172,18,MUTED)
                self.skin.frame('card',748,150,410,443)
                self.text('현재 선택',953,560,25,GOLD,True,display=True)
                player=game.player
                keys=[player.style]+[k for k in C.AUGMENTS if k in player.augments]
                keys=(keys+[None,None])[:3]
                for i,key in enumerate(keys):
                    y=510-i*116;catalog=C.STYLES if i==0 else C.AUGMENTS
                    if key:
                        spent=(key=='revive' and player.revive_used) or (key=='unyielding' and player.unyielding_used)
                        active=key=='unyielding' and player.unyielding_left>0
                        title=catalog[key][0]+(' · 발동 중' if active else ' · 소모' if spent else '')
                        self.skin.seal(key,780,y+7,32,MUTED if spent and not active else GOLD)
                        self.text(title,810,y,21,MUTED if spent and not active else GOLD,display=True)
                        for j,line in enumerate(choice_detail(key,player)):
                            self.text(line,780,y-34-j*22,18,INK if j<2 else MUTED)
                    else:
                        self.text(('전투 스타일 미선택','첫 번째 증강 미선택','두 번째 증강 미선택')[i],780,y,21,MUTED)
                        self.text(('첫 전투 돌파 후 선택','두 번째 돌파 후 선택','세 번째 돌파 후 선택')[i],780,y-34,18,MUTED)
                self.text('아이콘: Lorc / Game-icons.net · CC BY 3.0',640,46,15,MUTED,True)
            else:
                self.text(ui.settings_status,640,565,18,MUTED,True)
                self.text('← → 로 음량 조절 · ENTER 또는 클릭으로 변경',640,526,18,MUTED,True)
                self.text('M 음소거   F7/F8 음량   F6 흔들림   F1 조작 안내',640,78,18,MUTED,True)
        for i,(action,label,x,y,w,h) in enumerate(ui.buttons(game)):
            selected=i==ui.focus
            value={'volume':f'{round(self.volume*100)}%','mute':'켜짐' if self.muted else '꺼짐',
                   'shake':'켜짐' if self.shake_enabled else '꺼짐','hints':'켜짐' if self.hints_enabled else '꺼짐'}.get(action,'')
            self.skin.button(label,x,y,w,h,selected,value)

    def result(self,game):
        p=game.player
        self.skin.frame('card',165,252,950,400)
        clear=game.state=='clear'
        self.text('벼랑 위에 닿은 칼날' if clear else '검은 다시 벼랑 아래로',640,574,44,GOLD if clear else INK,True,display=True)
        self.text('빼앗긴 도장에, 다시 검객이 섰다.' if clear else f'{game.stage["name"]}에서 멈춘 발걸음. 다음에는 더 높이.',640,514,21,MUTED,True)
        for i,stage in enumerate(C.STAGES):
            x=373+i*178;complete=clear or i<game.stage_index
            if i<3:box(x,449,178,2,(72,85,98))
            p2.draw_circle(x,450,9,*(GOLD if complete else RED if i==game.stage_index else MUTED))
            self.text(stage['name'],x,411,18,GOLD if complete else MUTED,True)
        self.text(f'처치 {p.kills}     패링 {p.parries}회     {int(game.time)//60:02d}:{int(game.time)%60:02d}',640,367,25,TEAL,True)
        names=[C.STYLES[p.style][0]] if p.style else []
        names += [C.AUGMENTS[k][0] for k in C.AUGMENTS if k in p.augments]
        self.text('이번 판: '+(' · '.join(names) or '아직 선택한 힘 없음'),640,329,21,GOLD,True)
        if not clear:self.text(last_hit_text(game.last_hit),640,292,18,INK,True)

    def draw(self, game, dt, mouse=(0,0), gallery=None):
        self.clock+=dt
        hp=game.player.hp
        if hp<self.hp_seen:self.hp_delay=.22
        elif hp>self.hp_seen:self.hp_trail=hp
        self.hp_delay=max(0.,self.hp_delay-dt)
        if self.hp_delay==0:self.hp_trail=max(hp,self.hp_trail-dt*C.MAX_HP*.9)
        self.hp_seen=hp
        p2.clear_canvas()
        if gallery is not None:
            self.gallery(gallery)
            return
        if game.state=='title': self.title(); self.menu(game,mouse); return
        # Negative native viewports can discard the world on SDL/D3D drivers.
        # Shake world coordinates instead, leaving the HUD and viewport intact.
        camera=game.camera+(math.sin(self.clock*111)*game.shake if self.shake_enabled else 0.)
        self.environment(game,camera)
        for actor in [*game.enemies,game.player]:
            if actor is game.player or actor.alive or actor.elapsed<.5:self.shadow(actor,game,camera)
        p=game.player
        name=('attack' if p.combo_index==0 else f'attack{p.combo_index+1}') if p.action=='attack' else p.action if p.action in ('parry','hurt','death') else 'jump' if not p.grounded else 'run' if p.moving else 'idle'
        seconds=p.action_time if p.action in ('attack','parry','hurt','death') else self.clock
        if name=='run': seconds=p.run_time
        if p.action=='idle' and not p.moving and p.parry_feedback>0:
            name='parry';seconds=p.action_time
        if name=='parry':seconds=parry_pose_time(self.hero_data['animations']['parry'],seconds,p.parry_feedback)
        if p.action=='attack':
            if p.attack_from_run and seconds<self.hero_data['animations']['brake']['frames'][0]['durationMs']/1000:
                name='brake'
            else:seconds=attack_pose_time(self.hero_data['animations'][name],seconds,p.combo_index)
        face=p.facing
        if p.counter_left>0 and p.action in ('hurt','idle'):
            name='attack3'
            seconds=counter_pose_time(self.hero_data['animations'][name],1-p.counter_left/C.COUNTER_DISPLAY)
            face=p.counter_facing
        frame=None
        if name=='jump': frame=1 if p.vy>300 else 2 if p.vy>0 else 3 if p.vy>-300 else 4
        alpha=.45 if p.invulnerable>0 and int(self.clock*16)%2 else 1.
        if p.counter_left>C.COUNTER_DISPLAY-.12:alpha=1.
        # The successful sweep passes on the far side of the opponent. Keeping
        # it on the foreground layer makes a non-damaging parry look like a stab.
        for enemy in sorted(game.enemies,key=lambda e:e.alive):self.draw_enemy(enemy,camera)
        self.draw_hero(name,seconds,p.x-camera,p.y,face,alpha=alpha,frame=frame)
        # The readied thrust runs in front of the coat at close range.
        for enemy in game.enemies:
            if self.enemy_pose(enemy)==('boss-extra',0):
                data=self.enemy_data['boss-extra']; ax,ay=data['frames'][0]['anchor']
                scale=182/data['referenceBodyHeight']; image=self.enemies['boss-extra']
                dx,dy,_=self.enemy_weight(enemy)
                image.clip_composite_draw(224,image.h-269,177,14,0,'h' if enemy.facing<0 else '',
                    enemy.x-camera+enemy.facing*((312.5-ax)*scale+dx),enemy.y+(ay-262)*scale+dy,177*scale,14*scale)
        if p.counter_ready:
            # Ready charge follows the body; clash sparks remain at the contact.
            for i in range(4):
                phase=(self.clock*1.6+i*.25)%1
                sx=p.x-camera+(i%2*2-1)*(20+phase*8)
                sy=p.y+45+phase*43
                box(sx,sy,2,6,RED,round(160*math.sin(phase*math.pi)))
        if p.action=='heal':
            progress=min(1.,p.action_time/C.HEAL_TIME)
            box(p.x-camera-24,p.y+158,48,4,(25,35,40),220)
            box(p.x-camera-24,p.y+158,48*progress,4,TEAL,230)
        self.effects(game,camera)
        if game.state!='reward' and not game.result_visible:
            self.hud(game,camera,mouse)
        boss=next((e for e in game.enemies if e.alive and e.state=='transition'),None)
        if boss:
            self.skin.frame('band',375,300,530,95)
            self.text('아직 끝나지 않았다',640,350,32,RED,True,display=True)
        if game.state=='reward':self.reward(game,mouse);self.menu(game,mouse)
        elif game.state=='paused' or game.result_visible:
            box(0,0,1280,720,(7,12,19),210)
            if game.state=='paused':
                self.skin.frame('band',380,470,520,135)
                self.text('일시정지',640,551,44,INK,True,display=True)
                self.text('ESC 계속하기 · 방향키 선택 · ENTER 확인',640,493,18,MUTED,True)
            else:
                self.result(game)
            self.menu(game,mouse)

    def gallery(self, index):
        box(0,0,1280,720,(14,22,31))
        labels=[('idle','대기'),('run','이동'),('jump','점프'),('attack','내려베기'),('attack2','올려베기'),('attack3','마무리 베기'),('parry','패링'),('hurt','피격'),('death','사망')]
        name,label=labels[index%len(labels)]
        self.text('주인공 모션 보기',640,655,32,GOLD,True)
        self.text(f'{index%9+1} / 9   {label}',640,597,25,INK,True)
        box(140,169,1000,2,(90,101,108))
        self.draw_hero(name,self.clock,300,170,1,240)
        self.draw_hero(name,self.clock,980,170,-1,240)
        self.text('오른쪽 / 왼쪽 방향',640,123,18,MUTED,True)
        self.text('← → 모션 변경   ·   ENTER 게임 시작   ·   ESC 종료',640,65,21,TEAL,True)


def capture(path):
    """Capture the real SDL renderer to PNG; no image dependency at runtime."""
    width,height=C.WIDTH,C.HEIGHT
    pixels=(ctypes.c_ubyte*(width*height*4))()
    result=p2.SDL_RenderReadPixels(p2.renderer,None,p2.SDL_PIXELFORMAT_ABGR8888,pixels,width*4)
    if result: raise RuntimeError('SDL screenshot failed')
    raw=bytes(pixels)
    rows=b''.join(b'\0'+raw[y*width*4:(y+1)*width*4] for y in range(height))
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(png)
