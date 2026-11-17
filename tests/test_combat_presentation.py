import unittest
from bladegame import motion,config as C
from bladegame.core import Game,Controls,Enemy


class CombatPresentationTests(unittest.TestCase):
    def game(self):
        g=Game(104);g.start();g.stage_index=1;g.player.x=1100
        g.enemies=[Enemy(99,'sword',2200,state='stunned',timer=99)]
        return g

    def test_left_facing_keeps_more_view_in_front_of_the_player(self):
        g=self.game();g.player.facing=-1
        for _ in range(240):g.tick(1/120)
        self.assertGreater(g.player.x-g.camera,C.WIDTH*.55)
        self.assertLessEqual(g.camera,g.stage['width']-C.WIDTH)
        g.player.facing=1
        old=g.camera;g.tick(1/60)
        self.assertGreater(g.camera,old)
        self.assertLess(g.camera-old,40)

    def test_camera_response_is_consistent_across_render_rates(self):
        cameras=[]
        for fps in (30,60,144):
            g=self.game();g.player.facing=-1
            for _ in range(fps):g.tick(1/fps)
            cameras.append(g.camera)
        self.assertLess(max(cameras)-min(cameras),.01)

    def test_blade_edge_matches_grip_and_mirrors_the_actual_tip(self):
        anim={'referenceBodyHeight':100,'loop':False,'frames':[
            {'durationMs':100,'swordAngleDeg':0,'anchor':[0,0],'grip':[0,0]} for _ in range(8)]}
        weapon={'bladeToBodyRatio':.8,'bladeLength':100,'grip':[0,0],'opaqueBounds':[0,0,100,20]}
        edge=motion.blade_edge
        self.assertEqual(edge(anim,weapon,.32,100,200,1,100),((100,200),(180,200)))
        self.assertEqual(edge(anim,weapon,.32,100,200,-1,100),((100,200),(20,200)))

    def test_group_handoff_uses_recovery_without_overlapping_committed_attacks(self):
        g=self.game();p=g.player
        first=Enemy(20,'sword',p.x+90,state='active',timer=.001,facing=-1,strike_spent=True)
        second=Enemy(21,'sword',p.x-90,state='approach',facing=1)
        g.enemies=[first,second];g.attack_owner=first.uid
        g._update_enemy(first,.01)
        self.assertEqual(first.state,'recovery');self.assertEqual(g.attack_owner,first.uid)
        g._update_enemy(first,.21);g._update_enemy(second,.01)
        self.assertEqual(first.state,'recovery');self.assertGreater(first.timer,0)
        self.assertEqual(second.state,'windup');self.assertEqual(g.attack_owner,second.uid)
        g._update_enemy(first,1.)
        self.assertEqual(g.attack_owner,second.uid)

    def test_group_never_commits_two_attacks_at_once(self):
        g=self.game();p=g.player;p.invulnerable=99
        g.enemies=[Enemy(20,'sword',p.x+90),Enemy(21,'sword',p.x-90),Enemy(22,'spear',p.x+205)]
        for _ in range(720):
            g.tick(1/120,Controls())
            self.assertLessEqual(sum(e.state in ('windup','active') for e in g.enemies),1)

    def test_blade_ribbon_is_only_visible_during_the_power_stroke(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).resolve().parents[1]/'assets/player/animations.json').read_text('utf-8'))
        anim=data['animations']['attack'];weapon=data['weapon']
        ribbon=motion.blade_ribbon
        self.assertEqual(ribbon(anim,weapon,.1,500,112,1,148),[])
        self.assertGreater(len(ribbon(anim,weapon,.28,500,112,1,148)),4)
        self.assertEqual(ribbon(anim,weapon,.6,500,112,1,148),[])
        right=ribbon(anim,weapon,.28,500,112,1,148)
        left=ribbon(anim,weapon,.28,500,112,-1,148)
        for (rx,ry,ra),(lx,ly,la) in zip(right,left):
            self.assertAlmostEqual(rx+lx,1000);self.assertAlmostEqual(ry,ly);self.assertEqual(ra,la)


if __name__=='__main__':unittest.main()
