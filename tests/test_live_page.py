from fastapi.testclient import TestClient
from admin.main import app

def test_live_overlay_html_served():
    with TestClient(app) as client:
        res = client.get("/live/")
        assert res.status_code == 200
        assert "Gemini娘 直播大屏" in res.text
        assert "live2dcubismcore" in res.text

def test_live_bgm_static_audio_served():
    with TestClient(app) as client:
        res = client.get("/live/bgm/bgm_01.mp3")
        assert res.status_code == 200
        assert len(res.content) > 1000000

def test_api_bgm_control():
    with TestClient(app) as client:
        res = client.post("/api/bgm/control", json={"action": "next", "payload": "下一首"})
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

def test_api_music_endpoints():
    with TestClient(app) as client:
        # 1. 歌单解析
        pl_res = client.get("/api/music/playlist")
        assert pl_res.status_code == 200
        assert "playlist" in pl_res.json()

        # 2. 在线搜索点歌
        s_res = client.get("/api/music/search?keyword=晴天")
        assert s_res.status_code == 200
        assert "status" in s_res.json()

