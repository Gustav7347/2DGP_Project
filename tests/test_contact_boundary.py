import unittest
from bladegame.core import Game, Controls, Enemy
from bladegame import config as C


class ContactBoundaryTests(unittest.TestCase):
    def setup_contact(self):
        g=Game(11);g.start();p=g.player;p.invulnerable=0
        e=Enemy(99,'sword',p.x+85,hp=300,max_hp=300,state='windup',timer=.004)
        g.enemies=[e];g.attack_owner=e.uid
        g._begin_attack();p.action_time=C.ATTACKS[0]['impact']-.004
        return g,p,e

    def test_contact_freezes_before_committed_retaliation_and_recoil(self):
        g,p,e=self.setup_contact();x=e.x
        g.tick(1/120)
        self.assertEqual(p.action,'attack')
        self.assertEqual(p.hp,C.MAX_HP)
        self.assertEqual(e.state,'windup')
        self.assertEqual(e.x,x)
        for _ in range(30):g.tick(1/120)
        self.assertLess(p.hp,C.MAX_HP)

    def test_long_frame_still_returns_the_contact_pose(self):
        g,p,e=self.setup_contact();e.timer=10
        g.tick(.1)
        self.assertTrue(p.attack_fired)
        self.assertLess(p.action_time,C.ATTACKS[0]['impact']+.01)
        g.tick(.1)
        self.assertGreater(p.action_time,C.ATTACKS[0]['impact']+.05)

    def test_late_click_after_finisher_waits_for_full_recovery_then_attacks_once(self):
        g,p,e=self.setup_contact();e.x=1800;e.timer=99
        g._begin_attack(2);p.action_time=.54
        p.attack_fired=p.attack_sounded=True
        g.tick(.01,Controls(attack=True))
        self.assertEqual(p.combo_index,2)
        for _ in range(8):g.tick(.01)
        self.assertEqual(p.combo_index,2)
        for _ in range(80):g.tick(.01)
        self.assertEqual([x['combo'] for x in g.events if x['kind']=='attack'],[1])

    def test_early_finisher_click_does_not_queue_an_unintended_later_attack(self):
        g,p,e=self.setup_contact();e.x=1800;e.timer=99
        g._begin_attack(2)
        g.tick(.01,Controls(attack=True))
        for _ in range(130):g.tick(.01)
        self.assertEqual([x['combo'] for x in g.events if x['kind']=='attack'],[3])

    def test_first_accepted_finisher_click_survives_the_recovery_boundary(self):
        g,p,e=self.setup_contact();e.x=1800;e.timer=99
        g._begin_attack(2);p.action_time=.32166666666666666
        p.attack_fired=p.attack_sounded=True
        g.tick(1/120,Controls(attack=True))
        self.assertGreater(p.attack_queue,0)
        for _ in range(160):g.tick(1/120)
        self.assertEqual([x['combo'] for x in g.events if x['kind']=='attack'],[1])

    def test_contact_presentation_has_bounded_delay_and_no_catchup_burst(self):
        for dt in (1/60,.1,.25):
            g,p,e=self.setup_contact();e.timer=99
            before=g.time;wall=dt
            g.tick(dt);contact=p.action_time
            for _ in range(10):
                if p.action_time>contact+1e-6:break
                last_time=g.time;g.tick(dt);wall+=dt
                self.assertLessEqual(g.time-last_time,dt+1e-7)
            self.assertGreater(p.action_time,contact)
            self.assertLessEqual(wall-(g.time-before),C.IMPACTS[0]['stop']+dt+1e-7)

    def test_interruptions_clear_the_latched_finisher_click(self):
        for interruption in ('parry','hurt'):
            g,p,e=self.setup_contact();e.x=1800;e.timer=99
            g._begin_attack(2);p.action_time=.54;p.attack_fired=p.attack_sounded=True
            g.tick(1/120,Controls(attack=True))
            if interruption=='parry':g.tick(1/120,Controls(parry=True))
            else:g._hurt_player(1)
            self.assertEqual(p.attack_queue,0)
            for _ in range(160):g.tick(1/120)
            self.assertFalse(any(x['kind']=='attack' for x in g.events))


if __name__=='__main__':unittest.main()
