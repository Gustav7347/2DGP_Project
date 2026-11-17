import unittest
from bladegame.core import Game,Enemy
from bladegame.interface import combat_status


class CombatStatusTests(unittest.TestCase):
    def prepared_survival(self):
        game=Game(5);game.start();p=game.player
        p.augments={'unyielding','insight'};p.hp=1;p.invulnerable=0
        game._hurt_player(20)
        enemy=Enemy(99,'sword',p.x+85,state='active')
        game.enemies=[enemy];p.action='parry';p.action_time=.1;p.parry_ready=True
        game._enemy_strike(enemy)
        return game,enemy

    def test_prepared_insight_does_not_hide_the_active_survival_timer(self):
        game,enemy=self.prepared_survival();p=game.player
        self.assertTrue(p.unyielding_used);self.assertGreater(p.unyielding_left,0);self.assertTrue(p.insight)
        label=combat_status(p)
        self.assertIn('불굴',label);self.assertIn('초',label);self.assertIn('간파',label)

    def test_expired_or_consumed_effects_do_not_remain_in_status(self):
        game,enemy=self.prepared_survival();p=game.player
        enemy.state='stunned';enemy.timer=99;game.hit_stop=0
        for _ in range(420):game.tick(1/120)
        self.assertEqual(p.unyielding_left,0)
        self.assertEqual(combat_status(p),'간파 준비')
        game._begin_attack();self.assertEqual(combat_status(p),'')
        p.heals=0;self.assertEqual(combat_status(p),'사용함')


if __name__=='__main__':unittest.main()
