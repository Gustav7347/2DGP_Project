"""Make a source-and-assets play bundle; do not include Git or verification captures."""
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DESTINATION=ROOT.parent/'output'/'blade-below-cliff-playable.zip'
TOP=['main.py','run_game.bat','view_motions.bat','requirements.txt','README.md','PRD.md',
     'AGENTS.md','DECISIONS.md','DEVLOG.md','IMPLEMENTATION_STATUS.md','QUALITY_REVIEW.md','PRODUCT_REVIEW.md','MOTION_VFX_PLAN.md','ART_DIRECTION.md','project_planning.pptx','project_presentaion.pptx']
FOLDERS=['bladegame','assets','tests','tools','.agents','prompts']

if __name__=='__main__':
    files=[ROOT/name for name in TOP]
    for folder in FOLDERS:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    DESTINATION.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(DESTINATION,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for file in sorted(files): out.write(file,Path('blade-below-cliff')/file.relative_to(ROOT))
    with zipfile.ZipFile(DESTINATION) as check:
        assert check.testzip() is None
        assert 'blade-below-cliff/assets/player/run-v2.png' in check.namelist()
        assert 'blade-below-cliff/assets/player/run-rig-v1.png' in check.namelist()
        assert 'blade-below-cliff/assets/player/run-rig-v1.json' in check.namelist()
        assert 'blade-below-cliff/assets/player/run-authored-v6.png' in check.namelist()
        for name in ('run-stride-v7.png','parry-braced-v2.png','motion-registration-v7.json','MOTION_GENERATION_V7.md'):
            assert f'blade-below-cliff/assets/player/{name}' in check.namelist()
        for name in ('parry-guard-beat-v3.png','MOTION_GUARD_BEAT_V8.md'):
            assert f'blade-below-cliff/assets/player/{name}' in check.namelist()
        for name in ('run-cycle-v9.png','parry-guard-sweep-v9.png','motion-registration-v9.json','MOTION_V9.md'):
            assert f'blade-below-cliff/assets/player/{name}' in check.namelist()
        assert 'blade-below-cliff/assets/audio/parry-v9-1.wav' in check.namelist()
        for name in ('assets/enemies/sword-parried-v10.png','assets/enemies/sword-parried-v10.json',
                     'assets/environment/supports-v10.png','assets/environment/supports-v10.json','ART_DIRECTION.md','assets/ART_V10.md'):
            assert f'blade-below-cliff/{name}' in check.namelist()
        assert 'blade-below-cliff/assets/ui/health.png' in check.namelist()
        for name in ('spear-parried-clean-v11.png','boss-parried-v11.png','weapons-v11.png',
                     'spear-parried-v11.json','boss-parried-v11.json','weapons-v11.json'):
            assert f'blade-below-cliff/assets/enemies/{name}' in check.namelist()
        assert 'blade-below-cliff/assets/ART_V11.md' in check.namelist()
        assert 'blade-below-cliff/assets/audio/presentation-v2-impact-1.wav' in check.namelist()
        assert 'blade-below-cliff/assets/audio/parry-1-soft.wav' in check.namelist()
        for name in ('Galmuri9.ttf','Galmuri11.ttf','Galmuri11-Bold.ttf','Galmuri-OFL.txt'):
            assert f'blade-below-cliff/assets/fonts/{name}' in check.namelist()
    print(DESTINATION)
    print(len(files),'files;',round(DESTINATION.stat().st_size/1024/1024,2),'MiB; archive verified')
