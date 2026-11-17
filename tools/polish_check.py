"""Repeatable evidence collection. Does not declare art or listening quality passed."""
from pathlib import Path
import argparse, array, collections, datetime, json, math, struct, subprocess, sys, wave, zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BASE=ROOT/'verification'/'polish'


def audio_metrics():
    from bladegame.config import SOUND_FILES
    result=[]
    active={ROOT/'assets'/'audio'/n for n in SOUND_FILES.values()}
    for file in sorted(active):
        with wave.open(str(file),'rb') as sound:
            samples=array.array('h',sound.readframes(sound.getnframes()))
            if sys.byteorder!='little': samples.byteswap()
            peak=max(map(abs,samples),default=0)/32768
            rms=math.sqrt(sum((x/32768)**2 for x in samples)/max(1,len(samples)))
            result.append({'file':file.name,'seconds':round(len(samples)/sound.getframerate()/sound.getnchannels(),3),
                           'peak_dbfs':round(20*math.log10(max(peak,1e-9)),2),'rms_dbfs':round(20*math.log10(max(rms,1e-9)),2)})
    return result


def style_runs():
    from bladegame.core import Game
    from bladegame import autoplay, config
    results=[]
    for style in config.STYLES:
        game=Game(104);game.start()
        for frame in range(18000):
            if game.state=='reward':
                index=game.choices.index(style) if game.stage_index==0 else autoplay.choose(game)
                game.choose(index)
            game.tick(1/60,autoplay.control(game))
            if game.state in ('clear','dead'): break
        results.append({'style':style,'state':game.state,'hp':round(game.player.hp,2),'seconds':round(game.time,2)})
    return results


