import unittest
from bladegame.core import Game, Controls, Enemy, Strike, Rect
from bladegame import config as C


def advance(g, seconds):
    for _ in range(round(seconds*120)): g.tick(1/120)


class CombatTests(unittest.TestCase):
    def setUp(self):
        self.g=Game(17)
        self.g.start()
        self.p=self.g.player
        self.p.invulnerable=0
        self.e=self.g.enemies[0]
        self.e.x=self.p.x+85
        self.g.enemies=[self.e]

    def parry(self, enemy=None):
        self.p.parry_rewarded=False
        self.p.parried_targets.clear()
        self.p.action='parry'
        self.p.action_time=.1
        self.p.parry_ready=True
        self.g._enemy_strike(enemy or self.e)

    def test_direction_and_timed_window(self):
        self.parry()
        self.assertEqual(self.p.hp,100)
        self.assertEqual(self.p.parries,1)
        self.assertTrue(self.p.parry_ready)
        self.p.action='parry'; self.p.action_time=.181; self.p.parry_ready=True
        self.g._enemy_strike(self.e)
        self.assertEqual(self.p.hp,88)
        self.p.invulnerable=0; self.p.facing=-1
        self.parry()
        self.assertEqual(self.p.hp,76)

    def test_air_attack_and_parry(self):
        self.g.tick(1/120,Controls(jump=True,attack=True))
        self.assertFalse(self.p.grounded)
        self.assertEqual(self.p.action,'attack')
        self.g.tick(1/120,Controls(parry=True))
        self.assertEqual(self.p.action,'parry')

    def test_moon_boss_three_parries(self):
        self.p.style='moon'; self.p.hp=50
        boss=Enemy(9,'boss',self.p.x+90,hp=420,max_hp=420)
        self.g.enemies=[boss]
        for n in range(3):
            boss.state='active'
            self.parry(boss)
            self.assertEqual(boss.state,'stunned' if n==2 else 'active')
        self.assertEqual(boss.parry_count,0)
        self.assertEqual(self.p.hp,71)

    def test_counter_lethal_precedes_moon_healing(self):
        self.p.hp=3; self.p.style='moon'; self.p.augments={'counter'}
        self.parry()
        self.assertEqual(self.g.state,'dead')
        self.assertEqual(self.p.hp,0)
        self.assertEqual(self.e.hp,44)

    def test_survival_order_and_consumption_reset(self):
        self.p.augments={'unyielding','revive'}; self.p.hp=2
        self.g._hurt_player(20)
        self.assertTrue(self.p.unyielding_used)
        self.assertFalse(self.p.revive_used)
        self.g._hurt_player(500,ignore_invulnerability=True)
        self.assertEqual(self.p.hp,1)
        self.p.unyielding_left=0
        self.g._hurt_player(20,ignore_invulnerability=True)
        self.assertEqual(self.p.hp,100)
        self.assertTrue(self.p.revive_used)
        self.g._enter_stage(1)
        self.assertTrue(self.p.revive_used)
        self.g._hurt_player(500,ignore_invulnerability=True)
        self.assertEqual(self.g.state,'dead')
        self.g.start()
        self.assertFalse(self.g.player.unyielding_used)
        self.assertFalse(self.g.player.revive_used)
        self.assertEqual(self.g.player.augments,set())

    def test_chain_refresh_decay_and_blood_damage(self):
        self.p.style='chain'
        self.e.hp=self.e.max_hp=1000
        self.g._resolve_strike(Strike(Rect(0,0,1000,500),1))
        self.assertEqual(self.p.stacks,1)
        self.assertAlmostEqual(self.p.multiplier,1.045)
        self.e.state='stunned'; self.e.timer=10
        advance(self.g,2.5)
        self.assertEqual(self.p.stacks,0)
        self.p.style='blood'; self.p.hp=25
        self.assertAlmostEqual(self.p.multiplier,1.75)

    def test_echo_two_hits_without_recursion_and_bleed(self):
        self.p.augments={'echo','bleed'}
        self.e.hp=self.e.max_hp=1000
        self.e.state='stunned'; self.e.timer=10
        self.g.tick(1/120,Controls(attack=True))
        advance(self.g,.65)
        self.assertEqual(self.p.stacks,2)
        self.assertEqual(len(self.g.strikes),0)
        self.assertGreater(self.e.bleed_left,0)
        remaining=self.e.bleed_left*C.BLEED_DPS
        hp=self.e.hp
        self.parry()
        self.assertAlmostEqual(self.e.hp,hp-remaining)
        self.assertEqual(self.e.bleed_left,0)

    def test_insight_consumes_on_attack(self):
        self.p.augments={'insight'}
        self.parry()
        self.assertTrue(self.p.insight)
        self.p.action='idle'
        self.g.tick(.01,Controls(attack=True))
        advance(self.g,.09)
        self.assertTrue(self.p.attack_enhanced)
        self.assertFalse(self.p.insight)

    def test_attack_token_and_release(self):
        self.g.enemies.append(Enemy(20,'sword',self.p.x+90))
        self.g.tick(.01)
        self.assertEqual(sum(e.state=='windup' for e in self.g.enemies),1)
        owner=next(e for e in self.g.enemies if e.uid==self.g.attack_owner)
        self.g._hit_enemy(owner,500)
        self.g.tick(.01)
        self.assertNotEqual(self.g.attack_owner,owner.uid)

    def test_phase_change_once_and_death_priority(self):
        boss=Enemy(9,'boss',600,hp=420,max_hp=420)
        self.g.enemies=[boss]
        self.g._hit_enemy(boss,220)
        self.assertEqual(boss.phase,2)
        self.assertEqual(boss.state,'transition')
        advance(self.g,1.3)
        self.g._hit_enemy(boss,500)
        self.assertEqual(boss.state,'dead')
        self.assertEqual(sum(e['kind']=='boss_phase' for e in self.g.events),1)
        self.g.start()
        boss=Enemy(10,'boss',600,hp=420,max_hp=420)
        self.g.enemies=[boss]
        self.g._hit_enemy(boss,500)
        self.assertEqual(boss.phase,1)

    def test_full_loop_rewards_no_duplicates_and_heal_refill(self):
        for stage in range(4):
            self.assertEqual(self.g.stage_index,stage)
            self.g.player.heals=0
            for wave in range(len(self.g.stage['waves'])):
                if self.g.next_encounter:
                    self.g.player.x=self.g.next_encounter['trigger']
                    advance(self.g,.01)
                for e in self.g.living: self.g._hit_enemy(e,9999)
                advance(self.g,.8)
            self.assertEqual(self.g.player.heals,1)
            if stage<3:
                self.assertEqual(self.g.state,'reward')
                self.assertEqual(len(set(self.g.choices)),3)
                self.assertTrue(set(self.g.choices).isdisjoint(self.g.player.augments))
                self.g.choose(0)
            else: self.assertEqual(self.g.state,'clear')
        self.assertEqual(len(self.g.player.augments),2)

    def test_pause_freezes_everything(self):
        self.g.toggle_pause()
        old=(self.g.time,self.p.x,self.e.timer)
        self.g.tick(.25,Controls(move=1,attack=True))
        self.assertEqual(old,(self.g.time,self.p.x,self.e.timer))

    def test_three_hit_combo_queues_and_stops_without_input(self):
        self.e.x=1500
        self.g.tick(.01,Controls(attack=True))
        advance(self.g,.25)
        self.g.tick(.01,Controls(attack=True))
        advance(self.g,.15)
        self.assertEqual(self.p.combo_index,1)
        advance(self.g,.12)
        self.g.tick(.01,Controls(attack=True))
        advance(self.g,1.)
        hits=[e['combo'] for e in self.g.events if e['kind']=='attack']
        self.assertEqual(hits,[1,2,3])
        self.assertEqual(self.p.action,'idle')

    def test_input_not_lost_during_hit_stop(self):
        self.g.hit_stop=.08
        self.g.tick(.01,Controls(jump=True,parry=True))
        advance(self.g,.09)
        self.assertFalse(self.p.grounded)
        self.assertEqual(self.p.action,'parry')

    def test_phase_two_slash_to_thrust(self):
        boss=Enemy(9,'boss',self.p.x+100,hp=200,max_hp=420,phase=2,transitioned=True,pattern='chain')
        self.g.enemies=[boss]
        self.g._windup(boss)
        self.assertEqual(boss.current_attack,'slash')
        advance(self.g,.90)
        self.assertEqual(boss.combo_index,1)
        self.assertEqual(boss.current_attack,'thrust')
        self.assertEqual(self.g.attack_owner,boss.uid)


if __name__=='__main__': unittest.main()
