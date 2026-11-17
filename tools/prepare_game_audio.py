"""Authoring only (numpy): compose ready-made game sword and cutting contacts.

Reads preserved PCM copies of CC0 sources; game runtime does not require numpy.
"""
from pathlib import Path
import json,math,wave
import numpy as np

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/audio';RATE=44100


def read(name):
    with wave.open(str(BASE/name),'rb') as w:
        assert w.getframerate()==RATE and w.getsampwidth()==2
        return np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float).reshape(-1,w.getnchannels()).mean(1)/32768


def rms(x):return float(np.sqrt(np.mean(x*x)))


def piece(x,duration,speed=1.):
    active=np.flatnonzero(abs(x)>np.max(abs(x))*.035)
    if len(active):x=x[max(0,int(active[0])-66):]
    return np.interp(np.arange(round(duration*RATE))*speed,np.arange(len(x)),x,right=0.)


def level(x):return x*(.1/max(rms(x),1e-9))


def round_top(x):
    # Gentle shelf, retaining blade detail instead of low-passing the whole hit.
    alpha=1-math.exp(-2*math.pi*5400/RATE);low=0.;result=[]
    for value in x:
        low+=alpha*(value-low);result.append(low+(value-low)*.50)
    return np.asarray(result)


def finish(x,duration,hold=.09,decay=.10,target=.065,ceiling=.38):
    t=np.arange(len(x))/RATE
    envelope=np.minimum(1,t/.0015)*np.maximum(0,np.minimum(1,(duration-t)/.018))*np.exp(-np.maximum(0,t-hold)/decay)
    x=round_top(x)*envelope
    x*=min(target/max(rms(x),1e-9),ceiling/max(np.max(abs(x)),1e-9))
    return x


def save(name,x):
    assert np.isfinite(x).all() and np.max(abs(x))<=.48
    with wave.open(str(BASE/name),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(np.round(x*32767).astype('<i2').tobytes())
    return {'file':name,'seconds':len(x)/RATE,'rms':rms(x),'peak':float(np.max(abs(x)))}


def main():
    sword=read('source-game-sword.wav');rpg=read('source-game-rpg-slash.wav');rows=[]
    for i,(duration,speed) in enumerate(((.29,1.06),(.32,1.),(.38,.92)),1):
        blade=level(piece(sword,duration,speed));cut=level(piece(read(f'source-game-cut-{i}.wav'),duration))
        designed=level(piece(rpg,duration,speed))
        # Full contact source + cutting texture. No empty-swing noise as the hit's foreground.
        hit=finish(.62*blade+.24*designed+.44*cut,duration,target=.065+(i-1)*.004)
        rows.append(save(f'game-impact-{i}-soft.wav',hit))
        duration=.21
        metal=level(piece(read(f'parry-{i}-soft.wav'),duration,speed=.97+(i-1)*.015))
        body=level(piece(sword,duration,speed=1.05))
        parry=finish(.75*metal+.25*body,duration,hold=.032,decay=.045,target=.055,ceiling=.32)
        rows.append(save(f'game-parry-{i}-soft.wav',parry))
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
