from app.controller.ws_service import ws_manager

def test_start_brewing_flow(client):
    machine_id = "TEST_MACHINE_FLOW"

    with client.websocket_connect(f"/ws/machine/{machine_id}") as machine_ws:
        response = client.post(f"/machine/{machine_id}/stop")
        assert response.status_code == 200

        # 3. 머신 웹소켓으로 명령이 들어왔는지 확인
        command = machine_ws.receive_json()
        assert command["type"] == "STOP_BREW"