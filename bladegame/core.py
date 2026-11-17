"""Deterministic game simulation, independent of SDL and assets."""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import random
from . import config as C


@dataclass(frozen=True)
class Rect:
    left: float
    bottom: float
    right: float
    top: float

    def overlaps(self, other: Rect) -> bool:
        return self.left < other.right and self.right > other.left and self.bottom < other.top and self.top > other.bottom


@dataclass
class Controls:
    move: int = 0
    jump: bool = False
    attack: bool = False
    parry: bool = False
    heal: bool = False
    attack_held: bool = False

    def held(self):
        return Controls(move=self.move,attack_held=self.attack_held)


@dataclass
class Player:
    x: float = 160.0
    y: float = C.GROUND
    vy: float = 0.0
    facing: int = 1
    hp: float = C.MAX_HP
    heals: int = 1
    grounded: bool = True
    moving: bool = False
    run_time: float = 0.
    attack_from_run: bool = False
    jump_buffer: float = 0.
    coyote: float = 0.
    action: str = 'idle'
    action_time: float = 0.0
    invulnerable: float = 0.0
    parry_cooldown: float = 0.0
    parry_ready: bool = False
    parry_feedback: float = 0.
    counter_left: float = 0.
    counter_facing: int = 1
    counter_ready: bool = False
    attack_counter: bool = False
    parry_rewarded: bool = False
    parried_targets: set[int] = field(default_factory=set)
    attack_fired: bool = False
    attack_enhanced: bool = False
    combo_index: int = 0
    attack_queue: float = 0.
    attack_sounded: bool = False
    lunge_applied: float = 0.
    recoil_left: float = 0.
    recoil_time: float = .16
    recoil_distance: float = 0.
    style: str | None = None
    augments: set[str] = field(default_factory=set)
    stacks: int = 0
    since_hit: float = 0.0
    decay_fraction: float = 0.0
    insight: bool = False
    unyielding_left: float = 0.0
    unyielding_used: bool = False
    revive_used: bool = False
    kills: int = 0
    parries: int = 0

    @property
    def bounds(self):
        return Rect(self.x-23,self.y+5,self.x+23,self.y+126)

    @property
    def multiplier(self):
        value = 1.0
        if self.style == 'blood': value += (1.0-self.hp/C.MAX_HP)*C.BLOOD_BONUS
        if self.style == 'chain': value += self.stacks*C.CHAIN_BONUS
        if self.unyielding_left > 0: value += C.UNYIELDING_BONUS
        return value


@dataclass
class Enemy:
    uid: int
    kind: str
    x: float
    y: float = C.GROUND
    facing: int = -1
    hp: float = 44.0
    max_hp: float = 44.0
    state: str = 'approach'
    timer: float = 0.0
    elapsed: float = 0.0
    hurt: float = 0.0
    bleed_left: float = 0.0
    parry_count: int = 0
    phase: int = 1
    transitioned: bool = False
    pattern: str = 'slash'
    pattern_count: int = 0
    combo_index: int = 0
    strike_spent: bool = False
    windup_total: float = .65
    hurt_duration: float = .18
    parry_push_delay: float = 0.
    recoil_left: float = 0.
    recoil_time: float = .14
    recoil_distance: float = 0.
    hit_serial: int = 0
    moving: bool = False
    walk_time: float = 0.
    deflect_left: float = 0.
    deflect_context: dict = field(default_factory=dict)

    @property
    def alive(self): return self.hp > 0

    @property
    def boss(self): return self.kind == 'boss'

    @property
    def bounds(self):
        return Rect(self.x-27,self.y+4,self.x+27,self.y+(161 if self.boss else 123))

    @property
    def reach(self):
        if self.boss and self.current_attack=='thrust': return C.BOSS_THRUST_REACH
        return C.ENEMIES[self.kind]['reach']

    @property
    def current_attack(self):
        return 'thrust' if self.pattern=='thrust' or (self.pattern=='chain' and self.combo_index==1) else 'slash'

    @property
    def attack_bounds(self):
        end = self.x+self.facing*self.reach
        return Rect(min(self.x,end),self.y+30,max(self.x,end),self.y+(155 if self.boss else 115))


@dataclass
class Strike:
    rect: Rect
    damage: float
    delay: float = 0.0
    kind: str = 'normal'
    enhanced: bool = False
    combo_index: int = 0
    facing: int = 0


