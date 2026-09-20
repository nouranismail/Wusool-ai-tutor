from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_create_and_join_group_room_over_websocket():
    created = client.post("/api/group/rooms", json={"lesson_id": "math-properties-1"})
    assert created.status_code == 200
    room = created.json()
    assert len(room["code"]) == 6

    host_url = f"/ws/group/{room['code']}?name=teacher&role=host&token={room['host_token']}"
    child_url = f"/ws/group/{room['code']}?name=نور&role=participant"
    with client.websocket_connect(host_url) as host:
        assert host.receive_json()["type"] == "room_state"
        with client.websocket_connect(child_url) as child:
            child_state = child.receive_json()
            assert child_state["participants"] == ["نور"]
            host.receive_json()
            host.send_json({"type": "start"})
            assert host.receive_json()["active"] is True
            question = host.receive_json()
            assert question["type"] == "question"
            assert question["participant"] == "نور"


def test_unknown_group_room_returns_404():
    assert client.get("/api/group/rooms/UNKNOWN").status_code == 404
