import pytest
from admin.config import AppConfig, LLMConfig, VolcengineTTSConfig
from admin.core.ai.llm_client import LLMClient
from admin.core.tts.volcengine_client import VolcengineTTSClient
from admin.core.ai.orchestrator import AIOrchestrator

def test_volc_tts_request_payload():
    cfg = VolcengineTTSConfig(
        api_key="test-api-key",
        resource_id="seed-tts-2.0",
        speaker="zh_female_vv_uranus_bigtts"
    )
    client = VolcengineTTSClient(cfg)
    headers = client.build_headers()
    assert headers["X-Api-Key"] == "test-api-key"
    assert headers["X-Api-Resource-Id"] == "seed-tts-2.0"
    assert "X-Api-Request-Id" in headers

    payload = client.build_payload("测试台词")
    assert payload["req_params"]["text"] == "测试台词"
    assert payload["req_params"]["speaker"] == "zh_female_vv_uranus_bigtts"
    assert payload["req_params"]["model"] == "seed-tts-2.0-standard"

@pytest.mark.asyncio
async def test_llm_client_mock_when_no_api_key():
    cfg = LLMConfig(api_key="")
    client = LLMClient(cfg)
    reply, tokens = await client.complete("你好")
    assert "Gemini娘" in reply
    assert tokens > 0

@pytest.mark.asyncio
async def test_ai_orchestrator_mock():
    app_cfg = AppConfig()
    orchestrator = AIOrchestrator(app_cfg)
    speech = await orchestrator.generate_response("测试观众", "你好呀")
    assert speech.text != ""
    assert speech.motion == "Wave"
