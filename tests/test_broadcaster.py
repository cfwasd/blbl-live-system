import asyncio
import pytest
from admin.core.broadcast.broadcaster import Broadcaster
from admin.config import OBSConfig
from admin.core.obs.obs_client import OBSClientWrapper

@pytest.mark.asyncio
async def test_broadcaster_subscribe_and_dispatch():
    broadcaster = Broadcaster()
    q = broadcaster.subscribe()

    await broadcaster.broadcast("danmu", {"content": "测试广播"})
    event_type, data = await asyncio.wait_for(q.get(), timeout=1.0)

    assert event_type == "danmu"
    assert data["content"] == "测试广播"

    broadcaster.unsubscribe(q)
    assert len(broadcaster.clients) == 0

@pytest.mark.asyncio
async def test_broadcaster_stats_tracker():
    broadcaster = Broadcaster()
    broadcaster.record_danmu("用户A")
    broadcaster.record_danmu("用户A")
    broadcaster.record_danmu("用户B")
    broadcaster.record_ai_reply(150)
    broadcaster.record_blocked()

    stats = broadcaster.get_current_stats()
    assert stats["danmu_count"] == 3
    assert stats["total_tokens"] == 150
    assert stats["blocked_count"] == 1
    assert stats["top_users"][0]["uname"] == "用户A"
    assert stats["top_users"][0]["count"] == 2

def test_obs_client_wrapper_offline_graceful():
    obs = OBSClientWrapper(OBSConfig(host="127.0.0.1", port=4455, password=""))
    # 当 OBS 未开启时，应优雅返回 False，而不是抛出未捕获崩溃
    status = obs.get_status()
    assert status["connected"] is False
    assert status["streaming"] is False
    assert obs.start_streaming() is False
    assert obs.stop_streaming() is False
