"""Register original reaction/weapon PNGs without rewriting their pixels."""
from pathlib import Path
import json
from PIL import Image
from build_assets import bounds,grip

ROOT=Path(__file__).resolve().parents[1]/'assets/enemies'


def main():
    atlas=json.loads((ROOT/'animations.json').read_text('utf8'))
    hands={'spear':[(378,191),(337,138),(254,99),(340,161),(279,228),(262,232)],
           'boss':[(370,234),(338,159),(292,140),(352,193),(288,277),(274,288)]}
    for kind,guesses in hands.items():
        filename='spear-parried-clean-v11.png' if kind=='spear' else 'boss-parried-v11.png'
        image=Image.open(ROOT/filename).convert('RGBA')
        assert image.size==(1536,1024),image.size
        assert image.getpixel((0,0))[3]==0,'Background must remain transparent'
        frames=[]
        for i,guess in enumerate(guesses):
            x=i%3*512;y=i//3*512;cell=image.crop((x,y,x+512,y+512));b=bounds(cell)
            assert b and 0<b[0]<b[2]<512 and 0<b[1]<b[3]<512,(kind,i,b)
            h=grip(cell,guess);w,hh=(48,38) if kind=='boss' else (28,32)
            frames.append(dict(rect=[x,y,512,512],anchor=[250,b[3]],bounds=b,grip=h,
                               handOverlay=[round(h[0])-w//2,round(h[1])-hh//2,w,hh]))
        data=dict(file=filename,size=list(image.size),
                  referenceBodyHeight=470 if kind=='boss' else 400,frames=frames)
        (ROOT/f'{kind}-parried-v11.json').write_text(json.dumps(data,indent=2),encoding='utf8')
        atlas[kind+'-parried']=data
        print(kind,[(f['bounds'],f['grip']) for f in frames])
    (ROOT/'animations.json').write_text(json.dumps(atlas,ensure_ascii=False,indent=2),encoding='utf8')
    image=Image.open(ROOT/'weapons-v11.png').convert('RGBA')
    assert image.size==(1536,1024) and image.getpixel((0,0))[3]==0
    weapons=dict(file='weapons-v11.png',size=list(image.size))
    for kind,row,hand,tip,length in (('spear',0,(450,263),(1400,263),145),
                                     ('boss',1,(450,248),(1356,248),116)):
        b=bounds(image.crop((0,row*512,1536,(row+1)*512)))
        weapons[kind]=dict(rect=[b[0],row*512+b[1],b[2]-b[0],b[3]-b[1]],
                           grip=[hand[0]-b[0],hand[1]-b[1]],tip=[tip[0]-b[0],tip[1]-b[1]],
                           forwardLength=length)
    (ROOT/'weapons-v11.json').write_text(json.dumps(weapons,indent=2),encoding='utf8')
    print('Registered twelve body poses and two weapons; original PNG pixels unchanged')


if __name__=='__main__':main()
