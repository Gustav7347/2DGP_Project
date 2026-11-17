import itertools, json, unittest
from pathlib import Path
from unittest.mock import patch
from bladegame import config as C
from bladegame.core import Game, Controls, Enemy, Rect, Strike
from bladegame.render import Renderer


class PlannedScopeTests(unittest.TestCase):
    def test_all_45_style_augment_combinations_resolve_hit_and_parry(self):
        for style in C.STYLES:
            for augments in itertools.combinations(C.AUGMENTS,2):
                with self.subTest(style=style,augments=augments):
                    g=Game(2); g.start(); p=g.player
                    p.style=style; p.augments=set(augments); p.hp=50; p.invulnerable=0
                    e=Enemy(7,'sword',p.x+85,hp=500,max_hp=500,state='active')
                    g.enemies=[e]
                    g._resolve_strike(Strike(Rect(p.x,100,p.x+170,300),16))
                    hp=e.hp
                    self.assertEqual(p.stacks,1)
                    p.action='parry'; p.action_time=.1; p.parry_ready=True
                    g._enemy_strike(e)
                    self.assertEqual(p.parries,1)
                    expected=50-(C.ENEMIES['sword']['damage'] if 'counter' in augments else 0)+(C.MOON_HEAL if style=='moon' else 0)
                    self.assertAlmostEqual(p.hp,expected)
                    if style=='moon': self.assertEqual(e.state,'stunned')
                    if 'insight' in augments: self.assertTrue(p.insight)
                    if 'bleed' in augments: self.assertEqual(e.bleed_left,0)
                    if 'bleed' in augments:self.assertLess(e.hp,hp)
                    if 'counter' in augments:
                        self.assertTrue(p.counter_ready)
                        g._begin_attack()
                        self.assertTrue(p.attack_counter)
                        self.assertFalse(p.counter_ready)
                    self.assertGreater(p.hp,0)

    def test_movement_and_jump_are_stable_across_frame_rates(self):
        positions=[]
        for fps in (10,20,30,60,144):
            g=Game(7);g.start();g.enemies=[]
            for i in range(fps//2): g.tick(1/fps,Controls(move=1,jump=i==0))
            positions.append((g.player.x,g.player.y))
        self.assertLess(max(x for x,y in positions)-min(x for x,y in positions),.01)
        self.assertLess(max(y for x,y in positions)-min(y for x,y in positions),2.)

    def test_boss_patterns_and_stun_have_distinct_drawable_poses(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'assets/enemies/animations.json').read_text('utf-8'))
        boss=Enemy(8,'boss',700,hp=200,max_hp=420,phase=2,transitioned=True)
        poses={}
        for pattern,state in [('slash','windup'),('slash','active'),('thrust','windup'),('thrust','active'),('slash','stunned')]:
            boss.pattern=pattern;boss.state=state
            asset,frame=Renderer.enemy_pose(boss)
            self.assertLess(frame,len(data[asset]['frames']))
            poses[(pattern,state)]=(asset,frame)
        self.assertEqual(len(set(poses.values())),5)

    def test_configured_windup_and_healing_reach_gameplay(self):
        g=Game(3);g.start();p=g.player
        boss=Enemy(7,'boss',p.x+90,hp=420,max_hp=420,phase=2)
        g.enemies=[boss]
        with patch.object(C,'BOSS_FOLLOWUP_WINDUP',.8),patch.object(C,'BOSS_PHASE2_WINDUP',.5):
            g._windup(boss,True)
        self.assertAlmostEqual(boss.timer,.4)
        self.assertAlmostEqual(boss.windup_total,.4)
        p.hp=50;p.style='moon';p.action='parry';p.action_time=.1;p.parry_ready=True
        with patch.object(C,'MOON_HEAL',14): g._enemy_strike(boss)
        self.assertEqual(p.hp,64)


if __name__=='__main__': unittest.main()
