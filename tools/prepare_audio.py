"""Authoring: soften recorded transients and high frequencies, preserve sources."""
from pathlib import Path
import array, ctypes, math, os, sys, wave
os.environ['SDL_AUDIODRIVER']='dummy'
from pico2d import pico2d as sdl

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets'/'audio'


def decode(source):
    chunk=sdl.Mix_LoadWAV(str(source).encode('utf-8'))
    if not chunk: raise RuntimeError(str(source))
    samples=array.array('h',ctypes.string_at(chunk.contents.abuf,chunk.contents.alen))
    sdl.Mix_FreeChunk(chunk)
    if sys.byteorder!='little': samples.byteswap()
    return [(samples[i]+samples[i+1])/65536 for i in range(0,len(samples)-1,2)]


def trim_lead(samples):
    threshold=max(map(abs,samples))*.035
    start=next((i for i,x in enumerate(samples) if abs(x)>threshold),0)
    return samples[max(0,start-88):]


def soften(samples, destination, cutoff=2800, ceiling=.48, max_duration=1.15):
    mono=samples[:round(max_duration*44100)]
    alpha=1-math.exp(-2*math.pi*cutoff/44100)
    last=last2=dc=0.
    filtered=[]
    for i,x in enumerate(mono):
        dc+=.002*(x-dc)
        last+=alpha*(x-dc-last)
        last2+=alpha*(last-last2)
        fade=min(1.,i/88,(len(mono)-1-i)/1764)
        filtered.append(last2*max(0,fade))
    peak=max(max(map(abs,filtered)),.0001)
    gain=min(2.,ceiling/peak)
    data=array.array('h',(int(max(-ceiling,min(ceiling,x*gain))*32767) for x in filtered))
    if sys.byteorder!='little': data.byteswap()
    with wave.open(str(destination),'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(44100)
        out.writeframes(data.tobytes())
    print(destination.name,round(len(mono)/44100,3),'seconds',round(peak*gain,3),'peak')


if __name__=='__main__':
    sdl.SDL_Init(sdl.SDL_INIT_AUDIO)
    if sdl.Mix_OpenAudio(44100,sdl.AUDIO_S16LSB,2,1024): raise RuntimeError('Audio decoder unavailable')
    try:
        for name in ['swing-1.wav','swing-2.wav','swing-3.wav','cut.ogg','select.ogg','parry-1.ogg','parry-2.ogg','parry-3.ogg']:
            parry=name.startswith('parry')
            soften(trim_lead(decode(BASE/name)),BASE/(Path(name).stem+'-soft.wav'),
                   cutoff=2100 if parry else 2800,ceiling=.34 if parry else .48,
                   max_duration=.48 if parry else 1.15)
        steel=trim_lead(decode(BASE/'cut.ogg'))
        for i,(duration,ceiling) in enumerate(((.20,.30),(.24,.32),(.30,.36)),1):
            body=trim_lead(decode(BASE/f'body-{i}.flac'))
            length=round(duration*44100)
            mixed=[.82*(body[n] if n<len(body) else 0)+.10*(steel[n] if n<len(steel) else 0)
                   for n in range(length)]
            soften(mixed,BASE/f'impact-{i}-soft.wav',cutoff=2200,ceiling=ceiling,max_duration=duration)
    finally:
        sdl.Mix_CloseAudio(); sdl.SDL_Quit()
