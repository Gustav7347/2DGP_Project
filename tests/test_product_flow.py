import json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from bladegame.core import Game,Controls,Enemy
from bladegame.interface import Interface,choice_detail
from bladegame.preferences import Preferences,DEFAULTS
from bladegame import config as C


class ProductFlowTests(unittest.TestCase):
    def game(self):
        g=Game(3);g.start();g.enemies=[Enemy(99,'sword',2000,state='stunned',timer=99)]
        return g

    def test_retry_only_accepts_input_once_result_is_visible(self):
        g=self.game();g._hurt_player(999,ignore_invulnerability=True)
        ui=Interface()
        self.assertEqual(ui.button_at(g,640,230),-1)
        ui.activate(g,None)
        self.assertEqual(g.state,'dead')
        for _ in range(60):g.tick(1/60)
        self.assertEqual(ui.button_at(g,640,230),0)
        ui.activate(g,None)
        self.assertEqual((g.state,g.stage_index,g.player.hp),('playing',0,C.MAX_HP))

    def test_jump_pressed_just_before_landing_is_not_lost(self):
        g=self.game();p=g.player;p.y=C.GROUND+1;p.grounded=False;p.vy=-100
        g.tick(1/120,Controls(jump=True))
        for _ in range(4):g.tick(1/120)
        self.assertGreater(p.vy,0)
        self.assertEqual(sum(e['kind']=='jumped' for e in g.events),1)

    def test_expired_jump_buffer_does_not_create_an_automatic_jump(self):
        g=self.game();p=g.player;p.y=500;p.grounded=False
        g.tick(1/120,Controls(jump=True))
        for _ in range(120):g.tick(1/120)
        self.assertTrue(p.grounded)
        self.assertFalse(any(e['kind']=='jumped' for e in g.events))

    def test_ledge_grace_allows_one_jump_but_never_a_double_jump(self):
        g=self.game();p=g.player;x,top,width=g.stage['platforms'][0]
        p.x=x+width+14;p.y=top;p.grounded=True
        g.tick(1/120,Controls(move=1))
        for _ in range(8):g.tick(1/120,Controls(move=1))
        self.assertFalse(p.grounded)
        g.tick(1/120,Controls(jump=True))
        self.assertGreater(p.vy,0)
        for _ in range(18):g.tick(1/120,Controls(jump=True))
        self.assertEqual(sum(e['kind']=='jumped' for e in g.events),1)

    def test_route_requires_progress_before_the_next_encounter(self):
        g=Game(3);g.start()
        for e in g.living:g._hit_enemy(e,9999)
        for _ in range(240):g.tick(1/120)
        self.assertEqual(g.wave_index,0)
        self.assertEqual(g.state,'playing')
        trigger=g.next_encounter['trigger'];g.player.x=trigger
        g.tick(1/120)
        self.assertEqual(g.wave_index,1)
        self.assertEqual([e.x for e in g.living],g.encounter['positions'])
        self.assertTrue(all(e.state=='arriving' for e in g.living))

    def test_progress_evidence_survives_the_bounded_combat_event_tail(self):
        g=Game(3);g.start()
        for i in range(400):g.event('enemy_hit',enemy=i)
        self.assertEqual(len(g.events),300)
        self.assertTrue(any(e['kind']=='stage_entered' and e['stage']==1 for e in g.milestones))
        g.start();self.assertEqual(sum(e['kind']=='run_started' for e in g.milestones),1)

    def test_arrival_telegraph_does_not_attack_the_player(self):
        g=self.game();e=g.enemies[0];e.x=g.player.x+80;e.state='arriving';e.timer=C.ARRIVAL_TIME
        g.player.invulnerable=0
        for _ in range(60):g.tick(1/120)
        self.assertEqual(g.player.hp,C.MAX_HP)
        self.assertEqual(e.state,'arriving')
        self.assertIsNone(g.attack_owner)

    def test_stage_layouts_are_valid_and_final_stage_has_flanking_entries(self):
        for stage in C.STAGES:
            self.assertEqual(len(stage['encounters']),len(stage['waves']))
            self.assertEqual(sorted(e['trigger'] for e in stage['encounters']),[e['trigger'] for e in stage['encounters']])
            for kinds,area in zip(stage['waves'],stage['encounters']):
                self.assertEqual(len(kinds),len(area['positions']))
                self.assertTrue(all(40<x<stage['width']-40 for x in area['positions']))
        area=C.STAGES[2]['encounters'][1]
        self.assertLess(min(area['positions']),area['trigger'])
        self.assertGreater(max(area['positions']),area['trigger'])

    def test_help_pauses_and_returns_to_the_same_run(self):
        g=self.game();ui=Interface();old=(g.player.x,g.player.hp,g.time)
        ui.open_help(g);g.tick(.2,Controls(move=1))
        self.assertEqual(g.state,'paused');self.assertEqual(old,(g.player.x,g.player.hp,g.time))
        ui.back(g);self.assertEqual(g.state,'playing');self.assertEqual(ui.page,'main')

    def test_losing_focus_pauses_without_automatic_resume(self):
        g=self.game();ui=Interface();ui.focus_lost(g);ui.focus_lost(g)
        self.assertEqual(g.state,'paused')

    def test_menu_click_and_keyboard_use_the_same_actions(self):
        g=Game(3);ui=Interface();renderer=SimpleNamespace()
        for index in (1,2):
            action,label,x,y,w,h=ui.buttons(g)[index]
            self.assertEqual(ui.button_at(g,x+w/2,y+h/2),index)
            ui.activate(g,renderer,index)
            self.assertEqual(ui.page,'help' if index==1 else 'settings')
            ui.back(g)
        ui.activate(g,renderer,0);self.assertEqual(g.state,'playing')
        g.state='paused';ui.activate(g,renderer,0);self.assertEqual(g.state,'playing')

    def test_preferences_validate_and_survive_a_new_instance(self):
        temp_root=Path(__file__).resolve().parents[1]/'verification'/'test-temp'
        temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            path=Path(directory)/'settings.json';prefs=Preferences(path)
            self.assertEqual(prefs.load(),DEFAULTS)
            renderer=SimpleNamespace(volume=.10,muted=True,shake_enabled=False,hints_enabled=False)
            self.assertTrue(prefs.save(renderer))
            self.assertEqual(Preferences(path).load(),prefs.snapshot(renderer))
            path.write_text('{broken','utf-8');self.assertEqual(prefs.load(),DEFAULTS)
            path.write_text(json.dumps({'volume':99,'muted':'false','shake_enabled':False}),'utf-8')
            self.assertEqual(prefs.load()['volume'],.5);self.assertIs(prefs.load()['muted'],False)
            self.assertIs(prefs.load()['shake_enabled'],False)
            path.write_text('{"volume": NaN}','utf-8');self.assertEqual(prefs.load()['volume'],.15)

    def test_read_only_preferences_do_not_stop_play(self):
        with patch('pathlib.Path.mkdir',side_effect=PermissionError('read only')):
            self.assertFalse(Preferences(Path('unused')/'settings.json').save(SimpleNamespace(**DEFAULTS)))

    def test_reward_details_match_actual_balance_and_do_not_promise_another_style(self):
        g=self.game();g.player.style='moon'
        with patch.object(C,'INSIGHT_DAMAGE',2.25):
            self.assertIn('2.25',' '.join(choice_detail('insight',g.player)))
        self.assertNotIn('연참',' '.join(choice_detail('echo',g.player)))


if __name__=='__main__':unittest.main()
