"""Encode fixed before/final native captures, without launching player apps."""
from pathlib import Path
import json,subprocess
from export_guard_review import encode,FFMPEG

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'verification/art-direction-v11'
OUT=ROOT.parent/'output/blade-v11-review'


def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    for kind,phase in (('spear',1),('boss',1),('boss',2)):
        key=f'{kind}-{phase}';before=BASE/'clips'/f'{key}-before';after=BASE/'clips'/f'{key}-final'
        dest=OUT/f'{key}-before-after.mp4'
        encode(['-framerate','30','-i',str(before/'frame-%04d.png'),
                '-framerate','30','-i',str(after/'frame-%04d.png'),'-filter_complex',
                '[0:v]scale=640:360[a];[1:v]scale=640:360[b];[a][b]hstack=inputs=2','-an','-t','7'],dest)
        rows.append(dict(file=dest.name,left='v10 before',right='v11 final',audio=False))
        dest=OUT/f'{key}-v11.mp4'
        encode(['-framerate','30','-i',str(after/'frame-%04d.png'),'-i',str(after/'audio.wav'),
                '-t','7','-c:a','aac','-b:a','160k'],dest)
        rows.append(dict(file=dest.name,audio=True,audio_source='unchanged runtime event mix; not listened'))
    for key in ('spear-1-1-0-contact','spear-1--1-1-sweep','boss-2-1-0-contact','boss-2-1-0-sweep'):
        dest=OUT/f'{key}-comparison.png'
        cmd=[str(FFMPEG),'-hide_banner','-loglevel','error','-y',
             '-i',str(BASE/'before'/f'{key}.png'),'-i',str(BASE/'final'/f'{key}.png'),
             '-filter_complex','[0:v]scale=640:360[a];[1:v]scale=640:360[b];[a][b]hstack=inputs=2',
             '-frames:v','1',str(dest)]
        subprocess.run(cmd,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
        rows.append(dict(file=dest.name,left='v10 before',right='v11 final'))
    (OUT/'index.json').write_text(json.dumps(dict(files=rows,watched_full_speed=False,listened=False,
        fixture='fixed positions/inputs/HP and boss phase; not a human playthrough'),indent=2),encoding='utf8')
    print(f'{len(rows)} media files exported to {OUT}')


if __name__=='__main__':main()
