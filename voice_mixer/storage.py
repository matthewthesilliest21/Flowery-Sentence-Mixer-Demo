import json
import os
from pathlib import Path
from .models import Fragment

def _dedupe(fragments):
    unique=[]; seen=set()
    for fragment in fragments:
        key=(
            fragment.kind, fragment.text,
            os.path.normcase(str(Path(fragment.source).resolve())),
            fragment.start, fragment.end, fragment.confidence, tuple(fragment.phones),
            fragment.left_context, fragment.right_context,
        )
        if key in seen: continue
        seen.add(key); unique.append(fragment)
    return unique

def load_library(path):
    p = Path(path)
    if not p.exists(): return []
    data = json.loads(p.read_text(encoding="utf-8"))
    fragments = [Fragment.from_dict(x) for x in data.get("fragments", [])]

    # WhisperX writes paths relative to the project root. Resolve them from
    # the library location so rendering also works when launched elsewhere.
    root = p.resolve().parent.parent
    for fragment in fragments:
        source = Path(fragment.source)
        if not source.is_absolute():
            source = root / source
        fragment.source = str(source.resolve())

    # A real indexed library can coexist with the demo tones in library.json.
    # Keep the demo fallback for demo-only libraries, but prefer the recordings
    # whenever at least one real audio source is present.
    has_real_audio = any(
        Path(f.source).is_file() and "demo_audio" not in Path(f.source).parts
        for f in fragments
    )
    if has_real_audio:
        fragments = [f for f in fragments if "demo_audio" not in Path(f.source).parts]
    return fragments

def save_library(path, fragments):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    root = p.resolve().parent.parent
    records = []
    for fragment in _dedupe(fragments):
        record = fragment.to_dict()
        source = Path(fragment.source)
        if not source.is_absolute():
            source = root / source
        source = source.resolve()
        try:
            record["source"] = source.relative_to(root).as_posix()
        except ValueError:
            record["source"] = str(source)
        records.append(record)
    p.write_text(json.dumps({"version":1,"fragments":records}, indent=2), encoding="utf-8")
