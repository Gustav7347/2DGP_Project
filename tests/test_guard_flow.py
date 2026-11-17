import unittest
from bladegame.core import Game, Controls, Enemy
from bladegame import config as C


class GuardFlowTests(unittest.TestCase):
    def setUp(self):
        self.g=Game(41); self.g.start(); self.p=self.g.player
        self.p.invulnerable=0; self.p.hp=50
        self.a=Enemy(91,'sword',self.p.x+85,hp=500,max_hp=500,state='recovery',timer=99)
        self.b=Enemy(92,'sword',self.p.x+95,hp=500,max_hp=500,state='recovery',timer=99)
        self.g.enemies=[self.a,self.b]

    def guard(self):
        self.g.hit_stop=0; self.p.parry_cooldown=0
        self.g.tick(1/120,Controls(parry=True))

    def advance(self,seconds):
        for _ in range(round(seconds*120)): self.g.tick(1/120)

    def test_hold_does_not_create_additional_cuts(self):
        self.a.x=self.b.x=1800
        for i in range(180): self.g.tick(1/120,Controls(attack=i==0,attack_held=True))
        self.assertEqual([e['combo'] for e in self.g.events if e['kind']=='attack'],[1])

    def test_guard_blocks_two_targets_but_heals_once(self):
        self.p.style='moon'; self.guard()
        self.g._enemy_strike(self.a); self.g._enemy_strike(self.b)
        self.assertEqual(self.p.hp,57)
        self.assertEqual(self.p.parries,1)
        self.assertEqual([self.a.state,self.b.state],['stunned','stunned'])
        self.assertGreater(self.a.recoil_left,0)

    def test_sweep_pushes_both_sides_once_and_leaves_far_enemy_in_place(self):
        self.p.x=500
        self.a.x=575
        self.b.x=425
        far=Enemy(93,'sword',700,state='recovery',timer=99)
        boss=Enemy(94,'boss',575,state='recovery',timer=99)
        self.g.enemies.extend([far,boss])
        self.guard()
        self.assertTrue(all(e.recoil_left==0 for e in self.g.enemies))
        self.g._enemy_strike(self.a)
        initial=[e.x for e in self.g.enemies]
        for e in self.g.enemies:self.g._advance_recoil(e,C.PARRY_PUSH_TIME)
        self.assertGreater(self.a.x,initial[0])
        self.assertLess(self.b.x,initial[1])
        self.assertEqual(far.x,initial[2])
        self.assertAlmostEqual(boss.x-initial[3],(self.a.x-initial[0])*C.BOSS_PUSH_SCALE)
        self.g._enemy_strike(self.a)
        self.assertEqual(self.b.recoil_left,0)

    def test_boss_multihit_counts_once_per_guard(self):
        self.p.style='moon'; self.a.kind='boss'; self.guard()
        self.g._enemy_strike(self.a); self.g._enemy_strike(self.a)
        self.assertEqual(self.a.parry_count,1)
        self.assertEqual(self.p.hp,57)
        self.guard(); self.g._enemy_strike(self.a)
        self.assertEqual(self.a.parry_count,2)

    def test_turning_guard_uses_input_direction_immediately(self):
        self.p.facing=-1; self.g._begin_attack()
        self.g.tick(1/120,Controls(move=1,parry=True))
        self.g._enemy_strike(self.a)
        self.assertEqual(self.p.hp,50)
        self.assertEqual(self.p.facing,1)

    def test_deflected_enemy_trail_does_not_cover_the_guard_followthrough(self):
        self.g.effect('enemy_slash',self.a.x,self.a.y,.32,enemy=self.a.uid)
        self.g.effect('enemy_slash',self.b.x,self.b.y,.32,enemy=self.b.uid)
        self.guard(); self.g._enemy_strike(self.a)
        trails=[e['enemy'] for e in self.g.effects if e['kind']=='enemy_slash']
        self.assertEqual(trails,[self.b.uid])

    def test_counter_is_stored_until_next_attack_and_consumed_once(self):
        self.p.augments={'counter'}; self.guard(); before=self.a.hp
        self.g._enemy_strike(self.a)
        self.assertEqual(self.a.hp,before)
        self.assertEqual(self.p.hp,38)
        self.assertTrue(self.p.counter_ready)
        self.assertGreater(self.p.parry_feedback,0)
        self.advance(.6)
        self.g.tick(1/120,Controls(attack=True)); self.advance(.4)
        self.assertAlmostEqual(before-self.a.hp,C.BASE_DAMAGE*C.COUNTER_DAMAGE)
        self.assertFalse(self.p.counter_ready)
        self.assertEqual(sum(e['kind']=='counter' for e in self.g.events),1)

    def test_heal_is_stationary_and_spent_only_on_completion(self):
        x=self.p.x; self.g.tick(1/120,Controls(heal=True,move=1))
        self.assertEqual(self.p.hp,50); self.assertEqual(self.p.heals,1)
        self.advance(.25)
        self.g.tick(1/120,Controls(move=1,jump=True,attack=True))
        self.assertEqual(self.p.x,x); self.assertTrue(self.p.grounded)
        self.advance(1.2)
        self.assertEqual((self.p.hp,self.p.heals),(100,0))

    def test_parry_and_damage_cancel_heal_without_spending(self):
        self.g.tick(1/120,Controls(heal=True)); self.g.tick(1/120,Controls(parry=True))
        self.assertEqual((self.p.action,self.p.hp,self.p.heals),('parry',50,1))
        self.p.action='idle'; self.g.tick(1/120,Controls(heal=True))
        self.g._hurt_player(12); self.advance(1.3)
        self.assertEqual((self.p.hp,self.p.heals),(38,1))


if __name__=='__main__': unittest.main()
