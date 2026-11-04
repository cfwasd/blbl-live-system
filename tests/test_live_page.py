from fastapi.testclient import TestClient
from admin.main import app

def test_live_overlay_html_served():
    with TestClient(app) as client:
        res = client.get("/live/")
        assert res.status_code == 200
        assert "Gemini娘 直播大屏" in res.text
        assert "live2dcubismcore" in res.text
