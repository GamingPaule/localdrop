import pytest
from unittest.mock import AsyncMock
from hub import ConnectionManager


@pytest.mark.asyncio
async def test_connect_registers_device():
    m = ConnectionManager()
    ws = AsyncMock()
    await m.connect("d1", ws, "MyPC", "pc")
    assert "d1" in m.connections
    assert m.connections["d1"]["name"] == "MyPC"


@pytest.mark.asyncio
async def test_connect_broadcasts_device_list():
    m = ConnectionManager()
    ws = AsyncMock()
    await m.connect("d1", ws, "MyPC", "pc")
    ws.send_json.assert_called_once()
    msg = ws.send_json.call_args[0][0]
    assert msg["type"] == "devices"
    assert msg["devices"][0] == {"id": "d1", "name": "MyPC", "kind": "pc"}


@pytest.mark.asyncio
async def test_disconnect_removes_device():
    m = ConnectionManager()
    ws = AsyncMock()
    await m.connect("d1", ws, "MyPC", "pc")
    m.disconnect("d1")
    assert "d1" not in m.connections


@pytest.mark.asyncio
async def test_broadcast_notifies_all_devices():
    m = ConnectionManager()
    ws1, ws2 = AsyncMock(), AsyncMock()
    await m.connect("d1", ws1, "PC", "pc")
    await m.connect("d2", ws2, "Phone", "mobile")
    ws1.reset_mock()
    ws2.reset_mock()
    await m.broadcast_devices()
    ws1.send_json.assert_called_once()
    ws2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_send_to_targets_single_device():
    m = ConnectionManager()
    ws1, ws2 = AsyncMock(), AsyncMock()
    await m.connect("d1", ws1, "PC", "pc")
    await m.connect("d2", ws2, "Phone", "mobile")
    ws1.reset_mock()
    ws2.reset_mock()
    await m.send_to("d2", {"type": "incoming", "filename": "photo.jpg"})
    ws2.send_json.assert_called_once_with({"type": "incoming", "filename": "photo.jpg"})
    ws1.send_json.assert_not_called()


@pytest.mark.asyncio
async def test_send_to_unknown_device_does_nothing():
    m = ConnectionManager()
    await m.send_to("nonexistent", {"type": "incoming"})  # must not raise
