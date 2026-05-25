from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.db import get_db
import asyncio, json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active: list[tuple[WebSocket, list[str]]] = []

    async def connect(self, ws: WebSocket, brand_ids: list[str]):
        await ws.accept()
        self.active.append((ws, brand_ids))

    def disconnect(self, ws: WebSocket):
        self.active = [(w, b) for w, b in self.active if w != ws]

    async def broadcast_to(self, brand_id: str, data: dict):
        dead = []
        for ws, ids in self.active:
            if brand_id in ids:
                try:
                    await ws.send_text(json.dumps(data))
                except Exception:
                    dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

manager = ConnectionManager()

@router.websocket('/ws/competitor')
async def competitor_ws(websocket: WebSocket, brand_ids: str):
    """
    Frontend connects: ws://localhost:8000/competitor/ws/competitor?brand_ids=uuid1,uuid2,uuid3
    On new CVI snapshot for any of those brands, pushes updated panel data.
    """
    ids = [b.strip() for b in brand_ids.split(',') if b.strip()][:3]
    await manager.connect(websocket, ids)
    db = get_db()
    try:
        while True:
            # Poll latest snapshots for all brands every 3s
            # (Supabase Python client doesn't support server-side WS push to FastAPI directly)
            panel = []
            for bid in ids:
                snap = db.table('cvi_snapshots')\
                    .select('score, level, is_anomaly, recorded_at')\
                    .eq('brand_id', bid)\
                    .order('recorded_at', desc=True)\
                    .limit(1).execute().data
                brand = db.table('brands').select('name').eq('id', bid).single().execute()
                panel.append({
                    'brand_id':   bid,
                    'brand_name': brand.data['name'] if brand.data else bid[:8],
                    **( snap[0] if snap else {'score': 0, 'level': 'LOW', 'is_anomaly': False})
                })
            await websocket.send_text(json.dumps({'panel': panel}))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
