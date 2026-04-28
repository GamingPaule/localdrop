import asyncio
import json
import uuid
from pathlib import Path

import httpx
import websockets
import websockets.exceptions


def _device_id() -> str:
    id_file = Path.home() / "AppData" / "Roaming" / "LocalDrop" / "device_id"
    if id_file.exists():
        return id_file.read_text().strip()
    did = str(uuid.uuid4())
    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(did)
    return did


class LocalDropClient:
    def __init__(self, server_url: str, device_name: str, download_folder: Path, on_incoming):
        self.server_url = server_url.rstrip("/")
        self.device_id = _device_id()
        self.device_name = device_name
        self.download_folder = download_folder
        self.on_incoming = on_incoming  # callable(filename: str)
        self._running = False

    def _ws_url(self) -> str:
        return self.server_url.replace("http://", "ws://").replace("https://", "wss://") + f"/ws/{self.device_id}"

    async def run(self):
        self._running = True
        while self._running:
            try:
                async with websockets.connect(self._ws_url(), ping_interval=20) as ws:
                    await ws.send(json.dumps({
                        "type": "register",
                        "name": self.device_name,
                        "kind": "pc",
                    }))
                    async for raw in ws:
                        msg = json.loads(raw)
                        if msg.get("type") == "incoming":
                            asyncio.create_task(self._download(msg))
            except (OSError, websockets.exceptions.WebSocketException):
                if self._running:
                    await asyncio.sleep(5)

    async def _download(self, msg: dict):
        url = f"{self.server_url}/download/{msg['file_id']}"
        self.download_folder.mkdir(parents=True, exist_ok=True)
        dest = self.download_folder / msg["filename"]
        try:
            async with httpx.AsyncClient(timeout=120) as http:
                r = await http.get(url)
                r.raise_for_status()
                dest.write_bytes(r.content)
            self.on_incoming(msg["filename"])
        except Exception as e:
            self.on_incoming(f"Fehler beim Empfangen: {e}")

    def stop(self):
        self._running = False
