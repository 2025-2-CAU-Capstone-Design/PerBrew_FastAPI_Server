"""
Not started	Machine	Request Brewing	성공 시 recipe 송신	
POST	/{machine_id}/brew	
App	Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: machine_id string
Body (JSON): { "user_id": "string", "recipe_id": "string" }
Example: { "user_id": "usr_001", "recipe_id": "rcp_abc123" }	200: { "status": "accepted", "machine_id": "string", "brew_id": "string" }
400: { "error": "invalid_request", "message": "..." }
404: { "error": "machine_not_found", "message": "..." }
409: { "error": "brew_in_progress", "message": "..." }
500: { "error": "machine_unavailable", "message": "..." }


Not started	Machine	레시피 송신	머신에 레시피 송신/브루잉 시작	
POST	/{machine_id}/recipe	
Server	Machine	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: machine_id string
Body (JSON): { "recipe_id": "string", "water_temperature_c": number, "dose_g": number, "grind_level": "string", "pouring_steps": [ { "step_no": integer, "water_g": number, "pour_time_s": integer, "technique": "center|spiral_out|pulse" } ] }
Example: { "recipe_id": "rcp_abc123", "water_temperature_c": 92, "dose_g": 18, "grind_level": "medium-fine", "pouring_steps": [ { "step_no": 1, "water_g": 40, "pour_time_s": 20, "technique": "center" } ] }	200: { "status": "started", "machine_id": "string", "brew_id": "string" }
400: { "error": "invalid_recipe", "message": "..." }
404: { "error": "machine_not_found", "message": "..." }
500: { "error": "machine_unavailable", "message": "serial timeout" }


Not started	Machine	원두 무게 송신	서버에 현재 원두 무게를 전송	
POST	/bean_weight	
Machine	Server	
Headers: Content-Type: application/json
Body (JSON): { "machine_id": "string", "bean_weight_g": number }
Example: { "machine_id": "raspi-001", "bean_weight_g": 17.9 }	200: { "status": "ok" }
400: { "error": "invalid_weight", "message": "..." }


Not started	Machine	Post Bean Weight	App에 현재 원두 무게 전송	
POST	/bean_weight	
Server	App	
Headers: Authorization: Bearer <token>
Body (JSON): { "bean_weight_g": number, "timestamp": "ISO-8601" }	200: { "status": "received" }
408: { "error": "no_response", "message": "no weight updates (5 attempts)" }


Not started	Machine	Brewing Status		
GET	/{machine_id}/brewing-status	
Machine	Server	
Path params: machine_id string
Query: brew_id string (optional)
Headers: Authorization: Bearer <token>	200: { "brew_id": "string", "phase": "idle|rinsing|blooming|pouring|done|error", "step_no": integer|null, "elapsed_s": integer, "temperature_c": number|null, "tds": number|null, "progress_pct": integer }
404: { "error": "brew_not_found", "message": "..." }


Not started	Machine	Stop Brewing	App 에서 5회 이상 bea_weight 에 대한 response가 없으면, machine에서 브루잉 종료	
POST	/{machine_id}/stop	
Server	Machine	
Path params: machine_id string
Headers: Authorization: Bearer <token>	200: { "status": "stopped", "machine_id": "string", "brew_id": "string" }
404: { "error": "brew_not_found", "message": "..." }


Not started	Machine	Machine Registration	머신 등록	
POST	/{user_id}/{machine_id}	
Machine	Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: user_id string, machine_id string
Body (JSON): { "nickname": "string|null" }	201: { "user_id": "string", "machine_id": "string", "status": "registered" }
409: { "error": "already_registered", "message": "..." }


Not started	Machine	Create Log	머신 성공 브루잉 결과 로그 저장	
POST	/usr/{usr_id}/log	
Machine	Server	
Headers: Content-Type: application/json
Path params: usr_id string
Body (JSON): { "brew_id": "string", "recipe_id": "string", "result": { "tds": number|null, "temperature_c": number|null, "notes": "string|null" } }	201: { "status": "logged", "log_id": "string" }
400: { "error": "invalid_body", "message": "..." }

"""
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.controller.machine_service import MachineController
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.machine_schema import (
    BrewRequest,           # { user_id, recipe_id }
    MachineRegisterSchema, # 머신 등록
    MachineNicknameUpdate,  # 닉네임 변경
    MachineBrewLog         # 머신 결과 로그
)

router = APIRouter()

# 1) Machine Registration
@router.post("/{machine_id}/register")
async def regist_machine(
    machine_id: str, 
    payload: MachineRegisterSchema,  # MachineRegisterSchema 대신 새로운 스키마 사용
    db: Session = Depends(get_db)
):
    # user_id 파라미터 제거, current_user 전달
    print("machine register request : " + machine_id)
    result = await MachineController.regist_machine(db, payload.email, machine_id, payload)
    if not result:
        raise HTTPException(status_code=500, detail="failed_to_register_machine")
    return result


# 2) 레시피 전송 및 준비 -> ESP32로 레시피 전송 및 무게 측정 모드로 진입
@router.post("/{machine_id}/prepare")
async def prepare_brewing(
    machine_id: str, 
    payload: BrewRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MachineController.send_brewing_recipe(db, current_user, machine_id, payload)


@router.post("/log")
async def create_brew_log(
    payload: MachineBrewLog, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # usr_id 파라미터 제거, current_user 전달
    return await MachineController.create_brew_log(db, current_user, payload)

@router.patch("/{machine_id}/nickname")
async def update_nickname(
    machine_id: str,
    payload: MachineNicknameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MachineController.update_nickname(db, current_user, machine_id, payload)

@router.get('/list')
async def get_machine_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MachineController.get_machine_list(db, current_user)

#############################################################################################
#############################################################################################
# deprecated : 브루잉 요청 API -> ws_router의 웹소켓으로 대체
# 3) Request Brewing
@router.post("/{machine_id}/start")
async def start_brewing(
    machine_id: str,
    current_user: User = Depends(get_current_user)
):
    return await MachineController.send_brewing_request(current_user, machine_id)

# deprecated : 중단 요청 API -> ws_router의 웹소켓으로 대체
# 4) Stop Brewing
@router.post("/{machine_id}/stop")
async def stop_brewing(
    machine_id: str,
    current_user: User = Depends(get_current_user)
):
    return await MachineController.stop_brewing(current_user, machine_id)

