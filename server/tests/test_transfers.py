import time
import pytest
from pathlib import Path
from transfers import TransferStore, MAX_AGE_SECONDS


@pytest.fixture
def store(tmp_path, monkeypatch):
    import transfers
    monkeypatch.setattr(transfers, "TRANSFER_DIR", tmp_path)
    return TransferStore()


@pytest.mark.asyncio
async def test_save_writes_file(store, tmp_path):
    await store.save("abc", "photo.jpg", "device-1", b"image data")
    assert (tmp_path / "abc_photo.jpg").exists()


@pytest.mark.asyncio
async def test_get_returns_metadata(store):
    await store.save("abc", "photo.jpg", "device-1", b"data")
    meta = store.get("abc")
    assert meta["filename"] == "photo.jpg"
    assert meta["target"] == "device-1"
    assert "path" in meta


@pytest.mark.asyncio
async def test_get_unknown_returns_none(store):
    assert store.get("unknown") is None


@pytest.mark.asyncio
async def test_delete_removes_file_and_metadata(store, tmp_path):
    await store.save("abc", "photo.jpg", "device-1", b"data")
    await store.delete("abc")
    assert not (tmp_path / "abc_photo.jpg").exists()
    assert store.get("abc") is None


@pytest.mark.asyncio
async def test_delete_unknown_does_not_raise(store):
    await store.delete("nonexistent")  # must not raise


@pytest.mark.asyncio
async def test_cleanup_removes_expired_file(store, tmp_path):
    await store.save("old", "old.txt", "device-1", b"data")
    store._meta["old"]["created"] = time.time() - MAX_AGE_SECONDS - 1
    await store.cleanup_old()
    assert store.get("old") is None
    assert not (tmp_path / "old_old.txt").exists()


@pytest.mark.asyncio
async def test_cleanup_keeps_fresh_file(store):
    await store.save("new", "new.txt", "device-1", b"data")
    await store.cleanup_old()
    assert store.get("new") is not None


@pytest.mark.asyncio
async def test_cleanup_removes_orphaned_disk_files(store, tmp_path):
    orphan = tmp_path / "orphan_file.txt"
    orphan.write_bytes(b"orphan")
    await store.cleanup_old()
    assert not orphan.exists()
