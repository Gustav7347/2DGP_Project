"""Pose timing and continuous blade rotation; body pixels stay on authored frames."""

import math
from .config import ATTACKS,PARRY_WINDOW


def parry_pose_time(animation,seconds,feedback=0.):
    ready=animation['frames'][0]['durationMs']/1000+1e-8
    guard=sum(f['durationMs'] for f in animation['frames'][:2])/1000+1e-8
    contact=sum(f['durationMs'] for f in animation['frames'][:3])/1000+1e-8
    followthrough=sum(f['durationMs'] for f in animation['frames'][:4])/1000+1e-8
    neutral=sum(f['durationMs'] for f in animation['frames'][:5])/1000+1e-8
    if feedback>0:
        elapsed=max(0.,.22-feedback)
        if elapsed<.025:return guard
        if elapsed<.105:return contact+(followthrough-contact-2e-8)*(elapsed-.025)/.080
        return followthrough if elapsed<.15 else neutral
    if seconds<=PARRY_WINDOW:
        return ready if seconds<.035 else guard
    return neutral


def counter_pose_time(animation,progress):
    start=sum(f['durationMs'] for f in animation['frames'][:4])/1000
    end=sum(f['durationMs'] for f in animation['frames'])/1000
    return start+(end-start)*max(0.,min(1.,progress))


def deflect_frame(left):
    elapsed=max(0.,.22-left)
    for i,end in enumerate((.035,.07,.115,.16,.19,.22)):
        if elapsed<end:return i
    return 5


def attack_pose_time(animation, seconds, combo_index):
    if combo_index: return seconds
    attack=ATTACKS[0]
    ready=animation['frames'][0]['durationMs']/1000
    contact=sum(f['durationMs'] for f in animation['frames'][:4])/1000
    end=sum(f['durationMs'] for f in animation['frames'])/1000
    time=max(0.,min(seconds,attack['time']))
    if time<=attack['impact']:
        return ready+(contact-ready)*time/attack['impact']
    return contact+(end-contact)*(time-attack['impact'])/(attack['time']-attack['impact'])


def run_weight(step):
    """Torso lead, torso elevation, and sole clearance in pixels at gameplay scale."""
    toe_off=.72
    if step<toe_off:
        stance=step/toe_off
        bend=math.sin(math.pi*stance)
        return 3*bend,-8*bend,0.
    flight=(step-toe_off)/(1-toe_off)
    lift=4*flight*(1-flight)
    return -2*lift,5*lift,5*lift


def sample_frame(animation, seconds):
    durations=[f['durationMs']/1000 for f in animation['frames']]
    total=sum(durations)
    time=seconds%total if animation['loop'] else min(max(0.,seconds),total-1e-8)
    for i,duration in enumerate(durations):
        if time<duration: return i,time/duration
        time-=duration
    return len(durations)-1,1.


def blade_angle(animation, seconds):
    index,phase=sample_frame(animation,seconds)
    start=animation['frames'][index]['swordAngleDeg']
    end=animation['frames'][min(index+1,len(animation['frames'])-1)]['swordAngleDeg']
    if index not in (2,3,4):
        phase=phase*phase*(3-2*phase)
    return start+(end-start)*phase


def held_blade_angle(animation, seconds):
    index, phase = sample_frame(animation, seconds)
    frame = animation['frames'][index]
    if animation.get('poseRoles') is not None and index == 3:
        ease = phase * phase * (3 - 2 * phase)
        return -90 * (1 - ease)
    return frame['swordAngleDeg']


def grip_travel(animation, index, phase, scale):
    frames=animation['frames']
    current=frames[index]
    following=frames[min(index+1,len(frames)-1)]
    ease=phase*phase*(3-2*phase)
    dx,dy=[(following['grip'][k]-following['anchor'][k])-
           (current['grip'][k]-current['anchor'][k]) for k in (0,1)]
    # Only the torso contribution is continuous; the arm extension is drawn.
    distance=math.hypot(dx,dy)
    gain=min(1.,animation['referenceBodyHeight']*.065/max(1.,distance))
    return dx*scale*ease*gain,-dy*scale*ease*gain


def blade_edge(animation,weapon,seconds,x,y,facing,height,continuous=True):
    frame=animation['frames'][sample_frame(animation,seconds)[0]]
    scale=height/animation['referenceBodyHeight']
    gx=x+facing*(frame['grip'][0]-frame['anchor'][0])*scale
    gy=y+(frame['anchor'][1]-frame['grip'][1])*scale
    if 'tip' in frame:
        tx,ty=frame['tip']
        return (gx,gy),(x+facing*(tx-frame['anchor'][0])*scale,y+(frame['anchor'][1]-ty)*scale)
    if continuous:
        index,phase=sample_frame(animation,seconds)
        dx,dy=grip_travel(animation,index,phase,scale)
        gx+=facing*dx
        gy+=dy
    length=height*weapon['bladeToBodyRatio']*(weapon['opaqueBounds'][2]-weapon['grip'][0])/weapon['bladeLength']
    angle=math.radians(blade_angle(animation,seconds) if continuous else held_blade_angle(animation, seconds))
    return (gx,gy),(gx+facing*math.cos(angle)*length,gy-math.sin(angle)*length)


def parry_contact(animation,weapon,x,y,facing,hint,height=148,*,seconds=0.,feedback=.22):
    pose=parry_pose_time(animation,seconds,feedback)
    frame=animation['frames'][sample_frame(animation,pose)[0]]
    scale=height/animation['referenceBodyHeight']
    def world(point):
        return x+facing*(point[0]-frame['anchor'][0])*scale,y+(frame['anchor'][1]-point[1])*scale
    grip,tip=world(frame['grip']),world(frame['tip'])
    dx,dy=tip[0]-grip[0],tip[1]-grip[1]
    along=max(0.,min(1.,((hint[0]-grip[0])*dx+(hint[1]-grip[1])*dy)/(dx*dx+dy*dy)))
    return grip[0]+dx*along,grip[1]+dy*along


def blade_ribbon(animation,weapon,seconds,x,y,facing,height):
    if animation.get("integratedWeapon"):return []
    index,phase=sample_frame(animation,seconds)
    if index<2 or (index==2 and phase<.55) or index>5 or (index==5 and phase>=.35):return []
    fade=1-phase/.35 if index==5 else 1.
    # Draw the recent sweep around the current hand. Discrete wrist poses
    # otherwise leave a kink where two sprite frames meet in a single trail.
    hand,_=blade_edge(animation,weapon,seconds,x,y,facing,height)
    points=[]
    for n in range(25):
        u=n/24
        t=max(0.,seconds-(1-u)*.033)
        old_index,old_phase=sample_frame(animation,t)
        if old_index<2 or (old_index==2 and old_phase<.55):continue
        grip,tip=blade_edge(animation,weapon,t,x,y,facing,height)
        dx,dy=tip[0]-grip[0],tip[1]-grip[1]
        belly=math.sin(math.pi*u)**1.3
        outer=.98+.02*u
        inner=outer-.19*belly-.012*u
        opacity=round(240*fade*u**.65)
        points.extend(((hand[0]+dx*inner,hand[1]+dy*inner,round(opacity*.16*belly)),
                       (hand[0]+dx*outer,hand[1]+dy*outer,opacity)))
    return points
