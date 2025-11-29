from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.database import get_db
from app.controller.ws_service import ws_manager
from app.core.config import settings
from app.models.user import User
from app.models.machine import Machine
from app.controller.machine_service import MachineController
from app.schemas.machine_schema import MachineBrewLog

import json

router = APIRouter()

# [Machine] 커피 머신 연결
@router.websocket("/machine/{machine_id}")
async def websocket_machine_endpoint(
        websocket: WebSocket, 
        machine_id: str, 
        db: Session = Depends(get_db)
    ):
    await ws_manager.connect_machine(machine_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # 비즈니스 로직은 서비스 계층으로 위임
            msg_type = await ws_manager.process_machine_message(machine_id, data)
            if msg_type == "BREW_DONE":
                await handle_brew_done(machine_id, data, db)
            
    except WebSocketDisconnect:
        ws_manager.disconnect_machine(machine_id)
    except json.JSONDecodeError:
        print(f"[WS Error] Machine {machine_id} sent non-JSON data")
    except Exception as e:
        print(f"[WS Error] Machine {machine_id}: {e}")
        ws_manager.disconnect_machine(machine_id)


# [App] 앱 연결
@router.websocket("/app/{machine_id}")
async def websocket_app_endpoint(
    websocket: WebSocket, 
    machine_id: str, 
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    # JWT 토큰 검증 및 사용자 확인
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_identifier = email

    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect_app(machine_id, websocket)
    try:
        while True:
            # 앱은 주로 수신만 하지만, 혹시 보낸다면 무시하거나 핑퐁 처리
            _ = await websocket.receive_json()
            
    except WebSocketDisconnect:
        ws_manager.disconnect_app(machine_id, websocket)
    except Exception as e:
        print(f"[WS Error] App {user_identifier}: {e}")
        ws_manager.disconnect_app(machine_id, websocket)


async def handle_brew_done(machine_id: str, data: dict, db: Session):
    # 1. 머신 소유자 찾기
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        print(f"[WS] BREW_DONE but machine row not found: {machine_id}")
        return

    user = db.query(User).get(machine.user_id)
    if not user:
        print(f"[WS] BREW_DONE but user not found: machine_id={machine_id}")
        return

    brew_log_payload = MachineBrewLog(
        recipe_id=data["recipe_id"],
        machine_id=machine_id,
        result=data["result"],
    )

    log_result = await MachineController.create_brew_log(db, user, brew_log_payload)

    await ws_manager.broadcast_to_apps(
        machine_id,
        {
            "type": "BREW_LOG_CREATED",
            "machine_id": machine_id,
            "log": log_result,
        },
    )