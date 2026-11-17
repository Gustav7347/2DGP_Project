"""Register generated originals without changing their pixels. Pillow: authoring only."""
import json
from pathlib import Path
from PIL import Image
from build_assets import bounds,grip

ROOT=Path(__file__).resolve().parents[1]/'assets/player'

def register(file,columns,order,hands,angles,durations,reference,anchors):
    image=Image.open(ROOT/file).convert('RGBA');frames=[]
    for i,source in enumerate(order):
        left=round(source%columns*image.width/columns);right=round((source%columns+1)*image.width/columns)
        top=round(source//columns*image.height/2);bottom=round((source//columns+1)*image.height/2)
        cell=image.crop((left,top,right,bottom));box=bounds(cell);hand=grip(cell,hands[i])
        frames.append(dict(rect=[left,top,right-left,bottom-top],anchor=[anchors[i][0],box[3]+anchors[i][1]],
            grip=hand,swordAngleDeg=angles[i],durationMs=durations[i],opaqueBounds=box,
            sourceFrame=source,handOverlay=[round(hand[0])-12,round(hand[1])-14,24,28]))
    return dict(file=file,size=list(image.size),referenceBodyHeight=reference,loop=columns==4,frames=frames)

def main():
    run=register('run-cycle-v9.png',3,list(range(6)),[(239,253),(230,237),(237,236),(237,246),(229,243),(236,237)],
                 [14]*6,[100,100,80,100,100,80],442,
                 [(270,0),(270,0),(270,14),(270,0),(270,0),(270,14)])
    run['loop']=True
    run['footContacts']=[dict(frame=0,foot='near'),dict(frame=3,foot='far')]
    run['cycleNotes']='Remade near contact/support/push-off then far contact/support/push-off. Dark far calf remains consistent.'
    parry=register('parry-guard-sweep-v9.png',3,list(range(6)),
        [(276,275),(286,211),(286,211),(345,190),(374,191),(277,275)],
        [21,-90,-90,-32,0,21],[35,35,50,70,65,85],442,[(270,0)]*6)
    parry['poseRoles']=['neutral','guard-raise','guard-contact','sweep-start','horizontal-deflect','neutral']
    result=dict(run=run,parry=parry)
    (ROOT/'motion-registration-v9.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    atlas=json.loads((ROOT/'animations.json').read_text('utf8'));atlas['animations'].update(result)
    (ROOT/'animations.json').write_text(json.dumps(atlas,ensure_ascii=False,indent=2),encoding='utf8')
    print('Registered v9 run/guard/sweep originals; image pixels unchanged')

if __name__=='__main__':main()
