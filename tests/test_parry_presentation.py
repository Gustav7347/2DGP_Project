import json,math,unittest
from pathlib import Path
from bladegame import motion
from bladegame.core import Game,Enemy

DATA=json.loads((Path(__file__).resolve().parents[1]/'assets/player/animations.json').read_text('utf-8'))
ANIM=DATA['animations']['parry']


class ParryPresentationTests(unittest.TestCase):
    def pose(self,seconds,feedback=0):
        return motion.parry_pose_time(ANIM,seconds,feedback)

    def test_parry_input_immediately_shows_a_guard_pose(self):
        self.assertEqual(motion.sample_frame(ANIM,self.pose(0))[0],1)

    def test_early_and_late_successes_show_the_same_contact_pose(self):
        for seconds in (.005,.08,.179):
            self.assertEqual(motion.sample_frame(ANIM,self.pose(seconds,.22))[0],2)

    def test_success_recovers_to_the_neutral_frame(self):
        self.assertEqual(motion.sample_frame(ANIM,self.pose(.3,.005))[0],5)

    def test_guard_stays_raised_until_the_parry_window_ends(self):
        self.assertEqual(motion.sample_frame(ANIM,self.pose(.179))[0],2)

    def test_guard_is_vertical_and_deflection_finishes_horizontally(self):
        for i in (1,2):self.assertEqual(ANIM['frames'][i]['swordAngleDeg'],-90)
        self.assertEqual(ANIM['frames'][4]['swordAngleDeg'],0)

    def test_a_miss_does_not_play_the_success_impact_pose(self):
        seen={motion.sample_frame(ANIM,self.pose(t/1000))[0] for t in range(340)}
        self.assertNotIn(3,seen)
        self.assertNotIn(4,seen)
        self.assertIn(5,seen)

    def test_success_quickly_advances_into_knockaway_followthrough(self):
        self.assertEqual(motion.sample_frame(ANIM,self.pose(.1,.14))[0],3)
        self.assertEqual(motion.sample_frame(ANIM,self.pose(.1,.10))[0],4)

    def test_clash_point_is_on_the_displayed_guard_blade_in_both_directions(self):
        contact=motion.parry_contact
        points=[]
        for face in (1,-1):
            result=contact(ANIM,DATA['weapon'],500,112,face,(500+face*54,204))
            self.assertIsNotNone(result)
            cx,cy=result;frame=ANIM['frames'][2];scale=148/ANIM['referenceBodyHeight']
            gx=500+face*(frame['grip'][0]-frame['anchor'][0])*scale
            gy=112+(frame['anchor'][1]-frame['grip'][1])*scale
            angle=math.radians(frame['swordAngleDeg']);ux=face*math.cos(angle);uy=-math.sin(angle)
            self.assertAlmostEqual((cx-gx)*uy-(cy-gy)*ux,0,places=6)
            self.assertGreaterEqual((cx-gx)*ux+(cy-gy)*uy,0)
            points.append(result)
        self.assertAlmostEqual(points[0][0]+points[1][0],1000)
        self.assertAlmostEqual(points[0][1],points[1][1])

    def test_success_records_contact_origin_before_player_moves_or_turns(self):
        g=Game(104);g.start();p=g.player;p.x=500;p.invulnerable=0
        p.action='parry';p.action_time=.08;p.parry_ready=True;p.facing=1
        e=Enemy(99,'sword',585,state='active',facing=-1);g.enemies=[e];g._enemy_strike(e)
        effect=next(e for e in g.effects if e['kind']=='parry')
        self.assertEqual(effect.get('origin'),(500,112))
        p.x=800;p.facing=-1
        self.assertEqual(effect['origin'],(500,112));self.assertEqual(effect.get('facing'),1)


if __name__=='__main__':unittest.main()
