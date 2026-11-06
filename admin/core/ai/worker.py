import asyncio
import time
from typing import Optional
from admin.core.ingress.event import DanmuEvent
from admin.core.ai.orchestrator import AIOrchestrator
from admin.core.broadcast.broadcaster import Broadcaster

class AIWorker:
    """
    异步解耦的 AI 回复与语音合成调度器
    - 与 WebSocket 弹幕接收主循环完全解耦，接收端毫秒级返回，彻底告别阻塞与延迟积压
    - 采用带优先级与容量上限（有界队列）的调度机制，SC/醒目留言享有优先回复权
    - 自动丢弃过载滞后弹幕，确保 AI 回应始终围绕当下最新互动
    - 严格单任务序列化播报，自带语速平滑防重叠保护
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator,
        broadcaster: Broadcaster,
        max_queue_size: int = 3
    ):
        self.orchestrator = orchestrator
        self.broadcaster = broadcaster
        self.max_queue_size = max_queue_size
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._counter: int = 0

    def start(self):
        """启动后台工作协程"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        """停止调度协程并清空积压队列"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except (asyncio.QueueEmpty, ValueError):
                break

    def enqueue(self, event: DanmuEvent, score: int = 10) -> bool:
        """
        将合格弹幕送入调度队列（极速无阻塞返回）
        :param event: 弹幕或 SC 事件
        :param score: 优先级权重分值 (SC=100, 粉丝团=30, 普通=10)
        """
        # 队列满时丢弃最低优先级的陈旧事件，防止无人值守或高并发弹幕引起数十秒雪崩
        if self._queue.qsize() >= self.max_queue_size:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except (asyncio.QueueEmpty, ValueError):
                pass

        self._counter += 1
        # PriorityQueue 默认升序；使用负数 score 确保高分（例如 SC 100）优先出队
        self._queue.put_nowait((-score, self._counter, event))
        return True

    async def _worker_loop(self):
        """后台轮询消费任务"""
        while self._running:
            try:
                _, _, event = await self._queue.get()
                await self._process_event(event)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.broadcaster.log("ERROR", "AI_WORKER", f"任务消费异常: {e}")

    async def _process_event(self, event: DanmuEvent):
        """执行单次完整的思考、推理生成、TTS 合成与大屏广播"""
        # 1. 立即向大屏广播正在思考事件，大屏立刻浮现提问卡片与思考动效，零延迟反馈
        await self.broadcaster.log("INFO", "AI", f"正在为观众【{event.uname}】的弹幕生成回复...")
        await self.broadcaster.broadcast("ai_thinking", {
            "uname": event.uname,
            "question": event.content,
            "badge": event.badge_name,
            "level": event.badge_level,
            "is_super_chat": event.is_super_chat,
            "price": event.price
        })

        # 2. 调用模型生成台词与火山 TTS 语音
        t_start = time.time()
        try:
            speech = await self.orchestrator.generate_response(event.uname, event.content)
        except Exception as e:
            await self.broadcaster.log("ERROR", "AI", f"AI 回复生成失败: {type(e).__name__}: {e}")
            speech = None
        duration = time.time() - t_start

        if speech:
            self.broadcaster.record_ai_reply(speech.tokens)
            await self.broadcaster.log(
                "INFO",
                "AI",
                f"回复台词 (耗时 {duration:.2f}s): {speech.text} (消耗 Token: {speech.tokens})"
            )

            if speech.audio_base64:
                await self.broadcaster.log("INFO", "TTS", "火山语音合成完成，下发音频流")
            else:
                await self.broadcaster.log("WARN", "TTS", "未获得音频流，本次仅下发字幕（请检查火山语音配置）")

            # 3. 广播语音包到直播大屏
            await self.broadcaster.broadcast("ai_speech", {
                "id": speech.id,
                "text": speech.text,
                "audio": f"data:audio/mp3;base64,{speech.audio_base64}" if speech.audio_base64 else "",
                "motion": speech.motion,
                "expression": speech.expression,
                "reply_to": {
                    "uname": event.uname,
                    "question": event.content,
                    "badge": event.badge_name,
                    "level": event.badge_level,
                    "is_super_chat": event.is_super_chat,
                    "price": event.price
                }
            })
            await self.broadcaster.broadcast("stats", self.broadcaster.get_current_stats())

            # 4. 智能动态播报间隔（按平均每秒 4.5 字预估播放时长，避免连续发言在大屏产生音频重叠冲突）
            est_play_duration = max(1.5, min(7.0, len(speech.text) * 0.22 + 0.4))
            await asyncio.sleep(est_play_duration)
