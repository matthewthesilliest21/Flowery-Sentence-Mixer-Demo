"""Transcribe new recordings with WhisperX and add their fragments to the library."""
import argparse
from pathlib import Path

from voice_mixer.ingest import save_whisperx_result, save_raw_result
from voice_mixer.storage import load_library

ROOT = Path(__file__).resolve().parent
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default=str(ROOT / 'input_audio'))
    parser.add_argument('--library', default=str(ROOT / 'data' / 'library.json'))
    parser.add_argument('--model', default='small')
    parser.add_argument('--language', default='en')
    parser.add_argument('--device', default='auto')
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--force', action='store_true', help='Re-transcribe already indexed recordings')
    args = parser.parse_args()

    input_dir = Path(args.input).resolve()
    library_path = Path(args.library).resolve()
    raw_dir = ROOT / 'data' / 'whisperx_raw'
    if not input_dir.is_dir():
        raise SystemExit(f'Audio input folder not found: {input_dir}')

    files = sorted(p.resolve() for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS)
    if not files:
        raise SystemExit(f'No supported audio files found in {input_dir}')

    existing_sources = {
        str(Path(fragment.source).resolve()).casefold()
        for fragment in load_library(library_path)
        if fragment.kind in {'character', 'word', 'phrase', 'phone'}
    }
    pending = []
    skipped = 0
    for audio_path in files:
        raw_path = raw_dir / f'{audio_path.stem}.json'
        already_indexed = str(audio_path).casefold() in existing_sources
        if not args.force and already_indexed and raw_path.is_file():
            print(f'Skipping already indexed recording: {audio_path.name}')
            skipped += 1
        else:
            pending.append(audio_path)
    if not pending:
        print(f'No new recordings to transcribe ({skipped} already indexed). Use --force to refresh them.')
        return

    try:
        import torch
        import whisperx
    except ImportError as error:
        raise SystemExit('WhisperX is not installed. Run pip install -r requirements_ai.txt') from error

    device = ('cuda' if torch.cuda.is_available() else 'cpu') if args.device == 'auto' else args.device
    compute_type = 'float16' if device == 'cuda' else 'int8'
    model = whisperx.load_model(args.model, device, compute_type=compute_type)
    raw_dir.mkdir(parents=True, exist_ok=True)
    alignment_models = {}

    for audio_path in pending:
        print('Transcribing', audio_path.name)
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, batch_size=args.batch_size, language=args.language)
        language = result['language']
        if language not in alignment_models:
            alignment_models[language] = whisperx.load_align_model(language_code=language, device=device)
        align_model, metadata = alignment_models[language]
        result = whisperx.align(result['segments'], align_model, metadata, audio, device, return_char_alignments=True)
        save_raw_result(result, raw_dir / f'{audio_path.stem}.json')
        count = save_whisperx_result(result, str(audio_path), library_path)
        print('Added', count, 'fragments')


if __name__ == '__main__':
    main()
