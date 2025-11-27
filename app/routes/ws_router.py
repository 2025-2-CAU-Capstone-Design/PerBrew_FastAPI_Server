from fastapi import APIRouter, HTTPException, status, Depends, Query, WebSocket
from sqlalchemy.orm import Session
from app.core.database import get_db
from controller.users_service import UserController

from schemas.user_schema import (
    UserSignUp,
    UserLogin,
    UserInfoUpdate,
    UserPreferenceUpdate,
    UserPreference,
    UserRead,
    TokenResponse,
    PaginatedBrewLogs,
)
from schemas.machine_schema import (
    BrewRequest,
    PouringStep,
    MachineRecipeSend,
    BeanWeight,
    AppBeanWeightPush,
    MachineRegisterSchema,
    BrewResult,
    MachineBrewLog,
    BrewAccepted,
    RecipeStarted,
    OkResponse,
    BrewPhase,
    BrewingStatusResponse,
    BrewingStoppedResponse,
    RegistrationResponse,
    LogCreatedResponse
)

router = APIRouter()

# @ws_router -> @router 로 변경해야 함
@router.websocket("/brewing/{usr_id}/{machine_id}")
async def brewing_websocket(websocket: WebSocket, machine_id: str, usr_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received from {machine_id} (User: {usr_id}): {data}")
            
            # 에코 응답 (테스트용)
            await websocket.send_json({"status": "received", "data": data})
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        # 연결 종료 처리 등
        await websocket.close()