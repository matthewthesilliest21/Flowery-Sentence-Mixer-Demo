import math, wave
from pathlib import Path
from .models import Fragment
from .storage import save_library

RATE=22050

def tone(path, freq, duration):
    path.parent.mkdir(parents=True,exist_ok=True); n=int(RATE*duration)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        frames=bytearray()
        for i in range(n):
            t=i/RATE; a=min(1,t/.025,(duration-t)/.04 if duration>t else 0); s=int(0.22*32767*max(0,a)*math.sin(2*math.pi*freq*t)); frames += int(s).to_bytes(2,'little',signed=True)
        w.writeframes(frames)

def create_demo(root, phone_demo=False):
    root=Path(root); audio=root/'demo_audio'; data=root/'data'; data.mkdir(exist_ok=True)
    items=[
      *(([('your','your',190,'word',.22,('Y','UH','R')),('dad','dad',205,'word',.24,('D','AE','D'))] if phone_demo else [('your_dads',"your dad's",220,'phrase',.65,('Y','UH','R','D','AE','D','Z')),('your_dad','your dad',200,'phrase',.52,('Y','UH','R','D','AE','D'))])),
      ('z','z',440,'phone',.12,('Z',)),
      ('s','s',392,'phone',.12,('S',)),
      ('falling','falling',300,'word',.55,('F','AO','L','IH','NG')),
      ('hey_guys','hey guys',170,'phrase',.60,('HH','EY','G','AY','Z')),
      ('im_falling',"i'm falling",280,'phrase',.95,('AY','M','F','AO','L','IH','NG')),
    ]
    fr=[]
    for name,text,freq,kind,dur,phones in items:
        p=audio/f'{name}.wav'; tone(p,freq,dur)
        fr.append(Fragment(kind,text,str(p),0,dur,.95,phones))
    # Keep the disposable tone library separate from real indexed recordings.
    out=data/('phone_demo_library.json' if phone_demo else 'demo_library.json'); save_library(out,fr); return out
