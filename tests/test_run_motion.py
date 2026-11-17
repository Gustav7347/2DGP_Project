import json,unittest
from pathlib import Path
from bladegame.motion import sample_frame
from bladegame.config import MOVE_SPEED
from bladegame.core import Game,Controls,Enemy


class RunMotionTests(unittest.TestCase):
    def test_blocked_movement_does_not_run_in_place(self):
        g=Game(1);g.start();p=g.player
        g.enemies=[Enemy(99,'sword',1000,state='recovery',timer=99)]
        for face,x in ((-1,40),(1,g.stage['width']-40)):
            p.x=x;p.run_time=.2
            g.tick(1/60,Controls(move=face))
            self.assertEqual(p.x,x)
            self.assertFalse(p.moving)
            self.assertEqual(p.run_time,0.)

    def test_live_run_uses_alternating_body_poses_with_registered_contacts(self):
        root=Path(__file__).resolve().parents[1]/'assets/player'
        data=json.loads((root/'animations.json').read_text('utf-8'))['animations']['run']
        self.assertTrue(data['integratedWeapon'])
        self.assertTrue(data['loop'])
        self.assertEqual(len({tuple(f['rect']) for f in data['frames']}),4)
        for f in data['frames']:
            x,y,w,h=f['rect']
            self.assertTrue(0<=x<x+w<=data['size'][0] and 0<=y<y+h<=data['size'][1])
            self.assertTrue(0<=f['anchor'][1]<=h)
        elapsed=0.
        for i,frame in enumerate(data['frames']):
            self.assertEqual(sample_frame(data,elapsed+.001)[0],i)
            elapsed+=frame['durationMs']/1000
        contacts=data['footContacts']
        self.assertEqual([f['foot'] for f in contacts],['near','far'])
        self.assertEqual([sum(f['durationMs'] for f in data['frames'][:c['frame']]) for c in contacts],[0,280])
        self.assertAlmostEqual(elapsed,.56)
        self.assertEqual(sample_frame(data,.56)[0],0)


if __name__=='__main__':unittest.main()
