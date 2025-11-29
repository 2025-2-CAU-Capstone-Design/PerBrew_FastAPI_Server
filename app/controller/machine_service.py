from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.schemas.machine_schema import (
    BrewRequest, MachineRegisterSchema, MachineBrewLog
)
from app.models.machine import Machine
from app.models.recipe import Recipe
from app.models.brew_log import BrewLog
from app.models.user import User
from app.controller.ws_service import ws_manager # WebSocket 매니저 임포트
import json


# 레시피 전송
class MachineController:

    @staticmethod
    async def regist_machine(db: Session, email: str, machine_id: str, payload: MachineRegisterSchema):
        existing = db.query(Machine).filter(Machine.machine_id == machine_id).first()
        if existing:
            # user.user_id 사용
            if existing.email != email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="machine_already_registered_to_another_user"
                )
            existing.nickname = payload.nickname
            db.commit()
            return {"status" : "updated", "machine_id": machine_id }
 
        new_machine = Machine(
            machine_id=machine_id,
            email=email, # user.user_id 사용
            nickname=payload.nickname
            # ip 
            # firmware_version
            # 생략
        )
        db.add(new_machine)
        db.commit()
        return {"status": "registered", "machine_id": machine_id}

    @staticmethod
    async def send_brewing_recipe(db: Session, user: User, machine_id: str, payload: BrewRequest):
        if machine_id not in ws_manager.active_connections or ws_manager.active_connections[machine_id]["machine"] is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="machine_not_connected"
            )
        
        recipe = db.query(Recipe).filter(Recipe.id == payload.recipe_id).first()
        if not recipe:
            raise HTTPException(
                status_code=404, detail="recipe_not_found"
            )
        
        # ESP32 파싱 구조에 맞게 수정
        total_time = 0
        steps_data = []
        if recipe.pouring_steps:
            for step in recipe.pouring_steps:
                pouring_time = int(step.pour_time_s)
                waiting_time = int(step.wait_time_s) if step.wait_time_s else 0
                steps_data.append({
                    "step": step.step_number,
                    "water_g" : float(step.water_g),
                    "technique": step.technique.value if step.technique else "center",
                    "pour_time_s": pouring_time,
                    "wait_time_s": waiting_time
                })
                total_time += pouring_time + waiting_time

        grind_val = 90 # 기본값
        if recipe.grind_level and recipe.grind_level.isdigit():
            grind_val = int(recipe.grind_level)

        command_payload = {
            "type": "RECIPE_DATA", 
            "recipe": {
                "rinsing": recipe.rinsing,
                "water_temperature_c": float(recipe.water_temperature_c),
                "dose_g": float(recipe.dose_g),
                "total_brew_time_s": int(recipe.total_brew_time_s) if recipe.total_brew_time_s else total_time,
                "grind_level": grind_val,
                "grind_microns": recipe.grind_microns if recipe.grind_microns else 600,
                "pouring_steps": steps_data
            }
        }

        success = await ws_manager.send_command_to_machine(machine_id, command_payload)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send command to machine")

        return {"status": "accepted", "machine_id": machine_id, "brew_id": "new_brew_id"}
    

    # 브루잉 시작 요청
    @staticmethod
    async def send_brewing_request(user: User, machine_id: str):
        if (machine_id not in ws_manager.active_connections 
            or ws_manager.active_connections[machine_id]["machine"] is None):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="machine_not_connected"
            )
        
        success = await ws_manager.send_command_to_machine(machine_id, {"type": "START_BREW"})
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send start brew command to machine")
        return {"status": "started", "machine_id": machine_id, "brew_id": "dummy_brew_id"}

    @staticmethod
    async def stop_brewing(user: User, machine_id: str):
        success = await ws_manager.send_command_to_machine(machine_id, {"type": "STOP_BREW"})
        if not success:
             raise HTTPException(status_code=503, detail="Machine not connected")
        return {"status": "stopped", "machine_id": machine_id}


    @staticmethod
    async def create_brew_log(db: Session, user: User, payload: MachineBrewLog):
        new_log = BrewLog(
            user_id=user.user_id,
            recipe_id=payload.recipe_id,
            machine_id=payload.machine_id,
            # result 필드 파싱 필요 (JSON -> DB 컬럼)
            tds= None, # 머신에 탑재 못했음.
            avg_temp=payload.result.temperature_c,
            extraction_yield=None # 계산 필요 시 추가
        )
        db.add(new_log)
        db.commit()
        return {"status": "logged", "log_id": str(new_log.id)}
    