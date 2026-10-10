from pathlib import Path
import os
import shutil
import sys

from pydub import AudioSegment, effects

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))


def get_ffmpeg_path():
    """Return a usable FFmpeg path without requiring it for WAV operations."""
    bundled = RESOURCE_ROOT / "ffmpeg.exe"
    if bundled.is_file():
        return bundled

    if not getattr(sys, "frozen", False):
        local = PROJECT_ROOT / ".venv" / "Scripts" / "ffmpeg.exe"
        if local.is_file():
            ffmpeg_dir = str(local.parent)
            path_entries = os.environ.get("PATH", "").split(os.pathsep)
            if ffmpeg_dir not in path_entries:
                os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            return local

    located = shutil.which("ffmpeg.exe") or shutil.which("ffmpeg")
    return Path(located) if located else None


FFMPEG_PATH = get_ffmpeg_path()
if FFMPEG_PATH is not None:
    AudioSegment.converter = str(FFMPEG_PATH)

def load_fragment(source,start,end):
    audio=AudioSegment.from_file(source)
    return audio[max(0,int(start*1000)):max(1,int(end*1000))]

def prepare(seg):
    if not len(seg): return seg
    try:
        seg=effects.normalize(seg, headroom=2.0)
    except Exception:
        pass
    if seg.dBFS != float('-inf'):
        seg=seg.apply_gain(max(-12,min(12,-20-seg.dBFS)))
    fade_in_ms=min(5,len(seg)//3)
    fade_out_ms=min(12,len(seg)//3)
    if fade_in_ms: seg=seg.fade_in(fade_in_ms)
    if fade_out_ms: seg=seg.fade_out(fade_out_ms)
    return seg

def render_plan(plan,out_path,crossfade_ms=40):
    missing=[step.target_text for step in plan.steps if not step.audio_fragments]
    if missing:
        raise ValueError('Cannot render an incomplete sentence; missing audio for: '+', '.join(missing))
    pieces=[]
    for step in plan.steps:
        for fragment in step.audio_fragments:
            pieces.append(prepare(load_fragment(fragment.source,fragment.start,fragment.end)))
    if not pieces: raise ValueError("No existing audio fragments matched the sentence.")
    result=pieces[0]
    for p in pieces[1:]:
        x=min(crossfade_ms,len(result)//2,len(p)//2)
        result=result.append(p,crossfade=max(0,x))
    p=Path(out_path); p.parent.mkdir(parents=True,exist_ok=True)
    result.export(p,format="wav")
