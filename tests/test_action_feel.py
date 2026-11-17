import unittest
from bladegame.core import Game,Controls,Enemy,Strike,Rect
from bladegame.render import Renderer


class ActionFeelTests(unittest.TestCase):
    def game(self):
        game=Game(5);game.start();game.enemies=[Enemy(99,'sword',1800,state='recovery',timer=99)]
        return game

    def test_short_and_long_holds_both_remain_one_cut(self):
        for held_frames,expected in ((12,[1]),(108,[1])):
            game=self.game()
            for i in range(200):
                game.tick(1/120,Controls(attack=i==0,attack_held=i<held_frames))
            self.assertEqual([e['combo'] for e in game.events if e['kind']=='attack'],expected)

    def test_attack_step_is_continuous_not_an_impact_teleport(self):
        game=self.game(); xs=[game.player.x]
        for i in range(60):
            game.tick(1/120,Controls(attack=i==0));xs.append(game.player.x)
        self.assertGreater(xs[-1],xs[0]+15)
        self.assertLess(max(b-a for a,b in zip(xs,xs[1:])),4)

    def test_hit_recoil_moves_over_time(self):
        game=self.game();enemy=Enemy(20,'sword',240,hp=500,max_hp=500,state='recovery',timer=10)
        game.enemies=[enemy];x=enemy.x
        game._resolve_strike(Strike(Rect(160,100,330,280),10))
        self.assertEqual(enemy.x,x)
        for i in range(40):game.tick(1/120)
        self.assertGreater(enemy.x,x+5)

    def test_echo_keeps_original_direction_after_player_turns(self):
        game=self.game();enemy=Enemy(20,'sword',240,hp=500,max_hp=500,state='recovery',timer=10)
        game.enemies=[enemy];game.player.facing=-1;game.player.combo_index=2
        strike=Strike(Rect(160,100,330,280),10,kind='echo')
        strike.facing=1;strike.combo_index=0
        x=enemy.x;game._resolve_strike(strike)
        for i in range(40):game.tick(1/120)
        self.assertGreater(enemy.x,x)

    def test_damage_flash_does_not_hide_committed_attack_pose(self):
        for state,pose in (('windup',2),('active',3)):
            with self.subTest(state=state):
                enemy=Enemy(20,'sword',240,state=state,hurt=.18)
                self.assertEqual(Renderer.enemy_pose(enemy),('sword',pose))

    def test_empty_cut_does_not_create_hit_stop(self):
        game=self.game()
        for i in range(65):game.tick(1/120,Controls(attack=i==0))
        self.assertEqual(game.hit_stop,0)
        self.assertFalse(any(e['kind']=='enemy_hit' for e in game.events))

    def test_hit_stop_preserves_single_edge_input(self):
        game=self.game();game.hit_stop=.05
        game.tick(1/120,Controls(parry=True))
        for _ in range(12): game.tick(1/120)
        self.assertEqual(game.player.action,'parry')
        self.assertFalse(game.pending.parry)


if __name__=='__main__':unittest.main()
