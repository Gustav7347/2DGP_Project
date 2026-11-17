import unittest
import json
from pathlib import Path
from bladegame.core import Game, Controls, Enemy
from bladegame.render import Renderer
from bladegame.motion import parry_contact


class EnemyDeflectionTests(unittest.TestCase):
    def contact(self, kind, phase=1, counter=False, count=0):
        g=Game(41);g.start();p=g.player
        p.x=500;p.facing=1;p.invulnerable=0;p.hp=100;p.style='moon'
        p.augments={'counter'} if counter else set()
        e=Enemy(91,kind,585,facing=-1,hp=500,max_hp=500,state='active',
                timer=.1,phase=phase,parry_count=count)
        g.enemies=[e];g.tick(1/120,Controls(parry=True));g._enemy_strike(e)
        return g,e

    def test_each_enemy_has_its_own_contact_pose_and_counter_skips_it(self):
        for kind in ('sword','spear','boss'):
            for phase in ((1,2) if kind=='boss' else (1,)):
                with self.subTest(kind=kind,phase=phase):
                    g,e=self.contact(kind,phase)
                    self.assertGreater(e.deflect_left,0)
                    self.assertEqual(Renderer.enemy_pose(e),(kind+'-parried',0))
                    g,e=self.contact(kind,phase,counter=True)
                    self.assertEqual(e.deflect_left,0)
                    self.assertNotEqual(Renderer.enemy_pose(e)[0],kind+'-parried')

    def test_boss_braces_twice_and_third_contact_resolves_to_real_stun(self):
        for phase in (1,2):
            for count in (0,1,2):
                g,e=self.contact('boss',phase,count=count)
                self.assertEqual(e.state,'stunned' if count==2 else 'active')
                e.deflect_left=.13
                self.assertEqual(Renderer.enemy_pose(e)[0],
                                 'boss-extra' if count==2 else 'boss-parried')

    def test_new_boss_followup_and_phase_transition_cannot_be_hidden(self):
        g,e=self.contact('boss',2)
        e.deflect_left=.22
        g._windup(e,followup=True)
        self.assertEqual(e.deflect_left,0)
        self.assertNotEqual(Renderer.enemy_pose(e)[0],'boss-parried')
        e.deflect_left=.22;e.state='transition'
        self.assertEqual(Renderer.enemy_pose(e),('boss-extra',2))
        e.hp=0
        self.assertEqual(Renderer.enemy_pose(e),('boss',5))

    def test_first_ground_contact_stays_below_the_hat(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'assets/player/animations.json').read_text('utf8'))
        for kind in ('sword','spear','boss'):
            g,e=self.contact(kind)
            fx=next(fx for fx in g.effects if fx['kind']=='parry')
            point=parry_contact(data['animations']['parry'],data['weapon'],*fx['origin'],fx['facing'],
                                (fx['x'],fx['y']),seconds=fx['pose_time'],feedback=fx['pose_feedback'])
            self.assertLess(point[1],g.player.y+110)


if __name__=='__main__':unittest.main()
