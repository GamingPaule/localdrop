import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api(tmp_path, monkeypatch):
    import transfers
    monkeypatch.setattr(transfers, "TRANSFER_DIR", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    import main
    main.store._meta.clear()
    main.manager.connections.clear()
    with TestClient(main.app) as c:
        yield c


def test_root_returns_html(api):
    r = api.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_qr_returns_html(api):
    r = api.get("/qr")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_qr_png_returns_image(api):
    r = api.get("/qr.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_download_nonexistent_returns_404(api):
    r = api.get("/download/does-not-exist")
    assert r.status_code == 404


def test_upload_notifies_target_and_download_works(api, tmp_path):
    with api.websocket_connect("/ws/target-device") as ws:
        ws.send_json({"type": "register", "name": "Phone", "kind": "mobile"})
        ws.receive_json()  # devices broadcast

        r = api.post(
            "/upload",
            data={"target": "target-device", "from_name": "PC"},
            files={"file": ("hello.txt", b"hello world", "text/plain")},
        )
        assert r.status_code == 200
        file_id = r.json()["file_id"]

        msg = ws.receive_json()
        assert msg["type"] == "incoming"
        assert msg["filename"] == "hello.txt"
        assert msg["file_id"] == file_id
        assert msg["from"] == "PC"
        assert msg["size"] == 11

    r2 = api.get(f"/download/{file_id}")
    assert r2.status_code == 200
    assert r2.content == b"hello world"


def test_websocket_device_list_updates_on_connect(api):
    with api.websocket_connect("/ws/d1") as ws1:
        ws1.send_json({"type": "register", "name": "PC", "kind": "pc"})
        msg = ws1.receive_json()
        assert msg["type"] == "devices"
        assert len(msg["devices"]) == 1

        with api.websocket_connect("/ws/d2") as ws2:
            ws2.send_json({"type": "register", "name": "Phone", "kind": "mobile"})
            ws2.receive_json()  # d2 sees [d2]
            update = ws1.receive_json()
            assert len(update["devices"]) == 2
