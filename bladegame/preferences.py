"""Small local settings file. Invalid data or a read-only disk never stops play."""
from pathlib import Path
import json, math, os

DEFAULTS={'volume':.15,'muted':False,'shake_enabled':True,'hints_enabled':True}


class Preferences:
    def __init__(self,path=None):
        base=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.config'))
        self.path=Path(path) if path is not None else base/'BladeBelowCliff'/'settings.json'

    def load(self):
        values=DEFAULTS.copy()
        try:
            data=json.loads(self.path.read_text('utf-8'))
            if not isinstance(data,dict):return values
            volume=data.get('volume')
            if type(volume) in (int,float) and math.isfinite(volume):values['volume']=max(0.,min(.5,volume))
            for key in ('muted','shake_enabled','hints_enabled'):
                if type(data.get(key)) is bool:values[key]=data[key]
        except (OSError,ValueError,UnicodeError):pass
        return values

    @staticmethod
    def snapshot(renderer):return {key:getattr(renderer,key) for key in DEFAULTS}

    def save(self,renderer):
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.snapshot(renderer),ensure_ascii=False,indent=2),'utf-8')
            temporary.replace(self.path)
            return True
        except OSError:return False
