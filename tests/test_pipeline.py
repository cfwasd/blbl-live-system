import pytest
from admin.core.ingress.event import DanmuEvent
from admin.core.pipeline.pipeline_manager import PipelineManager

def test_pipeline_aho_corasick_filter(tmp_path):
    words_file = tmp_path / "banned.txt"
    words_file.write_text("广告\n外挂\n黑产\n", encoding="utf-8")

    manager = PipelineManager(banned_words_path=str(words_file), cooldown_seconds=5)

    # 命中敏感词
    bad_event = DanmuEvent(uid=1, uname="违规者", content="专业广告引流")
    res1 = manager.process(bad_event)
    assert res1.is_blocked is True
    assert res1.reason == "sensitive_word"

    # 正常弹幕
    good_event = DanmuEvent(uid=2, uname="正常观众", content="主播晚上好呀")
    res2 = manager.process(good_event)
    assert res2.is_blocked is False
    assert res2.score == 10

def test_pipeline_cooldown(tmp_path):
    words_file = tmp_path / "banned.txt"
    words_file.write_text("", encoding="utf-8")

    manager = PipelineManager(banned_words_path=str(words_file), cooldown_seconds=10)

    event1 = DanmuEvent(uid=100, uname="活跃用户", content="第一句话")
    res1 = manager.process(event1)
    assert res1.can_trigger_ai is True

    # 连续发言进入冷却期（大屏仍显示，但不触发 AI 回复）
    event2 = DanmuEvent(uid=100, uname="活跃用户", content="第二句话刷屏")
    res2 = manager.process(event2)
    assert res2.is_blocked is False
    assert res2.can_trigger_ai is False

def test_pipeline_super_chat_bypass_cooldown(tmp_path):
    words_file = tmp_path / "banned.txt"
    words_file.write_text("", encoding="utf-8")

    manager = PipelineManager(banned_words_path=str(words_file), cooldown_seconds=10)
    sc_event = DanmuEvent(uid=100, uname="土豪", content="给你98块", price=98.0, is_super_chat=True)
    res = manager.process(sc_event)
    assert res.score == 100
    assert res.can_trigger_ai is True
