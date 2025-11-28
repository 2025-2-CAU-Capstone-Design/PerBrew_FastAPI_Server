from fastapi import WebSocket
from typing import Dict, List, Any
import json

class ConnectionManager:
    def __init__(self):
        # { "machine_id": { "machine": WebSocket | None, "apps": [WebSocket, ...] } }
        self.active_connections: Dict[str, Dict[str, Any]] = {}

    async def connect_machine(self, machine_id: str, websocket: WebSocket):
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

    async def connect_app(self, machine_id: str, websocket: WebSocket):
        await websocket.accept()
        if machine_id not in self.active_connections:
            self.active_connections[machine_id] = {"machine": None, "apps": []}
        
        self.active_connections[machine_id]["apps"].append(websocket)
        print(f"[WS Service] App connected to machine: {machine_id}")

    def disconnect_machine(self, machine_id: str):
        if machine_id in self.active_connections:
            self.active_connections[machine_id]["machine"] = None
            print(f"[WS Service] Machine disconnected: {machine_id}")

    def disconnect_app(self, machine_id: str, websocket: WebSocket):
        if machine_id in self.active_connections:
            if websocket in self.active_connections[machine_id]["apps"]:
                self.active_connections[machine_id]["apps"].remove(websocket)
                print(f"[WS Service] App disconnected from: {machine_id}")

    # [NEW] 머신 메시지 처리 로직 (라우터에서 이동)
    async def process_machine_message(self, machine_id: str, data: dict):
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
            # TODO: 여기서 DB 저장 서비스 호출 가능 (비동기)
        else:
            print(f"[WS] Unknown msg from {machine_id}: {data}")

        # 2. 앱들에게 브로드캐스트 (Relay)
        await self.broadcast_to_apps(machine_id, data)

    # 앱 -> 머신 명령 전달
    async def send_command_to_machine(self, machine_id: str, message: dict):
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
    async def broadcast_to_apps(self, machine_id: str, message: dict):
        if machine_id in self.active_connections:
            for app_ws in self.active_connections[machine_id]["apps"][:]:
                try:
                    await app_ws.send_json(message)
                except Exception as e:
                    print(f"[WS Service] Error sending to app: {e}")

ws_manager = ConnectionManager()