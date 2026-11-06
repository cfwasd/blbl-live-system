import asyncio
import pytest
from admin.config import AppConfig
from admin.core.ingress.event import DanmuEvent
from admin.core.ai.orchestrator import AIOrchestrator
from admin.core.broadcast.broadcaster import Broadcaster
from admin.core.ai.worker import AIWorker

@pytest.mark.asyncio
async def test_ai_worker_priority_and_non_blocking():
    app_cfg = AppConfig()
    orchestrator = AIOrchestrator(app_cfg)
    broadcaster = Broadcaster()
    worker = AIWorker(orchestrator, broadcaster, max_queue_size=5)

    processed_events = []
    # 模拟快速处理以加速测试
    async def mock_process(event):
        processed_events.append(event)
    worker._process_event = mock_process

    # 1. 连续入队：普通弹幕先入队，高价值 SC 后入队
    danmu_normal = DanmuEvent(uid=1001, uname="普通观众", content="普通弹幕")
    danmu_sc = DanmuEvent(uid=1002, uname="土豪观众", content="高额醒目留言", is_super_chat=True, price=50.0)

    # 入队应当毫秒级立即返回
    assert worker.enqueue(danmu_normal, score=10) is True
    assert worker.enqueue(danmu_sc, score=100) is True

    # 启动工作协程
    worker.start()
    await asyncio.sleep(0.05)
    await worker.stop()

    # 校验：高优先级 SC 应当优先出队并被处理
    assert len(processed_events) == 2
    assert processed_events[0].uname == "土豪观众"
    assert processed_events[1].uname == "普通观众"

@pytest.mark.asyncio
async def test_ai_worker_queue_bound_drops_old_items():
    app_cfg = AppConfig()
    orchestrator = AIOrchestrator(app_cfg)
    broadcaster = Broadcaster()
    # 队列上限设为 2
    worker = AIWorker(orchestrator, broadcaster, max_queue_size=2)

    # 入队 4 条
    for i in range(4):
        e = DanmuEvent(uid=i + 1, uname=f"观众{i}", content=f"内容{i}")
        worker.enqueue(e, score=10)

    # 队列中应该只有最多 2 条任务，旧任务已被安全淘汰
    assert worker._queue.qsize() <= 2
    await worker.stop()
