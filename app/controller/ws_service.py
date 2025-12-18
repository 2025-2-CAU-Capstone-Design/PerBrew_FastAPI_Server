from fastapi import WebSocket
from typing import Dict, List, Any
import json

class ConnectionManager:
    def __init__(self):
        # { "machine_id": { "machine": WebSocket | None, "apps": [{"ws": WebSocket, "user": str}, ...] } }
        self.active_connections: Dict[str, Dict[str, Any]] = {}

    async def connect_machine(self, machine_id: str, websocket: WebSocket):
        # ...existing code...
        await websocket.accept()
        if machine_id not in self.active_connections:
            self.active_connections[machine_id] = {"machine": None, "apps": []}
        
        # 기존 연결 정리
        if self.active_connections[machine_id]["machine"] is not None:
            try:
                await self.active_connections[machine_id]["machine"].close()
            except:
                pass
            
        self.active_connections[machine_id]["machine"] = websocket
        print(f"[WS Service] Machine connected: {machine_id}")

    def set_last_recipe(self, machine_id: str, recipe_id: int):
        if machine_id in self.active_connections:
            self.active_connections[machine_id]["last_recipe_id"] = recipe_id

    # [추가] 레시피 ID 조회
    def get_last_recipe(self, machine_id: str) -> int | None:
        if machine_id in self.active_connections:
            return self.active_connections[machine_id].get("last_recipe_id")
        return None
    
    # [CHANGED] user_email 인자 추가 및 저장 구조 변경 (Dict로 저장)
    async def connect_app(self, machine_id: str, websocket: WebSocket, user_email: str = "Unknown"):
        await websocket.accept()
        if machine_id not in self.active_connections:
            self.active_connections[machine_id] = {"machine": None, "apps": []}
        print(f"[WS Service] Connecting app to machine: {machine_id} (User: {user_email})")
        # WebSocket 객체와 사용자 정보를 함께 저장
        connection_info = {"ws": websocket, "user": user_email}
        self.active_connections[machine_id]["apps"].append(connection_info)
        print(f"[WS Service] App connected to machine: {machine_id} (User: {user_email})")

    def disconnect_machine(self, machine_id: str):
        # ...existing code...
        if machine_id in self.active_connections:
            self.active_connections[machine_id]["machine"] = None
            print(f"[WS Service] Machine disconnected: {machine_id}")

    # [CHANGED] 저장 구조 변경에 따른 연결 해제 로직 수정
    def disconnect_app(self, machine_id: str, websocket: WebSocket):
        if machine_id in self.active_connections:
            apps_list = self.active_connections[machine_id]["apps"]
            # 리스트에서 해당 웹소켓을 가진 항목 찾아서 제거
            for conn in apps_list:
                if conn["ws"] == websocket:
                    apps_list.remove(conn)
                    print(f"[WS Service] App disconnected from: {machine_id} (User: {conn['user']})")
                    break

    #  머신 메시지 처리 로직 (라우터에서 이동)
    async def process_machine_message(self, machine_id: str, data: dict):
        # ...existing code...
        msg_type = data.get("type")
        
        # 1. 로그 및 모니터링
        if msg_type == "LOADCELL_VALUE":
            # 무게 데이터는 너무 빈번하므로 로그 생략 (디버깅 시 주석 해제)
            # print(f"[WS] Weight from {machine_id}: {data}")
            pass
        elif msg_type == "BREW_STATUS":
            print(f"[WS] Status from {machine_id}: {data}")
        elif msg_type == "BREW_DONE":
            print(f"[WS] Brewing Done: {machine_id}")
        else:
            print(f"[WS] Unknown msg from {machine_id}: {data}")

        # 2. 앱들에게 브로드캐스트 (Relay)
        await self.broadcast_to_apps(machine_id, data)
        return msg_type

    # 앱 -> 머신 명령 전달
    async def send_command_to_machine(self, machine_id: str, message: dict):
        # ...existing code...
        if machine_id in self.active_connections:
            machine_ws = self.active_connections[machine_id]["machine"]
            if machine_ws:
                try:
                    await machine_ws.send_json(message)
                    return True
                except Exception as e:
                    print(f"[WS Service] Error sending to machine: {e}")
                    return False
        return False

    # 내부 유틸리티: 브로드캐스트
    # [CHANGED] 저장 구조 변경에 따른 브로드캐스트 로직 수정
    async def broadcast_to_apps(self, machine_id: str, message: dict):
        if machine_id in self.active_connections:
            print(len(self.active_connections[machine_id]["apps"]))
            # apps 리스트의 각 항목은 이제 dict임
            for conn in self.active_connections[machine_id]["apps"][:]:
                app_ws = conn["ws"]
                print(f"[WS Service] Broadcasting to app (User: {conn['user']}) for machine: {machine_id}")
                try:
                    await app_ws.send_json(message)
                except Exception as e:
                    print(f"[WS Service] Error sending to app ({conn['user']}): {e}")

ws_manager = ConnectionManager()