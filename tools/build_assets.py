"""Read sprite coordinates; never rewrite image pixels. Requires Pillow for authoring only."""
from pathlib import Path
import json, math
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'


def bounds(im):
    return im.getchannel('A').point(lambda a:255 if a>160 else 0).getbbox()


def grip(im, guess):
    gx,gy=guess
    samples=[]
    for y in range(max(0,gy-65),min(im.height,gy+66)):
        for x in range(max(0,gx-65),min(im.width,gx+66)):
            r,g,b,a=im.getpixel((x,y))
            if a>160 and r>130 and g>85 and b>50 and 17<r-g<62 and 8<g-b<53:
                weight=math.exp(-((x-gx)**2+(y-gy)**2)/850)
                samples.append((x,y,weight))
    total=sum(w for x,y,w in samples)
    return [round(sum(x*w for x,y,w in samples)/total,2),round(sum(y*w for x,y,w in samples)/total,2)] if total else list(guess)


def build_player():
    animations={}
    guesses={
        'idle':[(160,335)]*6,
        'run':[(160,320)]*6,
        'jump':[(160,345),(160,310),(160,285),(160,265),(160,285),(160,330)],
        'parry':[(160,335),(220,280),(240,255),(250,250),(210,300),(160,335)],
        'hurt':[(160,335),(175,335),(190,335),(190,335),(175,335),(160,335)],
        'death':[(160,335),(170,340),(180,390),(200,430),(230,450),(230,450)],
    }
    durations={'idle':[180,180,200,180,180,200],'run':[85]*6,'jump':[75,75,110,150,110,80],
               'parry':[35,35,50,70,65,85],'hurt':[30]*6,'death':[90,100,120,140,160,180]}
    angles={'parry':[21,-40,-72,-60,-30,21],'death':[21,25,10,5,0,0]}
    for name in guesses:
        image=Image.open(ASSETS/'player'/f'{name}.png').convert('RGBA')
        xs=[round(i*image.width/3) for i in range(4)]
        ys=[round(i*image.height/2) for i in range(3)]
        frames=[]
        for i in range(6):
            col,row=i%3,i//3
            x,y,w,h=xs[col],ys[row],xs[col+1]-xs[col],ys[row+1]-ys[row]
            cell=image.crop((x,y,x+w,y+h))
            box=bounds(cell)
            anchor=[round(165*w/512,2),box[3]]
            hand=grip(cell,[round(guesses[name][i][0]*w/512),round(guesses[name][i][1]*h/512)])
            frames.append({'rect':[x,y,w,h],'anchor':anchor,'grip':hand,
                           'swordAngleDeg':angles.get(name,[18 if name=='run' else 21]*6)[i],
                           'durationMs':durations[name][i],
                           'handOverlay':[round(hand[0])-8,round(hand[1])-9,16,18]})
        animations[name]={'file':name+'.png','size':list(image.size),'referenceBodyHeight':404,
                          'loop':name in ('idle','run'),'frames':frames}
    attack=json.loads((ASSETS/'player'/'attack-source.json').read_text('utf-8'))
    animations['attack']={'file':'attack.png','size':attack['bodySize'],
                          'referenceBodyHeight':attack['referenceBodyHeight'],'loop':False,'frames':attack['frames']}
    combos={
        'attack2':{'grips':[(318,326),(190,274),(196,270),(277,236),(314,176),(344,137),(333,136),(327,118)],
                   'angles':[12,-170,-175,-5,-35,-75,-95,-105], 'times':[45,45,50,25,25,65,65,110]},
        'attack3':{'grips':[(159,102),(156,71),(180,100),(333,215),(367,235),(356,260),(359,262),(215,257)],
                   'angles':[-135,-130,-125,-55,5,24,24,21], 'times':[75,65,70,25,30,110,110,165]},
    }
    for name,settings in combos.items():
        im=Image.open(ASSETS/'player'/f'{name}.png').convert('RGBA')
        frames=[]
        for i in range(8):
            x0=round((i%4)*im.width/4); x1=round((i%4+1)*im.width/4)
            y0=round((i//4)*im.height/2); y1=round((i//4+1)*im.height/2)
            box=bounds(im.crop((x0,y0,x1,y1)))
            hand=list(settings['grips'][i])
            frames.append({'rect':[x0,y0,x1-x0,y1-y0],'anchor':[(x1-x0)*.447,box[3]],'grip':hand,
                           'swordAngleDeg':settings['angles'][i],'durationMs':settings['times'][i],
                           'handOverlay':[round(hand[0])-8,round(hand[1])-9,16,18]})
        animations[name]={'file':name+'.png','size':list(im.size),'referenceBodyHeight':379,'loop':False,'frames':frames}
    im=Image.open(ASSETS/'player'/'run-authored-v6.png').convert('RGBA')
    frames=[]
    for i in range(8):
        x=round(i%4*im.width/4);x1=round((i%4+1)*im.width/4)
        y=round(i//4*im.height/2);y1=round((i//4+1)*im.height/2)
        cell=im.crop((x,y,x1,y1));hand=grip(cell,[194,281])
        frames.append({'rect':[x,y,x1-x,y1-y],'anchor':[205,420],'grip':hand,
                       'swordAngleDeg':14,'durationMs':70,'opaqueBounds':bounds(cell),
                       'handOverlay':[round(hand[0])-9,round(hand[1])-10,18,20]})
    animations['run']={'file':'run-authored-v6.png','size':list(im.size),
                       'referenceBodyHeight':280,'loop':True,'frames':frames}
    # Authoring must preserve the inspected, hand-registered body/weapon joints.
    registered=json.loads((ASSETS/'player'/'motion-registration-v7.json').read_text('utf-8'))
    animations.update(registered)
    latest=ASSETS/'player'/'motion-registration-v9.json'
    if latest.exists():animations.update(json.loads(latest.read_text('utf-8')))
    animations.update(json.loads((ASSETS/'player'/'run-registration-v26.json').read_text('utf8')))
    result={'sourceOrigin':'top-left','animations':animations,'weapon':attack['weapon']}
    (ASSETS/'player'/'animations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')


def build_enemies():
    data={}
    for name in ('sword','spear','boss'):
        image=Image.open(ASSETS/'enemies'/f'{name}.png').convert('RGBA')
        frames=[]
        for i in range(6):
            x0=round((i%3)*image.width/3); x1=round((i%3+1)*image.width/3)
            y0=round((i//3)*image.height/2); y1=round((i//3+1)*image.height/2)
            cell=image.crop((x0,y0,x1,y1))
            box=bounds(cell)
            # Root stays around the torso, independent of blade length.
            anchor=[(box[0]+box[2])*.5 if i==5 else (x1-x0)*.42,box[3]]
            frames.append({'rect':[x0,y0,x1-x0,y1-y0],'anchor':anchor,'bounds':box})
        b=frames[0]['bounds']
        data[name]={'file':name+'.png','size':list(image.size),'referenceBodyHeight':b[3]-b[1],'frames':frames}
    extra=Image.open(ASSETS/'enemies'/'boss-extra.png').convert('RGBA')
    frames=[]
    # Use the five clean poses. The unused thrust cell crosses its grid boundary;
    # the thrust is a dedicated single-pose image instead.
    for source_index in (0,2,3,4,5):
        x0=round((source_index%3)*extra.width/3); x1=round((source_index%3+1)*extra.width/3)
        y0=round((source_index//3)*extra.height/2); y1=round((source_index//3+1)*extra.height/2)
        if source_index == 0: y1 = 450  # Exclude the next row's topknot.
        b=bounds(extra.crop((x0,y0,x1,y1)))
        frames.append({'rect':[x0,y0,x1-x0,y1-y0],'anchor':[(x1-x0)*.42,b[3]],'bounds':b})
    standing=frames[2]['bounds']
    data['boss-extra']={'file':'boss-extra.png','size':list(extra.size),'referenceBodyHeight':standing[3]-standing[1],'frames':frames}
    thrust=Image.open(ASSETS/'enemies'/'boss-thrust.png').convert('RGBA')
    b=bounds(thrust)
    data['boss-thrust']={'file':'boss-thrust.png','size':list(thrust.size),'referenceBodyHeight':round((b[3]-b[1])/.95),
        'frames':[{'rect':[0,0,*thrust.size],'anchor':[thrust.width*.42,b[3]],'bounds':b}]}
    parried=ASSETS/'enemies'/'sword-parried-v10.json'
    if parried.exists():data['sword-parried']=json.loads(parried.read_text('utf8'))
    for kind in ('spear','boss'):
        parried=ASSETS/'enemies'/f'{kind}-parried-v11.json'
        if parried.exists():data[kind+'-parried']=json.loads(parried.read_text('utf8'))
    data.update(json.loads((ASSETS/'enemies'/'gait-v22.json').read_text('utf8')))
    (ASSETS/'enemies'/'animations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')


def build_terrain():
    im=Image.open(ASSETS/'environment'/'terrain.png').convert('RGBA')
    frames=[]
    for i in range(4):
        x0=round((i%2)*im.width/2); x1=round((i%2+1)*im.width/2)
        y0=round((i//2)*im.height/2); y1=round((i//2+1)*im.height/2)
        b=bounds(im.crop((x0,y0,x1,y1)))
        frames.append({'rect':[x0+b[0],y0+b[1],b[2]-b[0],b[3]-b[1]]})
    (ASSETS/'environment'/'terrain.json').write_text(json.dumps({'file':'terrain.png','size':list(im.size),'frames':frames},indent=2),'utf-8')


if __name__=='__main__':
    build_player()
    if (ASSETS/'enemies'/'boss.png').exists(): build_enemies()
    build_terrain()
    print('Sprite coordinates ready. Original PNG pixels unchanged.')
