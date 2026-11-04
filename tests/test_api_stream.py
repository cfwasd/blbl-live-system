import pytest
from fastapi.testclient import TestClient
from admin.main import app

def test_api_config_get():
    with TestClient(app) as client:
        res = client.get("/api/config")
        assert res.status_code == 200
        data = res.json()
        assert "llm" in data
        assert "volc_tts" in data

def test_api_danmu_injection():
    with TestClient(app) as client:
        payload = {"uname": "小测", "content": "测试一下弹幕"}
        res = client.post("/api/test/danmu", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

def test_api_banned_words_crud():
    with TestClient(app) as client:
        res = client.get("/api/banned-words")
        assert res.status_code == 200
        initial_words = res.json()["words"]
        assert isinstance(initial_words, list)

        update_res = client.post("/api/banned-words", json={"words": ["新词1", "新词2"]})
        assert update_res.status_code == 200

        get_res = client.get("/api/banned-words")
        assert "新词1" in get_res.json()["words"]
