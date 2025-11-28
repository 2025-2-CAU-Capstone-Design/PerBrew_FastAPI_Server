from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.controller.ws_service import ws_manager
import json

router = APIRouter()

# [Machine] 커피 머신 연결
@router.websocket("/machine/{machine_id}")
async def websocket_machine_endpoint(websocket: WebSocket, machine_id: str, db: Session = Depends(get_db)):
    await ws_manager.connect_machine(machine_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # 비즈니스 로직은 서비스 계층으로 위임
            await ws_manager.process_machine_message(machine_id, data)
            
    except WebSocketDisconnect:
        ws_manager.disconnect_machine(machine_id)
    except json.JSONDecodeError:
        print(f"[WS Error] Machine {machine_id} sent non-JSON data")
    except Exception as e:
        print(f"[WS Error] Machine {machine_id}: {e}")
        ws_manager.disconnect_machine(machine_id)


# [App] 앱 연결
@router.websocket("/app/{machine_id}/{user_id}")
async def websocket_app_endpoint(websocket: WebSocket, machine_id: str, user_id: str, db: Session = Depends(get_db)):
    await ws_manager.connect_app(machine_id, websocket)
    try:
        while True:
            # 앱은 주로 수신만 하지만, 혹시 보낸다면 무시하거나 핑퐁 처리
            _ = await websocket.receive_json()
            
    except WebSocketDisconnect:
        ws_manager.disconnect_app(machine_id, websocket)
    except Exception as e:
        print(f"[WS Error] App {user_id}: {e}")
        ws_manager.disconnect_app(machine_id, websocket)