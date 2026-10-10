# Flowery Sentence Mixer Demo

A small Windows desktop app that searches and recombines the included Flowery voice recordings. It does not synthesize missing speech or use AI to create audio.

## Run the packaged Windows app

1. Download VoiceLineMixer-portable.zip from the repository's Releases page.
2. Extract the entire ZIP, keeping its folder structure.
3. Open VoiceLineMixer.exe.

Python is not required. The recordings and timing library are included. Built audio is saved under %LOCALAPPDATA%\VoiceLineMixer\output.

WAV playback and export work without additional software. MP3 export requires FFmpeg; if it is unavailable, use WAV.

## Run from source

Install Python 3.12 64-bit. In PowerShell, from the project folder, run:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
~~~

Enter a sentence, click BUILD, and use Play latest audio. The plan shows which recordings and time ranges were used. You can save the result as WAV or, when FFmpeg is available, MP3.

The optional transcription dependencies are not needed to use the included recordings. They are for transcribing custom recordings.

## Build the portable Windows ZIP

Build on Windows with Python 3.12. Install the runtime and build dependencies, then run:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build_portable.ps1
~~~

The script creates dist\VoiceLineMixer-portable.zip. Upload that ZIP to a GitHub Release so people can download the packaged app without Python.

This project is fan-made and is not affiliated with Toby Fox.
