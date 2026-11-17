from pathlib import Path
import array, json, struct, sys, unittest, wave
from bladegame.config import SOUND_FILES

ASSETS=Path(__file__).resolve().parents[1]/'assets'


class AssetContracts(unittest.TestCase):
    def test_enemy_reaction_grips_and_weapon_crops_are_usable(self):
        data=json.loads((ASSETS/'enemies/weapons-v11.json').read_text('utf8'))
        raw=(ASSETS/'enemies'/data['file']).read_bytes();width,height=struct.unpack('>II',raw[16:24])
        for kind in ('spear','boss'):
            weapon=data[kind];x,y,w,h=weapon['rect']
            self.assertTrue(0<=x<x+w<=width and 0<=y<y+h<=height)
            self.assertTrue(0<=weapon['grip'][0]<weapon['tip'][0]<=w)
            self.assertTrue(0<=weapon['grip'][1]<=h)
            self.assertGreater(weapon['forwardLength'],100)
            anim=json.loads((ASSETS/'enemies'/f'{kind}-parried-v11.json').read_text('utf8'))
            for frame in anim['frames']:
                ox,oy,ow,oh=frame['handOverlay'];gx,gy=frame['grip']
                self.assertTrue(0<=ox<gx<ox+ow<=512 and 0<=oy<gy<oy+oh<=512)

    def test_atlas_rectangles_fit_actual_png(self):
        for folder in ('player','enemies'):
            data=json.loads((ASSETS/folder/'animations.json').read_text('utf-8'))
            animations=data['animations'] if folder=='player' else data
            for name,anim in animations.items():
                raw=(ASSETS/folder/anim['file']).read_bytes()
                width,height=struct.unpack('>II',raw[16:24])
                self.assertEqual(list((width,height)),anim['size'],name)
                for frame in anim['frames']:
                    x,y,w,h=frame['rect']
                    self.assertTrue(0<=x<x+w<=width and 0<=y<y+h<=height,(name,frame))

    def test_softened_sounds_have_headroom_and_short_duration(self):
        files=sorted({ASSETS/'audio'/n for n in SOUND_FILES.values()})
        self.assertTrue(all(p.is_file() for p in files))
        for path in files:
            with wave.open(str(path),'rb') as wav:
                self.assertEqual(wav.getsampwidth(),2)
                self.assertLess(wav.getnframes()/wav.getframerate(),1.2)
                samples=array.array('h',wav.readframes(wav.getnframes()))
                if sys.byteorder!='little': samples.byteswap()
                self.assertLessEqual(max(map(abs,samples)),15729,path.name)


if __name__=='__main__': unittest.main()
