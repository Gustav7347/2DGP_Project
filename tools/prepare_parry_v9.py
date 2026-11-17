"""Short stylized clash candidates from preserved CC0 recordings. No playback.

Authoring uses numpy/SDL decoding; the game only loads finished WAV files.
"""
import json
from pathlib import Path
from prepare_presentation_audio import extract_sources,decode_sources,piece,finish,write_cue

ROOT=Path(__file__).resolve().parents[1]

def main():
    paths,sources,archives=extract_sources()
    audio=decode_sources(paths,['py','-3']);outputs=[]
    # One family, three small recording variations. Short cut texture supplies
    # blade identity without extending the metal recording's scraping tail.
    for i in range(1,4):
        duration=.19
        metal=piece(audio[f'metal{i}'],duration,speed=.94)
        blade=piece(audio['slice2'],duration,speed=1.08,delay=.009,offset=.180)
        cue=finish(.66*metal+.34*blade,hold=.025,decay=.032,target=.060,ceiling=.36,shelf=.16)
        outputs.append(write_cue(f'parry-v9-{i}.wav',cue,[
            dict(source=f'metal{i}',gain=.66,speed=.94),
            dict(source='slice2',gain=.34,speed=1.08,delay=.009,offset_after_trim=.180)]))
    for label,weights,hold,decay in [('A',(.85,.15),.012,.025),('B',(.66,.34),.025,.032),('C',(.45,.55),.035,.042)]:
        duration=.22
        cue=finish(weights[0]*piece(audio['metal2'],duration,speed=.94)+
                   weights[1]*piece(audio['slice2'],duration,speed=1.08,delay=.009,offset=.180),
                   hold=hold,decay=decay,target=.060,ceiling=.36,shelf=.16)
        outputs.append(write_cue(f'parry-v9-candidate-{label}.wav',cue,[dict(metal_gain=weights[0],blade_gain=weights[1])]))
    manifest=dict(version=9,license='CC0-1.0',sources=sources,packs=archives,outputs=outputs,
                  listened=False,default_family='B-like: 0.19 seconds, three recording variants',
                  reason='Latest request: short blade clash, no long metallic scraping, retain blade texture.')
    (ROOT/'assets/licenses/parry-v9.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps([dict(file=r['file'],peak=round(r['peak'],3),rms=round(r['rms'],3),tail=round(r['energy_after_150ms'],4)) for r in outputs]))

if __name__=='__main__':main()
