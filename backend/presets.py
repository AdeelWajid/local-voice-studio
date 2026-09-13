import json
from pathlib import Path
from uuid import uuid4
from backend.config import DATA

DEFAULTS=[('Neutral',[0,0,0,0,0,0,0,0],.6),('Happy',[.8,0,0,0,0,0,.2,.3],.65),('Sad',[0,0,.75,0,0,.45,0,.2],.6),('Calm',[0,0,0,0,0,0,0,.8],.6),('Controlled Anger',[0,.72,.08,0,.12,.05,0,.38],.7)]
def preset_file(): return DATA/'presets.json'
def list_presets():
    path=preset_file()
    if not path.exists(): path.write_text(json.dumps([{'id':str(uuid4()),'name':n,'vector':v,'alpha':a} for n,v,a in DEFAULTS]),encoding='utf8')
    return json.loads(path.read_text(encoding='utf8'))
def save_preset(payload):
    presets=list_presets(); item={'id':str(uuid4()),'name':str(payload.get('name','Custom')).strip()[:100],'vector':payload.get('vector',[0]*8),'alpha':payload.get('alpha',.6)}; presets.append(item); preset_file().write_text(json.dumps(presets,ensure_ascii=False,indent=2),encoding='utf8'); return item
