import json
import socket
from pathlib import Path

SETTINGS_PATH = Path.home() / "AppData" / "Roaming" / "LocalDrop" / "config.json"

_DEFAULTS = {
    "server_url": "http://192.168.1.1:8765",
    "device_name": socket.gethostname(),
    "download_folder": str(Path.home() / "Desktop" / "Transfers"),
}


def load() -> dict:
    if not SETTINGS_PATH.exists():
        _write(_DEFAULTS.copy())
        import subprocess
        subprocess.Popen(["notepad.exe", str(SETTINGS_PATH)])
        raise SystemExit("Bitte server_url in der Konfigurationsdatei eintragen und LocalDrop neu starten.")
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {**_DEFAULTS, **data}


def _write(data: dict):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
