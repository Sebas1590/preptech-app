import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
from iot import lessons  # noqa: E402
from iot.interpreter import simulate  # noqa: E402

client = TestClient(server.app)


@pytest.mark.parametrize("lesson", lessons.LESSONS, ids=lambda l: l["id"])
def test_solution_passes_and_starter_fails(lesson):
    ok = client.post("/api/iot/simulate", json={"code": lesson["solution"], "lesson_id": lesson["id"]}).json()
    assert ok["ok"] and ok["passed"], ok["checks"]
    bad = client.post("/api/iot/simulate", json={"code": lesson["starter"], "lesson_id": lesson["id"]}).json()
    assert not bad["ok"] or not bad["passed"]  # starter vacío: error de "loop sin delay" o checks fallidos


def test_syntax_error_reports_line():
    r = simulate("void setup() {}\nvoid loop() {\n  int x = ;\n}")
    assert not r.ok and r.error_line == 3


def test_loop_without_delay_is_stopped():
    r = simulate("void setup(){}\nvoid loop(){ int a = 1; }")
    assert not r.ok and "delay" in r.error


def test_blink_timeline_and_serial():
    code = "void setup(){pinMode(2,OUTPUT);Serial.begin(9600);}\nvoid loop(){digitalWrite(2,HIGH);Serial.println(\"on\");delay(1000);digitalWrite(2,LOW);delay(1000);}"
    r = simulate(code, duration_ms=4000)
    assert [e["value"] for e in r.events if e["kind"] == "digital"] == [1, 0, 1, 0]
    assert r.serial[0]["text"] == "on"


def test_adc_range_per_board():
    code = "void setup(){}\nvoid loop(){Serial.println(analogRead(A0));delay(1000);}"
    assert simulate(code, "esp32", {"36": 100}, 1500).serial[0]["text"] == "4095"
    assert simulate(code, "arduino-uno", {"14": 100}, 1500).serial[0]["text"] == "1023"


def test_ai_status_never_leaks_key():
    server.store.ui_key, server.store.verified = "sk-test-1234567890abcd", True
    body = client.get("/api/ai/status").json()
    assert body["connected"] and "sk-test-1234567890abcd" not in str(body)
    client.delete("/api/ai/connect")
    assert client.get("/api/ai/status").json()["source"] in (None, "entorno")


def test_chat_requires_connection(monkeypatch):
    monkeypatch.setattr(server.store, "ui_key", None)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    r = client.post("/api/coach/chat", json={"message": "hola"})
    assert r.status_code == 409


def test_chat_rejects_bad_area_and_empty_message():
    assert client.post("/api/coach/chat", json={"message": "hola", "area": "x"}).status_code == 422
