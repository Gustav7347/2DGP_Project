"""Encode captured frames; does not launch apps or claim video/listening approval."""
from pathlib import Path
import argparse,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'verification/guard-v9'
FFMPEG=ROOT/'verification/video-tools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v9.0.2.exe'
OUT=ROOT.parent/'output/blade-v9-review'

def encode(args,dest):
    command=[str(FFMPEG),'-hide_banner','-loglevel','error','-y',*args,
             '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
    result=subprocess.run(command,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:raise RuntimeError(result.stderr)
    assert dest.is_file() and dest.stat().st_size>1000

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',type=int,choices=(9,10),default=9)
    version=parser.parse_args().version
    assert FFMPEG.is_file()
    out=ROOT.parent/f'output/blade-v{version}-review';out.mkdir(parents=True,exist_ok=True)
    base=BASE if version==9 else ROOT/'verification/art-direction-v10'
    rows=[]
    for name in (('movement','contact') if version==9 else ('contact',)):
        before=base/f'{name}-before' if version==9 else BASE/f'{name}-final'
        after=base/f'{name}-final'
        assert all((folder/'frame-0000.png').is_file() for folder in (before,after))
        dest=out/f'{name}-before-after.mp4'
        encode(['-framerate','30','-i',str(before/'frame-%04d.png'),'-framerate','30','-i',str(after/'frame-%04d.png'),
                '-filter_complex','[0:v]scale=640:360[a];[1:v]scale=640:360[b];[a][b]hstack=inputs=2',
                '-an','-t','7'],dest)
        rows.append(dict(file=dest.name,left=f'v{version-1} before',right=f'v{version} after',audio=False))
    for name in (('contact','counter') if version==9 else ('contact',)):
        folder=base/f'{name}-final';dest=out/f'{name}-v{version}.mp4'
        encode(['-framerate','30','-i',str(folder/'frame-%04d.png'),'-i',str(folder/'audio.wav'),
                '-t','7','-c:a','aac','-b:a','160k'],dest)
        rows.append(dict(file=dest.name,audio=True,fixture='fixed inputs/positions/target HP, not a human playthrough'))
    if version==10:
        for name in ('stage-2','stage-3','reward-style','reward-augment'):
            dest=out/f'{name}-before-after.png'
            command=[str(FFMPEG),'-hide_banner','-loglevel','error','-y','-i',str(base/f'screens-before/{name}.png'),
                     '-i',str(base/f'screens-final/{name}.png'),'-filter_complex','hstack=inputs=2','-frames:v','1',str(dest)]
            result=subprocess.run(command,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode:raise RuntimeError(result.stderr)
            assert dest.is_file() and dest.stat().st_size>1000
    (out/'index.json').write_text(json.dumps(dict(videos=rows,watched_full_speed=False,listened=False),indent=2),encoding='utf8')
    print(out)

if __name__=='__main__':main()
