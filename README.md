# VoiceLineMixer

A small Windows desktop app that builds sentences from the included Flowey voice recordings. It rearranges recorded audio fragments; it does not synthesize missing speech.

## Run the packaged version

1. Download `VoiceLineMixer-portable.zip` from the project's Releases page.
2. Extract the whole ZIP while keeping its folder structure.
3. Open `VoiceLineMixer.exe`.

Python is not required. The recordings and timing library are included. Built audio is saved under `%LOCALAPPDATA%\VoiceLineMixer\output` so it remains writable if the app is placed in a protected folder.

WAV playback and export work without additional software. MP3 export is enabled when FFmpeg is available on the computer; otherwise, use WAV.

## Run from source

Install Python 3.12, then from this folder run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Enter a sentence, click **BUILD**, and use **Play latest audio**. The plan shows which recordings and time ranges were used. You can save the result as WAV, or as MP3 when FFmpeg is available.

## Build the portable Windows ZIP

Build on Windows with Python 3.12. Install the runtime and build dependencies, then run the build script:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build_portable.ps1
```

The script creates `dist\VoiceLineMixer-portable.zip`. Share that ZIP as a GitHub Release asset. Recipients do not need Python.

This project is fan-made and is not affiliated with Toby Fox.
