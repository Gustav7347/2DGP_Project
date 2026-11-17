"""Check actual SDL mixer voice ownership at zero volume, without user playback."""
from pathlib import Path
import argparse,json,sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    from types import SimpleNamespace
    from pico2d import pico2d as p2
    from bladegame.render import Renderer
    p2.open_canvas(1280,720);p2.SDL_HideWindow(p2.window)
    try:
        if not p2.audio_on:raise RuntimeError('Audio device unavailable: not verified')
        r=Renderer();r.volume=0.
        assert p2.Mix_AllocateChannels(-1)>=6
        r.play_sound('swing1');r.play_sound('impact1');r.play_sound('echo');r.play_sound('footstep1')
        before=[int(p2.Mix_Playing(i)) for i in range(6)]
        assert before[0] and before[1] and before[4] and before[5],before
        r.sound(SimpleNamespace(state='playing',events=[{'kind':'parry'}]))
        after=[int(p2.Mix_Playing(i)) for i in range(6)]
        assert not after[0] and after[1] and after[2] and after[4] and after[5],after
        r.toggle_mute();assert not p2.Mix_Playing(-1)
        result={'status':'passed','purpose':'zero-volume SDL mixer routing; not listening assessment',
                'before_parry':before,'after_parry':after,'mute_stops_all':True,'echo_preserves_contact':True,'foley_preserves_contact':True}
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2),'utf-8');print(json.dumps(result))
    finally:p2.close_canvas()


if __name__=='__main__':main()