class Game:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.state = 'title'
        self.player = Player()
        self.stage_index = 0
        self.wave_index = 0
        self.enemies: list[Enemy] = []
        self.choices: list[str] = []
        self.strikes: list[Strike] = []
        self.effects: list[dict] = []
        self.notices: list[tuple[str,float]] = []
        self.events: list[dict] = []
        self.milestones: list[dict] = []
        self.last_hit: dict | None = None
        self.time = 0.0
        self.stage_time = 0.0
        self.clear_wait = 0.0
        self.camera = 0.0
        self.attack_owner: int | None = None
        self.next_uid = 1
        self.transition_banner = 0.0
        self.hit_stop = 0.
        self.shake = 0.
        self.pending=Controls()
        self.practiced=set()

    @property
    def stage(self): return C.STAGES[self.stage_index]

    @property
    def result_visible(self):
        return self.state=='clear' or (self.state=='dead' and self.player.action_time>.85)

    @property
    def living(self): return [e for e in self.enemies if e.alive]

    @property
    def next_encounter(self):
        index=self.wave_index+1
        return self.stage['encounters'][index] if not self.living and index<len(self.stage['waves']) else None

    @property
    def encounter(self): return self.stage['encounters'][self.wave_index]

    def event(self, kind, **values):
        event={'kind':kind,'time':round(self.time,3),**values}
        self.events.append(event)
        self.events = self.events[-300:]
        if kind in ('run_started','stage_entered','wave_spawned','stage_cleared','reward_selected','boss_phase','run_cleared','player_died'):
            self.milestones.append(event)

    def notice(self, text, seconds=2.0):
        self.notices.append((text,seconds))
        self.notices = self.notices[-4:]

    def effect(self, kind, x, y, seconds=.35, **values):
        self.effects.append({'kind':kind,'x':x,'y':y,'life':seconds,'max_life':seconds,**values})

    def start(self):
        self.player = Player()
        self.time = 0.0
        self.events = []
        self.milestones=[]
        self.last_hit=None
        self.next_uid = 1
        self.practiced=set()
        self._enter_stage(0)
        self.event('run_started')

    def _enter_stage(self, index):
        self.stage_index = index
        self.wave_index = 0
        self.state = 'playing'
        self.choices = []
        self.enemies = []
        self.strikes = []
        self.effects = []
        self.notices = []
        self.attack_owner = None
        self.camera = 0.0
        self.stage_time = self.clear_wait = 0.0
        self.transition_banner = 2.5
        self.hit_stop=self.shake=0.
        self.pending=Controls()
        p = self.player
        p.x,p.y,p.vy,p.facing = 160.,C.GROUND,0.,1
        p.grounded,p.action,p.action_time = True,'idle',0.
        p.parry_ready = False
        p.parry_feedback=0.
        p.counter_left=0.
        p.counter_ready=p.attack_counter=p.parry_rewarded=False
        p.parried_targets.clear()
        p.jump_buffer=p.coyote=p.run_time=0.
        p.attack_queue=0.
        p.combo_index=0
        p.recoil_left=p.lunge_applied=0.
        p.stacks,p.since_hit,p.decay_fraction = 0,0.,0.
        p.invulnerable = .5
        self._spawn_wave()
        self.event('stage_entered',stage=index+1)

    def _spawn_wave(self):
        kinds = self.stage['waves'][self.wave_index]
        positions = self.encounter['positions']
        for kind,x in zip(kinds,positions):
            hp = C.ENEMIES[kind]['hp']
            enemy=Enemy(self.next_uid,kind,float(x),hp=hp,max_hp=hp)
            if self.wave_index>0:
                enemy.state,enemy.timer='arriving',C.ARRIVAL_TIME
                self.effect('land',enemy.x,enemy.y+2,C.ARRIVAL_TIME,power=1.)
            self.next_uid += 1
            self.enemies.append(enemy)
        self.notice(self.encounter['name'])
        self.event('wave_spawned',stage=self.stage_index+1,wave=self.wave_index+1)

    def choose(self, index):
        if self.state != 'reward' or not 0 <= index < len(self.choices): return False
        choice = self.choices[index]
        if self.stage_index == 0:
            self.player.style = choice
        else:
            self.player.augments.add(choice)
        self.event('reward_selected',choice=choice)
        self._enter_stage(self.stage_index+1)
        return True

    def toggle_pause(self):
        if self.state=='playing': self.state='paused'
        elif self.state=='paused': self.state='playing'

    def tick(self, dt, controls=None):
        if self.state not in ('playing','dead'): return
        controls = controls or Controls()
        controls=Controls(controls.move,controls.jump or self.pending.jump,controls.attack or self.pending.attack,
                          controls.parry or self.pending.parry,controls.heal or self.pending.heal,controls.attack_held)
        self.pending=Controls()
        remaining=max(0.,min(float(dt),.25))
        while remaining > 1e-8:
            step=min(remaining,1/120)
            if self.hit_stop>0:
                frozen=min(step,self.hit_stop)
                self.hit_stop-=frozen
                remaining-=frozen
                # Keep edge inputs until simulation resumes; held state is separate.
                continue
            self._step(step,controls)
            controls=controls.held()
            remaining-=step
            if self.hit_stop>0:
                # Always present a new contact before retaliation/recovery. Do not
                # carry a slow frame's excess time into a catch-up movement burst.
                self.hit_stop=max(0.,self.hit_stop-remaining)
                break
            if self.state not in ('playing','dead'): break
        self.pending=Controls(jump=controls.jump,attack=controls.attack,parry=controls.parry,heal=controls.heal)

    def _step(self, dt, c):
        for effect in self.effects: effect['life']-=dt
        self.effects=[e for e in self.effects if e['life']>0]
        self.notices=[(text,t-dt) for text,t in self.notices if t>dt]
        if self.state=='dead':
            self.player.action_time+=dt
            return
        self.time+=dt
        self.shake=max(0.,self.shake-dt*28)
        self.stage_time+=dt
        self.transition_banner=max(0.,self.transition_banner-dt)
        self._update_player(dt,c)
        if self.hit_stop>0:return
        for strike in list(self.strikes):
            if strike not in self.strikes: continue
            strike.delay-=dt
            if strike.delay<=0:
                self.strikes.remove(strike)
                self._resolve_strike(strike)
                if self.hit_stop>0:return
        for enemy in self.enemies:
            self._update_enemy(enemy,dt)
            if self.state=='dead' or self.hit_stop>0: break
        if self.state!='playing' or self.hit_stop>0: return
        self._check_progress(dt)
        target=max(0.,min(self.stage['width']-C.WIDTH,self.player.x-C.WIDTH*(.5-.12*self.player.facing)))
        self.camera+=(target-self.camera)*(1-math.exp(-dt*5.))

    def _update_player(self, dt, c):
        p=self.player
        p.invulnerable=max(0.,p.invulnerable-dt)
        p.parry_cooldown=max(0.,p.parry_cooldown-dt)
        p.parry_feedback=max(0.,p.parry_feedback-dt)
        p.counter_left=max(0.,p.counter_left-dt)
        p.jump_buffer=max(0.,p.jump_buffer-dt)
        if c.jump:p.jump_buffer=C.JUMP_BUFFER
        p.coyote=C.COYOTE_TIME if p.grounded else max(0.,p.coyote-dt)
        p.unyielding_left=max(0.,p.unyielding_left-dt)
        p.since_hit+=dt
        if p.since_hit>C.CHAIN_GRACE:
            p.decay_fraction+=dt*C.CHAIN_DECAY
            loss=int(p.decay_fraction)
            p.stacks=max(0,p.stacks-loss)
            p.decay_fraction-=loss
        p.action_time+=dt
        self._advance_recoil(p,dt)
        # An accepted final-recovery click stays latched until recovery completes.
        if p.action!='attack' or p.combo_index!=2:
            p.attack_queue=max(0.,p.attack_queue-dt)
        if c.move*p.facing<0 and p.grounded and p.action=='idle':
            p.run_time=0.
        transition=any(e.alive and e.state=='transition' for e in self.enemies)
        # Accepted cancellation owns this step before an old action can hit/finish.
        if not transition and c.parry and p.parry_cooldown<=0 and p.action!='hurt':
            if c.move:p.facing=1 if c.move>0 else -1
            p.action,p.action_time,p.parry_ready='parry',0.,True
            p.parry_rewarded=False
            p.parried_targets.clear()
            self.practiced.add('parry')
            p.parry_feedback=0.
            p.attack_queue=0.
            p.counter_left=p.run_time=0.
            p.parry_cooldown=C.PARRY_COOLDOWN
        if p.action=='attack':
            attack=C.ATTACKS[p.combo_index]
            if p.combo_index<2 and c.attack:
                p.attack_queue=C.COMBO_BUFFER
            elif p.combo_index==2 and c.attack and p.action_time>=attack['time']-C.COMBO_BUFFER:
                p.attack_queue=C.COMBO_BUFFER
            u=max(0.,min(1.,(p.action_time-attack['impact']+C.LUNGE_LEAD)/C.LUNGE_TIME))
            displacement=attack['step']*(u*u*(3-2*u))
            p.x=max(40.,min(self.stage['width']-40,p.x+p.facing*(displacement-p.lunge_applied)))
            p.lunge_applied=displacement
            if not p.attack_sounded and p.action_time>=attack['impact']-.075:
                p.attack_sounded=True
                self.event('swing',combo=p.combo_index+1)
            if not p.attack_fired and p.action_time>=attack['impact']:
                p.attack_fired=True
                reach=attack['reach']*(C.INSIGHT_RANGE if p.attack_enhanced else 1.)
                end=p.x+p.facing*reach
                rect=Rect(min(p.x,end),p.y+8,max(p.x,end),p.y+151)
                damage=C.BASE_DAMAGE*p.multiplier*attack['damage']*(C.INSIGHT_DAMAGE if p.attack_enhanced else 1.)
                if p.attack_counter:
                    damage*=C.COUNTER_DAMAGE
                    self.event('counter')
                if 'echo' in p.augments:
                    self._resolve_strike(Strike(rect,damage*C.ECHO_DAMAGE,kind='counter' if p.attack_counter else 'normal',enhanced=p.attack_enhanced,combo_index=p.combo_index,facing=p.facing))
                    self.strikes.append(Strike(rect,damage*C.ECHO_DAMAGE,C.ECHO_DELAY,'echo',p.attack_enhanced,p.combo_index,p.facing))
                else: self._resolve_strike(Strike(rect,damage,kind='counter' if p.attack_counter else 'normal',enhanced=p.attack_enhanced,combo_index=p.combo_index,facing=p.facing))
                self.effect('slash',p.x+p.facing*43,p.y+85,.30 if p.combo_index==2 else .25,facing=p.facing,reach=reach,
                            enhanced=p.attack_enhanced or p.attack_counter,combo=p.combo_index)
                self.event('attack',combo=p.combo_index+1)
            if p.attack_fired and p.combo_index<2 and p.attack_queue>0 and p.action_time>=attack['link']:
                if c.move: p.facing=1 if c.move>0 else -1
                self._begin_attack(p.combo_index+1)
            elif p.action_time>=attack['time']:
                p.action='idle'
                if p.combo_index==2 and p.attack_queue>0:
                    if c.move:p.facing=1 if c.move>0 else -1
                    self._begin_attack()
        elif p.action=='parry':
            if p.action_time>C.PARRY_WINDOW: p.parry_ready=False
            if p.action_time>=C.PARRY_TIME: p.action='idle'
        elif p.action=='hurt' and p.action_time>=C.HURT_TIME: p.action='idle'
        elif p.action=='heal' and p.action_time>=C.HEAL_TIME:
            p.hp=C.MAX_HP
            p.heals=0
            p.action='idle'
            self.effect('heal',p.x,p.y+75,.7)
            self.notice('회복약 사용 · 체력 전체 회복')
            self.event('healed')
        if c.move and p.action=='idle' and not transition: p.facing=1 if c.move>0 else -1
        if c.heal and self.can_heal():
            p.action,p.action_time='heal',0.
            p.jump_buffer=p.attack_queue=0.
            self.event('heal_started')
        if not transition:
            if c.attack and p.action=='idle':
                self._begin_attack()
        p.moving=bool(c.move) and not transition and p.action!='heal'
        if p.moving:
            if p.action=='idle':p.counter_left=0.
            self.practiced.add('move')
            if p.action=='idle': p.facing=1 if c.move>0 else -1
            speed=C.MOVE_SPEED*(C.ATTACK_MOVE_FACTOR if p.action in ('attack','parry') else 1.)
            if p.action=='hurt': speed*=C.HURT_MOVE_FACTOR
            previous_x=p.x
            p.x=max(40.,min(self.stage['width']-40,p.x+c.move*speed*dt))
            if p.action=='idle' and p.grounded:
                distance=abs(p.x-previous_x)
                p.moving=distance>1e-6
                p.run_time=p.run_time+distance/C.MOVE_SPEED if p.moving else 0.
        else: p.run_time=0.
        if p.action=='heal':p.jump_buffer=0.
        if p.jump_buffer>0 and (p.grounded or p.coyote>0) and not transition:
            p.vy=C.JUMP_SPEED
            p.grounded=False
            p.jump_buffer=p.coyote=0.
            self.practiced.add('jump')
            self.event('jumped')
        previous_y=p.y
        if not p.grounded:
            p.vy-=C.GRAVITY*dt
            p.y+=p.vy*dt
        if p.vy<=0:
            landing=C.GROUND
            for x,top,width in self.stage['platforms']:
                if x-15<p.x<x+width+15 and previous_y>=top and p.y<=top:
                    landing=max(landing,top)
            if p.y<=landing:
                if not p.grounded:
                    fall_speed=-p.vy
                    p.run_time=0.
                    self.effect('land',p.x,landing+2,.22,power=min(1.,max(.25,fall_speed/C.JUMP_SPEED)))
                    self.event('landed')
                p.y,p.vy,p.grounded=landing,0.,True
        if p.grounded and p.y>C.GROUND:
            if not any(x-15<p.x<x+w+15 and abs(p.y-y)<.1 for x,y,w in self.stage['platforms']):
                p.grounded=False

    def _begin_attack(self, index=0):
        p=self.player
        self.practiced.add('attack')
        p.attack_from_run=index==0 and p.grounded and p.run_time>0
        p.counter_left=p.run_time=0.
        p.combo_index=index
        p.action,p.action_time,p.attack_fired,p.attack_sounded='attack',0.,False,False
        p.attack_enhanced,p.insight=p.insight,False
        p.attack_counter,p.counter_ready=p.counter_ready,False
        if p.attack_counter:self.effect('combat_label',p.x-p.facing*38,p.y+180,.35,text='육참골단')
        if p.attack_enhanced:self.effect('combat_label',p.x-p.facing*38,p.y+155,.35,text='간파')
        p.attack_queue=0.
        p.lunge_applied=0.

    def can_heal(self):
        p=self.player
        return (p.heals>0 and p.hp<C.MAX_HP and p.action=='idle' and p.grounded
                and not any(e.alive and e.state=='transition' for e in self.enemies))

    def _advance_recoil(self, actor, dt):
        old=actor.recoil_left
        if old<=0: return
        actor.recoil_left=max(0.,old-dt)
        fraction=(old/actor.recoil_time)**2-(actor.recoil_left/actor.recoil_time)**2
        actor.x=max(40.,min(self.stage['width']-40,actor.x+actor.recoil_distance*fraction))

    def _resolve_strike(self, strike):
        if self.state!='playing': return
        for enemy in self.enemies:
            if enemy.alive and enemy.state!='transition' and strike.rect.overlaps(enemy.bounds):
                direction=strike.facing or self.player.facing
                edge=enemy.bounds.left if direction>0 else enemy.bounds.right
                contact_x=max(strike.rect.left,min(strike.rect.right,edge))
                self._hit_enemy(enemy,strike.damage,combo_index=strike.combo_index,
                                facing=direction,impact_kind=strike.kind,contact_x=contact_x)
                if strike.kind in ('normal','echo','counter'):
                    p=self.player
                    p.stacks=min(C.CHAIN_CAP,p.stacks+1)
                    p.since_hit=p.decay_fraction=0.
                    if 'bleed' in p.augments and enemy.alive: enemy.bleed_left=C.BLEED_TIME
        if strike.kind=='echo':
            facing=strike.facing or self.player.facing
            origin=strike.rect.left if facing>0 else strike.rect.right
            self.effect('slash',origin+facing*43,strike.rect.bottom+77,.23,
                        facing=facing,reach=strike.rect.right-strike.rect.left,echo=True,combo=strike.combo_index)

    def _hit_enemy(self, enemy, damage, bleed=False, *, combo_index=0, facing=None, impact_kind='normal', contact_x=None):
        if not enemy.alive or enemy.state=='transition': return
        enemy.hp=max(0.,enemy.hp-damage)
        if not bleed:
            if enemy.kind=='sword' and impact_kind in ('normal','counter','echo'):
                enemy.deflect_left=0.
                enemy.deflect_context.clear()
            impact=C.IMPACTS[combo_index]
            factor=C.ECHO_IMPACT_SCALE if impact_kind=='echo' else .45 if impact_kind=='bleed_release' else 1.
            enemy.hurt=enemy.hurt_duration=impact['hurt']*factor
            enemy.recoil_time=enemy.recoil_left=impact['recoil']
            enemy.recoil_distance=(facing or self.player.facing)*impact['push']*factor*(C.BOSS_PUSH_SCALE if enemy.boss else 1.)
            self.hit_stop=max(self.hit_stop,impact['stop']*factor)
            self.shake=max(self.shake,impact['shake']*factor)
            enemy.hit_serial+=1
            self.effect('number',enemy.x+(enemy.hit_serial%3-1)*15,enemy.y+120+(enemy.hit_serial%2)*17,.52,
                        text=str(round(damage)),bleed=False,finisher=combo_index==2)
            self.effect('hit',enemy.x if contact_x is None else contact_x,enemy.y+80,.26,
                        finisher=combo_index==2,combo=combo_index,facing=facing or self.player.facing)
            self.event('enemy_hit',enemy=enemy.uid,damage=round(damage,2),combo=combo_index+1,impact=impact_kind)
        if enemy.hp<=0:
            enemy.state,enemy.elapsed,enemy.bleed_left='dead',0.,0.
            self.player.kills+=1
            if self.attack_owner==enemy.uid: self.attack_owner=None
            self.event('enemy_defeated',enemy=enemy.uid,boss=enemy.boss)
        elif enemy.boss and enemy.hp<=enemy.max_hp*C.BOSS_PHASE_THRESHOLD and not enemy.transitioned:
            enemy.transitioned=True
            enemy.phase=2
            enemy.state,enemy.timer,enemy.elapsed='transition',C.BOSS_TRANSITION,0.
            enemy.bleed_left=0.
            enemy.recoil_left=0.
            self.strikes=[]
            self.attack_owner=None
            self.player.action,self.player.action_time='idle',0.
            self.player.parry_ready=False
            self.notice('도장주 · 2페이즈',2.)
            self.event('boss_phase',phase=2)

    def _hurt_player(self, damage, *, ignore_invulnerability=False, direction=0, enemy=None, reason='unblocked'):
        p=self.player
        if self.state!='playing' or (p.invulnerable>0 and not ignore_invulnerability): return False
        p.attack_queue=0.
        self.last_hit={'enemy_kind':enemy.kind if enemy else None,'attack':enemy.current_attack if enemy else None,
                       'reason':reason if enemy else 'unknown','stage':self.stage_index+1}
        if p.unyielding_left>0:
            p.hp=max(1.,p.hp-damage)
        elif damage>=p.hp:
            if 'unyielding' in p.augments and not p.unyielding_used:
                p.hp=1.
                p.unyielding_used=True
                p.unyielding_left=C.UNYIELDING_TIME
                self.notice('불굴 · 3초 동안 버틴다')
                self.event('unyielding_used')
            elif 'revive' in p.augments and not p.revive_used:
                p.hp=C.MAX_HP
                p.revive_used=True
                self.notice('회생 · 치명상 무효, 전체 회복')
                self.event('revive_used')
            else:
                p.hp=0.
                p.action,p.action_time,p.parry_ready='death',0.,False
                self.state='dead'
                self.strikes=[]
                self.event('player_died',stage=self.stage_index+1,hit=self.last_hit.copy())
                return True
        else: p.hp-=damage
        p.invulnerable=C.INVULNERABILITY
        p.recoil_time=p.recoil_left=C.PLAYER_RECOIL_TIME
        p.recoil_distance=(direction or -p.facing)*C.PLAYER_HIT_PUSH
        self.hit_stop=max(self.hit_stop,.045)
        self.shake=max(self.shake,3.)
        if p.action=='heal':
            self.effect('heal_interrupted',p.x,p.y,1.1)
        p.action,p.action_time,p.parry_ready='hurt',0.,False
        p.run_time=0.
        self.effect('hurt',p.x,p.y+70,.25,facing=direction or -p.facing)
        self.event('player_hit',damage=damage,hp=round(p.hp,2),hit=self.last_hit.copy())
        return True

    def _push_parry_area(self, attacker):
        p=self.player
        for target in self.living:
            dx=target.x-p.x
            distance=math.hypot(dx,target.y-p.y)
            if target is not attacker and distance>C.PARRY_PUSH_RADIUS:
                continue
            strength=1.-.5*min(distance/C.PARRY_PUSH_RADIUS,1.)
            push=C.PARRY_PUSH*strength*(C.BOSS_PUSH_SCALE if target.boss else 1.)
            direction=(1 if dx>0 else -1) if dx else p.facing
            target.recoil_time=target.recoil_left=C.PARRY_PUSH_TIME
            target.recoil_distance=direction*push
            target.parry_push_delay=.10

    def _enemy_strike(self, enemy):
        p=self.player
        if not enemy.attack_bounds.overlaps(p.bounds): return
        damage=C.ENEMIES[enemy.kind]['damage']
        facing_enemy=(enemy.x-p.x)*p.facing>=-18
        if p.parry_ready and p.action=='parry' and p.action_time<=C.PARRY_WINDOW and facing_enemy:
            first=not p.parry_rewarded
            new_target=enemy.uid not in p.parried_targets
            p.parry_rewarded=True
            p.parried_targets.add(enemy.uid)
            counter='counter' in p.augments
            if first:
                p.parry_feedback=.22
                p.parries+=1
            contact=dict(origin=(p.x,p.y),facing=p.facing,pose_time=p.action_time,pose_feedback=p.parry_feedback)
            # Ground contacts belong below the hat; airborne guards still project
            # this hint onto their actual blade rather than inventing a fixed point.
            hint=(p.x+p.facing*54,min(p.y+120,enemy.y+100))
            self.effect('parry',*hint,.28,counter=counter,**contact)
            if not counter and new_target:
                enemy.deflect_left=.22
                enemy.deflect_context=dict(**contact,hint=hint)
            self.hit_stop=max(self.hit_stop,.075)
            self.shake=max(self.shake,5.)
            if first:self.event('parry',enemy=enemy.uid)
            # Damage remains the cost of storing a counter; death wins over rewards.
            if counter:
                action_time=p.action_time
                self._hurt_player(damage,ignore_invulnerability=True,direction=enemy.facing,enemy=enemy,reason='counter_cost')
                if self.state=='dead': return
                p.action,p.action_time,p.parry_ready='parry',action_time,True
                p.recoil_left=0.
                p.counter_ready=True
            if first:
                self._push_parry_area(enemy)
            if not counter:
                self.effects=[e for e in self.effects if not (e['kind']=='enemy_slash' and e.get('enemy')==enemy.uid)]
            if p.style=='moon' and first:
                p.hp=min(C.MAX_HP,p.hp+C.MOON_HEAL)
            if p.style=='moon' and new_target:
                enemy.parry_count+=1
                if not enemy.boss or enemy.parry_count>=C.BOSS_PARRIES:
                    enemy.parry_count=0
                    enemy.state,enemy.timer,enemy.elapsed='stunned',C.BOSS_STUN if enemy.boss else C.NORMAL_STUN,0.
                    if self.attack_owner==enemy.uid: self.attack_owner=None
                    self.effect('stun',enemy.x,enemy.y+165,enemy.timer)
                    self.event('enemy_stunned',enemy=enemy.uid)
            if 'insight' in p.augments and first: p.insight=True
            if 'bleed' in p.augments and new_target and enemy.bleed_left>0:
                remaining=enemy.bleed_left*C.BLEED_DPS
                enemy.bleed_left=0.
                self._hit_enemy(enemy,remaining,impact_kind='bleed_release')
                self.effect('number',enemy.x,enemy.y+175,.65,text=f'출혈 {round(remaining)}',bleed=True)
        else:
            reason='unblocked'
            if not facing_enemy:reason='behind'
            elif p.action=='parry' and p.action_time>C.PARRY_WINDOW:reason='window_ended'
            elif p.action=='parry' and not p.parry_ready:reason='spent'
            self._hurt_player(damage,direction=enemy.facing,enemy=enemy,reason=reason)

    def _windup(self, enemy, followup=False):
        # A new committed attack must show its own preparation, never old recoil.
        enemy.deflect_left=0.
        enemy.deflect_context={}
        enemy.state,enemy.elapsed,enemy.strike_spent='windup',0.,False
        enemy.facing=1 if self.player.x>enemy.x else -1
        enemy.timer=C.BOSS_FOLLOWUP_WINDUP if enemy.boss and followup else C.ENEMIES[enemy.kind]['windup']
        if enemy.boss and enemy.phase==2: enemy.timer*=C.BOSS_PHASE2_WINDUP
        enemy.windup_total=enemy.timer
        self.attack_owner=enemy.uid
        self.event('enemy_windup',enemy=enemy.uid,pattern=enemy.pattern)

    def _update_enemy(self, enemy, dt):
        enemy.moving=False
        enemy.deflect_left=max(0.,enemy.deflect_left-dt)
        enemy.elapsed+=dt
        enemy.hurt=max(0.,enemy.hurt-dt)
        # On a deflection let contact register before the blade drives the target back.
        delay=min(dt,enemy.parry_push_delay)
        enemy.parry_push_delay-=delay
        self._advance_recoil(enemy,dt-delay)
        if not enemy.alive: return
        if enemy.state=='arriving':
            enemy.timer-=dt
            if enemy.timer<=0:enemy.state='approach'
            return
        if enemy.bleed_left>0 and enemy.state!='transition':
            duration=min(dt,enemy.bleed_left)
            enemy.bleed_left-=duration
            self._hit_enemy(enemy,C.BLEED_DPS*duration,bleed=True)
            if not enemy.alive: return
        if enemy.state=='transition':
            enemy.timer-=dt
            if enemy.timer<=0: enemy.state,enemy.timer='recovery',C.BOSS_PHASE_RECOVERY
            return
        if enemy.state=='stunned':
            enemy.timer-=dt
            if enemy.timer<=0: enemy.state='approach'
            return
        if enemy.hurt>0 and not enemy.boss and enemy.state in ('approach','recovery'): return
        if enemy.state=='windup':
            enemy.timer-=dt
            if enemy.timer<=0:
                enemy.state,enemy.timer,enemy.elapsed='active',C.ENEMY_ACTIVE,0.
                self.effect('enemy_slash',enemy.x+enemy.facing*40,enemy.y+85,.32,
                            facing=enemy.facing,thrust=enemy.current_attack=='thrust',enemy=enemy.uid)
        if enemy.state=='active':
            if enemy.current_attack=='thrust':
                enemy.x=max(45,min(self.stage['width']-45,enemy.x+enemy.facing*C.ENEMIES[enemy.kind]['thrust_speed']*dt))
            if not enemy.strike_spent and enemy.attack_bounds.overlaps(self.player.bounds):
                enemy.strike_spent=True
                self._enemy_strike(enemy)
                if enemy.state!='active' or self.state!='playing': return
            enemy.timer-=dt
            if enemy.timer<=0:
                if enemy.boss and ((enemy.pattern=='combo' and enemy.combo_index<2) or (enemy.pattern=='chain' and enemy.combo_index<1)):
                    enemy.combo_index+=1
                    self._windup(enemy,True)
                else:
                    enemy.state,enemy.timer,enemy.elapsed='recovery',C.BOSS_RECOVERY if enemy.boss else C.ENEMY_RECOVERY,0.
            return
        if enemy.state=='recovery':
            enemy.timer-=dt
            if not enemy.boss and enemy.elapsed>=C.GROUP_HANDOFF and self.attack_owner==enemy.uid:
                self.attack_owner=None
            if enemy.timer<=0:
                enemy.state='approach'
                if self.attack_owner==enemy.uid: self.attack_owner=None
            return
        if enemy.state!='approach': return
        p=self.player
        delta=p.x-enemy.x
        enemy.facing=1 if delta>0 else -1
        distance=abs(delta)
        stop=C.ENEMIES[enemy.kind]['stop']
        waiting=sum(1 for e in self.enemies if e is not enemy and e.alive and
                    (e.x-p.x)*(enemy.x-p.x)>0 and abs(e.x-p.x)<distance)
        approach_stop=stop+waiting*C.WAITING_DISTANCE
        previous_x=enemy.x
        if distance>approach_stop:
            enemy.x+=enemy.facing*C.ENEMIES[enemy.kind]['speed']*dt
        elif distance<40:
            enemy.x-=enemy.facing*60*dt
        enemy.moving=abs(enemy.x-previous_x)>1e-6
        if enemy.moving:enemy.walk_time+=(enemy.x-previous_x)*enemy.facing/C.ENEMIES[enemy.kind]['speed']
        visible=self.camera+30<enemy.x<self.camera+C.WIDTH-30
        if self.attack_owner is None and visible and distance<stop+20 and p.y<enemy.y+110:
            if enemy.boss:
                patterns=C.BOSS_PATTERNS[enemy.phase]
                enemy.pattern=patterns[enemy.pattern_count%len(patterns)]
                enemy.pattern_count+=1
            else: enemy.pattern='thrust' if enemy.kind=='spear' else 'slash'
            enemy.combo_index=0
            self._windup(enemy)

    def _check_progress(self, dt):
        if self.living:
            self.clear_wait=0.
            return
        self.clear_wait+=dt
        if self.clear_wait<C.CLEAR_WAIT: return
        if self.wave_index+1<len(self.stage['waves']):
            if self.player.x<self.next_encounter['trigger']:return
            self.clear_wait=0.
            self.wave_index+=1
            self._spawn_wave()
            return
        self.clear_wait=0.
        self.player.heals=1
        self.strikes=[]
        self.attack_owner=None
        self.event('stage_cleared',stage=self.stage_index+1)
        if self.stage_index==3:
            self.state='clear'
            self.event('run_cleared')
        else:
            self.state='reward'
            pool=list(C.STYLES) if self.stage_index==0 else [k for k in C.AUGMENTS if k not in self.player.augments]
            self.choices=self.rng.sample(pool,3)