def screen_content(path):
    """Inspect our own unfiltered RGBA SDL captures, not arbitrary image files."""
    raw=Path(path).read_bytes()
    if raw[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('Expected PNG capture')
    width,height=struct.unpack('>II',raw[16:24]); offset=8; compressed=[]
    while offset<len(raw):
        length=struct.unpack('>I',raw[offset:offset+4])[0]
        if raw[offset+4:offset+8]==b'IDAT': compressed.append(raw[offset+8:offset+8+length])
        offset+=length+12
    pixels=zlib.decompress(b''.join(compressed)); stride=width*4+1
    counts=collections.Counter()
    for y in range(200,height-140,10):
        if pixels[y*stride]!=0: raise ValueError('Unsupported capture filtering')
        for x in range(64,width-64,10):
            point=y*stride+1+x*4
            counts[pixels[point:point+3]]+=1
    dominance=counts.most_common(1)[0][1]/sum(counts.values())
    return {'file':str(Path(path).resolve().relative_to(ROOT)),'dominant_fraction':round(dominance,4),'nonblank':dominance<.97}


def motion_sheets(destination):
    from pico2d import pico2d as p2
    from bladegame.render import Renderer, capture, box, GOLD, INK, MUTED
    destination=destination.resolve()
    destination.mkdir(parents=True,exist_ok=True)
    p2.open_canvas(1280,720)
    p2.SDL_HideWindow(p2.window)
    p2.lattice_on=False
    p2.SDL_SetRenderDrawBlendMode(p2.renderer,p2.SDL_BLENDMODE_BLEND)
    paths=[]
    try:
        renderer=Renderer(); renderer.muted=True
        for name,anim in renderer.hero_data['animations'].items():
            for face,label in ((1,'right'),(-1,'left')):
                p2.clear_canvas(); box(0,0,1280,720,(14,22,31))
                renderer.text(f'{name} / {label} / frame sequence',640,660,25,GOLD,True)
                elapsed=0.
                for i,frame in enumerate(anim['frames']):
                    col,row=i%4,i//4
                    base=390-row*300
                    x=col*320+(90 if face>0 else 230)
                    p2.draw_line(col*320+10,base,col*320+309,base,95,102,110)
                    renderer.draw_hero(name,elapsed,x,base,face,180 if name=='run' else 110,frame=i)
                    renderer.text(f'{i+1} / {elapsed*1000:.0f} ms',col*320+15,base-35,15,INK)
                    elapsed+=frame['durationMs']/1000
                renderer.text('Static sequence: movement quality still requires time-based visual review.',640,35,15,MUTED,True)
                file=destination/f'{name}-{label}.png'
                capture(file); paths.append(str(file.relative_to(ROOT)))
                p2.update_canvas()
        (destination/'index.json').write_text(json.dumps(paths,indent=2),'utf-8')
    finally: p2.close_canvas()


def main():
    parser=argparse.ArgumentParser(description='게임 점검 증거 수집')
    parser.add_argument('--runtime',action='store_true')
    parser.add_argument('--capture-motions',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.capture_motions:
        motion_sheets(args.capture_motions)
        return 0
    BASE.mkdir(parents=True,exist_ok=True)
    now=datetime.datetime.now(datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=9)))
    run=BASE/'runs'/now.strftime('%Y%m%d-%H%M%S')
    run.mkdir(parents=True,exist_ok=True)
    report={'created_at':now.isoformat(),'checks':[],'human_review':{
        'motion_naturalness':'not_evaluated_by_automation','audio_listening':'not_performed','difficulty':'not_evaluated_by_automation'}}

    def execute(name, arguments, timeout=120):
        try:
            result=subprocess.run([sys.executable,'-X','utf8',*arguments],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
            (run/(name+'.log')).write_text(result.stdout+'\n'+result.stderr,'utf-8')
            check={'name':name,'status':'passed' if result.returncode==0 else 'failed','exit_code':result.returncode,
                   'log':str((run/(name+'.log')).relative_to(ROOT))}
        except (OSError,subprocess.TimeoutExpired) as error:
            check={'name':name,'status':'unverified','reason':str(error)}
        report['checks'].append(check)
        return check

    execute('tests',['-m','unittest','discover','-s','tests','-v'])
    report['style_runs']=style_runs()
    report['checks'].append({'name':'three_style_runs','status':'passed' if all(r['state']=='clear' for r in report['style_runs']) else 'failed'})
    try:
        metrics=audio_metrics()
        report['audio']=metrics
        from bladegame.config import SOUND_FILES
        required=set(SOUND_FILES.values())
        present={m['file'] for m in metrics}
        report['checks'].append({'name':'audio_metrics','status':'passed' if required<=present and all(m['peak_dbfs']<=-6 for m in metrics) else 'failed'})
    except (OSError,wave.Error) as error:
        report['checks'].append({'name':'audio_metrics','status':'failed','reason':str(error)})
    if args.runtime:
        execute('audio_channels',['tools/audio_channel_check.py','--report',str(run/'audio-channels.json')],30)
        for name,options in [('input',['--input-check']),('ui',['--ui-check']),('loop',['--autoplay','--fast','--frames','18000'])]:
            output=run/(name+'.json')
            check=execute(name,['main.py',*options,'--quiet-check','--capture-dir',str(run/name),'--report',str(output)],150)
            if check['status']=='passed':
                try:
                    result=json.loads(output.read_text('utf-8'))
                    check['result']=result['state']
                    if name=='input': valid=all(result.get('input_check',{}).values()) and len(result.get('input_check',{}))>=7
                    elif name=='ui':valid=all(result.get('ui_check',{}).values()) and len(result.get('ui_check',{}))>=13
                    else:
                        events=result['milestones']
                        valid=(result['state']=='clear' and {e['stage'] for e in events if e['kind']=='stage_entered'}=={1,2,3,4}
                               and sum(e['kind']=='reward_selected' for e in events)==3 and any(e['kind']=='boss_phase' and e['phase']==2 for e in events))
                    if not valid: check['status']='failed'; check['reason']='Required flow evidence missing'
                except (OSError,ValueError,KeyError) as error:
                    check['status']='unverified'; check['reason']=str(error)
        check=execute('motion_frames',['tools/polish_check.py','--capture-motions',str(run/'motions')],60)
        if check['status']=='passed':
            report['motion_sheets']=json.loads((run/'motions'/'index.json').read_text('utf-8'))
        try:
            report['frame_content']=[screen_content(p) for p in (run/'loop').glob('*.png')]
            valid=bool(report['frame_content']) and all(c['nonblank'] for c in report['frame_content'])
            report['checks'].append({'name':'nonblank_game_frames','status':'passed' if valid else 'failed'})
        except (OSError,ValueError,zlib.error) as error:
            report['checks'].append({'name':'nonblank_game_frames','status':'unverified','reason':str(error)})
    else:
        report['checks'].append({'name':'runtime','status':'unverified','reason':'Run with --runtime for SDL input, full loop and motion captures.'})
    statuses={c['status'] for c in report['checks']}
    report['status']='failed' if 'failed' in statuses else 'partial' if 'unverified' in statuses else 'passed'
    payload=json.dumps(report,ensure_ascii=False,indent=2)
    (run/'report.json').write_text(payload,'utf-8')
    (BASE/'latest.json').write_text(payload,'utf-8')
    lines=['# 이번 게임 점검',f'실행: {report["created_at"]}',f'자동 검사: {report["status"]}','','| 검사 | 결과 |','| --- | --- |']
    lines += [f'| {c["name"]} | {c["status"]} |' for c in report['checks']]
    lines += ['','모션 자연스러움·체감 난이도·청취 평가는 자동 통과로 처리하지 않음.','',f'상세 증거: `{run.relative_to(ROOT)}`','',
              '의도·변경 기록: DECISIONS.md / DEVLOG.md. 기획 대비 현황: IMPLEMENTATION_STATUS.md.']
    (BASE/'latest.md').write_text('\n'.join(lines)+'\n','utf-8')
    print(json.dumps({'status':report['status'],'checks':report['checks'],'report':str(BASE/'latest.md')},ensure_ascii=False,indent=2))
    return 0 if report['status']=='passed' or (not args.runtime and 'failed' not in statuses) else 1


if __name__=='__main__': raise SystemExit(main())
