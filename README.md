---Flowery Sentence Mixer Demo---

A desktop sentence mixer using the included Flowery recordings. It searches and recombines recorded audio. It DOES NOT use AI to create missing sound.

Included

How to use:

1. Download my project. On its GitHub page, click Code > Download ZIP, then
extract the ZIP

2. Install Python 3.12 64-bit. Open PowerShell or Command Prompt in the
extracted project folder. In file explorer, you can open the folder,
click its address bar, type powershell, and press enter

3. Check the Python version and create the project environment
by running these one after the other:
=======
Tkinter desktop GUI
Flowery voicelines
CMUdict phoneme lookup via pronouncing
Candidate scoring and assembly explanations
WAV extraction, normalization, and crossfades via pydub
Optional WhisperX transcription + alignment importer
JSON library storage
CLI sentence builder
How to use:

Download my project. On its GitHub page, click Code > Download ZIP, then extract the ZIP

Install Python 3.12 64-bit. Open PowerShell or Command Prompt in the extracted project folder. In file explorer, you can open the folder, click its address bar, type powershell, and press enter

Check the Python version and create the project environment by running these one after the other:

py -3.12 --version

py -3.12 -m venv .venv

4. Install the requirements by running these one after the other:

.\.venv\Scripts\python.exe -m pip install --upgrade pip

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

5. Launch the project:

.\.venv\Scripts\python.exe app.py

Or just make a shortcut to app.py.

Enter a sentence, click BUILD, and click Play latest audio.
You can save the result as WAVor mp3. You need FFmpeg to save in mp3

Since you viewer probably just want to make Flowery say silly things,
installing the "AI" requirements isn't needed. The only thing it does
is transcribe the voicelines and stuff, which would be useful if you wanted
to make sentences with custom sounds.



I have no affiliation with Toby Fox and this was made purely for fun. I'm also kind of a medium-experience coder, and it took me a lot of spaggethi code for this.
