import pytest
from fastapi.testclient import TestClient
from admin.main import app

def test_full_pipeline_e2e():
    with TestClient(app) as client:
        # 1. 验证静态资源和模型挂载
        admin_res = client.get("/admin/")
        assert admin_res.status_code == 200

        live_res = client.get("/live/")
        assert live_res.status_code == 200

        model_res = client.get("/models/gemini/gemini.model3.json")
        assert model_res.status_code == 200
        assert "ParamMouthOpenY" in model_res.text

        # 2. 模拟弹幕注入与指令识别 (切歌)
        cmd_res = client.post("/api/test/danmu", json={"uname": "测试者", "content": "切歌"})
        assert cmd_res.status_code == 200

        # 3. 模拟普通弹幕与 AI 回复
        danmu_res = client.post("/api/test/danmu", json={"uname": "小可爱", "content": "主播好呀"})
        assert danmu_res.status_code == 200

        # 4. 模拟房管插播
        speak_res = client.post("/api/broadcast/speak", json={"text": "紧急通告：欢迎新观众"})
        assert speak_res.status_code == 200

        # 5. 校验配置热推
        cfg_res = client.get("/api/config")
        assert cfg_res.status_code == 200
        assert "llm" in cfg_res.json()

        # 6. 校验 OBS 接口
        obs_res = client.get("/api/live/status")
        assert obs_res.status_code == 200
        assert "streaming" in obs_res.json()
