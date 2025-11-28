from app.controller.ws_service import ws_manager

def test_websocket_communication(client):
    machine_id = "TEST_MACHINE_001"
    user_id = "TEST_USER_001"

    # 1. 머신 연결 (WebSocket)
    with client.websocket_connect(f"/ws/machine/{machine_id}") as machine_ws:
        
        # 2. 앱 연결 (WebSocket)
        with client.websocket_connect(f"/ws/app/{machine_id}/{user_id}") as app_ws:
            
            # 3. 머신 -> 서버로 데이터 전송
            machine_data = {
                "type": "BREW_STATUS",
                "temperature": 95.5,
                "step": 1
            }
            machine_ws.send_json(machine_data)

            # 4. 앱이 그 데이터를 받았는지 확인
            received_data = app_ws.receive_json()
            assert received_data == machine_data
            assert received_data["type"] == "BREW_STATUS"