import argparse
from pathlib import Path
from voice_mixer.storage import load_library
from voice_mixer.planner import plan_sentence
from voice_mixer.audio import render_plan
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(); p.add_argument('sentence'); p.add_argument('--library',default=str(ROOT/'data/library.json')); p.add_argument('--output',default=str(ROOT/'output/result.wav')); a=p.parse_args()
lib=load_library(a.library)
if not lib: raise SystemExit('Library is empty.')
plan=plan_sentence(a.sentence,lib)
for s in plan.steps:
    if not s.audio_fragments: print(s.target_text,'-> MISSING |',s.reason)
    elif len(s.audio_fragments)==1: print(s.target_text,'->',Path(s.audio_fragments[0].source).name,'|',s.reason)
    else: print(s.target_text,'->','+'.join(f'{Path(f.source).name}:{f.phones[0] if f.phones else f.text}' for f in s.audio_fragments),'|',s.reason)
try:
    render_plan(plan,a.output)
except ValueError as error:
    raise SystemExit(str(error))
print('Wrote',a.output)
