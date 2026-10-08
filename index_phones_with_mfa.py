"""Align reviewed transcripts and add phone, word, and phrase clips to the library.

Use the Voice Line Mixer Python environment. Pass --mfa-exe to use a separate
MFA environment without changing the system PATH.
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from voice_mixer.models import Fragment
from voice_mixer.phonetics import phones_for_word
from voice_mixer.storage import load_library, save_library
from voice_mixer.text import normalize

ROOT = Path(__file__).resolve().parent
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"}
SILENCE_LABELS = {"", "sil", "silence", "sp", "spn", "pau"}
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
INTERVAL = re.compile(
    rf'intervals\s*\[\d+\]:\s*xmin\s*=\s*({NUMBER})\s*'
    rf'xmax\s*=\s*({NUMBER})\s*text\s*=\s*"((?:[^"]|"")*)"',
    re.MULTILINE,
)


def _transcribed_text(raw_path):
    if not raw_path.is_file():
        return ""
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    return " ".join(segment.get("text", "").strip() for segment in data.get("segments", [])).strip()


def prepare_transcripts(input_dir, transcript_path):
    """Create or append a human-review TSV without replacing prior corrections."""
    input_dir = Path(input_dir)
    transcript_path = Path(transcript_path)
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if transcript_path.exists():
        with transcript_path.open("r", encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                name = (row.get("audio_file") or "").strip()
                if name:
                    existing[name] = row.get("transcript", "")

    missing = []
    for audio_path in sorted(input_dir.iterdir()):
        if audio_path.is_file() and audio_path.suffix.lower() in AUDIO_EXTENSIONS:
            if audio_path.name not in existing:
                raw_path = ROOT / "data" / "whisperx_raw" / f"{audio_path.stem}.json"
                missing.append({"audio_file": audio_path.name, "transcript": _transcribed_text(raw_path)})

    needs_header = not transcript_path.exists()
    with transcript_path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["audio_file", "transcript"], delimiter="\t")
        if needs_header:
            writer.writeheader()
        writer.writerows(missing)
    return len(missing), transcript_path


def _load_transcripts(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        return {
            (row.get("audio_file") or "").strip(): " ".join((row.get("transcript") or "").split())
            for row in csv.DictReader(stream, delimiter="\t")
            if (row.get("audio_file") or "").strip()
        }


def _tier_intervals(textgrid_path, tier_suffix):
    text = Path(textgrid_path).read_text(encoding="utf-8-sig")
    blocks = re.split(r"(?=^\s*item\s+\[\d+\]:)", text, flags=re.MULTILINE)
    found_tier = False
    for block in blocks:
        name = re.search(r'^\s*name\s*=\s*"([^"]*)"', block, re.MULTILINE)
        if not name or not name.group(1).lower().endswith(tier_suffix):
            continue
        found_tier = True
        for match in INTERVAL.finditer(block):
            start, end = float(match.group(1)), float(match.group(2))
            label = match.group(3).replace('""', '"').strip().upper()
            if label.lower() in SILENCE_LABELS or end <= start:
                continue
            yield start, end, label
    if not found_tier:
        raise ValueError(f"No MFA {tier_suffix} tier found in {textgrid_path}")


def _phone_intervals(textgrid_path):
    for start, end, label in _tier_intervals(textgrid_path, "phones"):
        yield start, end, re.sub(r"\d+$", "", label)


def _word_phone_sequence(start, end, phone_intervals):
    midpoint_matches = [
        phone for phone_start, phone_end, phone in phone_intervals
        if start <= (phone_start + phone_end) / 2 <= end
    ]
    return tuple(midpoint_matches)


def _phone_contexts(phone_intervals, word_intervals):
    by_word = {}
    contexts = {}
    for index, (start, end, _phone) in enumerate(phone_intervals):
        midpoint = (start + end) / 2
        word_index = next(
            (i for i, (word_start, word_end, _text) in enumerate(word_intervals)
             if word_start <= midpoint <= word_end),
            None,
        )
        if word_index is None:
            contexts[index] = ("", "")
        else:
            by_word.setdefault(word_index, []).append((index, phone_intervals[index][2]))

    for phones in by_word.values():
        for position, (index, _phone) in enumerate(phones):
            left = phones[position - 1][1] if position else "^"
            right = phones[position + 1][1] if position + 1 < len(phones) else "$"
            contexts[index] = (left, right)
    return contexts


def _source_key(source):
    path = Path(source)
    if not path.is_absolute():
        path = ROOT / path
    return os.path.normcase(str(path.resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(ROOT / "input_audio"))
    parser.add_argument("--transcripts", default=str(ROOT / "data" / "phone_transcripts.tsv"))
    parser.add_argument("--library", default=str(ROOT / "data" / "library.json"))
    parser.add_argument("--work-dir", default=str(ROOT / "data" / "mfa_phone_work"))
    parser.add_argument("--mfa-exe", help="MFA executable path; defaults to MFA_EXE or PATH lookup")
    parser.add_argument("--alignments", help="Import an existing MFA TextGrid directory instead of running alignment")
    parser.add_argument("--prepare-transcripts", action="store_true", help="Create or append the transcript review TSV and exit")
    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    transcript_path = Path(args.transcripts).resolve()
    added, transcript_path = prepare_transcripts(input_dir, transcript_path)
    if args.prepare_transcripts or added:
        print(f"Transcript review file: {transcript_path}")
        if added:
            print(f"Added {added} recording(s) using WhisperX text as a starting point.")
        print("Review and correct every transcript before phone alignment; MFA trusts the supplied words.")
        print("Run this script again after reviewing the TSV to create phone fragments.")
        return

    transcripts = _load_transcripts(transcript_path)
    audio_files = [p for p in sorted(input_dir.iterdir()) if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS]
    ready = [(p, transcripts.get(p.name, "")) for p in audio_files if transcripts.get(p.name, "")]
    skipped = [p.name for p in audio_files if not transcripts.get(p.name, "")]
    if not ready:
        raise SystemExit("No non-empty reviewed transcripts were found.")
    if skipped:
        print("Skipping recordings with blank transcripts: " + ", ".join(skipped))

    if args.alignments:
        aligned = Path(args.alignments).resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        work_root = Path(args.work_dir).resolve() / stamp
        corpus = work_root / "corpus" / "voice"
        corpus.mkdir(parents=True, exist_ok=False)
        for audio_path, transcript in ready:
            shutil.copy2(audio_path, corpus / audio_path.name)
            (corpus / f"{audio_path.stem}.lab").write_text(transcript + "\n", encoding="utf-8")

        mfa_exe = args.mfa_exe or os.environ.get("MFA_EXE") or shutil.which("mfa")
        if not mfa_exe:
            raise SystemExit("MFA was not found. Install/activate the separate MFA environment or pass --mfa-exe.")
        mfa_exe = str(Path(mfa_exe).resolve()) if Path(mfa_exe).exists() else mfa_exe
        env = os.environ.copy()
        # Keep MFA's config/cache/temp files inside this project, and make the
        # conda environment's DLLs available when its Windows entry point starts.
        env["MFA_ROOT_DIR"] = str(ROOT / "data" / "mfa_config")
        mfa_scripts = Path(mfa_exe).parent if Path(mfa_exe).is_absolute() else None
        if mfa_scripts:
            mfa_prefix = mfa_scripts.parent
            path_entries = [str(mfa_scripts), str(mfa_prefix / "Library" / "bin")]
            if env.get("PATH"):
                path_entries.append(env["PATH"])
            env["PATH"] = os.pathsep.join(path_entries)

        aligned = work_root / "aligned"
        mfa_temp = work_root / "mfa_temp"
        mfa_temp.mkdir(parents=True, exist_ok=True)
        for model_type in ("acoustic", "dictionary", "g2p"):
            subprocess.run([mfa_exe, "model", "download", model_type, "english_us_arpa"], cwd=ROOT, env=env, check=True)
        subprocess.run(
            [mfa_exe, "align", "--single_speaker", "--g2p_model_path", "english_us_arpa",
             "--temporary_directory", str(mfa_temp),
             "--output_format", "long_textgrid",
             str(corpus.parent), "english_us_arpa", "english_us_arpa", str(aligned)],
            cwd=ROOT, env=env, check=True,
        )

    if not aligned.is_dir():
        raise SystemExit(f"MFA alignment directory not found: {aligned}")

    audio_by_stem = {audio_path.stem.casefold(): audio_path.resolve() for audio_path, _ in ready}
    transcript_by_source = {audio_path.resolve(): transcript for audio_path, transcript in ready}
    new_fragments = []
    aligned_stems = set()
    for textgrid_path in aligned.rglob("*.TextGrid"):
        source = audio_by_stem.get(textgrid_path.stem.casefold())
        if source is None:
            continue
        intervals = list(_phone_intervals(textgrid_path))
        if not intervals:
            print(f"No non-silence phone intervals found for {source.name}")
            continue
        words = list(_tier_intervals(textgrid_path, "words"))
        contexts = _phone_contexts(intervals, words)
        aligned_stems.add(source.stem.casefold())
        for index, (start, end, phone) in enumerate(intervals):
            left_context, right_context = contexts.get(index, ("", ""))
            new_fragments.append(Fragment("phone", phone, str(source), start, end, .9, (phone,), left_context, right_context))
        for start, end, text in words:
            word = normalize(text)
            if word:
                aligned_phones = _word_phone_sequence(start, end, intervals)
                new_fragments.append(Fragment(
                    "word", word, str(source), start, end, .95,
                    aligned_phones or phones_for_word(word),
                ))
        if words:
            transcript = normalize(transcript_by_source[source])
            if transcript:
                new_fragments.append(Fragment("phrase", transcript, str(source), words[0][0], words[-1][1], .95))

    if not new_fragments:
        raise SystemExit(f"MFA completed, but no phone intervals were imported. Alignment files: {aligned}")
    replaced_sources = {_source_key(str(path.resolve())) for path, _ in ready if path.stem.casefold() in aligned_stems}
    current = load_library(args.library)
    replaceable = {"phone", "word", "phrase"}
    current = [f for f in current if not (f.kind in replaceable and _source_key(f.source) in replaced_sources)]
    save_library(args.library, current + new_fragments)
    counts = {kind: sum(fragment.kind == kind for fragment in new_fragments) for kind in replaceable}
    print(
        f"Imported {counts['phone']} phone, {counts['word']} word, and "
        f"{counts['phrase']} phrase clips from {len(aligned_stems)} recordings."
    )
    print(f"Alignment files: {aligned}")
    print(f"Updated library: {Path(args.library).resolve()}")


if __name__ == "__main__":
    main()
