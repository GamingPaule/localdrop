from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, dict] = {}

    async def connect(self, device_id: str, websocket: WebSocket, name: str, kind: str):
        self.connections[device_id] = {"ws": websocket, "name": name, "kind": kind}
        await self.broadcast_devices()

    def disconnect(self, device_id: str):
        self.connections.pop(device_id, None)

    async def broadcast_devices(self):
        devices = [
            {"id": k, "name": v["name"], "kind": v["kind"]}
            for k, v in self.connections.items()
        ]
        msg = {"type": "devices", "devices": devices}
        for conn in list(self.connections.values()):
            try:
                await conn["ws"].send_json(msg)
            except Exception:
                pass

    async def send_to(self, device_id: str, message: dict):
        conn = self.connections.get(device_id)
        if conn:
            try:
                await conn["ws"].send_json(message)
            except Exception:
                pass
