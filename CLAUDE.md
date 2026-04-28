# LocalDrop

AirDrop-ähnliches Dateiübertragungs-Tool für das Heimnetz.

## Was wird gebaut

- **server/** — Python FastAPI + WebSocket Relay-Server (läuft als Docker Container auf TrueNAS SCALE)
- **tray/** — Python Windows System-Tray-App (hält WebSocket-Verbindung, empfängt Dateien nach `Desktop\Transfers\`)
- **ui/** — Vanilla-JS Browser-PWA (AirDrop-Bubbles, läuft auf Handy + PC Browser)

## Architektur

```
[Windows PC - Tray App] <--WebSocket--> [TrueNAS SCALE Docker Hub] <--WebSocket--> [Handy - Browser]
```

Alle Transfers laufen über TrueNAS als Relay. Kein direktes P2P.

## Spec & Plan

- Spec: `docs/superpowers/specs/2026-04-28-localdrop-design.md`
- Plan: `docs/superpowers/plans/2026-04-28-localdrop.md` ← **HIER WEITERLESEN**

## Tech Stack

- Server: Python 3.11 · FastAPI · uvicorn · WebSockets · aiofiles · qrcode · python-multipart
- Tray: pystray · Pillow · websockets · httpx · plyer · PyInstaller
- UI: Vanilla JS · CSS · PWA
- Deploy: Docker (TrueNAS) · PyInstaller .exe (Windows)

## Projektstruktur

```
localdrop/
├── server/
│   ├── hub.py                 # WebSocket ConnectionManager
│   ├── transfers.py           # File store / cleanup
│   ├── main.py                # FastAPI app (alle Endpoints)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       ├── conftest.py
│       ├── test_hub.py
│       ├── test_transfers.py
│       └── test_api.py
├── tray/
│   ├── settings.py            # Config laden/speichern
│   ├── client.py              # WebSocket Client + Download
│   ├── notifications.py       # Windows Toast Notifications
│   ├── main.py                # pystray Tray Icon
│   ├── requirements.txt
│   └── build.spec             # PyInstaller
└── ui/
    ├── index.html
    ├── app.js
    ├── style.css
    ├── manifest.json
    └── icon-192.png
```

## Tests

```bash
cd server
pip install -r requirements.txt
pytest tests/ -v
```

asyncio_mode = auto (in server/pytest.ini)
