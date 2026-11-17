"""Verification controller: uses normal controls, no damage or health overrides."""
from .core import Controls


def control(game):
    p=game.player
    c=Controls()
    if game.state!='playing': return c
    if not game.living:
        if game.next_encounter:c.move=1 if p.x<game.next_encounter['trigger'] else 0
        return c
    enemy=min(game.living,key=lambda e:abs(e.x-p.x))
    delta=enemy.x-p.x
    direction=1 if delta>0 else -1
    if abs(delta)>94 or (p.facing!=direction and p.action=='idle'): c.move=direction
    attacker=next((e for e in game.living if e.uid==game.attack_owner),None)
    imminent=attacker and attacker.state=='windup' and attacker.timer<.105
    in_reach=attacker and abs(attacker.x-p.x)<attacker.reach+22
    if imminent and in_reach and p.parry_cooldown<=0:
        c.parry=True
    elif abs(delta)<155 and p.action in ('idle','attack') and not (attacker and attacker.state=='windup' and attacker.timer<.25):
        c.attack=True
    c.heal=p.hp<45 and bool(p.heals)
    return c


def choose(game):
    if game.stage_index==0: return game.choices.index('moon')
    for key in ('bleed','echo','insight','revive','unyielding','counter'):
        if key in game.choices: return game.choices.index(key)
    return 0
