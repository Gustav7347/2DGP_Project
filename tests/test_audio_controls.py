import unittest
from unittest.mock import patch
from types import SimpleNamespace
from bladegame.render import Renderer


class AudioControlsTests(unittest.TestCase):
    def setUp(self):
        self.renderer=Renderer.__new__(Renderer)
        self.renderer.volume=.15
        self.renderer.muted=False
        self.renderer.last_event=None
        self.renderer.last_state='playing'
        self.renderer.sounds={'reward':object()}

    def test_volume_change_updates_already_playing_channels(self):
        with patch('bladegame.render.p2.audio_on',True), patch('bladegame.render.p2.Mix_Volume') as volume:
            self.renderer.set_volume(-.15)
        self.assertEqual(volume.call_count,6)
        self.assertEqual({call.args for call in volume.call_args_list},{(i,0) for i in range(6)})

    def test_muted_reward_is_not_replayed_after_unmuting(self):
        game=SimpleNamespace(state='reward',events=[])
        self.renderer.muted=True
        self.renderer.sound(game)
        self.renderer.muted=False
        with patch.object(self.renderer,'play_sound') as play:
            self.renderer.sound(game)
        play.assert_not_called()

    def test_mute_stops_current_sound_immediately(self):
        with patch('bladegame.render.p2.audio_on',True), patch('bladegame.render.p2.Mix_HaltChannel') as halt:
            self.renderer.toggle_mute()
        halt.assert_called_once_with(-1)
        self.assertTrue(self.renderer.muted)

    def test_combo_contacts_and_echo_use_distinct_audio_roles(self):
        self.renderer.sounds={k:object() for k in ('impact1','impact2','impact3','echo')}
        game=SimpleNamespace(state='playing',events=[
            {'kind':'enemy_hit','combo':i,'impact':'normal'} for i in (1,2,3)])
        game.events.append({'kind':'enemy_hit','combo':1,'impact':'echo'})
        with patch.object(self.renderer,'play_sound') as play:
            self.renderer.sound(game)
        self.assertEqual([c.args[0] for c in play.call_args_list],['impact1','impact2','impact3','echo'])
        self.assertNotEqual(Renderer.sound_channel('echo')[0],Renderer.sound_channel('impact1')[0])
        self.assertLess(Renderer.sound_channel('echo')[1],Renderer.sound_channel('impact1')[1])

    def test_footfalls_follow_run_beats_and_do_not_repeat_every_frame(self):
        p=SimpleNamespace(grounded=True,moving=True,action='idle',run_time=0.)
        g=SimpleNamespace(player=p,state='playing',stage_index=0,events=[])
        self.renderer.sounds={k:object() for k in ('footstep1','footstep2','land')}
        with patch.object(self.renderer,'play_sound') as play:
            for time in (0.,.08,.20,.29,.40,.57):
                p.run_time=time;self.renderer.sound(g)
            self.assertEqual([c.args[0] for c in play.call_args_list],['footstep1','footstep2','footstep1'])
            p.moving=False;self.renderer.sound(g)
            p.moving=True;p.grounded=False;self.renderer.sound(g)
            g.state='paused';p.grounded=True;self.renderer.sound(g)
            self.assertEqual(play.call_count,3)
        self.assertNotEqual(Renderer.sound_channel('footstep1')[0],Renderer.sound_channel('impact1')[0])

    def test_landing_owns_the_foley_channel_and_mute_does_not_replay_old_steps(self):
        p=SimpleNamespace(grounded=True,moving=True,action='idle',run_time=0.)
        g=SimpleNamespace(player=p,state='playing',events=[{'kind':'landed'}])
        self.renderer.sounds={k:object() for k in ('footstep1','land')}
        with patch.object(self.renderer,'play_sound') as play:
            self.renderer.sound(g)
            self.assertEqual([c.args[0] for c in play.call_args_list],['land'])
            self.renderer.muted=True;p.run_time=.3;self.renderer.sound(g)
            self.renderer.muted=False;self.renderer.sound(g)
            self.assertEqual(play.call_count,1)


if __name__=='__main__': unittest.main()
