"""Register original generated PNGs; never change their image pixels."""
from pathlib import Path
import json
from PIL import Image
from build_assets import bounds,grip

ROOT=Path(__file__).resolve().parents[1]/'assets'

def main():
    image=Image.open(ROOT/'enemies/sword-parried-v10.png').convert('RGBA')
    frames=[]
    hands=[(375,209),(352,160),(190,145),(318,207),(240,305),(164,300)]
    for i,hand in enumerate(hands):
        x=round(i%3*image.width/3);x1=round((i%3+1)*image.width/3)
        y=round(i//3*image.height/2);y1=round((i//3+1)*image.height/2)
        cell=image.crop((x,y,x1,y1));b=bounds(cell);h=grip(cell,hand)
        frames.append(dict(rect=[x,y,x1-x,y1-y],anchor=[250,b[3]],bounds=b,grip=h,
                           handOverlay=[round(h[0])-13,round(h[1])-16,26,32]))
    enemy=dict(file='sword-parried-v10.png',size=list(image.size),referenceBodyHeight=393,frames=frames)
    (ROOT/'enemies/sword-parried-v10.json').write_text(json.dumps(enemy,indent=2),encoding='utf8')
    atlas=json.loads((ROOT/'enemies/animations.json').read_text('utf8'));atlas['sword-parried']=enemy
    (ROOT/'enemies/animations.json').write_text(json.dumps(atlas,ensure_ascii=False,indent=2),encoding='utf8')
    image=Image.open(ROOT/'environment/supports-v10.png').convert('RGBA');frames=[]
    for i in range(4):
        x=round(i%2*image.width/2);x1=round((i%2+1)*image.width/2)
        y=round(i//2*image.height/2);y1=round((i//2+1)*image.height/2)
        b=bounds(image.crop((x,y,x1,y1)))
        frames.append(dict(rect=[x+b[0],y+b[1],b[2]-b[0],b[3]-b[1]]))
    (ROOT/'environment/supports-v10.json').write_text(json.dumps(dict(file='supports-v10.png',size=list(image.size),frames=frames),indent=2),encoding='utf8')
    print('Registered six enemy reaction poses and four support cutouts; PNG pixels unchanged')

if __name__=='__main__':main()
