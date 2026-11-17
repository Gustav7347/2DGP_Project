"""Initial playable balance. Times are seconds, distances are world pixels."""
WIDTH, HEIGHT = 1280, 720
SOUND_FILES = {**{f'swing{i}':f'blade-swing-v16-{i}.wav' for i in range(1,4)},
               **{f'parry{i}':f'parry-v9-{i}.wav' for i in range(1,4)},
               **{f'impact{i}':f'presentation-v2-impact-{i}.wav' for i in range(1,4)},
               'echo':'presentation-v2-impact-1.wav','counter':'presentation-v2-impact-3.wav',
               'hurt':'impact-2-soft.wav','reward':'presentation-v2-select.wav',
               'footstep1':'presentation-v2-footstep-1.wav','footstep2':'presentation-v2-footstep-2.wav',
               'jump':'presentation-v2-jump.wav','land':'presentation-v2-land.wav'}
GROUND = 112.0
MOVE_SPEED, JUMP_SPEED, GRAVITY = 280.0, 710.0, 1700.0
JUMP_BUFFER, COYOTE_TIME, ARRIVAL_TIME = .10, .08, .75
MAX_HP, BASE_DAMAGE = 100.0, 16.0
HURT_TIME, ATTACK_MOVE_FACTOR = .18, .38
ATTACKS = [
    {'time':.47, 'impact':.21, 'link':.33, 'damage':1., 'reach':165., 'step':20.},
    {'time':.43, 'impact':.165, 'link':.30, 'damage':.95, 'reach':165., 'step':24.},
    {'time':.65, 'impact':.235, 'link':.65, 'damage':1.3, 'reach':185., 'step':32.},
]
COMBO_BUFFER, HOLD_CHAIN_LEAD = .32, .10
LUNGE_LEAD, LUNGE_TIME = .07, .11
IMPACTS = [
    {'stop':.042,'shake':2.,'push':13.,'hurt':.13,'recoil':.14},
    {'stop':.048,'shake':2.4,'push':17.,'hurt':.15,'recoil':.15},
    {'stop':.072,'shake':4.2,'push':28.,'hurt':.20,'recoil':.18},
]
ECHO_IMPACT_SCALE, BOSS_PUSH_SCALE = .5, .20
PLAYER_HIT_PUSH, PLAYER_RECOIL_TIME, HURT_MOVE_FACTOR = 12., .16, .30
PARRY_WINDOW, PARRY_TIME, PARRY_COOLDOWN = .18, .34, .39
PARRY_PUSH, PARRY_PUSH_TIME, HEAL_TIME = 25., .16, .85
INVULNERABILITY = .40
COUNTER_DISPLAY = .30
CHAIN_CAP, CHAIN_BONUS, CHAIN_GRACE, CHAIN_DECAY = 12, .045, 2.0, 3.0
BLEED_TIME, BLEED_DPS = 2.8, 4.0
UNYIELDING_TIME, UNYIELDING_BONUS = 3.0, .50
BLOOD_BONUS, MOON_HEAL = 1., 7.
NORMAL_STUN, BOSS_STUN, BOSS_PARRIES = 1., 1.15, 3
INSIGHT_DAMAGE, INSIGHT_RANGE = 1.75, 1.5
ECHO_DAMAGE, ECHO_DELAY, COUNTER_DAMAGE = .65, .16, 2.6
BOSS_PHASE_THRESHOLD, BOSS_TRANSITION, BOSS_PHASE_RECOVERY = .5, 1.2, .6
ENEMY_ACTIVE, ENEMY_RECOVERY, BOSS_RECOVERY = .12, .70, .72
GROUP_HANDOFF = .20
BOSS_PHASE2_WINDUP, BOSS_FOLLOWUP_WINDUP = .85, .46
CLEAR_WAIT, WAITING_DISTANCE = .75, 72.
ENEMIES = {
    'sword': {'hp':44., 'damage':12., 'speed':111., 'windup':.65, 'reach':117., 'stop':90., 'thrust_speed':110.},
    'spear': {'hp':52., 'damage':15., 'speed':88., 'windup':.78, 'reach':205., 'stop':170., 'thrust_speed':110.},
    'boss': {'hp':420., 'damage':24., 'speed':108., 'windup':.76, 'reach':175., 'stop':140., 'thrust_speed':340.},
}
BOSS_THRUST_REACH = 250.
BOSS_PATTERNS = {1:['slash','thrust'], 2:['combo','chain','thrust','slash']}
STYLES = {
    'blood': ('혈인', '잃은 체력에 비례해 공격 피해 증가'),
    'moon': ('반월', '패링 시 회복 · 일반 적 기절\n보스는 3회 성공 시 기절'),
    'chain': ('연참', '적중마다 공격력 중첩\n2초 미적중 후 점차 감소'),
}
AUGMENTS = {
    'counter': ('육참골단', '패링해도 피해를 받는 대신\n다음 공격을 강화'),
    'echo': ('잔영검', '첫 타격 피해 감소\n같은 위치에 지연 검격'),
    'bleed': ('혈흔', '공격 시 출혈\n패링한 적의 잔여 출혈 피해 적용'),
    'insight': ('간파', '패링 후 다음 공격을\n넓고 강한 검격으로 변경'),
    'unyielding': ('불굴', '치명상에 체력 1로 3초 생존\n피해 증가 · 한 판 1회'),
    'revive': ('회생', '치명상 무시 후 전체 회복\n한 판 1회'),
}
STAGES = [
    {'name':'절벽 아래', 'subtitle':'잃어버린 도장으로 가는 첫 걸음', 'width':2050,
     'waves':[['sword'],['sword','sword']],
     'encounters':[{'trigger':0,'positions':[720],'name':'첫 검', 'hint':'베기가 닿기 직전, 적을 바라보고 패링'},
                   {'trigger':1080,'positions':[1430,1690],'name':'돌길의 두 검', 'hint':'앞선 적을 상대하고 다음 공격을 읽어라'}],
     'platforms':[(540,205,180),(900,300,185),(1210,205,185),(1570,230,190)]},
    {'name':'산길', 'subtitle':'긴 창의 사거리를 읽어라', 'width':2350,
     'waves':[['spear'],['sword','spear'],['spear','sword']],
     'encounters':[{'trigger':0,'positions':[720],'name':'창의 거리', 'hint':'긴 사거리를 넘거나 공격 뒤의 틈을 노려라'},
                   {'trigger':850,'positions':[1180,1440],'name':'검 뒤의 창', 'hint':'낮은 발판에서도 검격과 패링이 닿는다'},
                   {'trigger':1570,'positions':[1880,2150],'name':'산길의 끝', 'hint':'고른 스타일로 검과 창을 함께 상대하라'}],
     'platforms':[(500,205,220),(850,300,200),(1180,205,200),(1510,300,200),(1830,205,220)]},
    {'name':'도장 앞', 'subtitle':'선택한 힘으로 길을 열어라', 'width':2450,
     'waves':[['sword','spear'],['sword','spear','sword'],['spear','sword','sword']],
     'encounters':[{'trigger':0,'positions':[690,970],'name':'문지기', 'hint':'증강과 스타일의 연결을 시험하라'},
                   {'trigger':850,'positions':[610,1190,1490],'name':'협공', 'hint':'뒤에서도 적이 온다 · 보는 방향을 확인하라'},
                   {'trigger':1600,'positions':[1950,2240,1370],'name':'마지막 문턱', 'hint':'포위되기 전에 한쪽을 먼저 돌파하라'}],
     'platforms':[(450,205,200),(820,300,200),(1170,205,230),(1530,300,200),(1870,205,230)]},
    {'name':'도장', 'subtitle':'절벽 위에 남은 마지막 검', 'width':1280,
     'waves':[['boss']],
     'encounters':[{'trigger':0,'positions':[850],'name':'도장주', 'hint':'공격의 끝을 읽어라 · 체력 절반에서 2페이즈'}], 'platforms':[]},
]
