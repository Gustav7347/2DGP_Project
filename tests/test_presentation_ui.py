import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from bladegame.presentation import GameUI
from bladegame.render import Renderer
from bladegame.interface import Interface
from bladegame.core import Game
from bladegame import config as C


class PresentationTests(unittest.TestCase):
    def test_player_hud_stays_below_the_playable_ground(self):
        r=SimpleNamespace(text=Mock(),hp_trail=1.,hints_enabled=False,clock=0)
        r.hero={'idle':SimpleNamespace(h=1024,clip_draw=Mock())}
        skin=GameUI.__new__(GameUI);skin.r=r
        for name in ('frame','icon','bar','key','seal'):setattr(skin,name,Mock())
        g=Game(104);g.start();g.notices=[];g.transition_banner=0
        with patch('bladegame.presentation.rect'),patch('bladegame.presentation.p2.draw_line'):
            skin.hud(g,0,(0,0))
        panels=[call.args for call in skin.frame.call_args_list if call.args[1]<100 and call.args[2]<200]
        self.assertTrue(panels)
        for _,x,y,w,h,*_ in panels:self.assertLessEqual(y+h,C.GROUND-8)

    def help_text(self,player):
        renderer=Renderer.__new__(Renderer)
        renderer.ui=Interface();renderer.ui.page='help'
        renderer.volume=.15;renderer.muted=True;renderer.shake_enabled=renderer.hints_enabled=True
        renderer.text=Mock()
        renderer.skin=GameUI.__new__(GameUI);renderer.skin.r=renderer
        renderer.skin.frame=Mock();renderer.skin.seal=Mock();renderer.skin.button=Mock()
        with patch('bladegame.render.box'):
            renderer.menu(SimpleNamespace(state='paused',player=player),(0,0))
        return [call.args[0] for call in renderer.text.call_args_list]

    def test_help_exposes_owned_effects_without_hover(self):
        player=Game(104).player;player.style='chain';player.augments={'echo','revive'}
        words=self.help_text(player)
        for text in ('연참','잔영검','회생','적중마다 +4.5% · 최대 12중첩',
                     '연참과 연결: 적중 중첩을 두 번','치명상 무시 · 전체 체력 회복'):
            self.assertIn(text,words)
        self.assertNotIn('육참골단',words)

    def test_help_distinguishes_active_and_spent_survival_effects(self):
        player=Game(104).player;player.augments={'unyielding','revive'}
        player.unyielding_used=player.revive_used=True;player.unyielding_left=1.5
        words=self.help_text(player)
        self.assertIn('불굴 · 발동 중',words);self.assertIn('회생 · 소모',words)
        player.unyielding_left=0
        self.assertIn('불굴 · 소모',self.help_text(player))

    def test_help_explains_empty_reward_slots(self):
        words=self.help_text(Game(104).player)
        for text in ('전투 스타일 미선택','첫 전투 돌파 후 선택','두 번째 돌파 후 선택','세 번째 돌파 후 선택'):
            self.assertIn(text,words)

    def test_combat_toasts_stay_visible_at_both_screen_edges(self):
        skin=GameUI.__new__(GameUI);skin.frame=Mock();skin.r=SimpleNamespace(text=Mock())
        for width in (110,130,600):
            for x in (-40,2,640,1278,1330):
                skin.toast('간파',x,200,width)
                _,left,_,w,*_=skin.frame.call_args.args
                self.assertGreaterEqual(left,8)
                self.assertLessEqual(left+w,1272)
                self.assertAlmostEqual(skin.r.text.call_args.args[1],left+w/2)


if __name__=='__main__':unittest.main()
