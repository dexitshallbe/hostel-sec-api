from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime import broadcaster

router = APIRouter(tags=["ws"])


@router.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        while True:
            # Keep connection alive; client may also send pings
            _ = await ws.receive_text()
    except WebSocketDisconnect:
        await broadcaster.disconnect(ws)
    except Exception:
        await broadcaster.disconnect(ws)