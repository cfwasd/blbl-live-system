import asyncio
import time
from collections import Counter, deque
from typing import Set, Tuple, Any, Dict, List

class Broadcaster:
    def __init__(self):
        self.clients: Set[asyncio.Queue] = set()
        self.total_tokens: int = 0
        self.danmu_counter: Counter = Counter()
        self.danmu_count: int = 0
        self.ai_reply_count: int = 0
        self.blocked_count: int = 0
        self.start_time: float = time.time()
        self.logs: deque = deque(maxlen=200)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.clients.discard(q)

    async def broadcast(self, event_type: str, data: Any):
        dead_queues = []
        for q in self.clients:
            try:
                q.put_nowait((event_type, data))
            except asyncio.QueueFull:
                # 背压防护：队列满时丢弃一条旧消息并放入新消息
                try:
                    q.get_nowait()
                    q.put_nowait((event_type, data))
                except Exception:
                    dead_queues.append(q)
        for dq in dead_queues:
            self.clients.discard(dq)

    async def log(self, level: str, tag: str, message: str):
        now_str = time.strftime("%H:%M:%S")
        log_entry = {
            "time": now_str,
            "level": level.upper(),
            "tag": tag,
            "message": message
        }
        self.logs.append(log_entry)
        await self.broadcast("log", log_entry)

    def get_recent_logs(self) -> List[Dict[str, str]]:
        return list(self.logs)

    def record_danmu(self, uname: str):
        self.danmu_count += 1
        self.danmu_counter[uname] += 1

    def record_ai_reply(self, tokens: int):
        self.ai_reply_count += 1
        self.total_tokens += tokens

    def record_blocked(self):
        self.blocked_count += 1

    def get_current_stats(self) -> Dict[str, Any]:
        top5 = [{"rank": idx + 1, "uname": u, "count": c}
                for idx, (u, c) in enumerate(self.danmu_counter.most_common(5))]
        return {
            "total_tokens": self.total_tokens,
            "danmu_count": self.danmu_count,
            "ai_reply_count": self.ai_reply_count,
            "blocked_count": self.blocked_count,
            "top_users": top5,
            "uptime_seconds": int(time.time() - self.start_time)
        }
