from fastapi.testclient import TestClient
from admin.main import app

def test_admin_html_served():
    with TestClient(app) as client:
        res = client.get("/admin/")
        assert res.status_code == 200
        assert "大肥鱼 AI 主播管理控制台" in res.text
        assert "火山豆包语音" in res.text
        assert "OBS 纯透明通道" in res.text
