import asyncio
import os
import time
from pathlib import Path
import aiofiles
import aiofiles.os

# Im Docker-Container /data/transfers; lokal per LOCALDROP_DATA überschreibbar
TRANSFER_DIR = Path(os.environ.get("LOCALDROP_DATA", "/data/transfers"))
MAX_AGE_SECONDS = 86400  # 24 hours


class TransferStore:
    def __init__(self):
        self._meta: dict[str, dict] = {}

    async def save(self, file_id: str, filename: str, target: str, data: bytes):
        safe_name = Path(filename).name  # strip any path separators
        TRANSFER_DIR.mkdir(parents=True, exist_ok=True)
        path = TRANSFER_DIR / f"{file_id}_{safe_name}"
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        self._meta[file_id] = {
            "target": target,
            "filename": safe_name,
            "path": path,
            "created": time.time(),
        }

    def get(self, file_id: str) -> dict | None:
        return self._meta.get(file_id)

    async def delete(self, file_id: str):
        meta = self._meta.pop(file_id, None)
        if meta:
            try:
                await aiofiles.os.remove(meta["path"])
            except FileNotFoundError:
                pass

    async def cleanup_old(self):
        now = time.time()
        expired = [
            fid for fid, m in list(self._meta.items())
            if now - m["created"] > MAX_AGE_SECONDS
        ]
        for fid in expired:
            await self.delete(fid)

        known = {f"{fid}_{m['filename']}" for fid, m in self._meta.items()}
        if TRANSFER_DIR.exists():
            await asyncio.to_thread(self._cleanup_orphans, known)

    def _cleanup_orphans(self, known: set[str]):
        for entry in TRANSFER_DIR.iterdir():
            if entry.name not in known:
                try:
                    entry.unlink()
                except Exception:
                    pass
