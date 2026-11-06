import asyncio
import heapq
import time
from typing import Optional
from admin.core.ingress.event import DanmuEvent
from admin.core.ai.orchestrator import AIOrchestrator
from admin.core.broadcast.broadcaster import Broadcaster

class AIWorker:
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
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self):
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
        self._counter += 1
        new_item = (-score, self._counter, event)

        if self._queue.qsize() >= self.max_queue_size:
            try:
                worst_item = max(self._queue._queue, key=lambda x: (x[0], -x[1]))
                if new_item < worst_item:
                    self._queue._queue.remove(worst_item)
                    heapq.heapify(self._queue._queue)
                    self._queue.put_nowait(new_item)
                    return True
                else:
                    return False
            except Exception:
                pass

        self._queue.put_nowait(new_item)
        return True

    async def _worker_loop(self):
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
        await self.broadcaster.log("INFO", "AI", f"正在为观众【{event.uname}】的弹幕生成回复...")
        await self.broadcaster.broadcast("ai_thinking", {
            "uname": event.uname,
            "question": event.content,
            "badge": event.badge_name,
            "level": event.badge_level,
            "is_super_chat": event.is_super_chat,
            "price": event.price
        })

        t_start = time.time()
        try:
            speech = await self.orchestrator.generate_response(event.uname, event.content)
        except Exception as e:
            await self.broadcaster.log("ERROR", "AI", f"AI 回复生成失败: {type(e).__name__}: {e}")
            speech = None
        duration = time.time() - t_start

        if speech and speech.text:
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

            est_play_duration = max(1.5, min(7.0, len(speech.text) * 0.22 + 0.4))
            await asyncio.sleep(est_play_duration)
        else:
            fallback_text = f"欢迎【{event.uname}】来到直播间，雫酱一直在呢~"
            await self.broadcaster.broadcast("ai_speech", {
                "id": f"fallback_{int(time.time())}",
                "text": fallback_text,
                "audio": "",
                "motion": "Wave",
                "expression": "smile",
                "reply_to": {
                    "uname": event.uname,
                    "question": event.content,
                    "badge": event.badge_name,
                    "level": event.badge_level,
                    "is_super_chat": event.is_super_chat,
                    "price": event.price
                }
            })
            await asyncio.sleep(2.0)
