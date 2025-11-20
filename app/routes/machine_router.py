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

from fastapi import APIRouter, HTTPException, status, Query
from controller.machine_service import MachineController
from schemas.machine_schema import (
    BrewRequest,           # { user_id, recipe_id }
    MachineRecipeSend,     # 서버 -> 머신 레시피 송신
    BeanWeight,            # 머신 -> 서버 원두 무게
    AppBeanWeightPush,     # 서버 -> 앱 원두 무게 전달
    MachineRegisterSchema, # 머신 등록
    MachineBrewLog         # 머신 결과 로그
)

router = APIRouter()


# --------------------------------------------------
# App -> Server : 브루잉 요청(Request Brewing)
# --------------------------------------------------
@router.post("/{machine_id}/brew")
def request_brewing(machine_id: str, payload: BrewRequest):
    return MachineController.request_brewing(machine_id, payload)


# --------------------------------------------------
# Server -> Machine : 레시피 송신 및 브루잉 시작
# --------------------------------------------------
@router.post("/{machine_id}/recipe")
def send_recipe(machine_id: str, payload: MachineRecipeSend):
    return MachineController.send_recipe(machine_id, payload)


# --------------------------------------------------
# Machine -> Server : 원두 무게 송신
# --------------------------------------------------
@router.post("/bean_weight")
def report_bean_weight(payload: BeanWeight):
    return MachineController.report_bean_weight(payload)


# --------------------------------------------------
# Server -> App : 원두 무게 전달(push)
# --------------------------------------------------
@router.post("/bean_weight/app")
def push_bean_weight(payload: AppBeanWeightPush):
    return MachineController.push_bean_weight(payload)


# --------------------------------------------------
# Machine -> Server : 브루잉 상태 조회
# --------------------------------------------------
@router.get("/{machine_id}/brewing-status")
def brewing_status(machine_id: str, brew_id: str | None = None):
    return MachineController.brewing_status(machine_id, brew_id)


# --------------------------------------------------
# Server -> Machine : 브루잉 중단
# --------------------------------------------------
@router.post("/{machine_id}/stop")
def stop_brewing(machine_id: str):
    return MachineController.stop_brewing(machine_id)


# --------------------------------------------------
# Machine -> Server : 머신 등록
# --------------------------------------------------
@router.post("/{user_id}/{machine_id}")
def register_machine(user_id: str, machine_id: str, payload: MachineRegisterSchema):
    return MachineController.register_machine(user_id, machine_id, payload)


# --------------------------------------------------
# Machine -> Server : 브루잉 결과 로그 저장
# --------------------------------------------------
@router.post("/usr/{usr_id}/log")
def create_brew_log(usr_id: str, payload: MachineBrewLog):
    return MachineController.create_brew_log(usr_id, payload)
