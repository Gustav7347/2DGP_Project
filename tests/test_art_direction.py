import json,math,unittest
from pathlib import Path
from bladegame.core import Game,Controls,Enemy
from bladegame import motion,config as C

ROOT=Path(__file__).resolve().parents[1]

class ArtDirectionTests(unittest.TestCase):
    def fixture(self,face=1):
        g=Game(41);g.start();p=g.player;p.x=500;p.hp=50;p.invulnerable=0;p.facing=face
        g.enemies=[Enemy(i,'sword',p.x+face*(85+i-90),hp=500,max_hp=500,
                          facing=-face,state='recovery',timer=99) for i in (91,92)]
        return g,p

    def test_parry_cancels_heal_before_same_step_completion(self):
        g,p=self.fixture();p.action='heal';p.action_time=C.HEAL_TIME-.005
        g.tick(1/120,Controls(parry=True))
        self.assertEqual((p.action,p.hp,p.heals),('parry',50,1))
        self.assertFalse(any(e['kind']=='healed' for e in g.events))

    def test_parry_cancels_unfired_attack_before_same_step_impact(self):
        g,p=self.fixture();g._begin_attack();p.action_time=C.ATTACKS[0]['impact']-.005
        g.tick(1/120,Controls(move=-1,parry=True))
        self.assertEqual((p.action,p.facing),('parry',-1))
        self.assertEqual(g.enemies[0].hp,500)
        self.assertFalse(any(e['kind']=='attack' for e in g.events))

    def test_unavailable_parry_does_not_cancel_heal(self):
        g,p=self.fixture();p.action='heal';p.action_time=C.HEAL_TIME-.005;p.parry_cooldown=.2
        g.tick(1/120,Controls(parry=True))
        self.assertEqual((p.hp,p.heals),(100,0))

    def test_later_contact_records_the_pose_present_at_that_hit(self):
        data=json.loads((ROOT/'assets/player/animations.json').read_text('utf8'));anim=data['animations']['parry']
        for face in (1,-1):
            g,p=self.fixture(face);g.tick(1/120,Controls(parry=True));g._enemy_strike(g.enemies[0])
            start=g.time
            while g.time-start<.1-1e-8:g.tick(1/120)
            g._enemy_strike(g.enemies[1]);effect=next(e for e in reversed(g.effects) if e['kind']=='parry')
            self.assertIn('pose_feedback',effect)
            self.assertAlmostEqual(effect['pose_feedback'],p.parry_feedback)
            point=motion.parry_contact(anim,data['weapon'],*effect['origin'],face,(effect['x'],effect['y']),
                                       seconds=effect['pose_time'],feedback=effect['pose_feedback'])
            time=motion.parry_pose_time(anim,p.action_time,p.parry_feedback)
            a,b=motion.blade_edge(anim,data['weapon'],time,p.x,p.y,face,148,continuous=False)
            dx,dy=b[0]-a[0],b[1]-a[1]
            self.assertAlmostEqual((point[0]-a[0])*dy-(point[1]-a[1])*dx,0,places=6)

    def test_normal_parry_has_visual_enemy_reaction_but_counter_does_not(self):
        for counter in (False,True):
            g,p=self.fixture();p.augments={'counter'} if counter else set()
            g.tick(1/120,Controls(parry=True));g._enemy_strike(g.enemies[0])
            self.assertEqual(getattr(g.enemies[0],'deflect_left',0)>0,not counter)

if __name__=='__main__':unittest.main()
