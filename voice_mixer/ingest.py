from pathlib import Path
from .models import Fragment
from .phonetics import phones_for_word
from .storage import load_library, save_library
from .text import normalize
import json
import os

def char_records(seg): return seg.get('chars') or seg.get('characters') or []

def fragments_from_whisperx(result,source):
    out=[]
    for seg in result.get('segments',[]):
        words=seg.get('words',[])
        if words and seg.get('start') is not None and seg.get('end') is not None:
            text=normalize(seg.get('text',''))
            if text: out.append(Fragment('phrase',text,source,float(seg['start']),float(seg['end']),.9))
        for i,w in enumerate(words):
            raw=w.get('word','').strip(); start=w.get('start'); end=w.get('end')
            if not raw or start is None or end is None: continue
            word=normalize(raw); conf=float(w.get('score',.8) or .8)
            out.append(Fragment('word',word,source,float(start),float(end),conf,phones_for_word(word),words[i-1].get('word','') if i else '',words[i+1].get('word','') if i+1<len(words) else ''))
        for ch in char_records(seg):
            c=normalize(ch.get('char','')); start=ch.get('start'); end=ch.get('end')
            if c and start is not None and end is not None: out.append(Fragment('character',c,source,float(start),float(end),float(ch.get('score',.7) or .7)))
    return out

def save_raw_result(result,path):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,indent=2),encoding='utf-8')

def _source_key(source):
    return os.path.normcase(str(Path(source).resolve()))

def save_whisperx_result(result,source,library_path):
    current=load_library(library_path)
    source_key=_source_key(source)
    has_phone_alignment=any(f.kind=='phone' and _source_key(f.source)==source_key for f in current)

    # Re-indexing a recording should refresh WhisperX fragments instead of
    # appending duplicates. Keep MFA word/phrase timings when phone alignment
    # already exists, since those clips were aligned to the reviewed transcript.
    replace_kinds={'character'} if has_phone_alignment else {'character','word','phrase'}
    current=[f for f in current if not (_source_key(f.source)==source_key and f.kind in replace_kinds)]
    new=fragments_from_whisperx(result,source)
    if has_phone_alignment:
        new=[f for f in new if f.kind=='character']
    save_library(library_path,current+new)
    return len(new)
