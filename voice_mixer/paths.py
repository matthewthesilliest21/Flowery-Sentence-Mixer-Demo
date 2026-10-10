from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))

if getattr(sys, "frozen", False):
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    APP_DATA_ROOT = local_app_data / "VoiceLineMixer"
else:
    APP_DATA_ROOT = PROJECT_ROOT

LIBRARY_PATH = RESOURCE_ROOT / "data" / "library.json"
OUTPUT_PATH = APP_DATA_ROOT / "output" / "gui_result.wav"
