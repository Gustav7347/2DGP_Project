import math,unittest
from unittest.mock import patch
from types import SimpleNamespace
from bladegame.core import Game,Controls,Enemy
from bladegame import config as C
from bladegame.render import Renderer


class PolishIterationTests(unittest.TestCase):
    def test_low_ledge_allows_both_sides_to_connect_attacks(self):
        for stage in C.STAGES[:3]:
            x,top,width=next(p for p in stage['platforms'] if p[1]<=205)
            g=Game(3);g.start();p=g.player;p.x=x+width-20;p.y=top;p.grounded=True
            e=Enemy(99,'sword',p.x+85,state='stunned',timer=99,hp=100,max_hp=100);g.enemies=[e]
            self.assertTrue(e.attack_bounds.overlaps(p.bounds))
            g.tick(1/120,Controls(attack=True))
            for _ in range(40):g.tick(1/120)
            self.assertLess(e.hp,100)

    def test_ascending_steps_can_be_reached_with_the_existing_jump(self):
        for stage in C.STAGES[:3]:
            previous=(0,C.GROUND,stage['platforms'][0][0])
            for platform in stage['platforms']:
                x,y,width=platform;px,py,pw=previous;rise=y-py
                if rise>0:
                    discriminant=C.JUMP_SPEED**2-2*C.GRAVITY*rise
                    self.assertGreater(discriminant,0,(stage['name'],platform))
                    flight=(C.JUMP_SPEED+math.sqrt(discriminant))/C.GRAVITY
                    self.assertLessEqual(max(0,x-(px+pw)-30),flight*C.MOVE_SPEED,(stage['name'],platform))
                previous=platform

    def test_counter_uses_a_visual_reaction_without_extending_input_lock(self):
        g=Game(3);g.start();p=g.player;p.augments={'counter'};p.invulnerable=0
        e=Enemy(99,'sword',p.x+85,hp=500,max_hp=500,state='active');g.enemies=[e]
        p.action='parry';p.action_time=.1;p.parry_ready=True;g._enemy_strike(e)
        self.assertEqual(p.action,'parry');self.assertTrue(p.counter_ready)
        self.assertEqual(p.parry_feedback,0)
        self.assertEqual(p.hp,88)
        g.hit_stop=0;e.state='stunned';e.timer=99
        for _ in range(30):g.tick(1/120)
        g.tick(1/120,Controls(attack=True))
        self.assertEqual(p.action,'attack');self.assertEqual(p.counter_left,0)
        self.assertTrue(p.attack_counter);self.assertFalse(p.counter_ready)

    def test_lethal_counter_never_plays_the_attack_reaction(self):
        g=Game(3);g.start();p=g.player;p.hp=1;p.augments={'counter'}
        e=Enemy(99,'sword',p.x+85,state='active');g.enemies=[e]
        p.action='parry';p.parry_ready=True;g._enemy_strike(e)
        self.assertEqual(g.state,'dead');self.assertEqual(p.counter_left,0)

    def test_returning_from_an_action_starts_run_from_contact_pose(self):
        g=Game(3);g.start();p=g.player;p.run_time=.13
        g._begin_attack();self.assertEqual(p.run_time,0)
        p.action='idle';p.run_time=.13;g.tick(1/120,Controls(parry=True))
        self.assertEqual(p.run_time,0)

    def test_parry_preserves_its_cue_and_does_not_layer_a_second_hurt_cue(self):
        r=Renderer.__new__(Renderer);r.muted=False;r.last_event=None;r.last_state='playing';r.audio_counter=0
        r.sounds={k:object() for k in ('parry2','hurt','counter')}
        g=SimpleNamespace(state='playing',events=[{'kind':'parry'},{'kind':'player_hit'},
            {'kind':'enemy_hit','impact':'counter','combo':3},{'kind':'counter'}])
        with patch.object(r,'play_sound') as play,patch.object(r,'stop_sound') as stop:
            r.sound(g)
        self.assertEqual([call.args[0] for call in play.call_args_list],['parry2','counter'])
        stop.assert_called_once_with(0)
        self.assertNotEqual(r.sound_channel('echo')[0],r.sound_channel('counter')[0])


if __name__=='__main__':unittest.main()
