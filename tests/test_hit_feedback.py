import unittest
from bladegame.core import Game,Enemy
from bladegame import config as C
from bladegame.interface import last_hit_text
from bladegame.interface import Interface


class HitFeedbackTests(unittest.TestCase):
    def game(self):
        g=Game(4);g.start();g.player.invulnerable=0
        e=Enemy(99,'sword',g.player.x+85,state='active',facing=-1)
        g.enemies=[e]
        return g,e

    def test_front_hit_records_observed_source_without_guessing_intent(self):
        g,e=self.game();g._enemy_strike(e)
        self.assertEqual(g.last_hit,{'enemy_kind':'sword','attack':'slash','reason':'unblocked','stage':1})
        self.assertEqual(g.player.hp,88)
        self.assertIn('검사',last_hit_text(g.last_hit))
        self.assertEqual(g.events[-1]['hit'],g.last_hit)

    def test_behind_hit_and_expired_window_are_distinguished(self):
        for reason in ('behind','window_ended','spent'):
            with self.subTest(reason=reason):
                g,e=self.game();p=g.player;p.action='parry';p.action_time=.1;p.parry_ready=True
                if reason=='behind':e.x=p.x-85;e.facing=1
                elif reason=='window_ended':p.action_time=C.PARRY_WINDOW+.001
                else:p.parry_ready=False
                g._enemy_strike(e)
                self.assertEqual(g.last_hit['reason'],reason)
                self.assertEqual(p.hp,88)

    def test_success_at_window_boundary_does_not_create_damage_feedback(self):
        g,e=self.game();p=g.player;p.action='parry';p.action_time=C.PARRY_WINDOW;p.parry_ready=True
        g._enemy_strike(e)
        self.assertIsNone(g.last_hit);self.assertEqual(p.hp,100);self.assertEqual(p.parries,1)

    def test_invulnerable_and_out_of_range_hits_do_not_overwrite_feedback(self):
        g,e=self.game();g._enemy_strike(e);first=g.last_hit.copy()
        e.pattern='thrust';g.player.invulnerable=1;g._enemy_strike(e)
        self.assertEqual(g.last_hit,first)
        g.player.invulnerable=0;e.x=1500;g._enemy_strike(e)
        self.assertEqual(g.last_hit,first)

    def test_counter_lethal_is_recorded_before_healing_or_counter(self):
        g,e=self.game();p=g.player;p.hp=1;p.style='moon';p.augments={'counter'}
        p.action='parry';p.action_time=.1;p.parry_ready=True;g._enemy_strike(e)
        self.assertEqual(g.state,'dead');self.assertEqual(p.hp,0)
        self.assertEqual(g.last_hit['reason'],'counter_cost')
        self.assertIn('육참골단',last_hit_text(g.last_hit))
        self.assertEqual(g.events[-1]['kind'],'player_died')
        self.assertEqual(g.events[-1]['hit'],g.last_hit)
        self.assertEqual(e.hp,44)

    def test_survival_still_records_contact_without_claiming_hp_loss(self):
        for augment in ('unyielding','revive'):
            g,e=self.game();p=g.player;p.hp=1;p.augments={augment}
            g._enemy_strike(e)
            self.assertEqual(g.state,'playing');self.assertIsNotNone(g.last_hit)
            self.assertGreater(p.hp,0)

    def test_snapshot_survives_actor_changes_and_event_tail_but_new_run_resets_it(self):
        g,e=self.game();g._enemy_strike(e);first=g.last_hit.copy()
        e.kind='boss';e.pattern='thrust';e.x=50
        for _ in range(400):g.event('sample')
        self.assertEqual(g.last_hit,first)
        g._enter_stage(1);self.assertEqual(g.last_hit,first)
        g.start();self.assertIsNone(g.last_hit)

    def test_unknown_damage_uses_neutral_copy(self):
        g,e=self.game();g._hurt_player(20)
        self.assertIsNone(g.last_hit['enemy_kind']);self.assertEqual(g.last_hit['reason'],'unknown')
        self.assertEqual(last_hit_text(g.last_hit),'마지막 피격 정보 없음')
        self.assertEqual(last_hit_text(None),'마지막 피격 정보 없음')

    def test_counter_with_a_survival_augment_can_still_counter(self):
        for survival in ('unyielding','revive'):
            g,e=self.game();p=g.player;p.hp=1;p.style='moon';p.augments={'counter',survival}
            p.action='parry';p.action_time=.1;p.parry_ready=True;g._enemy_strike(e)
            self.assertEqual(g.state,'playing');self.assertGreater(p.hp,0);self.assertEqual(e.hp,44)
            self.assertTrue(p.counter_ready)
            self.assertEqual(g.last_hit['reason'],'counter_cost')
            g.hit_stop=0;g._begin_attack()
            for _ in range(40):g.tick(1/120)
            self.assertLess(e.hp,44)
            self.assertTrue(any(event['kind']=='counter' for event in g.events))

    def test_reward_help_preserves_choices_focus_and_paused_simulation(self):
        g,e=self.game();ui=Interface();g.state='reward';g.choices=['blood','moon','chain'];ui.reward_focus=2
        before=(g.time,g.player.x,list(g.choices),g.player.style)
        ui.open_help(g);g.tick(.25)
        self.assertEqual(g.state,'reward');self.assertEqual(ui.page,'help')
        ui.hover(g,270,350);self.assertEqual(ui.reward_focus,2)
        self.assertEqual((g.time,g.player.x,g.choices,g.player.style),before)
        ui.activate(g,None,0)
        self.assertEqual(ui.page,'main');self.assertEqual(g.state,'reward');self.assertEqual(ui.reward_focus,2)

    def test_behind_takes_priority_when_the_window_also_ended(self):
        g,e=self.game();p=g.player;e.x=p.x-85;e.facing=1
        p.action='parry';p.action_time=C.PARRY_WINDOW+.01;p.parry_ready=False
        g._enemy_strike(e);self.assertEqual(g.last_hit['reason'],'behind')


if __name__=='__main__':unittest.main()
