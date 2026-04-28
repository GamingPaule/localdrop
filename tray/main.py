import asyncio
import subprocess
import threading
import webbrowser
from pathlib import Path

from PIL import Image, ImageDraw
import pystray

import settings
from client import LocalDropClient
from notifications import notify


def _make_icon() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill="#4f8ef7")
    d.ellipse([22, 22, 42, 42], fill="#0d0d1a")
    return img


def main():
    try:
        cfg = settings.load()
    except SystemExit as e:
        print(e)
        return

    client = LocalDropClient(
        server_url=cfg["server_url"],
        device_name=cfg["device_name"],
        download_folder=Path(cfg["download_folder"]),
        on_incoming=lambda fname: notify("LocalDrop", f"Empfangen: {fname}"),
    )

    loop = asyncio.new_event_loop()

    def start_client():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.run())

    t = threading.Thread(target=start_client, daemon=True)
    t.start()

    def on_open(icon, item):
        webbrowser.open(cfg["server_url"])

    def on_folder(icon, item):
        folder = cfg["download_folder"]
        Path(folder).mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["explorer", folder])

    def on_quit(icon, item):
        client.stop()
        loop.call_soon_threadsafe(loop.stop)
        icon.stop()

    icon = pystray.Icon(
        "LocalDrop",
        _make_icon(),
        "LocalDrop",
        pystray.Menu(
            pystray.MenuItem("Öffnen", on_open, default=True),
            pystray.MenuItem("Transfers-Ordner", on_folder),
            pystray.MenuItem("Beenden", on_quit),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()
