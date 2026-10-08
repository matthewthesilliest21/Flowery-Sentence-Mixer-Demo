---Flowery Sentence Mixer Demo---

A desktop sentence mixer using the included Flowery recordings. It searches and recombines recorded audio. It DOES NOT use AI to create missing sound.

Included
- Tkinter desktop GUI
- Flowery voicelines
- CMUdict phoneme lookup via `pronouncing`
- Candidate scoring and assembly explanations
- WAV extraction, normalization, and crossfades via pydub
- Optional WhisperX transcription + alignment importer
- JSON library storage
- CLI sentence builder

Run the included Flowery library

powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py

after building a sentence in the GUI, use **Play latest audio** to listen, **Stop** to end playback, **Save WAV as…** to copy the WAV, or **Save MP3 as…** to export as MP3.

The mixer only renders a sentence when every word has matching audio. Missing words are listed in the assembly plan, and no incomplete WAV is created

Add more voice lines

Put additional `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, or `.aac` files in `input_audio/`. Then install the optional AI requirements and run:

powershell
pip install -r requirements_ai.txt
python index_with_whisperx.py

The indexer skips recordings that already have saved WhisperX results and library fragments

WhisperX supplies word and character timestamps, but it does not provide phone boundaries. To form words from real recorded phonemes, the optional MFA step below is also required.

Build words from phonemes

Install Montreal Forced Aligner in a separate Conda environment; it does not replace the Voice Line Mixer `.venv`. MFA's English acoustic model and dictionary provide phone-level alignments.

First create a transcript review file:

powershell
python index_phones_with_mfa.py --prepare-transcripts

Review `data/phone_transcripts.tsv` and correct any recognition errors before alignment. This matters because the aligner uses the supplied transcript to place phone boundaries.

Then run the phone indexer with MFA available on `PATH` (or pass its executable directly):

powershell
python index_phones_with_mfa.py --mfa-exe .mfa\aligner\Scripts\mfa.exe

The first run downloads the English MFA acoustic, pronunciation, and G2P models, aligns the reviewed transcripts, and updates phrase, word, and phone clips in `data/library.json`. The planner can then build an unrecorded word from its recorded phone sequence.

Only process recordings you own or have permission to edit.

I have no affiliation with Toby Fox and this was made purely for fun. I'm also kind of a medium-experience coder, and it took me a lot of spaggethi code for this.
