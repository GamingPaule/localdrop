import io
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import qrcode
from fastapi import BackgroundTasks, FastAPI, Form, Request, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from hub import ConnectionManager
from transfers import TRANSFER_DIR, TransferStore

manager = ConnectionManager()
store = TransferStore()

UI_DIR = Path(__file__).parent.parent / "ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    TRANSFER_DIR.mkdir(parents=True, exist_ok=True)
    await store.cleanup_old()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


@app.get("/", response_class=FileResponse)
async def root():
    return str(UI_DIR / "index.html")


@app.get("/qr", response_class=HTMLResponse)
async def qr_page(request: Request):
    host = request.headers.get("host", "localhost:8765")
    url = f"http://{host}"
    return HTMLResponse(f"""<!DOCTYPE html>
<html>
<body style="display:flex;flex-direction:column;align-items:center;padding:40px;
             font-family:sans-serif;background:#0d0d1a;color:white;gap:20px;">
  <h2 style="margin:0">LocalDrop</h2>
  <p style="opacity:.7;margin:0">Mit Handy scannen:</p>
  <img src="/qr.png" style="width:256px;height:256px;border-radius:12px;">
  <code style="opacity:.5;font-size:.9em">{url}</code>
</body>
</html>""")


@app.get("/qr.png")
async def qr_image(request: Request):
    host = request.headers.get("host", "localhost:8765")
    url = f"http://{host}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.websocket("/ws/{device_id}")
async def ws_endpoint(websocket: WebSocket, device_id: str):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        name = data.get("name", "Unknown")
        kind = data.get("kind", "pc")
        await manager.connect(device_id, websocket, name, kind)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(device_id)
        await manager.broadcast_devices()


@app.post("/upload")
async def upload(
    file: UploadFile,
    target: str = Form(...),
    from_name: str = Form(...),
):
    file_id = str(uuid.uuid4())
    data = await file.read()
    await store.save(file_id, file.filename, target, data)
    safe_filename = store.get(file_id)["filename"]
    await manager.send_to(target, {
        "type": "incoming",
        "file_id": file_id,
        "filename": safe_filename,
        "size": len(data),
        "from": from_name,
    })
    return {"file_id": file_id}


@app.get("/download/{file_id}")
async def download(file_id: str, background_tasks: BackgroundTasks):
    meta = store.get(file_id)
    if not meta:
        return Response(status_code=404)
    background_tasks.add_task(store.delete, file_id)
    return FileResponse(
        meta["path"],
        media_type="application/octet-stream",
        filename=meta["filename"],
    )
