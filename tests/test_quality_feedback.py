import unittest
from bladegame.core import Game,Controls,Enemy,Strike,Rect
from bladegame.render import Renderer


class QualityFeedbackTests(unittest.TestCase):
    def game(self):
        game=Game(23);game.start();game.enemies=[Enemy(99,'sword',1800,state='recovery',timer=99)]
        return game

    def test_waiting_enemy_does_not_walk_in_place(self):
        game=self.game();game.attack_owner=99
        enemy=Enemy(20,'sword',game.player.x+90)
        game.enemies.append(enemy);x=enemy.x
        game._update_enemy(enemy,.2)
        self.assertEqual(enemy.x,x)
        self.assertEqual(Renderer.enemy_pose(enemy),('sword',0))
        enemy.x=game.player.x+400;game._update_enemy(enemy,.2)
        self.assertTrue(enemy.moving)
        walk=enemy.walk_time;enemy.x=game.player.x+90;game._update_enemy(enemy,.2)
        self.assertFalse(enemy.moving)
        self.assertEqual(enemy.walk_time,walk)

    def test_contact_spark_uses_struck_edge_in_both_directions(self):
        for facing in (1,-1):
            game=self.game();enemy=Enemy(20,'sword',300,hp=200,max_hp=200)
            game.enemies=[enemy]
            game._resolve_strike(Strike(Rect(200,120,400,260),10,facing=facing))
            hit=next(e for e in game.effects if e['kind']=='hit')
            self.assertEqual(hit['x'],enemy.bounds.left if facing>0 else enemy.bounds.right)

    def test_landing_resets_run_phase_and_emits_one_ground_contact(self):
        game=self.game();landings=[]
        for frame in range(140):
            airborne=not game.player.grounded
            game.tick(1/120,Controls(move=1,jump=frame==0))
            if airborne and game.player.grounded:
                landings.append(game.player.run_time)
        self.assertEqual(landings,[0.])
        self.assertEqual(sum(e['kind']=='landed' for e in game.events),1)

    def test_successful_parry_feedback_survives_consumed_window(self):
        game=self.game();p=game.player
        enemy=Enemy(20,'sword',p.x+85,state='active',facing=-1)
        game.enemies=[enemy];p.action='parry';p.action_time=.1;p.parry_ready=True
        game._enemy_strike(enemy)
        self.assertTrue(p.parry_ready)
        self.assertGreater(p.parry_feedback,0)
        game._enter_stage(1)
        self.assertEqual(p.parry_feedback,0)

    def test_first_attack_prepares_immediately_and_blade_meets_damage_time(self):
        import json
        from pathlib import Path
        from bladegame import config as C
        from bladegame.motion import attack_pose_time,blade_angle
        data=json.loads((Path(__file__).resolve().parents[1]/'assets/player/animations.json').read_text('utf-8'))
        anim=data['animations']['attack']
        ready=attack_pose_time(anim,0.,0)
        self.assertGreater(Renderer.frame_at(anim,ready),0)
        contact=attack_pose_time(anim,C.ATTACKS[0]['impact'],0)
        self.assertLess(abs(blade_angle(anim,contact)),15.)


if __name__=='__main__':unittest.main()
