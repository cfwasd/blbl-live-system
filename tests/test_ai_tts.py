import pytest
from admin.config import AppConfig, LLMConfig, VolcengineTTSConfig
from admin.core.ai.llm_client import LLMClient
from admin.core.tts.volcengine_client import VolcengineTTSClient
from admin.core.ai.orchestrator import AIOrchestrator, extract_emotion

def test_extract_emotion():
    # 显式标签提取
    text, motion, exp = extract_emotion("[开心] 欢迎来到直播间！")
    assert text == "欢迎来到直播间！"
    assert motion == "Happy"
    assert exp == "smile"

    text2, motion2, exp2 = extract_emotion("[害羞] 谁、谁是笨蛋呀！")
    assert text2 == "谁、谁是笨蛋呀！"
    assert motion2 == "Shy"
    assert exp2 == "blush"

    text3, motion3, exp3 = extract_emotion("[思考] 唔...让我想想看呢")
    assert text3 == "唔...让我想想看呢"
    assert motion3 == "Think"
    assert exp3 == "think"

    # 隐式情感推断
    text4, motion4, exp4 = extract_emotion("哈哈太棒了，今天好开心！")
    assert motion4 == "Happy"
    assert exp4 == "smile"

    text5, motion5, exp5 = extract_emotion("为什么会这样呢？好奇")
    assert motion5 == "Think"
    assert exp5 == "think"

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

@pytest.mark.asyncio
async def test_ai_orchestrator_multi_turn_context():
    app_cfg = AppConfig()
    orchestrator = AIOrchestrator(app_cfg, max_history_turns=3)

    # 1. 初始空历史，仅包含 System Prompt 与当前用户
    init_msgs = orchestrator.build_messages("小明", "今天播什么")
    assert len(init_msgs) == 2
    assert init_msgs[0]["role"] == "system"
    assert init_msgs[1]["content"] == "观众【小明】说：今天播什么"

    # 2. 生成第 1 轮回复后，历史队列应当包含该记录
    await orchestrator.generate_response("小明", "今天播什么")
    assert len(orchestrator.dialogue_history) == 1
    assert orchestrator.dialogue_history[0]["uname"] == "小明"

    # 3. 构造第 2 轮 messages，应当包含上一轮的 user 与 assistant
    msgs_round2 = orchestrator.build_messages("小红", "那来首歌吧")
    assert len(msgs_round2) == 4
    assert msgs_round2[1]["role"] == "user"
    assert "今天播什么" in msgs_round2[1]["content"]
    assert msgs_round2[2]["role"] == "assistant"
    assert msgs_round2[3]["content"] == "观众【小红】说：那来首歌吧"

    # 4. 连续多轮互动，滑窗上限自动限制为 3 轮
    for i in range(5):
        await orchestrator.generate_response(f"观众{i}", f"弹幕{i}")
    assert len(orchestrator.dialogue_history) == 3

    # 5. 清空历史
    orchestrator.clear_history()
    assert len(orchestrator.dialogue_history) == 0
